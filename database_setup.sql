-- Database Setup Script for XAMPP MySQL
-- Loan Approval Prediction Application
-- 
-- Instructions:
-- 1. Open phpMyAdmin (http://localhost/phpmyadmin)
-- 2. Click on "SQL" tab
-- 3. Copy and paste this entire script
-- 4. Click "Go" to execute

-- Create the database
CREATE DATABASE IF NOT EXISTS loan_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Select the database
USE loan_app_db;

-- Create users table
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create loan_predictions table
CREATE TABLE IF NOT EXISTS loan_prediction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    gender INT NOT NULL,
    married INT NOT NULL,
    dependents INT NOT NULL,
    education INT NOT NULL,
    self_employed INT NOT NULL,
    applicant_income FLOAT NOT NULL,
    coapplicant_income FLOAT NOT NULL,
    loan_amount FLOAT NOT NULL,
    loan_amount_term FLOAT NOT NULL,
    credit_history INT NOT NULL,
    property_area INT NOT NULL,
    prediction_result VARCHAR(20) NOT NULL,
    probability FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_prediction_result (prediction_result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Display success message
SELECT 'Database setup completed successfully!' AS Status;
