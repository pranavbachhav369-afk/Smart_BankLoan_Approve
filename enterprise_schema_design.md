# Enterprise AI Loan Approval Management System - Database Schema Design

## Current Schema Analysis

### Existing Tables:
- `user` - User accounts
- `loan_applications` - Main application data (denormalized)
- `documents` - Document records
- `loan_workflow` - Workflow tracking
- `support_chat` - Chat messages
- `support_tickets` - Support tickets
- `support_replies` - Support replies
- `notifications` - User notifications

## New Normalized Schema

### 1. Applications Table (Modified)
```sql
CREATE TABLE loan_applications (
    application_id VARCHAR(30) PRIMARY KEY,
    user_id INT NOT NULL,
    application_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Personal Information
    full_name VARCHAR(120) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    marital_status ENUM('Single', 'Married', 'Divorced', 'Widowed') NOT NULL,
    dependents INT DEFAULT 0,
    
    -- Contact Information
    email_address VARCHAR(120) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    
    -- Employment Details
    employment_type ENUM('Salaried', 'Self-Employed', 'Business', 'Retired', 'Student') NOT NULL,
    company_name VARCHAR(200),
    employment_status ENUM('Employed', 'Self-Employed', 'Unemployed', 'Retired') NOT NULL,
    work_experience_years DECIMAL(5,2),
    monthly_income DECIMAL(15,2) NOT NULL,
    
    -- Financial Information
    annual_income DECIMAL(15,2) NOT NULL,
    other_income DECIMAL(15,2) DEFAULT 0,
    existing_loans DECIMAL(15,2) DEFAULT 0,
    monthly_debt DECIMAL(15,2) DEFAULT 0,
    credit_score INT,
    credit_history ENUM('Good', 'Fair', 'Poor', 'No History') NOT NULL,
    
    -- Loan Information
    loan_amount DECIMAL(15,2) NOT NULL,
    loan_purpose VARCHAR(200) NOT NULL,
    loan_amount_term INT NOT NULL,
    collateral_type VARCHAR(100),
    collateral_value DECIMAL(15,2),
    
    -- Education
    education_level ENUM('Graduate', 'Post-Graduate', 'Professional', 'Undergraduate', 'Other') NOT NULL,
    
    -- Property Information
    property_area ENUM('Urban', 'Semi-Urban', 'Rural') NOT NULL,
    property_type VARCHAR(100),
    
    -- Status
    application_status ENUM('Application Submitted', 'Documents Pending', 'Documents Approved', 
                           'Risk Analysis Running', 'Waiting for Admin', 'Approved', 'Rejected', 
                           'Need Correction', 'On Hold') DEFAULT 'Application Submitted',
    
    -- Timestamps
    submitted_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

### 2. Aadhaar Documents Table (New)
```sql
CREATE TABLE aadhaar_documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id VARCHAR(30) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    upload_date DATETIME NOT NULL,
    verification_status ENUM('Pending', 'Approved', 'Rejected', 'Query') DEFAULT 'Pending',
    verified_by INT,
    verification_date DATETIME,
    admin_remark TEXT,
    
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (verified_by) REFERENCES user(id)
);
```

### 3. AI Risk Analysis Table (New)
```sql
CREATE TABLE ai_risk_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id VARCHAR(30) NOT NULL,
    
    -- Prediction Results
    prediction_result ENUM('Approved', 'Rejected') NOT NULL,
    approval_probability DECIMAL(5,4) NOT NULL,
    risk_score DECIMAL(5,4) NOT NULL,
    risk_level ENUM('Low', 'Medium', 'High') NOT NULL,
    
    -- Model Information
    model_version VARCHAR(50),
    model_confidence DECIMAL(5,4),
    
    -- Feature Importance
    feature_importance JSON,
    
    -- AI Explanation
    ai_explanation TEXT,
    
    -- Analysis Status
    analysis_status ENUM('Pending', 'Running', 'Completed', 'Failed') DEFAULT 'Pending',
    analyzed_by INT,
    analysis_date DATETIME,
    
    -- Admin Review
    admin_review_status ENUM('Pending', 'Approved', 'Rejected', 'Request Manual Review') DEFAULT 'Pending',
    admin_review_comment TEXT,
    reviewed_by INT,
    review_date DATETIME,
    
    -- Timestamps
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (analyzed_by) REFERENCES user(id),
    FOREIGN KEY (reviewed_by) REFERENCES user(id)
);
```

### 4. Prediction History Table (New - Preserve History)
```sql
CREATE TABLE prediction_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id VARCHAR(30) NOT NULL,
    user_id INT NOT NULL,
    
    -- Historical Prediction Data
    prediction_result ENUM('Approved', 'Rejected') NOT NULL,
    approval_probability DECIMAL(5,4) NOT NULL,
    risk_score DECIMAL(5,4) NOT NULL,
    risk_level ENUM('Low', 'Medium', 'High') NOT NULL,
    
    -- Application Context
    loan_amount DECIMAL(15,2) NOT NULL,
    loan_amount_term INT NOT NULL,
    monthly_income DECIMAL(15,2) NOT NULL,
    credit_score INT,
    
    -- Model Information
    model_version VARCHAR(50),
    prediction_date DATETIME NOT NULL,
    
    -- Comparison Data
    is_current_prediction BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

### 5. Workflow Timeline Table (New)
```sql
CREATE TABLE workflow_timeline (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id VARCHAR(30) NOT NULL,
    
    -- Stage Information
    stage_name ENUM('Application Submitted', 'Documents Verification', 'AI Risk Analysis', 
                   'Previous Prediction Review', 'Final Approval') NOT NULL,
    stage_status ENUM('Pending', 'In Progress', 'Approved', 'Rejected', 'Need Correction', 'Hold') NOT NULL,
    
    -- Stage Details
    started_at DATETIME,
    completed_at DATETIME,
    duration_seconds INT,
    
    -- Admin Actions
    action_by INT,
    admin_comment TEXT,
    
    -- Stage Progress
    progress_percentage INT DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (action_by) REFERENCES user(id)
);
```

### 6. Approval History Table (New)
```sql
CREATE TABLE approval_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id VARCHAR(30) NOT NULL,
    
    -- Decision Information
    decision_type ENUM('Stage Update', 'Document Verification', 'Risk Analysis Review', 
                      'Final Approval', 'Rejection', 'Hold', 'Request Correction') NOT NULL,
    decision ENUM('Approve', 'Reject', 'Hold', 'Request Correction', 'Move Next') NOT NULL,
    
    -- Decision Context
    previous_stage VARCHAR(100),
    new_stage VARCHAR(100),
    decision_reason TEXT,
    
    -- Admin Information
    decided_by INT NOT NULL,
    decision_date DATETIME NOT NULL,
    
    -- Additional Notes
    admin_notes TEXT,
    
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (decided_by) REFERENCES user(id)
);
```

### 7. Admin Comments Table (New)
```sql
CREATE TABLE admin_comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    application_id VARCHAR(30) NOT NULL,
    admin_id INT NOT NULL,
    comment TEXT NOT NULL,
    comment_type ENUM('General', 'Query', 'Correction', 'Approval', 'Rejection') NOT NULL,
    is_visible_to_user BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES user(id)
);
```

### 8. Enhanced Notifications Table (Modified)
```sql
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    application_id VARCHAR(30),
    
    -- Notification Content
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type ENUM('Application Submitted', 'Document Approved', 'Document Rejected', 
                          'Request Document', 'Risk Analysis Completed', 'Stage Update', 
                          'Final Approval', 'Rejection', 'On Hold', 'Correction Required') NOT NULL,
    
    -- Priority
    priority ENUM('Low', 'Medium', 'High', 'Urgent') DEFAULT 'Medium',
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    
    -- Action Link
    action_link VARCHAR(255),
    
    -- Timestamps
    created_at DATETIME NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE
);
```

## Workflow Stages Configuration

### Stage 1: Application Submitted
- Status: Pending → In Progress → Approved
- Actions: Submit application, validate information

### Stage 2: Documents Verification
- Status: Pending → In Progress → Approved/Rejected/Query
- Actions: Upload Aadhaar, verify documents

### Stage 3: AI Risk Analysis
- Status: Pending → Running → Completed
- Actions: Run AI prediction, analyze risk

### Stage 4: Previous Prediction Review
- Status: Pending → In Progress → Approved/Rejected
- Actions: Review historical predictions, compare trends

### Stage 5: Final Approval
- Status: Pending → In Progress → Approved/Rejected/Hold/Need Correction
- Actions: Final decision, approve/reject loan

## Indexes

```sql
-- Performance Indexes
CREATE INDEX idx_applications_user ON loan_applications(user_id);
CREATE INDEX idx_applications_status ON loan_applications(application_status);
CREATE INDEX idx_applications_date ON loan_applications(submitted_at);
CREATE INDEX idx_aadhaar_application ON aadhaar_documents(application_id);
CREATE INDEX idx_risk_analysis_application ON ai_risk_analysis(application_id);
CREATE INDEX idx_prediction_history_user ON prediction_history(user_id);
CREATE INDEX idx_prediction_history_date ON prediction_history(prediction_date);
CREATE INDEX idx_timeline_application ON workflow_timeline(application_id);
CREATE INDEX idx_timeline_stage ON workflow_timeline(stage_name);
CREATE INDEX idx_approval_history_application ON approval_history(application_id);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
```

## Migration Strategy

1. Create new tables
2. Migrate existing data to new structure
3. Update foreign key relationships
4. Create indexes
5. Update application code
6. Test and validate
