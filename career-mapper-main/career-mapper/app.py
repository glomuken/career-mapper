from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
import cohere
import sqlite3  # legacy, will be removed from auth
from supabase_client import supabase
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
import re

app = Flask(__name__)
app.secret_key = "supersecret"  # Replace with a secure key

from werkzeug.utils import secure_filename
import PyPDF2
import docx

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Configure your Cohere client
cohere_client = cohere.Client("pHHE1J3cZ26v7eNET2cSIo8heriFpxOhemcHaehC")

def extract_text_from_resume(file_path):
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Public Website Routes ---
@app.route('/')
def home():
    return render_template("home.html", show_navbar=True)

@app.route('/about')
def about():
    return render_template("about.html", show_navbar=True)

@app.route('/gallery')
def gallery():
    return render_template("gallery.html", show_navbar=True)

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html", show_navbar=False)
    
    username = request.form['username']
    password = request.form['password']
    
    # Supabase: fetch user by username (email) and password
    response = supabase.table('users').select('*').eq('username', username).eq('password', password).execute()
    user = response.data[0] if response.data else None
    
    if user:
        session['username'] = username
        return redirect('/dashboard')
    
    return "Invalid credentials. <a href='/login'>Try again</a>"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html", show_navbar=False)
    
    # Handle form submission
    profile_type = request.form['profile_type']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirmPassword']
    
    # Validate passwords match
    if password != confirm_password:
        return "Passwords do not match. <a href='/signup'>Try again</a>"
    
    # Check if user exists in Supabase
    exists = supabase.table('users').select('id').eq('username', email).execute()
    if exists.data:
        return "Email already registered. <a href='/signup'>Try again</a> or <a href='/login'>Sign in</a>"
    
    # Prepare user data
    user_data = {
        "username": email,
        "password": password,
        "profile_type": profile_type,
        "name": request.form['name'],
        "email": request.form['email'],
        "phone": request.form['phone'],
        "country": request.form['country']
    }
    
    # Add profile-specific data and handle files
    if profile_type == 'student':
        user_data.update({
            "education_level": request.form.get('educationLevel'),
            "dream_role": request.form.get('dreamRole')
        })
        if 'gradesFile' in request.files:
            file = request.files['gradesFile']
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"grades_{email}_{filename}")
                file.save(filepath)
                user_data["grades_file"] = filepath
                
    elif profile_type == 'professional':
        user_data.update({
            "job_title": request.form.get('jobTitle'),
            "industry": request.form.get('industry'),
            "experience": request.form.get('experience'),
            "career_goals": request.form.get('careerGoals')
        })
        if 'professionalResume' in request.files:
            file = request.files['professionalResume']
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"resume_{email}_{filename}")
                file.save(filepath)
                user_data["resume_path"] = filepath
        
    elif profile_type == 'mentor':
        mentor_areas_list = request.form.getlist('mentorAreas')
        user_data.update({
            "profession": request.form.get('profession'),
            "mentor_experience": request.form.get('mentorExperience'),
            "mentor_areas": ', '.join(mentor_areas_list) if mentor_areas_list else None
        })
        if 'mentorResume' in request.files:
            file = request.files['mentorResume']
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"mentor_resume_{email}_{filename}")
                file.save(filepath)
                user_data["resume_path"] = filepath
    
    # Insert new user
    try:
        result = supabase.table('users').insert(user_data).execute()
        session['username'] = email
        return redirect('/dashboard')
    except Exception as e:
        return f"Registration failed: {str(e)}. <a href='/signup'>Try again</a>"

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

# --- Dashboard Routes ---
@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect('/login')
    
    # Get user data from database
    response = supabase.table('users').select('*').eq('username', session['username']).execute()
    user = response.data[0] if response.data else None
    
    if not user:
        return redirect('/login')
    
    # Get profile type and personalization status
    profile_type = user.get('profile_type', 'student')
    name = user.get('name', 'User')
    has_completed_personalization = False
    
    # Check if user has completed personalization based on profile type
    if profile_type == 'student':
        has_completed_personalization = user.get('career_test_scores') is not None
    elif profile_type == 'professional':
        has_completed_personalization = user.get('selected_areas') is not None
    elif profile_type == 'mentor':
        has_completed_personalization = user.get('mentor_preferences') is not None
    
    # Generate dynamic content based on profile type
    dashboard_content = get_dashboard_content(profile_type, name, user, has_completed_personalization)
    
    return render_template('dashboard.html', 
                         user=user,
                         profile_type=profile_type,
                         name=name,
                         dashboard_content=dashboard_content,
                         has_completed_personalization=has_completed_personalization,
                         show_navbar=False)

def get_dashboard_content(profile_type, name, user, has_completed_personalization):
    """Generate dynamic dashboard content based on user profile"""
    
    if profile_type == 'student':
        if not has_completed_personalization:
            return {
                'welcome_message': f"Hi {name}, let's start by exploring your career options",
                'primary_action': 'Take a quick Career Test',
                'primary_action_url': '/career-interest-test',
                'secondary_actions': [
                    {'title': 'Browse Career Paths', 'url': '/app', 'icon': '🎯'},
                    {'title': 'Upload Resume', 'url': '/tailor-resume', 'icon': '📄'},
                    {'title': 'Career Calendar', 'url': '/career-calendar', 'icon': '📅'}
                ],
                'tips': [
                    'Complete your career test to get personalized recommendations',
                    'Explore different career paths that match your interests',
                    'Start building your skills early for your dream career'
                ]
            }
        else:
            # Student has completed test - show results and next steps
            primary_interest = user.get('primary_interest', 'Not available')
            return {
                'welcome_message': f"Welcome back, {name}!",
                'primary_action': f'You are best matched for careers: {primary_interest}',
                'primary_action_url': '/app',
                'secondary_actions': [
                    {'title': 'View Full Results', 'url': '/career-interest-test', 'icon': '📊'},
                    {'title': 'Generate Career Plan', 'url': '/app', 'icon': '🎯'},
                    {'title': 'Tailor Resume', 'url': '/tailor-resume', 'icon': '📄'}
                ],
                'tips': [
                    f'Focus on developing skills for {primary_interest} careers',
                    'Create a timeline for reaching your career goals',
                    'Network with professionals in your field of interest'
                ]
            }
    
    elif profile_type == 'professional':
        # Generate job trends using Cohere
        try:
            prompt = f"""
            Generate 3 current job trends and opportunities for a professional in {user.get('industry', 'technology')} with {user.get('experience', '2-5')} years of experience. Include:
            1. Trending job titles
            2. Key skills in demand
            3. Brief market insights
            
            Format as brief, actionable insights.
            """
            
            response = cohere_client.generate(
                model='command-r-plus',
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
            job_trends = response.generations[0].text.strip()
        except:
            job_trends = "• Remote work opportunities are increasing\n• AI and automation skills are in high demand\n• Cross-functional collaboration is essential"
        
        return {
            'welcome_message': f"Hi {name}, here are today's top jobs and skill trends in your field",
            'primary_action': 'Explore Job Opportunities',
            'primary_action_url': '/app',
            'job_trends': job_trends,
            'secondary_actions': [
                {'title': 'Tailor Resume', 'url': '/tailor-resume', 'icon': '📄'},
                {'title': 'Skill Development', 'url': '/app', 'icon': '📚'},
                {'title': 'Career Calendar', 'url': '/career-calendar', 'icon': '📅'}
            ],
            'tips': [
                'Keep your skills updated with industry trends',
                'Network actively in your professional community',
                'Set clear career progression goals'
            ]
        }
    
    elif profile_type == 'mentor':
        return {
            'welcome_message': f"Hi {name}, welcome! Let's set up your first mentorship room",
            'primary_action': 'Set Up Mentorship Room',
            'primary_action_url': '/mentor-preferences',
            'secondary_actions': [
                {'title': 'Update Availability', 'url': '/mentor-preferences', 'icon': '📅'},
                {'title': 'View Mentees', 'url': '/app', 'icon': '👥'},
                {'title': 'Resource Library', 'url': '/app', 'icon': '📚'}
            ],
            'tips': [
                'Set clear boundaries and expectations with mentees',
                'Prepare resources and materials for sessions',
                'Track mentee progress and goals'
            ]
        }
    
    return {}

@app.route('/api/user', methods=['GET'])
def get_user():
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Fetch user data from Supabase
    response = supabase.table('users').select('*').eq('username', session['username']).execute()
    user = response.data[0] if response.data else None
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Mask the password field
    user['password'] = None
    
    return jsonify(user)

# --- Career Interest Test Routes ---
@app.route('/career-interest-test', methods=['GET', 'POST'])
def career_interest_test():
    if not session.get('username'):
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('career_interest_test.html', show_navbar=False)
    
    # Process POST - save results and generate career suggestions
    answers = request.form.to_dict()
    
    # Calculate scores for each category
    analytical_questions = ['q1', 'q6', 'q10', 'q15']
    creative_questions = ['q2', 'q11', 'q18']
    social_questions = ['q3', 'q8', 'q13', 'q16']
    technical_questions = ['q4', 'q7', 'q12', 'q15']
    leadership_questions = ['q5', 'q9', 'q17', 'q19']
    lifestyle_questions = ['q14', 'q20']
    
    scores = {
        'Analytical/Scientific': sum(int(answers.get(q, 0)) for q in analytical_questions),
        'Creative/Artistic': sum(int(answers.get(q, 0)) for q in creative_questions),
        'Social/Helping': sum(int(answers.get(q, 0)) for q in social_questions),
        'Technical/Practical': sum(int(answers.get(q, 0)) for q in technical_questions),
        'Leadership/Business': sum(int(answers.get(q, 0)) for q in leadership_questions),
        'Lifestyle/Balance': sum(int(answers.get(q, 0)) for q in lifestyle_questions)
    }
    
    # Find top 2 categories
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_interest = sorted_scores[0][0]
    secondary_interest = sorted_scores[1][0] if len(sorted_scores) > 1 else None
    
    # Generate AI recommendations using Cohere
    prompt = f"""
    You are a professional career counselor and vocational guidance expert. A student has completed a comprehensive career interest assessment with the following results:

    PRIMARY INTEREST AREA: {primary_interest} (Score: {sorted_scores[0][1]}/20)
    SECONDARY INTEREST AREA: {secondary_interest} (Score: {sorted_scores[1][1] if secondary_interest else 0}/20)

    COMPLETE ASSESSMENT SCORES:
    {chr(10).join([f"• {category}: {score}/20" for category, score in scores.items()])}

    Based on these results, please provide a comprehensive career guidance report that includes:

    1. **CAREER RECOMMENDATIONS** (3-5 specific careers that align with their interests):
       - Include job titles, brief descriptions, and why they match
       - Consider both primary and secondary interests
       - Range from entry-level to advanced positions

    2. **EDUCATIONAL PATHWAYS**:
       - Recommended degree programs or certifications
       - Specific courses or subjects to focus on
       - Alternative education options (bootcamps, online courses, etc.)

    3. **SKILL DEVELOPMENT PRIORITIES**:
       - Technical skills to develop
       - Soft skills to cultivate
       - Industry-specific competencies

    4. **IMMEDIATE NEXT STEPS** (actionable items for a student):
       - Specific activities they can start today
       - Networking opportunities
       - Volunteer work or internships to pursue
       - Online resources to explore

    5. **INDUSTRY INSIGHTS**:
       - Current job market trends in their interest areas
       - Salary expectations and growth prospects
       - Geographic considerations

    Format your response professionally with clear sections and bullet points. Be specific, encouraging, and actionable. Avoid generic advice.
    """
    
    try:
        response = cohere_client.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7
        )
        ai_recommendations = response.generations[0].text.strip()
    except Exception as e:
        ai_recommendations = f"""
**CAREER RECOMMENDATIONS**
Based on your primary interest in {primary_interest}, here are some career paths to explore:

• Data Analyst - Analyze complex datasets to help organizations make informed decisions
• Research Scientist - Conduct studies and experiments in your field of interest
• Business Analyst - Bridge the gap between IT and business to improve processes
• Project Manager - Lead teams and projects from conception to completion

**EDUCATIONAL PATHWAYS**
• Consider a bachelor's degree in your area of interest
• Look into relevant certifications and professional development courses
• Explore online learning platforms like Coursera, edX, or industry-specific training

**SKILL DEVELOPMENT PRIORITIES**
• Technical skills: Data analysis, research methods, project management tools
• Soft skills: Communication, critical thinking, problem-solving, teamwork
• Industry knowledge: Stay updated with trends and best practices

**IMMEDIATE NEXT STEPS**
• Research specific roles and companies in your field of interest
• Connect with professionals through LinkedIn and informational interviews
• Look for internships, volunteer opportunities, or entry-level positions
• Start building a portfolio or gaining relevant experience

**INDUSTRY INSIGHTS**
Your interest areas show strong growth potential with good salary prospects. Consider both traditional and emerging roles in your field.
        """
    
    # Save results to database
    try:
        supabase.table('users').update({
            'career_test_scores': scores,
            'primary_interest': primary_interest,
            'secondary_interest': secondary_interest,
            'ai_recommendations': ai_recommendations
        }).eq('username', session['username']).execute()
    except Exception as e:
        print(f"Error saving to database: {e}")
    
    return render_template('career_test_results.html', 
                         scores=scores, 
                         primary_interest=primary_interest,
                         secondary_interest=secondary_interest,
                         ai_recommendations=ai_recommendations,
                         show_navbar=False)

# --- Other Routes ---
@app.route('/app')
def app_page():
    if not session.get('username'):
        return redirect('/login')
    
    # Your existing app_page implementation
    return render_template('app.html', show_navbar=False)

@app.route('/tailor-resume', methods=['GET', 'POST'])
def tailor_resume():
    if not session.get('username'):
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('tailor_resume.html', show_navbar=False)
    
    # Your existing tailor resume implementation
    pass

@app.route('/career-calendar')
def career_calendar():
    if not session.get('username'):
        return redirect('/login')
    return render_template('career_calendar.html', show_navbar=False)

@app.route('/career-break')
def career_break():
    if not session.get('username'):
        return redirect('/login')
    return render_template('career_break.html', show_navbar=False)

@app.route('/generate-path', methods=['POST'])
def generate_path():
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    prompt = f"""
    You are a professional career advisor. Based on the following user details:

    - Name: {data['name']}
    - Age: {data['age']}
    - Country: {data['country']}
    - Current Education: {data['education']}
    - Current Career Info: {data['currentCareer']}
    - Dream Job: {data['dreamJob']}

    Generate a detailed, realistic, and country-specific career roadmap for {data['name']} that includes the following:

    1. Recommended degrees or certifications (with local context).
    2. Recommended subjects and practical skills to focus on.
    3. Events, workshops, or internships available in {data['country']}.
    4. Online courses and platforms to use (include specific course examples where possible).
    5. Time estimate to reach the dream job, broken down year by year or step by step.
    6. Extra tips to stand out in their chosen field.

    The output must be:
    - Written in plain English
    - Structured with clear headings and bullet points
    - Focused on realistic and actionable steps
    - Free from vague or generic suggestions

    Start your response with a title like: "Career Roadmap to Become a {data['dreamJob']} in {data['country']}"
    """

    try:
        response = cohere_client.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=1800,
            temperature=0.7
        )
        result = response.generations[0].text.strip()
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

    