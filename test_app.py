import importlib
import io
import os
import unittest


class AppDatabaseFlowTests(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        import app as app_module

        self.app_module = importlib.reload(app_module)
        self.app = self.app_module.app
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

        self.ctx = self.app.app_context()
        self.ctx.push()
        self.app_module.db.drop_all()
        self.app_module.db.create_all()

    def tearDown(self):
        self.app_module.db.drop_all()
        self.ctx.pop()

    def test_registration_persists_user(self):
        response = self.client.post('/register', data={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123',
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.app_module.User.query.count(), 1)
        user = self.app_module.User.query.filter_by(username='alice').one()
        self.assertEqual(user.email, 'alice@example.com')

    def test_prediction_and_dashboard_stats_are_persisted(self):
        response = self.client.post('/api/predict', json={
            'gender': 1,
            'married': 1,
            'dependents': 0,
            'education': 0,
            'self_employed': 0,
            'applicant_income': 8000,
            'coapplicant_income': 2000,
            'loan_amount': 50000,
            'loan_amount_term': 360,
            'credit_history': 1,
            'property_area': 2,
        })

        self.assertEqual(response.status_code, 200)
        # ML prediction is persisted in loan_predictions (not prediction_history,
        # which requires a valid application_id).
        self.assertEqual(self.app_module.LoanPrediction.query.count(), 1)

        prediction = self.app_module.LoanPrediction.query.one()
        self.assertEqual(prediction.prediction_result, 'Approved')
        self.assertIsNotNone(prediction.created_at)

        stats_response = self.client.get('/api/dashboard-stats')
        self.assertEqual(stats_response.status_code, 200)
        payload = stats_response.get_json()
        self.assertEqual(payload['total_predictions'], 1)
        self.assertEqual(payload['approved_count'], 1)
        self.assertEqual(payload['rejected_count'], 0)

    def test_prediction_page_uses_ml_prediction_endpoint(self):
        self.client.post('/register', data={
            'username': 'predictuser',
            'email': 'predict@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123',
        }, follow_redirects=False)
        self.client.post('/login', data={
            'username': 'predictuser',
            'password': 'secret123',
        }, follow_redirects=False)

        response = self.client.get('/predict')

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('/api/predict', html)

    def test_workflow_application_creation_and_document_upload(self):
        self.client.post('/register', data={
            'username': 'workflowuser',
            'email': 'workflow@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123',
        }, follow_redirects=False)
        self.client.post('/login', data={
            'username': 'workflowuser',
            'password': 'secret123',
        }, follow_redirects=False)

        create_response = self.client.post('/api/workflow/applications', json={
            'loan_amount': 50000,
            'loan_tenure': 36,
            'applicant_income': 9000,
            'credit_score': 760,
            'loan_purpose': 'Home Purchase',
            'full_name': 'Workflow User',
        })

        self.assertEqual(create_response.status_code, 201)
        payload = create_response.get_json()
        self.assertEqual(payload['status'], 'success')
        self.assertTrue(payload['application_id'])

        application = self.app_module.LoanApplication.query.get(payload['application_id'])
        self.assertIsNotNone(application)
        self.assertEqual(application.application_status, 'Application Submitted')

        document_response = self.client.post(
            f'/api/workflow/applications/{application.application_id}/documents',
            data={
                'document_type': 'income_proof',
                'document_name': 'Salary Slip',
            },
            content_type='multipart/form-data',
            buffered=True,
        )
        self.assertEqual(document_response.status_code, 200)

        self.assertEqual(self.app_module.DocumentRecord.query.count(), 1)

    def test_admin_workflow_stage_update_persists_comment_and_updates_user_view(self):
        self.client.post('/register', data={
            'username': 'adminuser',
            'email': 'admin@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123',
        }, follow_redirects=False)
        self.client.post('/register', data={
            'username': 'borrower',
            'email': 'borrower@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123',
        }, follow_redirects=False)

        self.client.post('/login', data={
            'username': 'borrower',
            'password': 'secret123',
        }, follow_redirects=False)

        create_response = self.client.post('/api/workflow/applications', json={
            'loan_amount': 120000,
            'loan_tenure': 48,
            'applicant_income': 15000,
            'credit_score': 780,
            'loan_purpose': 'Business Expansion',
            'full_name': 'Borrower One',
        })

        self.assertEqual(create_response.status_code, 201)
        application_id = create_response.get_json()['application_id']

        self.client.post('/logout', follow_redirects=False)
        self.client.post('/login', data={
            'username': 'adminuser',
            'password': 'secret123',
        }, follow_redirects=False)

        update_response = self.client.put(
            f'/api/admin/workflow/applications/{application_id}/stage',
            json={
                'stage': 'documents_verification',
                'status': 'Approved',
                'comment': 'Documents verified successfully',
            },
        )

        self.assertEqual(update_response.status_code, 200)
        payload = update_response.get_json()
        self.assertEqual(payload['status'], 'success')

        application = self.app_module.LoanApplication.query.get(application_id)
        self.assertEqual(application.application_status, 'Documents Approved')
        self.assertEqual(application.admin_comment, 'Documents verified successfully')

        workflow = application.workflow
        self.assertEqual(workflow.current_stage, 'documents_verification')
        self.assertEqual(workflow.admin_comment, 'Documents verified successfully')

        comments = self.app_module.AdminComment.query.filter_by(application_id=application_id).all()
        self.assertEqual(len(comments), 1)
        # admin_comments.comment_type is an ENUM column; the stage is mapped to
        # a safe ENUM value ('Correction' for documents_verification).
        self.assertEqual(comments[0].comment_type, 'Correction')
        self.assertEqual(comments[0].comment, 'Documents verified successfully')

    def test_prediction_analytics_use_ml_predictions_not_admin_decisions(self):
        self.client.post('/register', data={
            'username': 'analyst',
            'email': 'analyst@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123',
        }, follow_redirects=False)
        self.client.post('/login', data={
            'username': 'analyst',
            'password': 'secret123',
        }, follow_redirects=False)

        # Create a workflow application so there is an application_id to attach.
        create_response = self.client.post('/api/workflow/applications', json={
            'loan_amount': 80000,
            'loan_tenure': 36,
            'applicant_income': 12000,
            'credit_score': 720,
            'loan_purpose': 'Business Expansion',
            'full_name': 'Analyst User',
        })
        self.assertEqual(create_response.status_code, 201)
        application_id = create_response.get_json()['application_id']

        # Simulate an ML prediction persisted in the loan_predictions table.
        prediction = self.app_module.LoanPrediction(
            user_id=self.app_module.User.query.filter_by(username='analyst').one().id,
            application_id=application_id,
            input_features='{"applicant_income": 12000, "coapplicant_income": 0, "loan_amount": 80000, "credit_score": 720}',
            prediction_result='Approved',
            prediction_probability=0.82,
        )
        self.app_module.db.session.add(prediction)
        self.app_module.db.session.commit()

        # Admin workflow decision REJECTS the application.
        application = self.app_module.LoanApplication.query.get(application_id)
        application.application_status = 'Rejected'
        application.admin_comment = 'Manual rejection by admin'
        self.app_module.db.session.commit()

        # ML analytics must reflect the ML prediction (Approved) and ignore the
        # admin workflow decision (Rejected).
        response = self.client.get('/api/admin/prediction-analytics')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['status'], 'success')
        self.assertEqual(payload['summary']['total_predictions'], 1)
        self.assertEqual(payload['summary']['approved_predictions'], 1)
        self.assertEqual(payload['summary']['rejected_predictions'], 0)

        # Dashboard stats are also ML-only.
        stats_response = self.client.get('/api/dashboard-stats')
        self.assertEqual(stats_response.status_code, 200)
        stats_payload = stats_response.get_json()
        self.assertEqual(stats_payload['approved_count'], 1)
        self.assertEqual(stats_payload['rejected_count'], 0)


if __name__ == '__main__':
    unittest.main()
