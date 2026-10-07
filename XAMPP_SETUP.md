# XAMPP MySQL Database Setup Guide

This guide will help you set up the MySQL database for the Loan Approval Prediction application using XAMPP.

## Prerequisites

- XAMPP installed on your system
- XAMPP Apache and MySQL services running

## Step 1: Start XAMPP Services

1. Open XAMPP Control Panel
2. Start the **Apache** service
3. Start the **MySQL** service
4. Ensure both services show as "Running" (green indicator)

## Step 2: Create Database Using phpMyAdmin

### Option A: Using phpMyAdmin (Recommended)

1. Open your web browser
2. Navigate to: `http://localhost/phpmyadmin`
3. Click on the **SQL** tab at the top
4. Copy the entire contents of `database_setup.sql` file
5. Paste it into the SQL query box
6. Click **Go** to execute the script
7. You should see a success message: "Database setup completed successfully!"

### Option B: Manual Database Creation

1. Open phpMyAdmin: `http://localhost/phpmyadmin`
2. Click **New** in the left sidebar
3. Enter database name: `loan_app_db`
4. Select **utf8mb4_unicode_ci** as collation
5. Click **Create**
6. Run the SQL commands from `database_setup.sql` to create tables

## Step 3: Verify Database Creation

1. In phpMyAdmin, you should see `loan_app_db` in the left sidebar
2. Click on it to expand
3. You should see two tables:
   - `user` (for user accounts)
   - `loan_prediction` (for prediction records)

## Step 4: Configure Application

The application is already configured to use MySQL with XAMPP default settings:

**Database Connection String (in app.py):**
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/loan_app_db'
```

**Default XAMPP MySQL Credentials:**
- **Username:** `root`
- **Password:** (empty/blank)
- **Host:** `localhost`
- **Database:** `loan_app_db`

### If Your MySQL Credentials Are Different

If you've changed your MySQL root password or use different credentials, update the connection string in `app.py`:

```python
# Format: mysql+pymysql://username:password@localhost/database_name
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://your_username:your_password@localhost/loan_app_db'
```

## Step 5: Install MySQL Dependencies

Install the required Python packages for MySQL connectivity:

```bash
pip install PyMySQL cryptography
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Step 6: Run the Application

1. Open a terminal/command prompt
2. Navigate to the project directory:
   ```bash
   cd c:\xampp\htdocs\Bank_Project
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to: `http://localhost:5000`

## Troubleshooting

### Issue: "Access denied for user 'root'@'localhost'"

**Solution:** Update the password in the database connection string in `app.py` to match your MySQL root password.

### Issue: "Can't connect to MySQL server"

**Solution:** 
- Ensure MySQL service is running in XAMPP Control Panel
- Check that MySQL is running on port 3306 (default)
- Verify localhost is accessible

### Issue: "Unknown database 'loan_app_db'"

**Solution:** 
- Run the `database_setup.sql` script in phpMyAdmin
- Verify the database was created successfully

### Issue: "ModuleNotFoundError: No module named 'pymysql'"

**Solution:** Install the missing dependencies:
```bash
pip install PyMySQL cryptography
```

## Database Schema

### User Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - Hashed password
- `is_admin` - Admin status (boolean)
- `created_at` - Account creation timestamp

### Loan Prediction Table
- `id` - Primary key
- `user_id` - Foreign key to user table (nullable for guests)
- `gender`, `married`, `dependents`, `education`, `self_employed` - Personal details
- `applicant_income`, `coapplicant_income` - Financial details
- `loan_amount`, `loan_amount_term` - Loan details
- `credit_history` - Credit history status
- `property_area` - Property location
- `prediction_result` - Prediction outcome (Approved/Rejected)
- `probability` - Confidence score
- `created_at` - Prediction timestamp

## Security Notes

1. **Change Default Passwords:** Update the default XAMPP MySQL root password for production
2. **Update SECRET_KEY:** Change the `SECRET_KEY` in `app.py` for production
3. **Database Backups:** Regularly backup your database using phpMyAdmin export feature
4. **Access Control:** Ensure phpMyAdmin is not publicly accessible in production

## Additional Resources

- [XAMPP Documentation](https://www.apachefriends.org/)
- [phpMyAdmin Documentation](https://docs.phpmyadmin.net/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
