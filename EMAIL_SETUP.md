# Email Notification Setup Guide

This guide will help you configure Gmail email notifications for loan prediction results.

## How Email Notifications Work

When a logged-in user makes a loan prediction:
- The system automatically sends an email to their registered email address
- Email contains the prediction result (Approved/Rejected)
- Includes loan details and confidence score
- Different email templates for approved vs rejected predictions
- Emails are sent asynchronously in the background (doesn't slow down the app)

## Gmail Setup Instructions

### Step 1: Enable 2-Step Verification

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Click on **Security** in the left sidebar
3. Scroll to **2-Step Verification**
4. Click **Turn on** and follow the instructions

### Step 2: Generate App Password

1. After enabling 2-Step Verification, go back to [Google Account Security](https://myaccount.google.com/security)
2. Scroll down to **2-Step Verification**
3. Click **App passwords** (you may need to sign in again)
4. Click **Select app** → Choose **Mail**
5. Click **Select device** → Choose **Other (Custom name)**
6. Enter a name like "Loan Prediction App"
7. Click **Generate**
8. **Copy the 16-character password** (you won't see it again!)

### Step 3: Update Configuration in app.py

Open `app.py` and update the email configuration:

```python
# Email Configuration - Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-gmail@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'your-16-char-app-password'  # The App Password you generated
app.config['MAIL_DEFAULT_SENDER'] = 'your-gmail@gmail.com'  # Your Gmail address
app.config['MAIL_ASCII_ATTACHMENTS'] = False
```

**Important:**
- Use the **App Password**, NOT your regular Gmail password
- The App Password is 16 characters (may include spaces)
- Keep your App Password secure and don't share it

### Step 4: Test Email Configuration

1. Restart the Flask application
2. Register a new account with your email
3. Make a loan prediction while logged in
4. Check your Gmail inbox for the prediction result email

## Email Templates

### Approved Loan Email
- **Subject:** "Loan Prediction Result: Approved"
- **Header:** Purple gradient with congratulations message
- **Content:** 
  - Approved status in green
  - Loan details (amount, term, income)
  - Confidence score percentage
  - Note about AI-powered prediction

### Rejected Loan Email
- **Subject:** "Loan Prediction Result: Rejected"
- **Header:** Red/pink gradient
- **Content:**
  - Rejected status in red
  - Loan details
  - Confidence score
  - Suggestions for improvement
  - Note about AI-powered prediction

## Troubleshooting

### Issue: "AuthenticationError: Unable to authenticate"

**Solution:**
- Verify you're using the App Password, not regular password
- Make sure 2-Step Verification is enabled
- Regenerate the App Password if needed
- Check that MAIL_USERNAME matches your Gmail address

### Issue: "SMTPServerDisconnected: Connection unexpectedly closed"

**Solution:**
- Check your internet connection
- Verify MAIL_PORT is 587
- Ensure MAIL_USE_TLS is True
- Try restarting the application

### Issue: "Email not received"

**Solution:**
- Check Gmail spam folder
- Verify email address in user profile is correct
- Check Flask application logs for email errors
- Ensure user is logged in when making prediction

### Issue: "Email sending slows down the app"

**Solution:**
- Emails are already sent asynchronously in background threads
- If still experiencing delays, check server resources
- Consider using a dedicated email service like SendGrid for production

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `app.py` to `.gitignore` or use environment variables
   - Consider using `.env` file with python-dotenv

2. **Use environment variables for production:**
```python
import os
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
```

3. **Create a dedicated Gmail account** for the app
   - Don't use your personal Gmail
   - Create a separate account like `yourapp@gmail.com`

4. **Regularly rotate App Passwords**
   - Change App Passwords periodically
   - Revoke old passwords from Google Account settings

## Alternative Email Providers

If you prefer not to use Gmail, you can use other SMTP providers:

### Outlook/Hotmail
```python
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
```

### SendGrid (Recommended for Production)
```python
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = 'your-sendgrid-api-key'
```

### Mailgun
```python
app.config['MAIL_SERVER'] = 'smtp.mailgun.org'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-mailgun-username'
app.config['MAIL_PASSWORD'] = 'your-mailgun-password'
```

## Production Considerations

For production deployment:
- Use a dedicated email service (SendGrid, Mailgun, AWS SES)
- Implement email queue for high-volume sending
- Add email tracking and analytics
- Set up bounce handling and retry logic
- Use environment variables for all credentials
- Implement rate limiting to prevent abuse

## Testing Email Functionality

To test without sending real emails, you can use a test SMTP server:

```python
# For testing only
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 1025  # Test port
app.config['MAIL_USE_TLS'] = False
```

Or use Python's built-in email testing:
```bash
python -m smtpd -n -c DebuggingServer localhost:1025
```

This will print emails to console instead of sending them.
