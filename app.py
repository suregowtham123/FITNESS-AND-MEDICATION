import datetime
import json
import os
import re
from functools import wraps

import requests
from bs4 import BeautifulSoup
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'  # Use a strong, random key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer)
    role = db.Column(db.String(10), default='patient')  # 'patient' or 'doctor'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create database tables before the first request
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        age = request.form.get('age')
        role = request.form.get('role')

        # Simple validation
        if not username or not password or not age or not role:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, age=age, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registered Successfully', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# LLM-powered fitness route
@app.route('/fitness', methods=['GET', 'POST'])
@login_required
def llm_fitness():
    fitness_info = {}
    
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            try:
                # IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual API key
                API_KEY = "AIzaSyAiD4_Zr2OPb5O6AFwfBk5EAh0U5vBPEV4" 
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
                
                # Prepare the prompt for the generative model
                prompt = f"""Provide a detailed fitness plan for someone interested in '{query}'.
                The response must be a JSON object inside a single markdown code block. The JSON object must have the following keys:
                - "exercises": an array of up to 5 exercise names.
                - "daily_time": a string indicating the total daily exercise time (e.g., "30-45 minutes").
                - "time_allocation": a JSON object with exercise names as keys and their allocated time as values.
                - "calories_burned": a string with the estimated daily calories burned.
                - "diet": a string with dietary recommendations.
                """
                
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                }
                
                response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                response.raise_for_status()
                
                api_response = response.json()
                candidates = api_response.get('candidates', [])

                if not candidates or 'content' not in candidates[0] or 'parts' not in candidates[0]['content']:
                    raise ValueError("API response is missing required data.")

                generated_text = candidates[0]['content']['parts'][0].get('text', '')
                
                # Extract the JSON string from the markdown code block
                json_match = re.search(r'```json\n(.*?)\n```', generated_text, re.DOTALL)
                if json_match:
                    json_string = json_match.group(1)
                    generated_json = json.loads(json_string)
                    
                    fitness_info = {
                        "exercises": generated_json.get('exercises', []),
                        "daily_time": generated_json.get('daily_time', "N/A"),
                        "time_allocation": generated_json.get('time_allocation', {}),
                        "calories_burned": generated_json.get('calories_burned', "N/A"),
                        "diet": generated_json.get('diet', "N/A")
                    }
                else:
                    # If JSON is not found, provide a default error state
                    print(f"Failed to find JSON in API response: {generated_text}")
                    flash("An error occurred while processing the fitness information. Please try again later.", "error")
                    fitness_info = {
                        "exercises": [],
                        "daily_time": "An error occurred while fetching your fitness plan.",
                        "time_allocation": {},
                        "calories_burned": "An error occurred while fetching your fitness plan.",
                        "diet": "An error occurred while fetching your fitness plan."
                    }

            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                flash("Could not connect to the fitness service. Please try again later.", "error")
                fitness_info = {
                    "exercises": [],
                    "daily_time": "An error occurred while fetching your fitness plan.",
                    "time_allocation": {},
                    "calories_burned": "An error occurred while fetching your fitness plan.",
                    "diet": "An error occurred while fetching your fitness plan."
                }
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Failed to parse API response: {e}")
                flash("An error occurred while processing the fitness information. Please try again later.", "error")
                fitness_info = {
                    "exercises": [],
                    "daily_time": "An error occurred while fetching your fitness plan.",
                    "time_allocation": {},
                    "calories_burned": "An error occurred while fetching your fitness plan.",
                    "diet": "An error occurred while fetching your fitness plan."
                }
                
    return render_template('fitness.html', fitness_info=fitness_info)


# LLM-powered medication route
@app.route('/medication', methods=['GET', 'POST'])
@login_required
def llm_medication():
    low_power_meds = []
    high_power_meds = []

    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            try:
                # PASTE YOUR GEMINI API KEY HERE
                API_KEY = "AIzaSyAiD4_Zr2OPb5O6AFwfBk5EAh0U5vBPEV4"
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
                
                # Prepare the prompt for the generative model
                prompt = f"Provide detailed medication information for the symptom '{query}'. Categorize them into 'Normal and Low Power Medicines' and 'Antibiotics or High Power Medicines'. The format should be a JSON object with two keys, 'low_power_meds' and 'high_power_meds'. Each key should contain a JSON array of objects, with each object having a 'name', 'image', and 'info' key. Use placeholder URLs for images."
                
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": {
                            "type": "OBJECT",
                            "properties": {
                                "low_power_meds": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "name": {"type": "STRING"},
                                            "image": {"type": "STRING"},
                                            "info": {"type": "STRING"}
                                        }
                                    }
                                },
                                "high_power_meds": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "name": {"type": "STRING"},
                                            "image": {"type": "STRING"},
                                            "info": {"type": "STRING"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                response.raise_for_status()
                
                generated_json = json.loads(response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}'))
                
                low_power_meds = generated_json.get('low_power_meds', [])
                high_power_meds = generated_json.get('high_power_meds', [])

            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                flash("Could not connect to the medication service. Please try again later.", "error")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to parse API response: {e}")
                flash("An error occurred while processing the medication information. Please try again later.", "error")

    return render_template('medication.html', low_power_meds=low_power_meds, high_power_meds=high_power_meds)




@app.route('/doctor_comm', methods=['GET', 'POST'])
@login_required
def doctor_comm():
    access_allowed = False
    doctors = []
    
    # Check if the user is a doctor
    if current_user.role == 'doctor':
        return redirect(url_for('doctor_inbox'))

    # Check for POST request to validate access
    if request.method == 'POST':
        age_str = request.form.get('age')
        medication_days_str = request.form.get('medication_days')
        
        try:
            age = int(age_str)
            medication_days = int(medication_days_str)

            if (age > 40 and medication_days >= 10) or (age <= 40 and medication_days >= 30):
                access_allowed = True
                session['access_allowed'] = True
            else:
                flash('You do not meet the criteria to contact a doctor.', 'error')
        except (ValueError, TypeError):
            flash('Invalid input. Please enter valid numbers.', 'error')
        
    # Check if access was previously granted
    if session.get('access_allowed'):
        access_allowed = True
    
    if access_allowed:
        search_query = request.form.get('search_query', '')
        doctors_query = User.query.filter_by(role='doctor')
        
        if search_query:
            doctors_query = doctors_query.filter(User.username.like(f'%{search_query}%'))
        
        doctors = doctors_query.all()

    return render_template('doctor_comm.html', access_allowed=access_allowed, doctors=doctors)

@app.route('/doctor_inbox')
@login_required
def doctor_inbox():
    if current_user.role != 'doctor':
        flash('You are not authorized to view this page.', 'error')
        return redirect(url_for('dashboard'))

    # Get a list of unique users who have messaged the current doctor
    patient_ids = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).distinct().all()
    patients = []
    for (patient_id,) in patient_ids:
        patient = db.session.get(User, patient_id)
        if patient:
            patients.append(patient)

    return render_template('doctor_inbox.html', patients=patients)

@app.route('/chat/<other_user_id>', methods=['GET', 'POST'])
@login_required
def chat(other_user_id):
    # Ensure the other user exists
    other_user = db.session.get(User, other_user_id)
    if not other_user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))

    # Handle sending a new message
    if request.method == 'POST':
        content = request.form.get('message_content')
        if content:
            new_message = Message(
                sender_id=current_user.id,
                receiver_id=other_user.id,
                content=content
            )
            db.session.add(new_message)
            db.session.commit()
            return redirect(url_for('chat', other_user_id=other_user.id))

    # Fetch all messages between the two users
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == other_user.id),
            db.and_(Message.sender_id == other_user.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()

    return render_template('chat.html', other_user=other_user, messages=messages)

if __name__ == '__main__':
    if not os.path.exists('site.db'):
        with app.app_context():
            db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)




