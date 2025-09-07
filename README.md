# 🏥 Health App

A Flask-based web application that provides **personalized health and wellness guidance**.  
It integrates **AI-powered fitness and medication plans** with a secure **patient-doctor communication system**, making it a holistic platform for managing health in one place.  


## ✨ Wireframes
![Register Page](https://github.com/suregowtham123/FITNESS-AND-MEDICATION/blob/main/Screenshot%2025-09-07%221608.png)
![Login Page](https://github.com/suregowtham123/FITNESS-AND-MEDICATION/blob/main/Screenshot%202025-09-07%20221608.png)

![Dashboard](https://github.com/suregowtham123/FITNESS-AND-MEDICATION/blob/main/Screenshot%2025-09-07%221637.png)
![Doctor communication](https://github.com/suregowtham123/FITNESS-AND-MEDICATION/blob/main/Screenshot%2025-09-07%221649.png)







### 👤 User Authentication & Roles
- Secure login and registration system  
- Separate roles for **patients** and **doctors**  
- Session-based authentication with Flask-Login  

### 🏋️ AI-Powered Fitness Guidance
- Enter any health goal (e.g., *belly fat, cardio, arms, yoga*)  
- Get:
  - Recommended **exercise images**  
  - **Workout duration per day**  
  - **Calories burned estimation**  
  - **Diet plan**  
  - **Monthly weight loss prediction**  

### 💊 AI-Powered Medication Information
- Enter a **symptom** (e.g., headache, fever, cough)  
- Get:
  - Common medications & remedies  
  - Categorized recommendations  
  - Image references  

### 👨‍⚕️ Doctor Communication
- Patients can message doctors if they meet certain conditions:
  - **Age > 40 and 10+ days since registration**  
  - **Age ≤ 40 and 30+ days since registration**  
- Doctors can securely view and respond to patient queries  

### 💬 Real-time Chat (Optional Upgrade)
- Doctors and patients can exchange messages  
- Potential to integrate WebSocket or Firebase for real-time chat  



## 🛠️ Technologies Used

- **Backend**: Flask (Python)  
- **Database**: SQLite with Flask-SQLAlchemy  
- **Authentication**: Flask-Login  
- **AI Integration**: Gemini API (via `requests`)  
- **Web Scraping**: BeautifulSoup + Requests (for exercise/medicine images)  
- **Frontend**: HTML5, Jinja2 templates, Tailwind CSS  
- **Deployment**: Render.com (Gunicorn for production server)  



## 📂 Project Structure

fitness-medications-app/
│── app.py              # Main Flask app
│── init_db.py          # Database initialization script
│── requirements.txt    # Dependencies
│── templates/          # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── fitness.html
│   ├── medication.html
│   ├── doctor_comm.html
│── static/             # (Optional) CSS/JS/Images
│── database.db         # SQLite database (auto-created)


