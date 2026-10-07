import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Load dataset from model folder
csv_path = os.path.join('model', 'Loan_Data.csv')
if not os.path.exists(csv_path):
    csv_path = 'Loan_Data.csv'

df = pd.read_csv(csv_path)

# Data Imputation & Cleaning
df['Married'] = df['Married'].fillna(df['Married'].mode()[0])
df['Gender'] = df['Gender'].fillna(df['Gender'].mode()[0])
df['Dependents'] = df['Dependents'].fillna(df['Dependents'].mode()[0])
df['Self_Employed'] = df['Self_Employed'].fillna(df['Self_Employed'].mode()[0])
df['LoanAmount'] = df['LoanAmount'].fillna(df['LoanAmount'].median())
df['Loan_Amount_Term'] = df['Loan_Amount_Term'].fillna(df['Loan_Amount_Term'].mode()[0])
df['Credit_History'] = df['Credit_History'].fillna(df['Credit_History'].mode()[0])

# Encodings matching Main.ipynb
df['Gender_Encoded'] = df['Gender'].map({'Male': 1.0, 'Female': 0.0}).fillna(1.0)
df['Married_Encoded'] = df['Married'].map({'Yes': 1.0, 'No': 0.0}).fillna(0.0)

df['Dependents_Clean'] = df['Dependents'].astype(str).str.replace('+', '', regex=False)
df['Dependents_Clean'] = pd.to_numeric(df['Dependents_Clean'], errors='coerce').fillna(0.0)

df['Education_Encoded'] = df['Education'].map({'Graduate': 0.0, 'Not Graduate': 1.0}).fillna(0.0)
df['Self_Employed_Encoded'] = df['Self_Employed'].map({'Yes': 1.0, 'No': 0.0}).fillna(0.0)
df['Property_Area_Encoded'] = df['Property_Area'].map({'Rural': 0.0, 'Urban': 1.0, 'Semiurban': 2.0}).fillna(2.0)
df['Loan_Status_Target'] = df['Loan_Status'].map({'Y': 1, 'N': 0}).fillna(1)

# Feature Columns (11 features expected by app.py)
feature_cols = [
    'Gender_Encoded',
    'Married_Encoded',
    'Dependents_Clean',
    'Education_Encoded',
    'Self_Employed_Encoded',
    'ApplicantIncome',
    'CoapplicantIncome',
    'LoanAmount',
    'Loan_Amount_Term',
    'Credit_History',
    'Property_Area_Encoded'
]

X = df[feature_cols].values.astype(float)
y = df['Loan_Status_Target'].values.astype(int)

# Fit Scaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Random Forest Classifier (Tuned max_depth=4 giving ~82.5% accuracy)
rf_model = RandomForestClassifier(n_estimators=150, max_depth=4, random_state=42)
rf_model.fit(X_scaled, y)

accuracy = rf_model.score(X_scaled, y) * 100
print(f"=== Model Trained Successfully ===")
print(f"Accuracy Score: {accuracy:.2f}%")

# Save serialized model & scaler to models/ directory
os.makedirs('models', exist_ok=True)
model_path = os.path.join('models', 'loan_model.pkl')
scaler_path = os.path.join('models', 'scaler.pkl')

with open(model_path, 'wb') as f:
    pickle.dump(rf_model, f)

with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)

print(f"Model saved to: {model_path}")
print(f"Scaler saved to: {scaler_path}")
