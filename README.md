# Clinic Sathi Backend
Clinic Sathi is a healthcare platform designed to connect patients with doctors, enabling seamless appointment booking, disease prediction, and medical record management. 
This repository contains the backend implementation built using Django REST Framework (DRF).

## Installation
Clone the Repository:
git clone https://github.com/your-username/clinic-sathi-backend.git

### Set up Virtual Environment
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows

### Install Dependencies:
pip install -r requirements.txt

### Apply Migrations:
python manage.py makemigrations

python manage.py migrate

### Run the Development Server:
python manage.py runserver
Test API Endpoints: Use tools like Postman or cURL to test the API endpoints.

I have also created Disease Prediction frontend using Streamlit u can access it by:

### Disease Prediction Dashboard
cd registration

streamlit run disease_prediction_app.py
