from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import json
import numpy as np
import pickle
import os
import threading
from collections import defaultdict
import uuid
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency for local env files
    def load_dotenv():
        return False

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Database Configuration - MySQL for XAMPP
# Update these credentials to match your XAMPP MySQL setup
db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/loan_app_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine_options = {}
if db_url.startswith('mysql'):
    engine_options = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
    }
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'pranavbachhav369@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'zveq jvxz yclf szok')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'pranavbachhav369@gmail.com')
app.config['MAIL_ASCII_ATTACHMENTS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
mail = Mail(app)

# Load the ML model (will be integrated after user provides the model)
model = None
scaler = None

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'

    application_id = db.Column(db.String(30), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_number = db.Column(db.String(20), unique=True, nullable=True)
    
    # Personal Information
    full_name = db.Column(db.String(120), nullable=True)
    date_of_birth = db.Column(db.String(30), nullable=True)
    gender = db.Column(db.Integer, nullable=True)
    marital_status = db.Column(db.String(20), nullable=True)
    dependents = db.Column(db.Integer, nullable=True)
    
    # Contact Information
    email_address = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    alternate_phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    
    # Employment Details
    employment_type = db.Column(db.String(80), nullable=True)
    employment_status = db.Column(db.String(30), nullable=True)
    company_name = db.Column(db.String(120), nullable=True)
    work_experience_years = db.Column(db.Float, nullable=True)
    monthly_income = db.Column(db.Float, nullable=True)
    
    # Financial Information
    annual_income = db.Column(db.Float, nullable=True)
    other_income = db.Column(db.Float, nullable=True)
    existing_loans = db.Column(db.Float, nullable=True)
    monthly_debt = db.Column(db.Float, nullable=True)
    credit_score = db.Column(db.Float, nullable=True)
    credit_history = db.Column(db.Integer, nullable=True)
    
    # Loan Information
    loan_amount = db.Column(db.Float, nullable=True)
    loan_purpose = db.Column(db.String(120), nullable=True)
    loan_amount_term = db.Column(db.Float, nullable=True)
    collateral_type = db.Column(db.String(100), nullable=True)
    collateral_value = db.Column(db.Float, nullable=True)
    
    # Education
    education = db.Column(db.Integer, nullable=True)
    education_level = db.Column(db.String(50), nullable=True)
    
    # Property Information
    property_area = db.Column(db.Integer, nullable=True)
    property_type = db.Column(db.String(100), nullable=True)
    
    # Legacy fields for compatibility
    married = db.Column(db.Integer, nullable=True)
    self_employed = db.Column(db.Integer, nullable=True)
    applicant_income = db.Column(db.Float, nullable=True)
    coapplicant_income = db.Column(db.Float, nullable=True)
    collateral = db.Column(db.String(120), nullable=True)
    financial_notes = db.Column(db.Text, nullable=True)
    
    # Status
    application_status = db.Column(db.String(30), default='Application Submitted', nullable=False)
    ai_risk_level = db.Column(db.String(20), nullable=True)
    ai_risk_score = db.Column(db.Float, nullable=True)
    approval_probability = db.Column(db.Float, nullable=True)
    admin_comment = db.Column(db.Text, nullable=True)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref='loan_applications')
    documents = db.relationship('DocumentRecord', back_populates='application', cascade='all, delete-orphan', lazy='dynamic')
    workflow = db.relationship('LoanWorkflow', back_populates='application', cascade='all, delete-orphan', uselist=False)
    chat_messages = db.relationship('SupportChat', back_populates='application', cascade='all, delete-orphan', lazy='dynamic')
    aadhaar_document = db.relationship('AadhaarDocument', back_populates='application', cascade='all, delete-orphan', uselist=False)
    risk_analysis = db.relationship('AIRiskAnalysis', back_populates='application', cascade='all, delete-orphan', uselist=False)
    prediction_history = db.relationship('PredictionHistory', back_populates='application', cascade='all, delete-orphan', lazy='dynamic')
    timeline = db.relationship('WorkflowTimeline', back_populates='application', cascade='all, delete-orphan', lazy='dynamic')
    approval_history = db.relationship('ApprovalHistory', back_populates='application', cascade='all, delete-orphan', lazy='dynamic')
    admin_comments = db.relationship('AdminComment', back_populates='application', cascade='all, delete-orphan', lazy='dynamic')


class DocumentRecord(db.Model):
    __tablename__ = 'documents'

    document_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    document_name = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    verification_status = db.Column(db.String(20), default='Pending', nullable=False)
    admin_remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='documents')


class LoanWorkflow(db.Model):
    __tablename__ = 'loan_workflow'

    workflow_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False, unique=True)
    current_stage = db.Column(db.String(50), default='application_submitted', nullable=False)
    stage_status = db.Column(db.String(30), default='Application Submitted', nullable=False)
    admin_comment = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='workflow')


class LoanPrediction(db.Model):
    __tablename__ = 'loan_predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    application_id = db.Column(db.String(30), nullable=True)
    input_features = db.Column(db.Text, nullable=True)
    prediction_result = db.Column(db.String(20), nullable=False)
    prediction_probability = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref='loan_predictions')


class ApplicationWorkflow(db.Model):
    __tablename__ = 'application_workflow'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), nullable=False, unique=True)
    stage = db.Column(db.String(50), default='application_submitted', nullable=False)
    status = db.Column(db.String(30), default='Application Submitted', nullable=False)
    admin_message = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class ChatbotHistory(db.Model):
    __tablename__ = 'chatbot_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref='chatbot_history')


class SupportChat(db.Model):
    __tablename__ = 'support_chat'

    chat_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], backref='workflow_chats_as_user')
    admin = db.relationship('User', foreign_keys=[admin_id], backref='workflow_chats_as_admin')
    application = db.relationship('LoanApplication', back_populates='chat_messages')


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Pending', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref='support_tickets')
    replies = db.relationship('SupportReply', back_populates='ticket', cascade='all, delete-orphan', lazy='dynamic')


class SupportReply(db.Model):
    __tablename__ = 'support_replies'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)
    reply_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    ticket = db.relationship('SupportTicket', back_populates='replies')


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), default='Medium', nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    action_link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref='notifications')
    application = db.relationship('LoanApplication', backref='notifications')


class AadhaarDocument(db.Model):
    __tablename__ = 'aadhaar_documents'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=True)
    upload_date = db.Column(db.DateTime, nullable=False)
    verification_status = db.Column(db.String(20), default='Pending', nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verification_date = db.Column(db.DateTime, nullable=True)
    admin_remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='aadhaar_document')
    verifier = db.relationship('User', foreign_keys=[verified_by])


class AIRiskAnalysis(db.Model):
    __tablename__ = 'ai_risk_analysis'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    
    # Prediction Results
    prediction_result = db.Column(db.String(20), nullable=False)
    approval_probability = db.Column(db.Float, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    
    # Model Information
    model_version = db.Column(db.String(50), nullable=True)
    model_confidence = db.Column(db.Float, nullable=True)
    feature_importance = db.Column(db.Text, nullable=True)
    
    # AI Explanation
    ai_explanation = db.Column(db.Text, nullable=True)
    
    # Analysis Status
    analysis_status = db.Column(db.String(20), default='Pending', nullable=False)
    analyzed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    analysis_date = db.Column(db.DateTime, nullable=True)
    
    # Admin Review
    admin_review_status = db.Column(db.String(30), default='Pending', nullable=False)
    admin_review_comment = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    review_date = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='risk_analysis')
    analyzer = db.relationship('User', foreign_keys=[analyzed_by])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])


class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Historical Prediction Data
    prediction_result = db.Column(db.String(20), nullable=False)
    approval_probability = db.Column(db.Float, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    
    # Application Context
    loan_amount = db.Column(db.Float, nullable=False)
    loan_amount_term = db.Column(db.Float, nullable=False)
    monthly_income = db.Column(db.Float, nullable=False)
    credit_score = db.Column(db.Integer, nullable=True)
    
    # Model Information
    model_version = db.Column(db.String(50), nullable=True)
    prediction_date = db.Column(db.DateTime, nullable=False)
    
    # Comparison Data
    is_current_prediction = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='prediction_history')
    user = db.relationship('User', backref='prediction_history')


class WorkflowTimeline(db.Model):
    __tablename__ = 'workflow_timeline'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    
    # Stage Information
    stage_name = db.Column(db.String(50), nullable=False)
    stage_status = db.Column(db.String(20), nullable=False)
    
    # Stage Details
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Admin Actions
    action_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_comment = db.Column(db.Text, nullable=True)
    
    # Stage Progress
    progress_percentage = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='timeline')
    action_admin = db.relationship('User', foreign_keys=[action_by])


class ApprovalHistory(db.Model):
    __tablename__ = 'approval_history'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    
    # Decision Information
    decision_type = db.Column(db.String(50), nullable=False)
    decision = db.Column(db.String(30), nullable=False)
    
    # Decision Context
    previous_stage = db.Column(db.String(100), nullable=True)
    new_stage = db.Column(db.String(100), nullable=True)
    decision_reason = db.Column(db.Text, nullable=True)
    
    # Admin Information
    decided_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    decision_date = db.Column(db.DateTime, nullable=False)
    
    # Additional Notes
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='approval_history')
    decision_maker = db.relationship('User', foreign_keys=[decided_by])


class AdminComment(db.Model):
    __tablename__ = 'admin_comments'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), db.ForeignKey('loan_applications.application_id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(20), nullable=False)
    is_visible_to_user = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    application = db.relationship('LoanApplication', back_populates='admin_comments')
    admin = db.relationship('User', backref='admin_comments')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def commit_or_rollback():
    try:
        db.session.commit()
        db.session.flush()  # Ensure data is written to transaction
        return True
    except Exception as exc:
        db.session.rollback()
        print(f"Database commit error: {exc}")
        raise exc


def generate_application_id():
    """Generate a unique application ID"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(8))
    return f"APP-{random_str}"


def generate_application_number():
    """Generate a unique application number"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(10))
    return f"LOAN-{random_str}"


def create_notification(user_id, title, message, notification_type, application_id=None, priority='Medium', action_link=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        application_id=application_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        action_link=action_link,
        is_read=False
    )
    db.session.add(notification)
    return notification


def create_workflow_timeline_entry(application_id, stage_name, stage_status, action_by=None, admin_comment=None):
    """Create a workflow timeline entry"""
    timeline = WorkflowTimeline(
        application_id=application_id,
        stage_name=stage_name,
        stage_status=stage_status,
        started_at=datetime.now(timezone.utc),
        action_by=action_by,
        admin_comment=admin_comment,
        progress_percentage=0
    )
    db.session.add(timeline)
    return timeline


def ensure_application_workflow(application_id, stage='application_submitted', status='Application Submitted', admin_message=None):
    workflow = ApplicationWorkflow.query.filter_by(application_id=application_id).first()
    if workflow is None:
        workflow = ApplicationWorkflow(application_id=application_id)
        db.session.add(workflow)
    workflow.stage = stage
    workflow.status = status
    workflow.admin_message = admin_message
    workflow.updated_at = datetime.now(timezone.utc)
    return workflow


def create_approval_history(application_id, decision_type, decision, decided_by, previous_stage=None, new_stage=None, decision_reason=None, admin_notes=None):
    """Create an approval history entry"""
    history = ApprovalHistory(
        application_id=application_id,
        decision_type=decision_type,
        decision=decision,
        previous_stage=previous_stage,
        new_stage=new_stage,
        decision_reason=decision_reason,
        decided_by=decided_by,
        decision_date=datetime.now(timezone.utc),
        admin_notes=admin_notes
    )
    db.session.add(history)
    return history


def save_prediction_to_history(user_id, prediction_result, probability, loan_amount, applicant_income, coapplicant_income, loan_amount_term, credit_history, property_area):
    """Save prediction result to history"""
    history = PredictionHistory(
        user_id=user_id,
        prediction_result=prediction_result,
        approval_probability=probability,
        loan_amount=loan_amount,
        applicant_income=applicant_income,
        coapplicant_income=coapplicant_income,
        loan_amount_term=loan_amount_term,
        credit_history=credit_history,
        property_area=property_area,
        created_at=datetime.now(timezone.utc)
    )
    
    db.session.add(history)
    return history


def convert_gender_to_int(gender_value):
    """Convert gender string to integer for database storage"""
    if not gender_value:
        return 0
    gender_map = {
        'Male': 1,
        'Female': 0,
        'male': 1,
        'female': 0,
        'M': 1,
        'F': 0,
        '1': 1,
        '0': 0
    }
    return gender_map.get(gender_value, 0)


def safe_float_convert(value, default=0.0):
    """Safely convert value to float"""
    if not value:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_convert(value, default=0):
    """Safely convert value to int"""
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def create_workflow_snapshot(application):
    workflow = application.workflow
    current_stage = workflow.current_stage if workflow else 'application_submitted'
    stage_status = workflow.stage_status if workflow else 'Application Submitted'
    
    stage_order = [
        'application_submitted',
        'documents_verification',
        'ai_risk_analysis',
        'admin_review',
        'final_decision'
    ]
    
    try:
        current_idx = stage_order.index(current_stage)
    except ValueError:
        current_idx = 0

    timeline_map = {}
    if hasattr(application, 'timeline') and application.timeline:
        try:
            for item in application.timeline.all():
                timeline_map[item.stage_name] = item.updated_at or item.created_at or item.started_at
        except Exception:
            pass

    stages = {}
    for idx, key in enumerate(stage_order):
        is_past = idx < current_idx
        is_current = idx == current_idx
        
        if key == 'application_submitted':
            completed = True
            ts = application.created_at
            st_text = 'Application Submitted'
        elif key == 'documents_verification':
            has_docs = any(doc.verification_status in {'Approved', 'Rejected'} for doc in application.documents) if hasattr(application, 'documents') else False
            completed = is_past or has_docs or (is_current and stage_status in {'Approved', 'Completed', 'Documents Approved'})
            ts = timeline_map.get('Documents Verification') or (application.updated_at if completed else None)
            st_text = stage_status if is_current else ('Approved' if completed else 'Pending')
        elif key == 'ai_risk_analysis':
            has_risk = application.ai_risk_score is not None or application.approval_probability is not None
            completed = is_past or has_risk or (is_current and stage_status in {'Approved', 'Completed', 'AI Risk Analysis Completed'})
            ts = timeline_map.get('AI Risk Analysis') or timeline_map.get('Ai Risk Analysis') or (application.updated_at if completed else None)
            st_text = stage_status if is_current else ('Approved' if completed else 'Pending')
        elif key == 'admin_review':
            has_review = application.admin_comment is not None or application.application_status in {'Approved', 'Rejected'}
            completed = is_past or has_review or (is_current and stage_status in {'Approved', 'Completed', 'Admin Review Approved'})
            ts = timeline_map.get('Admin Review') or (application.updated_at if completed else None)
            st_text = stage_status if is_current else ('Approved' if completed else 'Pending')
        elif key == 'final_decision':
            completed = application.application_status in {'Approved', 'Rejected'} or (is_current and stage_status in {'Approved', 'Rejected'})
            ts = application.updated_at if completed else None
            st_text = application.application_status if completed else (stage_status if is_current else 'Pending')

        stages[key] = {
            'completed': bool(completed),
            'timestamp': ts.isoformat() if ts else None,
            'formatted': ts.strftime('%b %d, %Y %H:%M') if ts else ('Completed' if completed else ''),
            'status': st_text
        }

    return {
        'application_id': application.application_id,
        'user_id': application.user_id,
        'current_stage': current_stage,
        'stage_status': stage_status,
        'application_status': application.application_status,
        'admin_remark': application.admin_comment,
        'stages': stages,
        'ml_prediction': {
            'result': application.ai_risk_level,
            'probability': application.approval_probability,
            'risk_score': application.ai_risk_score,
        },
        'created_at': application.created_at.isoformat() if application.created_at else None,
        'created_at_formatted': application.created_at.strftime('%b %d, %Y %H:%M') if application.created_at else '',
        'updated_at': application.updated_at.isoformat() if application.updated_at else None,
    }


def serialize_application(application):
    """Serialize application with all enterprise fields for admin verification workbench"""
    return {
        'application_id': application.application_id,
        'application_number': application.application_number,
        'user_id': application.user_id,
        
        # Personal Information
        'full_name': application.full_name,
        'date_of_birth': application.date_of_birth,
        'gender': application.gender,
        'marital_status': application.marital_status,
        'dependents': application.dependents,
        
        # Contact Information
        'email_address': application.email_address,
        'phone_number': application.phone_number,
        'alternate_phone': application.alternate_phone,
        'address': application.address,
        'city': application.city,
        'state': application.state,
        'pincode': application.pincode,
        
        # Employment Details
        'employment_type': application.employment_type,
        'employment_status': application.employment_status,
        'company_name': application.company_name,
        'work_experience_years': application.work_experience_years,
        'monthly_income': application.monthly_income,
        
        # Financial Information
        'annual_income': application.annual_income,
        'other_income': application.other_income,
        'existing_loans': application.existing_loans,
        'monthly_debt': application.monthly_debt,
        'credit_score': application.credit_score,
        'credit_history': application.credit_history,
        
        # Loan Information
        'loan_amount': application.loan_amount,
        'loan_purpose': application.loan_purpose,
        'loan_amount_term': application.loan_amount_term,
        'collateral_type': application.collateral_type,
        'collateral_value': application.collateral_value,
        
        # Education
        'education_level': application.education_level,
        
        # Property Information
        'property_area': application.property_area,
        
        # Legacy fields for compatibility
        'marital_status': getattr(application, 'marital_status', None) or ('Married' if getattr(application, 'married', None) == 1 else 'Single'),
        'dependents': application.dependents if application.dependents is not None else 0,
        'education_level': getattr(application, 'education_level', None) or ('Graduate' if getattr(application, 'education', None) == 1 else 'Not Graduate'),
        'self_employed': application.self_employed,
        'employment_type': getattr(application, 'employment_type', None) or 'Salaried',
        'employment_status': getattr(application, 'employment_status', None) or 'Active',
        'company_name': getattr(application, 'company_name', None) or 'N/A',
        'work_experience_years': getattr(application, 'work_experience_years', None) or 0,
        'applicant_income': application.applicant_income or 0.0,
        'coapplicant_income': application.coapplicant_income or 0.0,
        'monthly_income': getattr(application, 'monthly_income', None) or application.applicant_income or 0.0,
        'annual_income': getattr(application, 'annual_income', None) or (application.applicant_income * 12 if application.applicant_income else 0.0),
        'other_income': getattr(application, 'other_income', None) or 0.0,
        'existing_loans': getattr(application, 'existing_loans', None) or 0.0,
        'monthly_debt': getattr(application, 'monthly_debt', None) or 0.0,
        'credit_score': getattr(application, 'credit_score', None) or (750 if application.credit_history == 1 else 600),
        'credit_history': application.credit_history if application.credit_history is not None else 1,
        'loan_amount': application.loan_amount or 0.0,
        'loan_amount_term': application.loan_amount_term or 36.0,
        'loan_purpose': getattr(application, 'loan_purpose', None) or 'Personal Loan',
        'property_area': application.property_area if application.property_area is not None else 1,
        'collateral': getattr(application, 'collateral', None) or 'None',
        'collateral_type': getattr(application, 'collateral_type', None) or 'N/A',
        'collateral_value': getattr(application, 'collateral_value', None) or 0.0,
        'financial_notes': getattr(application, 'financial_notes', None) or 'None',
        'address': getattr(application, 'address', None) or 'N/A',
        'city': getattr(application, 'city', None) or 'N/A',
        'state': getattr(application, 'state', None) or 'N/A',
        'pincode': getattr(application, 'pincode', None) or 'N/A',
        'application_status': application.application_status or 'Application Submitted',
        'ai_risk_level': application.ai_risk_level or 'Medium Risk',
        'ai_risk_score': application.ai_risk_score or 25.0,
        'admin_comment': application.admin_comment,
        'created_at': application.created_at.isoformat() if application.created_at else None,
        'updated_at': application.updated_at.isoformat() if application.updated_at else None,
        'documents': [
            {
                'document_id': doc.document_id,
                'document_type': doc.document_type,
                'document_name': doc.document_name,
                'file_path': doc.file_path,
                'verification_status': doc.verification_status,
                'admin_remark': doc.admin_remark,
            } for doc in application.documents.order_by(DocumentRecord.created_at.asc()).all()
        ] if hasattr(application, 'documents') and application.documents else [],
    }


def classify_prediction(approval_probability, ai_risk_level=None):
    if approval_probability is not None:
        return 'Approved' if approval_probability >= 0.5 else 'Rejected'
    if ai_risk_level:
        normalized = ai_risk_level.lower()
        if 'low' in normalized or 'safe' in normalized:
            return 'Approved'
        if 'high' in normalized or 'risk' in normalized and 'high' in normalized:
            return 'Rejected'
    return 'Rejected'


def get_risk_level_from_probability(approval_probability, ai_risk_level=None):
    if ai_risk_level:
        normalized = ai_risk_level.lower()
        if 'low' in normalized or 'safe' in normalized:
            return 'Low Risk'
        if 'high' in normalized:
            return 'High Risk'
        if 'medium' in normalized:
            return 'Medium Risk'
    if approval_probability is None:
        return 'Medium Risk'
    if approval_probability >= 0.75:
        return 'Low Risk'
    if approval_probability >= 0.5:
        return 'Medium Risk'
    return 'High Risk'


def build_prediction_analytics_payload(user_id=None, is_admin=False):
    """Admin/analytics payload built ONLY from ML predictions (loan_predictions)."""
    query = LoanPrediction.query
    if user_id is not None and not is_admin:
        query = query.filter_by(user_id=user_id)
    predictions = query.order_by(LoanPrediction.created_at.desc()).all()

    prediction_records = []
    for record in predictions:
        probability = float(record.prediction_probability or 0)
        prediction_result = record.prediction_result or classify_prediction(probability)
        risk_level = get_risk_level_from_probability(probability)
        prediction_records.append({
            'application_id': record.application_id,
            'prediction_result': prediction_result,
            'approval_probability': probability,
            'risk_level': risk_level,
            'created_at': record.created_at,
        })

    summary = {
        'total_predictions': len(prediction_records),
        'approved_predictions': sum(1 for item in prediction_records if item['prediction_result'] == 'Approved'),
        'rejected_predictions': sum(1 for item in prediction_records if item['prediction_result'] == 'Rejected'),
        'low_risk_count': sum(1 for item in prediction_records if item['risk_level'] == 'Low Risk'),
        'medium_risk_count': sum(1 for item in prediction_records if item['risk_level'] == 'Medium Risk'),
        'high_risk_count': sum(1 for item in prediction_records if item['risk_level'] == 'High Risk'),
        'avg_confidence': round(sum(item['approval_probability'] for item in prediction_records) / len(prediction_records), 2) if prediction_records else 0,
    }

    trend_counts = defaultdict(lambda: {'approved': 0, 'rejected': 0})
    probability_trend = defaultdict(list)
    for item in prediction_records:
        if not item['created_at']:
            continue
        day_key = item['created_at'].strftime('%Y-%m-%d')
        probability_trend[day_key].append(item['approval_probability'])
        if item['prediction_result'] == 'Approved':
            trend_counts[day_key]['approved'] += 1
        else:
            trend_counts[day_key]['rejected'] += 1

    return {
        'status': 'success',
        'summary': summary,
        'risk_distribution': [
            {'label': 'Low Risk', 'count': summary['low_risk_count']},
            {'label': 'Medium Risk', 'count': summary['medium_risk_count']},
            {'label': 'High Risk', 'count': summary['high_risk_count']},
        ],
        'prediction_trends': [
            {
                'date': day,
                'approved_count': counts['approved'],
                'rejected_count': counts['rejected'],
                'avg_probability': round(sum(probability_trend[day]) / len(probability_trend[day]), 4) if probability_trend.get(day) else 0,
            }
            for day, counts in sorted(trend_counts.items())
        ],
    }


def build_dashboard_payload(user_id=None):
    """Build dashboard analytics ONLY from ML prediction records (loan_predictions).

    Workflow/admin statuses are intentionally NOT used here, so admin
    approval/rejection decisions never affect the ML graphs.
    """
    query = LoanPrediction.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)

    predictions = query.order_by(LoanPrediction.created_at.desc()).all()
    total_predictions = len(predictions)
    approved_count = sum(1 for item in predictions if item.prediction_result == 'Approved')
    rejected_count = sum(1 for item in predictions if item.prediction_result == 'Rejected')
    approval_rate = round((approved_count / total_predictions * 100) if total_predictions else 0, 1)
    rejection_rate = round((rejected_count / total_predictions * 100) if total_predictions else 0, 1)
    risk_detection_rate = round((approved_count / total_predictions * 100) if total_predictions else 0, 1)

    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    monthly_predictions = sum(1 for item in predictions if item.created_at and item.created_at.month == current_month and item.created_at.year == current_year)
    daily_predictions = sum(1 for item in predictions if item.created_at and item.created_at.date() == datetime.now(timezone.utc).date())

    trend_counts = defaultdict(int)
    approved_by_day = defaultdict(int)
    rejected_by_day = defaultdict(int)
    probability_by_day = defaultdict(list)
    low_risk_count = 0
    medium_risk_count = 0
    high_risk_count = 0
    approved_incomes = []
    rejected_incomes = []
    approved_credits = []
    rejected_credits = []

    for item in predictions:
        prob = float(item.prediction_probability or 0)
        # Risk buckets derived purely from ML probability
        if prob >= 0.75:
            low_risk_count += 1
        elif prob >= 0.5:
            medium_risk_count += 1
        else:
            high_risk_count += 1

        if item.input_features:
            try:
                features = json.loads(item.input_features or '{}')
                income = float(features.get('applicant_income', 0) or 0) + float(features.get('coapplicant_income', 0) or 0)
                credit = float(features.get('credit_score', 0) or 0)
                if item.prediction_result == 'Approved':
                    approved_incomes.append(income)
                    approved_credits.append(credit)
                else:
                    rejected_incomes.append(income)
                    rejected_credits.append(credit)
            except (ValueError, TypeError):
                pass

        if not item.created_at:
            continue
        key = item.created_at.strftime('%Y-%m-%d')
        trend_counts[key] += 1
        probability_by_day[key].append(prob)
        if item.prediction_result == 'Approved':
            approved_by_day[key] += 1
        elif item.prediction_result == 'Rejected':
            rejected_by_day[key] += 1

    chart_labels = sorted(trend_counts.keys())
    chart_data = [
        {
            'date': label,
            'approved_count': approved_by_day.get(label, 0),
            'rejected_count': rejected_by_day.get(label, 0),
            'total_count': trend_counts[label],
            'avg_probability': round(
                sum(probability_by_day[label]) / len(probability_by_day[label]), 4
            ) if probability_by_day.get(label) else 0,
        }
        for label in chart_labels
    ]

    recent_activity = [
        {
            'application_id': item.application_id,
            'prediction_result': item.prediction_result,
            'approval_probability': item.prediction_probability,
            'created_at': item.created_at.isoformat() if item.created_at else None,
        }
        for item in predictions[:10]
    ]

    avg_income_approved = round(sum(approved_incomes) / len(approved_incomes), 2) if approved_incomes else 0
    avg_income_rejected = round(sum(rejected_incomes) / len(rejected_incomes), 2) if rejected_incomes else 0
    avg_credit_approved = round(sum(approved_credits) / len(approved_credits), 2) if approved_credits else 0
    avg_credit_rejected = round(sum(rejected_credits) / len(rejected_credits), 2) if rejected_credits else 0

    return {
        'total_predictions': total_predictions,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'approval_rate': approval_rate,
        'rejection_rate': rejection_rate,
        'risk_detection_rate': risk_detection_rate,
        'monthly_predictions': monthly_predictions,
        'daily_predictions': daily_predictions,
        'chart_data': chart_data,
        'recent_activity': recent_activity,
        'accuracy': round((approved_count / total_predictions * 100) if total_predictions else 0, 1),
        'total_users': User.query.count(),
        # ML-only risk distribution
        'risk_distribution': [
            {'label': 'Low Risk', 'count': low_risk_count},
            {'label': 'Medium Risk', 'count': medium_risk_count},
            {'label': 'High Risk', 'count': high_risk_count},
        ],
        # ML-only financial analysis from input_features
        'income_analysis': {
            'approved_avg': avg_income_approved,
            'rejected_avg': avg_income_rejected,
        },
        'credit_analysis': {
            'approved_avg': avg_credit_approved,
            'rejected_avg': avg_credit_rejected,
        },
    }


def get_ai_reply(message, history=None, application_context=None):
    context_info = ''
    if application_context:
        context_info = (
            '\n\nApplication Context:\n'
            f"- Application ID: {application_context.get('application_id')}\n"
            f"- Current Stage: {application_context.get('current_stage')}\n"
            f"- Application Status: {application_context.get('application_status')}\n"
            f"- Loan Amount: {application_context.get('loan_amount')}\n"
            f"- Documents Status: {application_context.get('documents_status')}\n"
            f"- Admin Remark: {application_context.get('admin_remark')}"
        )

    # Check which AI service to use
    ai_provider = os.getenv('AI_PROVIDER', 'gemini').lower()  # Default to Gemini
    
    # Try OpenAI first if configured
    if ai_provider == 'openai':
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_key_here':
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                
                # Build system prompt
                system_prompt = (
                    "You are a professional AI Financial Assistant integrated into the SmartLoanApprove loan approval dashboard.\n\n"
                    "CRITICAL RULE: You must not give the same generic answer for every user question.\n\n"
                    "Analyze each user's question carefully and generate a response according to the exact topic, context, and intent of the question.\n\n"
                    "Rules:\n\n"
                    "* Understand the user's actual requirement before answering.\n"
                    "* Give different answers for different questions.\n"
                    "* Do not repeat previous responses unless the question is the same.\n"
                    "* If the user asks a technical question, provide a technical solution.\n"
                )
                
                messages = [{"role": "system", "content": system_prompt}]
                
                if history and len(history) > 0:
                    recent_history = history[-10:] if len(history) > 10 else history
                    for item in recent_history:
                        role = 'user' if item['role'] == 'user' else 'assistant'
                        messages.append({"role": role, "content": item['content']})
                
                messages.append({"role": "user", "content": message})
                
                response = client.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                return response.choices[0].message.content
            except Exception as exc:
                print(f'OpenAI error: {exc}')
                pass # Fall back to Gemini if OpenAI fails
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key and gemini_key != 'your_api_key_here':
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'))
            
            conversation = [
                {
                    'role': 'user',
                    'parts': [
                        "You are a professional AI Financial Assistant integrated into the SmartLoanApprove loan approval dashboard.\n\n"
                        "CRITICAL RULE: You must not give the same generic answer for every user question.\n\n"
                        "Your role is to help users with:\n"
                        "- Loan-related queries and guidance\n"
                        "- Understanding their loan application status\n"
                        "- Financial advice and recommendations\n"
                        "- Dashboard feature explanations\n"
                        "- General banking and loan information\n\n"
                        "Guidelines for responses:\n"
                        "- Provide specific, contextual answers based on the user's question and their application context\n"
                        "- If asked about loan status, use the provided context to give accurate information\n"
                        "- Offer practical advice for improving loan approval chances based on their stage\n"
                        "- Be helpful but professional\n"
                        "- If you don't have specific information, guide the user to the right section\n"
                        "- Keep responses concise but informative\n"
                        "- Use a friendly, professional tone\n\n"
                        "Workflow stages users may ask about:\n"
                        "1. Application Submitted - Initial submission received\n"
                        "2. Documents Verification - Documents being reviewed\n"
                        "3. AI Risk Analysis - AI analyzing loan risk\n"
                        "4. Admin Review - Admin reviewing the application\n"
                        "5. Final Decision - Approved/Rejected/Pending\n\n"
                        "Do not say you are Gemini; introduce yourself as SmartLoanApprove AI Assistant."
                        + context_info
                    ],
                }
            ]
            
            if history and len(history) > 0:
                recent_history = history[-10:] if len(history) > 10 else history
                for item in recent_history:
                    role = 'user' if item['role'] == 'user' else 'model'
                    conversation.append({
                        'role': role,
                        'parts': [item['content']]
                    })
            
            # Add current message
            conversation.append({
                'role': 'user',
                'parts': [message],
            })
            
            response = model.generate_content(conversation)
            return response.text if getattr(response, 'text', None) else 'I am unable to generate a reply right now.'
        except Exception as exc:
            print(f'Gemini error: {exc}')
    
    # Fallback to dynamic responses if no AI service is available
    message_lower = message.lower()
    
    # Loan-related questions
    if any(word in message_lower for word in ['loan', 'approval', 'reject', 'credit', 'score', 'emi', 'interest', 'eligibility', 'income']):
        if 'credit score' in message_lower:
            return "Your credit score is a key factor in loan approval. A score above 750 is generally considered good. Factors affecting it include payment history, credit utilization, length of credit history, and types of credit. To improve it, pay bills on time, keep credit utilization below 30%, and avoid too many credit inquiries."
        elif 'emi' in message_lower:
            return "EMI (Equated Monthly Installment) is your monthly loan payment. It depends on the loan amount, interest rate, and tenure. You can use our EMI Calculator to estimate your monthly payments. Lower interest rates or longer tenure reduce EMI, but increase total interest paid."
        elif 'approval' in message_lower or 'reject' in message_lower:
            return "Loan approval depends on multiple factors: credit score, income stability, debt-to-income ratio, employment history, and existing liabilities. Our AI prediction analyzes these factors to give you an instant assessment. For better chances, maintain a good credit score and stable income."
        elif 'interest' in message_lower:
            return "Interest rates vary based on your credit profile, loan type, and market conditions. Generally, rates range from 8-15% for personal loans. A good credit score can help you negotiate lower rates. Fixed rates stay constant, while floating rates change with market conditions."
        else:
            return "For loan-related queries, I can help you understand credit scores, EMI calculations, interest rates, eligibility criteria, and the approval process. What specific aspect would you like to know more about?"
    
    # Dashboard/technical questions
    elif any(word in message_lower for word in ['dashboard', 'prediction', 'history', 'analytics', 'error', 'login', 'register', 'account']):
        if 'prediction' in message_lower:
            return "The AI Prediction feature analyzes your financial data to predict loan approval chances. Enter your income, credit score, loan amount, and other details to get an instant assessment. The prediction is based on machine learning models trained on historical loan data."
        elif 'history' in message_lower:
            return "Your Prediction History shows all past loan predictions you've made. You can view the results, dates, and details of each prediction. This helps track your loan applications and understand patterns in approval outcomes."
        elif 'analytics' in message_lower:
            return "The Data Analytics section provides insights into your loan predictions. You can view approval rates, rejection rates, trends over time, and other statistics. This helps you understand your loan application performance and identify areas for improvement."
        elif 'login' in message_lower or 'register' in message_lower:
            return "To use the dashboard features, you need to register and login. Registration requires a username, email, and password. After login, you can access predictions, history, analytics, and other personalized features."
        else:
            return "I can help you with dashboard features like predictions, history, analytics, and account management. What specific feature are you having trouble with?"
    
    # Support/help questions
    elif any(word in message_lower for word in ['help', 'support', 'contact', 'issue', 'problem']):
        return "If you need help with any issue, you can use our Support Center to create a support ticket. Our team will assist you with your queries. For immediate assistance, you can also check our FAQ section or contact support directly."
    
    # General greetings
    elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return f"Hello! I'm your SmartLoanApprove AI Assistant. I can help you with loan-related questions, dashboard features, financial guidance, and more. How can I assist you today?"
    
    # Default response
    else:
        return f"I understand you're asking about: '{message}'. As a SmartLoanApprove AI Assistant, I can help with loan queries, financial guidance, dashboard features, and general questions. Could you provide more details so I can give you a specific answer?"


def send_prediction_email(user_email, prediction_result, probability, loan_details):
    """Send prediction result email to user (async)"""
    def send_async_email():
        with app.app_context():
            try:
                print(f"[EMAIL] Attempting to send email to {user_email}...")
                print(f"[EMAIL] Mail config: server={app.config['MAIL_SERVER']}, port={app.config['MAIL_PORT']}, username={app.config['MAIL_USERNAME']}")
                print(f"[EMAIL] TLS enabled: {app.config['MAIL_USE_TLS']}")
                
                subject = f"Loan Prediction Result: {prediction_result}"
                
                # Create email content
                if prediction_result == 'Approved':
                    html_body = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                            .success {{ color: #28a745; font-size: 24px; font-weight: bold; }}
                            .details {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Congratulations!</h1>
                                <p>Your Loan Application Prediction</p>
                            </div>
                            <div class="content">
                                <p class="success">Status: APPROVED</p>
                                <p>Great news! Based on our analysis, your loan application is likely to be approved.</p>
                                
                                <div class="details">
                                    <h3>Loan Details:</h3>
                                    <p><strong>Loan Amount:</strong> ${loan_details['loan_amount']:,.2f}</p>
                                    <p><strong>Loan Term:</strong> {int(loan_details['loan_amount_term'])} days</p>
                                    <p><strong>Total Income:</strong> ${loan_details['total_income']:,.2f}</p>
                                    <p><strong>Confidence Score:</strong> {probability * 100:.1f}%</p>
                                </div>
                                
                                <p><strong>Note:</strong> This is an AI-powered prediction. Final approval is subject to lender's terms and conditions.</p>
                            </div>
                            <div class="footer">
                                <p>Loan Approval Prediction System</p>
                                <p>This is an automated message. Please do not reply.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                else:
                    html_body = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                            .rejected {{ color: #dc3545; font-size: 24px; font-weight: bold; }}
                            .details {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Loan Prediction Result</h1>
                                <p>Your Loan Application Prediction</p>
                            </div>
                            <div class="content">
                                <p class="rejected">Status: NOT APPROVED</p>
                                <p>Based on our analysis, your loan application may not be approved at this time.</p>
                                
                                <div class="details">
                                    <h3>Loan Details:</h3>
                                    <p><strong>Loan Amount:</strong> ${loan_details['loan_amount']:,.2f}</p>
                                    <p><strong>Loan Term:</strong> {int(loan_details['loan_amount_term'])} days</p>
                                    <p><strong>Total Income:</strong> ${loan_details['total_income']:,.2f}</p>
                                    <p><strong>Confidence Score:</strong> {probability * 100:.1f}%</p>
                                </div>
                                
                                <p><strong>Suggestions:</strong></p>
                                <ul>
                                    <li>Consider increasing your down payment</li>
                                    <li>Improve your credit history</li>
                                    <li>Reduce existing debt</li>
                                    <li>Try a smaller loan amount</li>
                                </ul>
                                
                                <p><strong>Note:</strong> This is an AI-powered prediction. Final approval is subject to lender's terms and conditions.</p>
                            </div>
                            <div class="footer">
                                <p>Loan Approval Prediction System</p>
                                <p>This is an automated message. Please do not reply.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                
                print(f"[EMAIL] Creating message object...")
                msg = Message(
                    subject=subject,
                    recipients=[user_email],
                    html=html_body
                )
                print(f"[EMAIL] Message created, attempting to send...")
                
                mail.send(msg)
                print(f"[SUCCESS] Email sent successfully to {user_email}")
            except Exception as e:
                print(f"[ERROR] Error sending email to {user_email}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
    
    # Send email in background thread
    thread = threading.Thread(target=send_async_email)
    thread.start()

class HeuristicModel:
    def predict_proba(self, features):
        features = np.asarray(features, dtype=float)
        if features.ndim == 1:
            features = features.reshape(1, -1)

        income = features[:, 5] + features[:, 6]
        loan_amount = features[:, 7]
        credit_history = features[:, 9]
        property_area = features[:, 10]

        score = 0.35 + np.clip(income / np.maximum(loan_amount, 1), 0, 1.2) * 0.12
        score += credit_history * 0.08
        score += property_area * 0.02
        score = np.clip(score, 0.05, 0.95)
        return np.column_stack((1 - score, score))


def load_model():
    global model, scaler
    model_path = os.path.join(app.root_path, 'models', 'loan_model.pkl')
    scaler_path = os.path.join(app.root_path, 'models', 'scaler.pkl')

    try:
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        else:
            model = HeuristicModel()

        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
        else:
            scaler = None
    except Exception as e:
        print(f"Error loading model: {e}")
        model = HeuristicModel()
        scaler = None

# Routes
@app.route('/')
def home():
    dashboard_user_id = None if current_user.is_authenticated and current_user.is_admin else (current_user.id if current_user.is_authenticated else None)
    stats = build_dashboard_payload(user_id=dashboard_user_id)
    return render_template('home.html', stats=stats)

@app.route('/api/dashboard-stats')
def dashboard_stats_api():
    try:
        dashboard_user_id = None if current_user.is_authenticated and current_user.is_admin else (current_user.id if current_user.is_authenticated else None)
        payload = build_dashboard_payload(user_id=dashboard_user_id)
        return jsonify({'status': 'success', **payload})
    except Exception as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 500

@app.route('/api/chart-data')
def chart_data_api():
    try:
        dashboard_user_id = None if current_user.is_authenticated and current_user.is_admin else (current_user.id if current_user.is_authenticated else None)
        payload = build_dashboard_payload(user_id=dashboard_user_id)
        return jsonify({'status': 'success', 'chart_data': payload['chart_data']})
    except Exception as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 500

@app.route('/api/recent-activity')
def recent_activity_api():
    try:
        dashboard_user_id = None if current_user.is_authenticated and current_user.is_admin else (current_user.id if current_user.is_authenticated else None)
        payload = build_dashboard_payload(user_id=dashboard_user_id)
        return jsonify({'status': 'success', 'recent_activity': payload['recent_activity']})
    except Exception as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        payload = request.get_json(silent=True) or {}
        message = (payload.get('message') or '').strip()
        application_id = payload.get('application_id')

        if not message:
            return jsonify({'status': 'error', 'reply': 'Please provide a message.'}), 400

        history = session.get('chat_history', [])
        application_context = None

        if current_user.is_authenticated:
            if application_id:
                try:
                    application = LoanApplication.query.filter_by(application_id=application_id).first()
                    if application and (application.user_id == current_user.id or current_user.is_admin):
                        workflow = application.workflow
                        documents = application.documents.all()
                        docs_status = 'Not uploaded'
                        if documents:
                            verified_count = sum(1 for d in documents if d.verification_status == 'Approved')
                            total_count = len(documents)
                            docs_status = f'{verified_count}/{total_count} verified'

                        application_context = {
                            'application_id': application.application_id,
                            'current_stage': workflow.current_stage if workflow else 'unknown',
                            'application_status': application.application_status,
                            'loan_amount': application.loan_amount,
                            'documents_status': docs_status,
                            'admin_remark': application.admin_comment,
                        }
                except Exception as e:
                    print(f'Error building application context: {e}')
            else:
                try:
                    latest_app = LoanApplication.query.filter_by(
                        user_id=current_user.id
                    ).order_by(LoanApplication.created_at.desc()).first()
                    if latest_app:
                        workflow = latest_app.workflow
                        documents = latest_app.documents.all()
                        docs_status = 'Not uploaded'
                        if documents:
                            verified_count = sum(1 for d in documents if d.verification_status == 'Approved')
                            total_count = len(documents)
                            docs_status = f'{verified_count}/{total_count} verified'
                        application_context = {
                            'application_id': latest_app.application_id,
                            'current_stage': workflow.current_stage if workflow else 'unknown',
                            'application_status': latest_app.application_status,
                            'loan_amount': latest_app.loan_amount,
                            'documents_status': docs_status,
                            'admin_remark': latest_app.admin_comment,
                        }
                except Exception as e:
                    print(f'Error building latest application context: {e}')

        reply = get_ai_reply(message, history, application_context)

        history.append({'role': 'user', 'content': message})
        history.append({'role': 'assistant', 'content': reply})
        session['chat_history'] = history

        if current_user.is_authenticated:
            chatbot_entry = ChatbotHistory(
                user_id=current_user.id,
                user_message=message,
                ai_response=reply,
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(chatbot_entry)
            commit_or_rollback()

        return jsonify({'status': 'success', 'reply': reply, 'history': history})
    except Exception as exc:
        return jsonify({'status': 'error', 'reply': 'Sorry, I ran into an error processing your request.', 'error': str(exc)}), 500
        return jsonify({'status': 'error', 'reply': 'Sorry, I could not process your request.', 'error': str(exc)}), 500

@app.route('/api/user-recent-activity')
@login_required
def user_recent_activity_api():
    try:
        payload = build_dashboard_payload(user_id=current_user.id)
        return jsonify({
            'status': 'success',
            'user_predictions_count': payload['total_predictions'],
            'user_approved_count': payload['approved_count'],
            'user_rejected_count': payload['rejected_count'],
            'user_approval_rate': payload['approval_rate'],
            'activities': payload['recent_activity']
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


# Support Ticket Routes
@app.route('/workflow')
@login_required
def workflow_page():
    return render_template('workflow.html')


@app.route('/loan-application')
@login_required
def loan_application_page():
    return render_template('loan_application.html')


@app.route('/support')
@login_required
def support_page():
    return render_template('support.html')


@app.route('/api/support/tickets', methods=['POST'])
@login_required
def create_support_ticket():
    try:
        payload = request.get_json(silent=True) or {}
        subject = (payload.get('subject') or '').strip()
        message = (payload.get('message') or '').strip()
        category = (payload.get('category') or '').strip() or None
        
        if not subject or not message:
            return jsonify({'status': 'error', 'message': 'Subject and message are required.'}), 400
        
        # Generate unique ticket ID
        import random
        import string
        ticket_id = 'TKT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Create support ticket
        ticket = SupportTicket(
            ticket_id=ticket_id,
            user_id=current_user.id,
            subject=subject,
            message=message,
            category=category,
            status='Pending'
        )
        
        db.session.add(ticket)
        commit_or_rollback()
        
        # Create notification for admin
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title=f'New Support Request: {ticket_id}',
                message=f'New support request received from {current_user.username} ({current_user.email}). Subject: {subject}',
                notification_type='support_request',
                is_read=False
            )
            db.session.add(notification)
        
        commit_or_rollback()
        
        return jsonify({
            'status': 'success',
            'ticket_id': ticket_id,
            'message': 'Support ticket created successfully.'
        })
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/support/tickets')
@login_required
def get_user_tickets():
    try:
        tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
        
        tickets_data = []
        for ticket in tickets:
            ticket_data = {
                'id': ticket.id,
                'ticket_id': ticket.ticket_id,
                'subject': ticket.subject,
                'message': ticket.message,
                'category': ticket.category,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                'created_at_formatted': ticket.created_at.strftime('%b %d, %Y %H:%M') if ticket.created_at else '',
                'replies_count': ticket.replies.count()
            }
            tickets_data.append(ticket_data)
        
        return jsonify({'status': 'success', 'tickets': tickets_data})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/support/tickets/<int:ticket_id>')
@login_required
def get_ticket_details(ticket_id):
    try:
        ticket = SupportTicket.query.get_or_404(ticket_id)
        
        # Check if user owns this ticket or is admin
        if not (current_user.id == ticket.user_id or current_user.is_admin):
            return jsonify({'status': 'error', 'message': 'Access denied.'}), 403
        
        replies = SupportReply.query.filter_by(ticket_id=ticket.id).order_by(SupportReply.created_at.asc()).all()
        
        replies_data = []
        for reply in replies:
            replies_data.append({
                'id': reply.id,
                'sender_type': reply.sender_type,
                'reply_message': reply.reply_message,
                'created_at': reply.created_at.isoformat() if reply.created_at else None,
                'created_at_formatted': reply.created_at.strftime('%b %d, %Y %H:%M') if reply.created_at else ''
            })
        
        return jsonify({
            'status': 'success',
            'ticket': {
                'id': ticket.id,
                'ticket_id': ticket.ticket_id,
                'subject': ticket.subject,
                'message': ticket.message,
                'category': ticket.category,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                'created_at_formatted': ticket.created_at.strftime('%b %d, %Y %H:%M') if ticket.created_at else '',
                'user': {
                    'username': ticket.user.username,
                    'email': ticket.user.email
                }
            },
            'replies': replies_data
        })
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/support/reply', methods=['POST'])
@login_required
def add_support_reply():
    try:
        payload = request.get_json(silent=True) or {}
        ticket_id = payload.get('ticket_id')
        reply_message = (payload.get('message') or '').strip()
        sender_type = 'admin' if current_user.is_admin else 'user'
        
        if not ticket_id or not reply_message:
            return jsonify({'status': 'error', 'message': 'Ticket ID and message are required.'}), 400
        
        ticket = SupportTicket.query.get_or_404(ticket_id)
        
        # Add reply
        reply = SupportReply(
            ticket_id=ticket.id,
            sender_type=sender_type,
            reply_message=reply_message
        )
        db.session.add(reply)
        
        # Update ticket status
        if sender_type == 'admin':
            ticket.status = 'In Progress'
        else:
            ticket.status = 'Pending'
        
        commit_or_rollback()
        
        # Create notification
        if sender_type == 'admin':
            # Notify user
            notification = Notification(
                user_id=ticket.user_id,
                title=f'Admin replied to your support request',
                message=f'Admin has replied to your support request {ticket.ticket_id}.',
                notification_type='support_reply',
                is_read=False
            )
            db.session.add(notification)
        else:
            # Notify admin
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title=f'User replied to support request',
                    message=f'User has replied to support request {ticket.ticket_id}.',
                    notification_type='support_reply',
                    is_read=False
                )
                db.session.add(notification)
        
        commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'Reply added successfully'}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/support/tickets/<int:ticket_id>/status', methods=['PUT'])
@login_required
def update_ticket_status(ticket_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied.'}), 403
        
        payload = request.get_json(silent=True) or {}
        status = payload.get('status')
        
        if not status or status not in ['Pending', 'In Progress', 'Resolved']:
            return jsonify({'status': 'error', 'message': 'Invalid status.'}), 400
        
        ticket = SupportTicket.query.get_or_404(ticket_id)
        ticket.status = status
        commit_or_rollback()
        
        # Notify user if resolved
        if status == 'Resolved':
            notification = Notification(
                user_id=ticket.user_id,
                title=f'Your support request has been resolved',
                message=f'Your support request {ticket.ticket_id} has been marked as resolved.',
                notification_type='support_resolved',
                is_read=False
            )
            db.session.add(notification)
            commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'Status updated successfully.'})
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


# Admin Support Management Routes
@app.route('/admin/support')
@login_required
def admin_support_page():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    return render_template('admin_support.html')


@app.route('/api/admin/support/tickets')
@login_required
def get_all_support_tickets():
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied.'}), 403
        
        tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
        
        tickets_data = []
        for ticket in tickets:
            tickets_data.append({
                'id': ticket.id,
                'ticket_id': ticket.ticket_id,
                'user': {
                    'username': ticket.user.username,
                    'email': ticket.user.email
                },
                'subject': ticket.subject,
                'message': ticket.message,
                'category': ticket.category,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                'created_at_formatted': ticket.created_at.strftime('%b %d, %Y %H:%M') if ticket.created_at else '',
                'replies_count': ticket.replies.count()
            })
        
        return jsonify({'status': 'success', 'tickets': tickets_data})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


# Notification Routes
@app.route('/api/notifications')
@login_required
def get_notifications():
    try:
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
                'created_at_formatted': notif.created_at.strftime('%b %d, %Y %H:%M') if notif.created_at else ''
            })
        
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
        return jsonify({
            'status': 'success',
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        if notification.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Access denied.'}), 403
        
        notification.is_read = True
        commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'Notification marked as read.'})
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'All notifications marked as read.'})
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


# ==================== Loan Application Workflow Routes ====================

@app.route('/api/workflow/applications', methods=['POST'])
@login_required
def create_loan_application():
    """Create a new loan application workflow"""
    try:
        payload = request.get_json(silent=True) or {}
        application_id = generate_application_id()

        application = LoanApplication(
            application_id=application_id,
            user_id=current_user.id,
            full_name=(payload.get('full_name') or '').strip() or current_user.username,
            email_address=(payload.get('email_address') or current_user.email or '').strip(),
            phone_number=(payload.get('phone_number') or '').strip(),
            date_of_birth=(payload.get('date_of_birth') or '').strip(),
            gender=int(payload.get('gender', 0)) if payload.get('gender') else None,
            married=int(payload.get('married', 0)) if payload.get('married') else None,
            marital_status=payload.get('marital_status'),
            dependents=int(payload.get('dependents', 0)) if payload.get('dependents') else None,
            education=int(payload.get('education', 0)) if payload.get('education') else None,
            education_level=payload.get('education_level'),
            self_employed=int(payload.get('self_employed', 0)) if payload.get('self_employed') else None,
            applicant_income=float(payload.get('applicant_income', 0)) if payload.get('applicant_income') else None,
            coapplicant_income=float(payload.get('coapplicant_income', 0)) if payload.get('coapplicant_income') else None,
            loan_amount=float(payload.get('loan_amount', 0)) if payload.get('loan_amount') else None,
            loan_amount_term=float(payload.get('loan_tenure') or payload.get('loan_amount_term', 0)) if (payload.get('loan_tenure') or payload.get('loan_amount_term')) else None,
            credit_history=int(payload.get('credit_history', 0)) if payload.get('credit_history') else None,
            property_area=int(payload.get('property_area', 0)) if payload.get('property_area') else None,
            loan_purpose=payload.get('loan_purpose'),
            employment_type=payload.get('employment_type'),
            employment_status=payload.get('employment_status'),
            company_name=payload.get('company_name'),
            existing_loans=float(payload.get('existing_loans')) if payload.get('existing_loans') else None,
            collateral=payload.get('collateral'),
            collateral_type=payload.get('collateral_type'),
            collateral_value=float(payload.get('collateral_value', 0)) if payload.get('collateral_value') else None,
            financial_notes=payload.get('financial_notes'),
            application_status='Application Submitted'
        )
        
        # Create workflow
        workflow = LoanWorkflow(
            application_id=application_id,
            current_stage='application_submitted',
            stage_status='Application Submitted'
        )
        application_workflow = ApplicationWorkflow(
            application_id=application_id,
            stage='application_submitted',
            status='Application Submitted',
            admin_message=None,
        )
        
        db.session.add(application)
        db.session.add(workflow)
        db.session.add(application_workflow)
        commit_or_rollback()
        
        return jsonify({
            'status': 'success',
            'application_id': application_id,
            'message': 'Loan application created successfully'
        }), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications', methods=['GET'])
@login_required
def get_user_workflows():
    """Get all loan applications for current user"""
    try:
        applications = LoanApplication.query.filter_by(user_id=current_user.id).order_by(LoanApplication.created_at.desc()).all()
        workflows = []
        for application in applications:
            workflow = application.workflow or LoanWorkflow(application_id=application.application_id)
            workflows.append(create_workflow_snapshot(application))
        return jsonify({'status': 'success', 'workflows': workflows}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications/<application_id>', methods=['GET'])
@login_required
def get_workflow_details(application_id):
    """Get details of a specific loan application"""
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        return jsonify({'status': 'success', 'workflow': create_workflow_snapshot(application), 'application': serialize_application(application)}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/admin/workflow/applications', methods=['GET'])
@login_required
def get_all_workflows_admin():
    """Get all loan applications (admin only) - returns full application data for verification workbench"""
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
        applications = LoanApplication.query.order_by(LoanApplication.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'workflows': [create_workflow_snapshot(app) for app in applications],
            'applications': [serialize_application(app) for app in applications]
        }), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/admin/workflow/applications/<application_id>/stage', methods=['PUT'])
@login_required
def update_workflow_stage(application_id):
    """Update workflow stage (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

        payload = request.get_json(silent=True) or {}
        stage = payload.get('stage')
        status = payload.get('status')
        comment = payload.get('comment')

        if not stage:
            return jsonify({'status': 'error', 'message': 'Stage is required'}), 400

        valid_stages = ['application_submitted', 'documents_verification', 'ai_risk_analysis', 'admin_review', 'final_decision']
        if stage not in valid_stages:
            return jsonify({'status': 'error', 'message': 'Invalid stage'}), 400

        valid_statuses = ['Approved', 'Rejected', 'Need Correction', 'On Hold', 'In Progress']
        if status and status not in valid_statuses:
            return jsonify({'status': 'error', 'message': 'Invalid status'}), 400

        workflow = LoanWorkflow.query.filter_by(application_id=application_id).first_or_404()
        application = workflow.application
        old_stage = workflow.current_stage
        
        workflow.current_stage = stage
        ensure_application_workflow(application_id, stage=stage, status=status or workflow.stage_status, admin_message=comment)
        
        # Set stage status based on provided status or default
        if status:
            workflow.stage_status = status
        else:
            workflow.stage_status = {
                'application_submitted': 'Application Submitted',
                'documents_verification': 'Documents Verification Pending',
                'ai_risk_analysis': 'AI Risk Analysis Completed',
                'admin_review': 'Admin Review Pending',
                'final_decision': application.application_status if application.application_status in {'Approved', 'Rejected'} else 'Final Decision Pending',
            }[stage]
        
        # Update application status based on stage and status
        if status == 'Approved':
            if stage == 'documents_verification':
                application.application_status = 'Documents Approved'
            elif stage == 'ai_risk_analysis':
                application.application_status = 'Risk Analysis Approved'
            elif stage == 'admin_review':
                application.application_status = 'Admin Review Approved'
        elif status == 'Rejected':
            if stage == 'documents_verification':
                application.application_status = 'Documents Rejected'
            elif stage == 'ai_risk_analysis':
                application.application_status = 'Risk Analysis Rejected'
            elif stage == 'admin_review':
                application.application_status = 'Admin Review Rejected'
        elif status == 'Need Correction':
            application.application_status = 'Need Correction'
        elif status == 'On Hold':
            application.application_status = 'On Hold'
        elif status == 'In Progress':
            application.application_status = 'Under Review'
        
        # Persist admin remark and comment
        if comment:
            application.admin_comment = comment
            workflow.admin_comment = comment
            comment_type_map = {
                'documents_verification': 'Correction',
                'ai_risk_analysis': 'Approval',
                'admin_review': 'Approval',
                'final_decision': 'Approval',
            }
            comment_type = comment_type_map.get(stage, 'General')
            admin_comment = AdminComment(
                application_id=application_id,
                admin_id=current_user.id,
                comment=comment,
                comment_type=comment_type,
                is_visible_to_user=True,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(admin_comment)
        
        # Create workflow timeline entry
        create_workflow_timeline_entry(
            application_id=application_id,
            stage_name=format_stage_name(stage),
            stage_status=status or workflow.stage_status
        )
        
        # Create notification for user based on action
        notification_title = get_notification_title(status, stage)
        notification_message = get_notification_message(status, stage, application_id, comment)
        
        create_notification(
            user_id=application.user_id,
            title=notification_title,
            message=notification_message,
            notification_type='Workflow Update',
            application_id=application_id,
            priority='High',
            action_link=f'/workflow?application_id={application_id}'
        )
        
        commit_or_rollback()

        return jsonify({'status': 'success', 'message': 'Workflow stage updated successfully', 'workflow': create_workflow_snapshot(application)}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


def format_stage_name(stage):
    """Format stage name for display"""
    return stage.replace('_', ' ').title()


def get_notification_title(status, stage):
    """Get notification title based on status and stage"""
    if status == 'Approved':
        return f'{format_stage_name(stage)} Approved'
    elif status == 'Rejected':
        return f'{format_stage_name(stage)} Rejected'
    elif status == 'Need Correction':
        return 'Correction Required'
    elif status == 'On Hold':
        return 'Application On Hold'
    elif status == 'In Progress':
        return f'{format_stage_name(stage)} In Progress'
    return 'Workflow Updated'


def get_notification_message(status, stage, application_id, comment):
    """Get notification message based on status and stage"""
    base_message = f'Your loan application {application_id} '
    if status == 'Approved':
        return base_message + f'{format_stage_name(stage).lower()} has been approved.'
    elif status == 'Rejected':
        return base_message + f'{format_stage_name(stage).lower()} has been rejected.' + (f' Reason: {comment}' if comment else '')
    elif status == 'Need Correction':
        return base_message + f'requires correction for {format_stage_name(stage).lower()}.' + (f' Details: {comment}' if comment else '')
    elif status == 'On Hold':
        return base_message + 'has been put on hold.' + (f' Reason: {comment}' if comment else '')
    elif status == 'In Progress':
        return base_message + f'{format_stage_name(stage).lower()} is now in progress.'
    return base_message + 'workflow has been updated.'


@app.route('/api/admin/workflow/applications/<application_id>/decision', methods=['PUT'])
@login_required
def update_final_decision(application_id):
    """Update final decision (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

        payload = request.get_json(silent=True) or {}
        decision = payload.get('decision')
        remark = payload.get('remark')

        if not decision:
            return jsonify({'status': 'error', 'message': 'Decision is required'}), 400

        valid_decisions = ['Approved', 'Rejected', 'Pending']
        if decision not in valid_decisions:
            return jsonify({'status': 'error', 'message': 'Invalid decision'}), 400

        workflow = LoanWorkflow.query.filter_by(application_id=application_id).first_or_404()
        application = workflow.application
        application.application_status = decision
        application.admin_comment = remark
        workflow.admin_comment = remark
        workflow.current_stage = 'final_decision'
        workflow.stage_status = decision
        ensure_application_workflow(application_id, stage='final_decision', status=decision, admin_message=remark)

        if remark:
            db.session.add(AdminComment(
                application_id=application_id,
                admin_id=current_user.id,
                comment=remark,
                comment_type='Approval' if decision == 'Approved' else 'Rejection' if decision == 'Rejected' else 'General',
                is_visible_to_user=True,
                created_at=datetime.now(timezone.utc)
            ))

        create_workflow_timeline_entry(
            application_id=application_id,
            stage_name='Final Decision',
            stage_status=decision,
            action_by=current_user.id,
            admin_comment=remark
        )
        commit_or_rollback()

        notification = Notification(
            user_id=application.user_id,
            title=f'Loan Application {decision}',
            message=f'Your loan application {application.application_id} has been {decision}.',
            notification_type='loan_decision',
            is_read=False,
        )
        db.session.add(notification)
        commit_or_rollback()

        return jsonify({'status': 'success', 'message': 'Final decision updated successfully', 'workflow': create_workflow_snapshot(application)}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/admin/comments/<application_id>', methods=['GET'])
@login_required
def get_admin_comments(application_id):
    """Get admin comments for an application"""
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        comments = AdminComment.query.filter_by(application_id=application_id).order_by(AdminComment.created_at.desc()).all()
        
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'admin_id': comment.admin_id,
                'stage': comment.comment_type,
                'comment': comment.comment,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'created_at_formatted': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else 'Recently'
            })
        
        return jsonify({'status': 'success', 'comments': comments_data}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/notifications/application/<application_id>', methods=['GET'])
@login_required
def get_application_notifications(application_id):
    """Get notifications for a specific application"""
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        notifications = Notification.query.filter_by(application_id=application_id).order_by(Notification.created_at.desc()).limit(10).all()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
                'created_at_formatted': notification.created_at.strftime('%Y-%m-%d %H:%M') if notification.created_at else 'Recently'
            })
        
        return jsonify({'status': 'success', 'notifications': notifications_data}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications/<application_id>/documents', methods=['POST'])
@login_required
def upload_document(application_id):
    """Upload application documents"""
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403

        document_type = request.form.get('document_type', '').strip()
        document_name = request.form.get('document_name', '').strip()
        file = request.files.get('file')
        if not document_type or not document_name:
            return jsonify({'status': 'error', 'message': 'Document type and name are required'}), 400

        upload_folder = os.path.join(app.root_path, 'uploads', 'documents')
        os.makedirs(upload_folder, exist_ok=True)
        saved_name = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            saved_name = f"{uuid.uuid4().hex}_{filename}"
            file.save(os.path.join(upload_folder, saved_name))

        record = DocumentRecord(
            application_id=application.application_id,
            document_type=document_type,
            document_name=document_name,
            file_path=os.path.join('uploads', 'documents', saved_name) if saved_name else None,
            verification_status='Pending',
        )
        db.session.add(record)
        commit_or_rollback()
        return jsonify({'status': 'success', 'message': 'Document uploaded successfully', 'document': {
            'document_id': record.document_id,
            'document_type': record.document_type,
            'document_name': record.document_name,
            'verification_status': record.verification_status,
        }}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications/<application_id>/documents', methods=['GET'])
@login_required
def get_application_documents(application_id):
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        documents = [
            {
                'document_id': doc.document_id,
                'document_type': doc.document_type,
                'document_name': doc.document_name,
                'file_path': doc.file_path,
                'verification_status': doc.verification_status,
                'admin_remark': doc.admin_remark,
                'is_aadhaar': False,
            }
            for doc in application.documents.order_by(DocumentRecord.created_at.asc()).all()
        ]
        if application.aadhaar_document:
            documents.insert(0, {
                'document_id': application.aadhaar_document.id,
                'document_type': 'aadhaar',
                'document_name': application.aadhaar_document.file_name,
                'file_path': application.aadhaar_document.file_path,
                'verification_status': application.aadhaar_document.verification_status,
                'admin_remark': application.aadhaar_document.admin_remark,
                'is_aadhaar': True,
            })
        return jsonify({'status': 'success', 'documents': documents}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/documents/<application_id>', methods=['GET'])
@login_required
def get_documents(application_id):
    """Get documents for an application (alias route for frontend compatibility)"""
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        documents = [
            {
                'document_id': doc.document_id,
                'document_type': doc.document_type,
                'document_name': doc.document_name,
                'file_path': doc.file_path,
                'verification_status': doc.verification_status,
                'admin_remark': doc.admin_remark,
                'is_aadhaar': False,
            }
            for doc in application.documents.order_by(DocumentRecord.created_at.asc()).all()
        ]
        if application.aadhaar_document:
            documents.insert(0, {
                'document_id': application.aadhaar_document.id,
                'document_type': 'aadhaar',
                'document_name': application.aadhaar_document.file_name,
                'file_path': application.aadhaar_document.file_path,
                'verification_status': application.aadhaar_document.verification_status,
                'admin_remark': application.aadhaar_document.admin_remark,
                'is_aadhaar': True,
            })
        return jsonify({'status': 'success', 'documents': documents}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications/<application_id>/documents/<int:document_id>', methods=['PUT'])
@login_required
def update_document_status(application_id, document_id):
    """Update document verification status (admin only) - users cannot change this"""
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin access required. Users cannot modify document status.'}), 403
        record = DocumentRecord.query.filter_by(document_id=document_id, application_id=application_id).first_or_404()
        payload = request.get_json(silent=True) or {}
        status = payload.get('verification_status', 'Approved')
        remark = payload.get('admin_remark')
        record.verification_status = status
        record.admin_remark = remark
        commit_or_rollback()
        return jsonify({'status': 'success', 'message': 'Document status updated'}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications/<application_id>/risk-analysis', methods=['POST'])
@login_required
def update_risk_analysis(application_id):
    """Update AI risk analysis (admin only) - users cannot change this"""
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin access required. Users cannot modify risk analysis.'}), 403
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        payload = request.get_json(silent=True) or {}
        risk_level = payload.get('risk_level') or 'Medium Risk'
        risk_score = payload.get('risk_score')
        probability = payload.get('approval_probability')
        application.ai_risk_level = risk_level
        application.ai_risk_score = risk_score
        application.approval_probability = probability
        application.application_status = 'AI Risk Analysis Completed'
        workflow = application.workflow
        if workflow:
            workflow.current_stage = 'admin_review'
            workflow.stage_status = 'AI Risk Analysis Completed'
        commit_or_rollback()
        return jsonify({'status': 'success', 'workflow': create_workflow_snapshot(application)}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/workflow/applications/<application_id>/conversation', methods=['GET', 'POST'])
@login_required
def workflow_conversation(application_id):
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403

        if request.method == 'POST':
            payload = request.get_json(silent=True) or {}
            message = (payload.get('message') or '').strip()
            reply = (payload.get('reply') or '').strip()
            if not message and not reply:
                return jsonify({'status': 'error', 'message': 'Message or reply is required'}), 400
            chat = SupportChat(application_id=application.application_id, user_id=current_user.id, admin_id=current_user.id if current_user.is_admin else None, message=message or 'Admin update', reply=reply or None)
            db.session.add(chat)
            commit_or_rollback()
            return jsonify({'status': 'success', 'chat': {'message': chat.message, 'reply': chat.reply, 'timestamp': chat.timestamp.isoformat() if chat.timestamp else None}}), 200

        chats = SupportChat.query.filter_by(application_id=application.application_id).order_by(SupportChat.timestamp.asc()).all()
        return jsonify({'status': 'success', 'chats': [{
            'message': chat.message,
            'reply': chat.reply,
            'timestamp': chat.timestamp.isoformat() if chat.timestamp else None,
        } for chat in chats]}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500



@app.route('/api/chat/messages/<application_id>', methods=['GET'])
@login_required
def get_chat_messages(application_id):
    """Get chat messages for an application"""
    try:
        application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
        
        # Check access
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        messages = SupportChat.query.filter_by(application_id=application_id)\
            .order_by(SupportChat.timestamp.asc()).all()
        
        return jsonify({
            'status': 'success',
            'messages': [{
                'chat_id': msg.chat_id,
                'user_id': msg.user_id,
                'admin_id': msg.admin_id,
                'message': msg.message,
                'reply': msg.reply,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                'timestamp_formatted': msg.timestamp.strftime('%b %d, %Y %H:%M') if msg.timestamp else '',
                'is_admin': msg.admin_id is not None
            } for msg in messages]
        }), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/chat/messages', methods=['POST'])
@login_required
def send_chat_message():
    """Send chat message"""
    try:
        payload = request.get_json(silent=True) or {}
        message = payload.get('message')
        application_id = payload.get('application_id')
        
        if not message:
            return jsonify({'status': 'error', 'message': 'Message is required'}), 400
        
        # Verify application access
        if application_id:
            application = LoanApplication.query.filter_by(application_id=application_id).first_or_404()
            if application.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        chat = SupportChat(
            user_id=current_user.id,
            admin_id=current_user.id if current_user.is_admin else None,
            application_id=application_id,
            message=message
        )
        db.session.add(chat)
        
        # Notify admin if user sends message
        if not current_user.is_admin and application_id:
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title='New Chat Message',
                    message=f'User sent a message for application {application_id}.',
                    notification_type='chat_message',
                    is_read=False
                )
                db.session.add(notification)
        
        commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'Message sent successfully'}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/admin/chat/messages/<int:chat_id>/reply', methods=['PUT'])
@login_required
def reply_chat_message(chat_id):
    """Reply to chat message (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
        
        payload = request.get_json(silent=True) or {}
        reply = payload.get('reply')
        
        if not reply:
            return jsonify({'status': 'error', 'message': 'Reply is required'}), 400
        
        chat = SupportChat.query.get_or_404(chat_id)
        chat.reply = reply
        chat.admin_id = current_user.id
        
        # Notify user
        notification = Notification(
            user_id=chat.user_id,
            title='Admin Reply',
            message=f'Admin replied to your message for application {chat.application_id}.',
            notification_type='chat_reply',
            is_read=False
        )
        db.session.add(notification)
        
        commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'Reply sent successfully'}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<path:filename>')
@login_required
def serve_uploaded_file(filename):
    """Serve uploaded documents for admin/user preview with path traversal protection"""
    try:
        clean_path = filename.replace('\\', '/')
        if clean_path.startswith('uploads/'):
            clean_path = clean_path[8:]
        
        uploads_dir = os.path.abspath(os.path.join(app.root_path, 'uploads'))
        target_file = os.path.abspath(os.path.join(uploads_dir, clean_path))
        
        if not target_file.startswith(uploads_dir):
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        if not os.path.exists(target_file):
            return jsonify({'status': 'error', 'message': 'File not found'}), 404

        dir_name = os.path.dirname(target_file)
        base_name = os.path.basename(target_file)
        return send_from_directory(dir_name, base_name)
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/enterprise-application')
@login_required
def enterprise_application_page():
    """Enterprise application submission page"""
    return render_template('enterprise_application.html')


@app.route('/predict')
@login_required
def prediction_page():
    """Prediction page"""
    return render_template('predict.html')


@app.route('/history')
@login_required
def prediction_history_page():
    """Prediction history page"""
    return render_template('history.html')


@app.route('/api/predict', methods=['POST'])
def predict_loan_application():
    """Generate an ML-style prediction result and persist it for analytics."""
    try:
        payload = request.get_json(silent=True) or {}
        applicant_income = float(payload.get('applicant_income', 0) or 0)
        coapplicant_income = float(payload.get('coapplicant_income', 0) or 0)
        loan_amount = float(payload.get('loan_amount', 0) or 0)
        loan_term = float(payload.get('loan_amount_term', payload.get('loan_tenure', 0)) or 0)
        credit_history = int(payload.get('credit_history', 0) or 0)
        property_area = int(payload.get('property_area', 0) or 0)

        feature_vector = np.array([
            float(payload.get('gender', 0) or 0),
            float(payload.get('married', 0) or 0),
            float(payload.get('dependents', 0) or 0),
            float(payload.get('education', 0) or 0),
            float(payload.get('self_employed', 0) or 0),
            applicant_income,
            coapplicant_income,
            loan_amount,
            loan_term,
            credit_history,
            property_area,
        ], dtype=float).reshape(1, -1)

        if model is not None and scaler is not None:
            scaled_features = scaler.transform(feature_vector)
            prediction_prob = float(model.predict_proba(scaled_features)[0][1])
        else:
            prediction_prob = float(HeuristicModel().predict_proba(feature_vector)[0][1])

        prediction_result = 'Approved' if prediction_prob >= 0.5 else 'Rejected'
        risk_score = round((1 - prediction_prob) * 100, 1)
        risk_level = 'Low Risk' if prediction_prob >= 0.75 else 'Medium Risk' if prediction_prob >= 0.5 else 'High Risk'

        application_id = payload.get('application_id')
        if application_id:
            application = LoanApplication.query.filter_by(application_id=application_id).first()
            if application:
                application.approval_probability = prediction_prob
                application.ai_risk_level = risk_level
                application.ai_risk_score = risk_score

        input_features = {
            'gender': payload.get('gender'),
            'married': payload.get('married'),
            'dependents': payload.get('dependents'),
            'education': payload.get('education'),
            'self_employed': payload.get('self_employed'),
            'applicant_income': applicant_income,
            'coapplicant_income': coapplicant_income,
            'loan_amount': loan_amount,
            'loan_amount_term': loan_term,
            'credit_history': credit_history,
            'property_area': property_area,
            'credit_score': payload.get('credit_score') or 0,
        }

        prediction_record = LoanPrediction(
            user_id=current_user.id if current_user.is_authenticated else None,
            application_id=application_id,
            input_features=json.dumps(input_features),
            prediction_result=prediction_result,
            prediction_probability=prediction_prob,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(prediction_record)

        # Only save to prediction_history when a valid application exists.
        # The prediction_history table has NOT NULL + FK constraints on
        # application_id, so standalone predictions (no application_id) must
        # be skipped here to avoid an IntegrityError.
        valid_application = None
        if application_id and current_user.is_authenticated:
            valid_application = LoanApplication.query.filter_by(
                application_id=application_id
            ).first()
            if valid_application and valid_application.user_id != current_user.id and not current_user.is_admin:
                valid_application = None

        if valid_application is not None:
            # Normalize risk_level to match the ENUM('Low','Medium','High') column.
            history_risk_level = risk_level.replace(' Risk', '')
            history = PredictionHistory(
                application_id=application_id,
                user_id=current_user.id,
                prediction_result=prediction_result,
                approval_probability=prediction_prob,
                risk_score=risk_score,
                risk_level=history_risk_level,
                loan_amount=loan_amount,
                loan_amount_term=loan_term,
                monthly_income=applicant_income,
                credit_score=payload.get('credit_score') or 0,
                model_version='1.0',
                prediction_date=datetime.now(timezone.utc),
                is_current_prediction=True,
            )
            PredictionHistory.query.filter_by(
                user_id=current_user.id, is_current_prediction=True
            ).update({'is_current_prediction': False})
            db.session.add(history)

        commit_or_rollback()

        return jsonify({
            'status': 'success',
            'prediction_result': prediction_result,
            'approval_probability': round(prediction_prob, 4),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'message': 'Prediction generated successfully',
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/prediction/history', methods=['GET'])
@login_required
def get_prediction_history():
    """Get prediction history for current user"""
    try:
        predictions = PredictionHistory.query.filter_by(user_id=current_user.id).order_by(PredictionHistory.prediction_date.desc()).all()
        
        history_data = []
        for pred in predictions:
            history_data.append({
                'id': pred.id,
                'application_id': pred.application_id or f"PRED-{pred.id}",
                'prediction_result': pred.prediction_result,
                'approval_probability': pred.approval_probability or 0.75,
                'risk_score': pred.risk_score or 25.0,
                'risk_level': pred.risk_level or 'Medium',
                'loan_amount': pred.loan_amount or 0.0,
                'loan_amount_term': pred.loan_amount_term or 36.0,
                'monthly_income': pred.monthly_income or 0.0,
                'credit_score': pred.credit_score or 700,
                'model_version': pred.model_version or '1.0',
                'prediction_date': pred.prediction_date.isoformat() if pred.prediction_date else None,
                'is_current_prediction': pred.is_current_prediction
            })
            
        if not history_data:
            loan_preds = LoanPrediction.query.filter_by(user_id=current_user.id).order_by(LoanPrediction.created_at.desc()).all()
            for lp in loan_preds:
                features = json.loads(lp.input_features or '{}')
                prob = lp.prediction_probability or 0.75
                r_score = round((1 - prob) * 100, 1)
                r_level = 'Low' if prob >= 0.75 else 'Medium' if prob >= 0.5 else 'High'
                history_data.append({
                    'id': lp.prediction_id,
                    'application_id': lp.application_id or f"PRED-{lp.prediction_id}",
                    'prediction_result': lp.prediction_result,
                    'approval_probability': prob,
                    'risk_score': r_score,
                    'risk_level': r_level,
                    'loan_amount': float(features.get('loan_amount', 0) or 0),
                    'loan_amount_term': float(features.get('loan_amount_term', 36) or 36),
                    'monthly_income': float(features.get('applicant_income', 0) or 0),
                    'credit_score': int(features.get('credit_score', 700) or 700),
                    'model_version': '1.0',
                    'prediction_date': lp.created_at.isoformat() if lp.created_at else None,
                    'is_current_prediction': True
                })
        
        return jsonify({'status': 'success', 'predictions': history_data}), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/prediction/history', methods=['POST'])
@login_required
def save_prediction_to_history_api():
    """Save prediction to history via API"""
    try:
        payload = request.get_json(silent=True) or {}

        application_id = payload.get('application_id')
        if not application_id:
            return jsonify({'status': 'error', 'message': 'application_id is required'}), 400

        # Verify the application exists and belongs to this user (or admin)
        application = LoanApplication.query.filter_by(application_id=application_id).first()
        if not application:
            return jsonify({'status': 'error', 'message': 'Application not found'}), 404
        if application.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403

        # Normalize risk_level to match the ENUM('Low','Medium','High') column.
        raw_risk_level = payload.get('risk_level') or 'Medium Risk'
        risk_level = str(raw_risk_level).replace(' Risk', '')
        if risk_level not in ('Low', 'Medium', 'High'):
            risk_level = 'Medium'

        history = PredictionHistory(
            application_id=application_id,
            user_id=current_user.id,
            prediction_result=payload.get('prediction_result'),
            approval_probability=payload.get('approval_probability'),
            risk_score=payload.get('risk_score'),
            risk_level=risk_level,
            loan_amount=payload.get('loan_amount'),
            loan_amount_term=payload.get('loan_amount_term'),
            monthly_income=payload.get('monthly_income'),
            credit_score=payload.get('credit_score'),
            model_version='1.0',
            prediction_date=datetime.now(timezone.utc),
            is_current_prediction=True
        )
        
        # Mark previous predictions as not current
        PredictionHistory.query.filter_by(user_id=current_user.id, is_current_prediction=True).update({'is_current_prediction': False})
        
        db.session.add(history)
        commit_or_rollback()
        
        return jsonify({'status': 'success', 'message': 'Prediction saved to history'}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/admin/prediction-analytics', methods=['GET'])
@login_required
def admin_prediction_analytics():
    """Return prediction-based analytics for the admin panel."""
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    return jsonify(build_prediction_analytics_payload(is_admin=True)), 200


@app.route('/api/enterprise/application/submit', methods=['POST'])
@login_required
def submit_enterprise_application():
    """Submit enterprise loan application"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
        
        # Check if user already has an active application
        existing_application = LoanApplication.query.filter_by(
            user_id=current_user.id
        ).filter(
            LoanApplication.application_status.in_([
                'Application Submitted', 'Documents Pending', 'Documents Approved',
                'Risk Analysis Running', 'Waiting for Admin', 'Need Correction', 'On Hold'
            ])
        ).first()
        
        if existing_application:
            return jsonify({
                'status': 'error',
                'message': f'You already have an active application: {existing_application.application_id}'
            }), 400
        
        # Generate application IDs
        application_id = generate_application_id()
        application_number = generate_application_number()
        
        # Get form data
        form_data = request.form.to_dict()
        
        # Get Aadhaar file
        aadhaar_file = request.files.get('aadhaar_file')
        if not aadhaar_file:
            return jsonify({'status': 'error', 'message': 'Aadhaar document is required'}), 400
        
        # Save Aadhaar file
        upload_folder = os.path.join(app.root_path, 'uploads', 'aadhaar')
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(aadhaar_file.filename)
        saved_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join('uploads', 'aadhaar', saved_name)
        aadhaar_file.save(os.path.join(upload_folder, saved_name))
        
        # Create loan application
        application = LoanApplication(
            application_id=application_id,
            user_id=current_user.id,
            application_number=application_number,
            
            # Personal Information
            full_name=form_data.get('full_name'),
            date_of_birth=form_data.get('date_of_birth'),
            gender=convert_gender_to_int(form_data.get('gender')),
            marital_status=form_data.get('marital_status'),
            dependents=int(form_data.get('dependents', 0)) if form_data.get('dependents') else 0,
            
            # Contact Information
            email_address=form_data.get('email_address'),
            phone_number=form_data.get('phone_number'),
            alternate_phone=form_data.get('alternate_phone'),
            address=form_data.get('address'),
            city=form_data.get('city'),
            state=form_data.get('state'),
            pincode=form_data.get('pincode'),
            
            # Employment Details
            employment_type=form_data.get('employment_type'),
            employment_status=form_data.get('employment_status'),
            company_name=form_data.get('company_name'),
            work_experience_years=safe_float_convert(form_data.get('work_experience_years'), None),
            monthly_income=safe_float_convert(form_data.get('monthly_income')),
            
            # Financial Information
            annual_income=safe_float_convert(form_data.get('annual_income')),
            other_income=safe_float_convert(form_data.get('other_income')),
            existing_loans=safe_float_convert(form_data.get('existing_loans')),
            monthly_debt=safe_float_convert(form_data.get('monthly_debt')),
            credit_score=safe_int_convert(form_data.get('credit_score'), None),
            credit_history=safe_int_convert(form_data.get('credit_history')),
            
            # Loan Information
            loan_amount=safe_float_convert(form_data.get('loan_amount')),
            loan_purpose=form_data.get('loan_purpose'),
            loan_amount_term=safe_float_convert(form_data.get('loan_amount_term')),
            collateral_type=form_data.get('collateral_type'),
            collateral_value=safe_float_convert(form_data.get('collateral_value'), None),
            
            # Education
            education_level=form_data.get('education_level'),
            
            # Property Information
            property_area=safe_int_convert(form_data.get('property_area')),
            
            # Status
            application_status='Application Submitted',
            submitted_at=datetime.now(timezone.utc),
        )
        
        db.session.add(application)
        db.session.flush()
        
        # Create Aadhaar document record
        aadhaar_file.seek(0)  # Reset file pointer to beginning
        file_size = len(aadhaar_file.read())
        aadhaar_doc = AadhaarDocument(
            application_id=application_id,
            file_path=file_path,
            file_name=filename,
            file_size=file_size,
            upload_date=datetime.now(timezone.utc),
            verification_status='Pending'
        )
        db.session.add(aadhaar_doc)
        
        # Create workflow
        workflow = LoanWorkflow(
            application_id=application_id,
            current_stage='application_submitted',
            stage_status='Application Submitted'
        )
        db.session.add(workflow)
        
        # Create workflow timeline entry for Application Submitted
        create_workflow_timeline_entry(
            application_id=application_id,
            stage_name='Application Submitted',
            stage_status='In Progress'
        )
        
        # Create notification for user
        create_notification(
            user_id=current_user.id,
            title='Application Submitted Successfully',
            message=f'Your loan application {application_id} has been submitted successfully.',
            notification_type='Application Submitted',
            application_id=application_id,
            priority='High',
            action_link=f'/workflow?application_id={application_id}'
        )
        
        commit_or_rollback()
        
        return jsonify({
            'status': 'success',
            'message': 'Application submitted successfully',
            'application_id': application_id,
            'application_number': application_number
        }), 201
        
    except Exception as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        if User.query.count() == 0 or not User.query.filter_by(is_admin=True).first():
            user.is_admin = True

        db.session.add(user)
        try:
            commit_or_rollback()
            print(f"User '{username}' registered successfully and saved to MySQL database with ID: {user.id}")
        except Exception as exc:
            print(f"Error saving user to MySQL database: {exc}")
            import traceback
            traceback.print_exc()
            flash(f'Could not save user: {exc}', 'danger')
            return redirect(url_for('register'))

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/make-me-admin')
@login_required
def make_me_admin():
    """Route to make current user admin (requires secret setup key)"""
    key = request.args.get('key', '')
    secret = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_123')
    if key != secret and not current_user.is_admin:
        flash('Access denied. Admin setup key required.', 'danger')
        return redirect(url_for('home'))
    current_user.is_admin = True
    db.session.commit()
    flash('Admin privileges granted!', 'success')
    return redirect(url_for('home'))

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/emi-calculator')
@login_required
def emi_calculator():
    return render_template('emi_calculator.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('home'))

    users = User.query.all()
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    regular_users = total_users - admin_users

    return render_template('admin.html', users=users, total_users=total_users,
                           admin_users=admin_users, regular_users=regular_users)

@app.route('/admin/workflow')
@login_required
def admin_workflow_page():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('home'))

    return render_template('admin_workflow.html')


@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'User {user.username} is now an admin.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/remove_admin/<int:user_id>')
@login_required
def remove_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot remove your own admin status.', 'danger')
        return redirect(url_for('admin'))
    
    user.is_admin = False
    db.session.commit()
    flash(f'Admin status removed from {user.username}.', 'success')
    return redirect(url_for('admin'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Public analytics API endpoint (aggregated system data)
@app.route('/api/public-analytics')
def public_analytics_api():
    try:
        all_predictions = LoanPrediction.query.order_by(LoanPrediction.created_at.asc()).all()
        all_users = User.query.count()

        if not all_predictions:
            return jsonify({
                'total_applications': 0,
                'total_users': all_users,
                'total_approved': 0,
                'total_rejected': 0,
                'approval_rate': 0,
                'rejection_rate': 0,
                'average_loan_amount': 0,
                'approval_vs_rejection': [0, 0],
                'prediction_trends': [],
                'approved_trends': [],
                'rejected_trends': []
            })

        approved_count = sum(1 for p in all_predictions if p.prediction_result == 'Approved')
        rejected_count = sum(1 for p in all_predictions if p.prediction_result == 'Rejected')
        total_count = len(all_predictions)
        approval_rate = round((approved_count / total_count * 100) if total_count > 0 else 0, 1)
        rejection_rate = round((rejected_count / total_count * 100) if total_count > 0 else 0, 1)

        avg_loan = round(sum(float(json.loads(p.input_features or '{}').get('loan_amount', 0) or 0) for p in all_predictions) / total_count, 2) if total_count > 0 else 0

        approved_trends = defaultdict(int)
        rejected_trends = defaultdict(int)
        all_trends = defaultdict(int)

        for prediction in all_predictions:
            date_key = prediction.created_at.strftime('%Y-%m-%d') if prediction.created_at else 'unknown'
            all_trends[date_key] += 1
            if prediction.prediction_result == 'Approved':
                approved_trends[date_key] += 1
            elif prediction.prediction_result == 'Rejected':
                rejected_trends[date_key] += 1

        sorted_all_trends = sorted(all_trends.items())
        sorted_approved_trends = sorted(approved_trends.items())
        sorted_rejected_trends = sorted(rejected_trends.items())

        return jsonify({
            'total_applications': total_count,
            'total_users': all_users,
            'total_approved': approved_count,
            'total_rejected': rejected_count,
            'approval_rate': approval_rate,
            'rejection_rate': rejection_rate,
            'average_loan_amount': avg_loan,
            'approval_vs_rejection': [approved_count, rejected_count],
            'prediction_trends': [{'date': date, 'count': count} for date, count in sorted_all_trends],
            'approved_trends': [{'date': date, 'count': count} for date, count in sorted_approved_trends],
            'rejected_trends': [{'date': date, 'count': count} for date, count in sorted_rejected_trends],
            'probabilities': [p.prediction_probability for p in all_predictions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Analytics API endpoint
@app.route('/api/analytics')
@login_required
def analytics_api():
    try:
        user_predictions = LoanPrediction.query.filter_by(user_id=current_user.id).order_by(LoanPrediction.created_at.desc()).all()

        if not user_predictions:
            return jsonify({
                'total_predictions': 0,
                'approved_count': 0,
                'rejected_count': 0,
                'approval_rate': 0,
                'average_loan_amount': 0,
                'average_credit_score': 0,
                'max_loan_amount': 0,
                'approval_vs_rejection': [0, 0],
                'prediction_trends': [],
                'loan_amount_analysis': {'approved': [], 'rejected': []},
                'credit_scatter': []
            })

        approved = [p for p in user_predictions if p.prediction_result == 'Approved']
        rejected = [p for p in user_predictions if p.prediction_result == 'Rejected']
        total_count = len(user_predictions)
        approved_count = len(approved)
        rejected_count = len(rejected)
        approval_rate = round((approved_count / total_count * 100) if total_count > 0 else 0, 1)

        avg_loan = round(sum(float(json.loads(p.input_features or '{}').get('loan_amount', 0) or 0) for p in user_predictions) / total_count, 2) if total_count > 0 else 0
        avg_credit = round(sum(float(json.loads(p.input_features or '{}').get('credit_score', 0) or 0) for p in user_predictions) / total_count, 2) if total_count > 0 else 0
        max_loan = max((float(json.loads(p.input_features or '{}').get('loan_amount', 0) or 0) for p in user_predictions), default=0)

        trends = defaultdict(int)
        for prediction in user_predictions:
            if prediction.created_at:
                trends[prediction.created_at.strftime('%Y-%m-%d')] += 1
        sorted_trends = sorted(trends.items())

        approved_amounts = [float(json.loads(p.input_features or '{}').get('loan_amount', 0) or 0) for p in approved]
        rejected_amounts = [float(json.loads(p.input_features or '{}').get('loan_amount', 0) or 0) for p in rejected]
        scatter_data = []
        for prediction in user_predictions:
            features = json.loads(prediction.input_features or '{}')
            scatter_data.append({
                'x': features.get('credit_score', 0) or 0,
                'y': features.get('loan_amount', 0) or 0,
                'status': prediction.prediction_result,
            })

        return jsonify({
            'total_predictions': total_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'approval_rate': approval_rate,
            'average_loan_amount': avg_loan,
            'average_credit_score': avg_credit,
            'max_loan_amount': max_loan,
            'approval_vs_rejection': [approved_count, rejected_count],
            'prediction_trends': [{'date': date, 'count': count} for date, count in sorted_trends],
            'loan_amount_analysis': {
                'approved': approved_amounts,
                'rejected': rejected_amounts
            },
            'credit_scatter': scatter_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Analytics page route
@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

# Create database tables and ensure proper session handling
with app.app_context():
    try:
        # Create tables in existing loan_app_db database
        db.create_all()
        print("Database tables checked/created successfully in loan_app_db.")
    except Exception as e:
        print(f"Error checking database tables: {e}")
        # Try to handle existing tables gracefully
        pass

    # Load the ML model at startup so it is available for all entry points
    load_model()
    print(f"ML model loaded: {'loan_model.pkl' if os.path.exists(os.path.join(app.root_path, 'models', 'loan_model.pkl')) else 'Heuristic fallback'}")

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)
    
