# Loan Approval Prediction Web Application

A professional, production-ready web application for predicting loan approvals using machine learning. Built with Flask, Bootstrap 5, and scikit-learn.

## Features

- **Modern UI**: Clean, responsive design using Bootstrap 5
- **ML Integration**: Ready to integrate trained machine learning models
- **Real-time Predictions**: Instant loan approval predictions
- **Input Validation**: Comprehensive form validation
- **Mobile Friendly**: Fully responsive across all devices
- **Multiple Pages**: Home, About, Prediction, and Contact pages
- **Secure**: Data validation and error handling
- **Professional Design**: Gradient backgrounds, smooth animations, and modern aesthetics

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Machine Learning**: scikit-learn, NumPy, Pandas
- **Styling**: Custom CSS with gradient designs
- **Icons**: Bootstrap Icons

## Project Structure

```
Bank_Project/
├── app.py                 # Flask application with routes and API
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── models/               # Directory for ML model files
│   ├── loan_model.pkl    # Trained ML model (to be added)
│   └── scaler.pkl        # Feature scaler (to be added)
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── home.html         # Home page
│   ├── about.html        # About page
│   ├── predict.html      # Prediction page with form
│   └── contact.html      # Contact page
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Custom CSS styling
    └── js/
        └── script.js     # JavaScript functionality
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd Bank_Project
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your trained ML model**
   - Place your trained model file as `models/loan_model.pkl`
   - Place your scaler file as `models/scaler.pkl` (if using feature scaling)
   - The model should be a scikit-learn model with `predict()` method
   - Optional: Include `predict_proba()` for probability estimates

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   - Navigate to `http://localhost:5000`
   - The application will be running on port 5000

## Usage

### Making Predictions

1. Navigate to the **Prediction** page
2. Fill in the loan application form with:
   - Personal information (gender, marital status, dependents, education, employment)
   - Financial information (income, loan amount, loan term, credit history)
   - Property details (property area)
3. Click **Get Prediction**
4. View the instant prediction result with confidence score

### Form Fields

The prediction form includes the following fields:

**Personal Information:**
- Gender: Male/Female
- Marital Status: Married/Unmarried
- Dependents: 0, 1, 2, or 3+
- Education: Graduate/Not Graduate
- Self Employed: Yes/No
- Property Area: Urban/Semi-Urban/Rural

**Financial Information:**
- Applicant Income: Annual income in dollars
- Coapplicant Income: Coapplicant's annual income in dollars
- Loan Amount: Requested loan amount in dollars
- Loan Term: Loan repayment period in days (default: 360)
- Credit History: Good (1) or Bad (0)

## ML Model Integration

### Model Requirements

Your ML model should:
- Be saved as a pickle file (`loan_model.pkl`)
- Be trained on loan approval data with the following features:
  1. Gender (0/1)
  2. Married (0/1)
  3. Dependents (0/1/2/3)
  4. Education (0/1)
  5. Self Employed (0/1)
  6. Applicant Income (float)
  7. Coapplicant Income (float)
  8. Loan Amount (float)
  9. Loan Amount Term (float)
  10. Credit History (0/1)
  11. Property Area (0/1/2)

- Have a `predict()` method that returns 0 (Rejected) or 1 (Approved)
- Optionally have a `predict_proba()` method for confidence scores

### Example Model Training Code Structure

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import pickle

# Load your dataset
df = pd.read_csv('loan_data.csv')

# Preprocess data
# ... your preprocessing steps ...

# Split features and target
X = df[['gender', 'married', 'dependents', 'education', 'self_employed', 
        'applicant_income', 'coapplicant_income', 'loan_amount', 
        'loan_amount_term', 'credit_history', 'property_area']]
y = df['loan_status']

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_scaled, y)

# Save model and scaler
pickle.dump(model, open('models/loan_model.pkl', 'wb'))
pickle.dump(scaler, open('models/scaler.pkl', 'wb'))
```

## API Endpoint

### POST /api/predict

Accepts JSON data with loan application details and returns prediction.

**Request Body:**
```json
{
    "gender": 1,
    "married": 1,
    "dependents": 0,
    "education": 0,
    "self_employed": 0,
    "applicant_income": 5000,
    "coapplicant_income": 2000,
    "loan_amount": 150000,
    "loan_amount_term": 360,
    "credit_history": 1,
    "property_area": 0
}
```

**Response:**
```json
{
    "prediction": "Approved",
    "probability": 0.85,
    "status": "success"
}
```

## Deployment

### Deploying to Render

1. Create a `Procfile` in the project root:
   ```
   web: python app.py
   ```

2. Create a `.gitignore` file:
   ```
   venv/
   __pycache__/
   *.pyc
   .DS_Store
   ```

3. Push your code to GitHub

4. Create a new account on [Render](https://render.com)

5. Connect your GitHub repository

6. Create a new Web Service
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Select Python as the runtime

7. Deploy and get your live URL

### Deploying to Railway

1. Similar to Render, create a Railway account

2. Connect your GitHub repository

3. Create a new service from your repository

4. Configure the build and start commands

5. Deploy and get your live URL

### Deploying to Hugging Face Spaces

1. Create a Hugging Face account

2. Create a new Space with Flask template

3. Upload your project files

4. The application will be deployed automatically

## Configuration

### Environment Variables

You can configure the following in `app.py`:

- `SECRET_KEY`: Flask secret key for session management
- `DEBUG`: Enable/disable debug mode
- `HOST`: Server host address
- `PORT`: Server port number

## Testing

### Manual Testing

1. Start the application: `python app.py`
2. Open `http://localhost:5000` in your browser
3. Test each page:
   - Home page should load with hero section
   - About page should display information
   - Prediction page should show the form
   - Contact page should display contact form
4. Test the prediction form:
   - Fill in all fields
   - Submit the form
   - Verify prediction result displays correctly
5. Test form validation:
   - Try submitting empty fields
   - Verify validation messages appear
   - Test with invalid data types

### Testing Without ML Model

The application includes a mock prediction mode that works without an ML model:
- It uses credit history as a simple predictor
- This allows testing the UI before model integration
- Once you add your model, it will automatically use it

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change the port in app.py or kill the process using port 5000
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Module not found:**
```bash
# Ensure you installed dependencies
pip install -r requirements.txt
```

**Model not loading:**
- Ensure the `models/` directory exists
- Check that `loan_model.pkl` is in the correct location
- Verify the model file is not corrupted

## Security Considerations

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive configuration
- Implement rate limiting for the API endpoint
- Add CSRF protection for forms
- Use HTTPS in production
- Sanitize user inputs
- Implement proper authentication if needed

## Future Enhancements

- User authentication and login
- Database integration for storing predictions
- Admin dashboard for viewing analytics
- Email notifications for predictions
- Multi-language support
- Advanced visualization of prediction factors
- Export prediction results to PDF
- Integration with actual banking APIs

## License

This project is for educational and demonstration purposes.

## Support

For support or questions:
- Email: info@loanpredict.com
- Open an issue on GitHub

## Credits

Built with Flask, Bootstrap 5, and scikit-learn.
Icons provided by Bootstrap Icons.
