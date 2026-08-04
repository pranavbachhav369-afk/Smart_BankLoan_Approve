# LoanPredict AI - Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- XAMPP (for MySQL database)

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure XAMPP MySQL
1. Start XAMPP Control Panel
2. Start Apache and MySQL services
3. Open phpMyAdmin at http://localhost/phpmyadmin
4. The application will automatically create the `bank_project` database

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- `SECRET_KEY`: Generate a random secret key
- `DATABASE_URL`: MySQL connection string (default: `mysql+pymysql://root:@localhost/bank_project`)
- `MAIL_USERNAME`: Your Gmail address
- `MAIL_PASSWORD`: Gmail App-Specific Password (not regular password)
- `GEMINI_API_KEY`: Google Gemini API key from https://makersuite.google.com/app/apikey

### 4. Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

### 5. Create Admin Account
1. Register a new account at `/register`
2. The first registered user automatically becomes admin
3. Or visit `/make-me-admin` after logging in

## MySQL Database Verification

### Verify Database Creation
1. Open phpMyAdmin: http://localhost/phpmyadmin
2. You should see a database named `bank_project`
3. Click on `bank_project` to view tables

### Verify Tables
The following tables should be created automatically:

#### `user` table
- id (INT, Primary Key, Auto Increment)
- username (VARCHAR 80, Unique)
- email (VARCHAR 120, Unique)
- password_hash (VARCHAR 200)
- is_admin (BOOLEAN, Default: FALSE)
- created_at (DATETIME)

#### `predictions` table
- id (INT, Primary Key, Auto Increment)
- user_id (INT, Foreign Key → user.id)
- age (INT)
- income (FLOAT)
- credit_score (INT)
- loan_amount (FLOAT)
- prediction_result (VARCHAR 20)
- prediction_probability (FLOAT)
- created_at (DATETIME)

### Verify User Registration
1. Register a new user in the application
2. Go to phpMyAdmin → `bank_project` → `user` table
3. You should see the new user record with all fields populated

### Verify Prediction Storage
1. Make a loan prediction in the application
2. Go to phpMyAdmin → `bank_project` → `predictions` table
3. You should see the prediction record with all fields populated

### Manual SQL Setup (if needed)
If automatic table creation fails, run the SQL script:
```bash
# In phpMyAdmin, import the file: mysql_setup.sql
# Or run manually in SQL tab:
```

See `mysql_setup.sql` for the complete SQL script.

## Features Implemented

### ✅ Database Storage
- All predictions automatically saved to database
- User authentication and session management
- Proper SQLAlchemy relationships and error handling

### ✅ Real-Time Dashboard
- KPI cards update every 5 seconds from database
- Line chart for approval/rejection trends
- Pie chart for approval vs rejection ratio
- Bar chart for daily prediction volume
- Recent activity feed with instant updates

### ✅ Auto-Refresh
- Dashboard updates automatically every 5 seconds
- Analytics page auto-refreshes every 5 seconds
- No page reload required

### ✅ Google Gemini AI Chatbot
- Professional floating chatbot widget (bottom-right)
- Glassmorphism design matching dashboard
- Typing animation and auto-scroll
- Enter to send, Shift+Enter for new line
- Mobile responsive
- API key stored securely in environment variables

### ✅ API Endpoints
- `/api/dashboard-stats` - Dashboard statistics
- `/api/chart-data` - Chart data
- `/api/recent-activity` - Recent predictions
- `/api/predictions` - All predictions
- `/api/chat` - AI chatbot
- `/api/analytics` - Analytics data
- `/api/public-analytics` - Public aggregated data

## Troubleshooting

### Email Not Working
- Use Gmail App-Specific Password (not regular password)
- Enable 2FA on Gmail
- Create App Password at: https://myaccount.google.com/apppasswords

### Gemini API Not Working
- Get API key from: https://makersuite.google.com/app/apikey
- Ensure API key is set in `.env` file
- Check API key has proper permissions

### Database Errors
- Ensure `instance` directory exists
- Check database file permissions
- For MySQL, ensure XAMPP MySQL is running

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` to random string
- [ ] Set `debug=False` in app.run()
- [ ] Use environment variables for all sensitive data
- [ ] Enable HTTPS
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Set up proper logging
- [ ] Implement rate limiting
- [ ] Add CSRF protection

### Recommended Hosting
- Heroku
- Railway
- AWS EC2
- DigitalOcean
- PythonAnywhere

## Support
For issues, contact:
- Email: pranavbachhav369@gmail.com
- Phone: +91 9529213949 / +91 7447877388
