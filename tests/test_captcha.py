import unittest
import io
import os
import captcha_util

class CaptchaTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-captcha-key'
        
        import app as app_module
        self.app_module = app_module
        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            self.app_module.db.create_all()

    def tearDown(self):
        with self.app.app_context():
            self.app_module.db.session.remove()
            self.app_module.db.drop_all()

    def test_captcha_util_text_generation(self):
        code = captcha_util.generate_captcha_text(5)
        self.assertEqual(len(code), 5)
        for char in code:
            self.assertIn(char, captcha_util.CAPTCHA_CHARS)

    def test_captcha_util_image_generation(self):
        code = captcha_util.generate_captcha_text(5)
        img_buf = captcha_util.generate_captcha_image(code)
        self.assertIsInstance(img_buf, io.BytesIO)
        content = img_buf.getvalue()
        self.assertTrue(len(content) > 500)
        # Check PNG header signature: \x89PNG\r\n\x1a\n
        self.assertTrue(content.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_captcha_image_endpoint(self):
        with self.client:
            response = self.client.get('/captcha-image')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'image/png')
            self.assertIn('no-cache', response.headers.get('Cache-Control', ''))
            
            with self.client.session_transaction() as sess:
                captcha_code = sess.get('captcha_text')
                self.assertIsNotNone(captcha_code)
                self.assertEqual(len(captcha_code), 5)

    def test_login_fails_with_invalid_captcha(self):
        # Register user
        self.client.post('/register', data={
            'username': 'captchatestuser',
            'email': 'captchatest@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }, follow_redirects=False)

        # Trigger captcha image to populate session
        self.client.get('/captcha-image')

        # Submit incorrect captcha
        response = self.client.post('/login', data={
            'username': 'captchatestuser',
            'password': 'password123',
            'captcha': 'WRONG'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn('Invalid or expired security code (CAPTCHA)', html)

    def test_login_succeeds_with_valid_captcha(self):
        # Register user
        self.client.post('/register', data={
            'username': 'captchasuccessuser',
            'email': 'captchasuccess@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }, follow_redirects=False)

        # Generate captcha in session
        self.client.get('/captcha-image')
        with self.client.session_transaction() as sess:
            valid_code = sess.get('captcha_text')

        # Login with correct captcha code (case-insensitive test)
        response = self.client.post('/login', data={
            'username': 'captchasuccessuser',
            'password': 'password123',
            'captcha': valid_code.lower()
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn('Welcome back', html)

    def test_captcha_single_use_prevents_replay(self):
        # Register user
        self.client.post('/register', data={
            'username': 'replayuser',
            'email': 'replay@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }, follow_redirects=False)

        # Generate captcha
        self.client.get('/captcha-image')
        with self.client.session_transaction() as sess:
            valid_code = sess.get('captcha_text')

        # First login attempt with wrong password but valid captcha consumes the captcha
        self.client.post('/login', data={
            'username': 'replayuser',
            'password': 'wrongpassword',
            'captcha': valid_code
        })

        # Second attempt trying to reuse the same captcha code should fail captcha verification
        response = self.client.post('/login', data={
            'username': 'replayuser',
            'password': 'password123',
            'captcha': valid_code
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn('Invalid or expired security code (CAPTCHA)', html)

if __name__ == '__main__':
    unittest.main()
