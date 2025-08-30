from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
import cohere
import sqlite3
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

@app.route('/tailor-resume', methods=['GET'])
def tailor_resume_form():
    if not session.get('username'):
        return redirect('/login')
    
    return '''<!DOCTYPE html>
<html>
<head>
  <title>Resume Tailor - AI Career Planner</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }
    .app-container {
      display: flex;
      min-height: 100vh;
    }
    .sidebar {
      width: 250px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      box-shadow: 2px 0 10px rgba(0,0,0,0.1);
      position: relative;
    }
    .sidebar h1 {
      font-size: 24px;
      margin-bottom: 30px;
      text-align: center;
      border-bottom: 2px solid rgba(255,255,255,0.2);
      padding-bottom: 15px;
    }
    .nav-item {
      padding: 12px 15px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(255,255,255,0.1);
    }
    .nav-item:hover {
      background: rgba(255,255,255,0.2);
      transform: translateX(5px);
    }
    .nav-item.active {
      background: rgba(255,255,255,0.3);
      font-weight: bold;
    }
    .main-content {
      flex: 1;
      padding: 30px;
      background-color: white;
      margin: 20px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .form-container {
      max-width: 800px;
    }
    .form-group {
      margin-bottom: 25px;
    }
    .form-group label {
      display: block;
      margin-bottom: 10px;
      font-weight: 600;
      color: #333;
      font-size: 16px;
    }
    .form-group input[type="file"] {
      width: 100%;
      padding: 15px;
      border: 2px dashed #667eea;
      border-radius: 8px;
      background: #f8f9fa;
      font-size: 16px;
      transition: all 0.3s ease;
      cursor: pointer;
    }
    .form-group input[type="file"]:hover {
      border-color: #764ba2;
      background: #e9ecef;
    }
    .form-group textarea {
      width: 100%;
      padding: 15px;
      border: 2px solid #e1e5e9;
      border-radius: 8px;
      font-size: 16px;
      resize: vertical;
      transition: border-color 0.3s ease;
      font-family: inherit;
      line-height: 1.5;
    }
    .form-group textarea:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .submit-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 30px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 10px;
    }
    .submit-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    .logout-container {
      position: absolute;
      bottom: 20px;
      left: 20px;
      right: 20px;
    }
    .logout-btn {
      background: rgba(220, 53, 69, 0.8);
      color: white;
      padding: 12px 20px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      font-size: 14px;
      font-weight: 500;
    }
    .logout-btn:hover {
      background: rgba(220, 53, 69, 1);
      transform: translateY(-2px);
    }
    .file-info {
      font-size: 14px;
      color: #666;
      margin-top: 5px;
    }
    .back-link {
      color: #667eea;
      text-decoration: none;
      font-weight: 500;
      margin-bottom: 20px;
      display: inline-block;
      transition: color 0.3s ease;
    }
    .back-link:hover {
      color: #764ba2;
    }
  </style>
</head>
<body>
  <div class="app-container">
    <div class="sidebar">
      <h1>Caria</h1>
      <div class="nav-item" onclick="window.location.href='/app'">
        🎯 Career Planner
      </div>
      <div class="nav-item">
        📊 Dashboard
      </div>
      <div class="nav-item active" onclick="window.location.href='/tailor-resume'">
        📝 Resume Tailor
      </div>
      <div class="nav-item active" onclick="window.location.href='/career-calendar'">
        📅 Career Calendar
      </div>
      <div class="nav-item" onclick="window.location.href='/career-break'">
        🏖️ Career Break Planner
      </div>
      <div class="nav-item">
        💡 Resources
      </div>
      <div class="nav-item">
        ⚙️ Settings
      </div>
      
      <div style="margin: 20px 0; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
        <div class="nav-item" onclick="window.location.href='/'" style="background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2);">
          🌐 Visit Site
        </div>
      </div>
      
      <div class="logout-container">
        <form method="POST" action="/logout">
          <button type="submit" class="logout-btn">
            🚪 Logout
          </button>
        </form>
      </div>
    </div>
    
    <div class="main-content">
      <div class="form-container">
        <a href="/app" class="back-link">← Back to Career Planner</a>
        
        <h2 style="margin-bottom: 10px; color: #333; font-size: 28px;">
          📝 AI Resume Tailor
        </h2>
        <p style="margin-bottom: 30px; color: #666; font-size: 16px;">
          Upload your resume and paste the job description to get an AI-optimized version tailored specifically for the position.
        </p>
        
        <form method="POST" action="/tailor-resume" enctype="multipart/form-data">
          <div class="form-group">
            <label for="resume">📄 Upload Your Resume (PDF or DOCX):</label>
            <input type="file" name="resume" id="resume" accept=".pdf,.docx" required>
            <div class="file-info">Supported formats: PDF, DOCX (Max size: 10MB)</div>
          </div>
          
          <div class="form-group">
            <label for="job_description">💼 Job Description:</label>
            <textarea name="job_description" id="job_description" rows="12" 
                     placeholder="Paste the complete job description here, including requirements, responsibilities, and qualifications..." 
                     required></textarea>
          </div>
          
          <button type="submit" class="submit-btn">
            ✨ Tailor My Resume
          </button>
        </form>
      </div>
    </div>
  </div>
</body>
</html>'''

@app.route('/tailor-resume', methods=['POST'])
def tailor_resume():
    if not session.get('username'):
        return redirect('/login')
    
    if 'resume' not in request.files:
        return "No file uploaded."
    
    file = request.files['resume']
    if file.filename == '':
        return "No selected file."
    
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return "Unsupported file format. Only PDF and DOCX are allowed."
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    resume_text = extract_text_from_resume(filepath)
    job_description = request.form['job_description']
    
    prompt = f"""
You are an expert resume writer. The following is a resume:

{resume_text}

And this is the job description the person wants to apply for:

{job_description}

Rewrite or tailor the resume so it is optimized and aligned with the job description.
Keep it realistic, keep achievements if relevant, and structure it professionally.

Output only the improved resume in plain text.
"""
    try:
        response = cohere_client.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7
        )
        tailored_resume = response.generations[0].text.strip()
        
        return f'''<!DOCTYPE html>
<html>
<head>
  <title>Tailored Resume - AI Career Planner</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }}
    .app-container {{
      display: flex;
      min-height: 100vh;
    }}
    .sidebar {{
      width: 250px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      box-shadow: 2px 0 10px rgba(0,0,0,0.1);
      position: relative;
    }}
    .sidebar h1 {{
      font-size: 24px;
      margin-bottom: 30px;
      text-align: center;
      border-bottom: 2px solid rgba(255,255,255,0.2);
      padding-bottom: 15px;
    }}
    .nav-item {{
      padding: 12px 15px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(255,255,255,0.1);
    }}
    .nav-item:hover {{
      background: rgba(255,255,255,0.2);
      transform: translateX(5px);
    }}
    .nav-item.active {{
      background: rgba(255,255,255,0.3);
      font-weight: bold;
    }}
    .main-content {{
      flex: 1;
      padding: 30px;
      background-color: white;
      margin: 20px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    .result-container {{
      max-width: 800px;
    }}
    .resume-output {{
      background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
      border: 1px solid #e9ecef;
      border-left: 4px solid #28a745;
      padding: 30px;
      border-radius: 12px;
      white-space: pre-wrap;
      line-height: 1.8;
      font-family: 'Georgia', 'Times New Roman', serif;
      font-size: 15px;
      margin-top: 20px;
      max-height: 70vh;
      overflow-y: auto;
      box-shadow: 0 4px 15px rgba(0,0,0,0.08);
      color: #2c3e50;
      position: relative;
    }}
    .resume-output::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, #28a745, #20c997, #17a2b8);
      border-radius: 12px 12px 0 0;
    }}
    .resume-header {{
      text-align: center;
      margin-bottom: 25px;
      padding-bottom: 15px;
      border-bottom: 2px solid #e9ecef;
    }}
    .resume-section {{
      margin-bottom: 20px;
    }}
    .resume-section h3 {{
      color: #28a745;
      font-size: 18px;
      margin-bottom: 10px;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .action-buttons {{
      margin-top: 25px;
      margin-bottom: 20px;
      display: flex;
      gap: 15px;
      flex-wrap: wrap;
      justify-content: center;
    }}
    .btn {{
      padding: 14px 24px;
      border: none;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .btn-primary {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }}
    .btn-primary:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }}
    .btn-secondary {{
      background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
      color: white;
    }}
    .btn-secondary:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(108, 117, 125, 0.4);
    }}
    .btn-success {{
      background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
      color: white;
    }}
    .btn-success:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
    }}
    .success-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
      color: #155724;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 20px;
      border: 1px solid #c3e6cb;
    }}
    .logout-container {{
      position: absolute;
      bottom: 20px;
      left: 20px;
      right: 20px;
    }}
    .logout-btn {{
      background: rgba(220, 53, 69, 0.8);
      color: white;
      padding: 12px 20px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      font-size: 14px;
      font-weight: 500;
    }}
    .logout-btn:hover {{
      background: rgba(220, 53, 69, 1);
      transform: translateY(-2px);
    }}
    .back-link {{
      color: #667eea;
      text-decoration: none;
      font-weight: 500;
      margin-bottom: 20px;
      display: inline-block;
      transition: color 0.3s ease;
    }}
    .back-link:hover {{
      color: #764ba2;
    }}
  </style>
</head>
<body>
  <div class="app-container">
    <div class="sidebar">
      <h1>Caria</h1>
            <div class="nav-item" onclick="window.location.href='/app'">
        🎯 Career Planner
      </div>
      <div class="nav-item">
        📊 Dashboard
      </div>
      <div class="nav-item active" onclick="window.location.href='/tailor-resume'">
        📝 Resume Tailor
      </div>
      <div class="nav-item active" onclick="window.location.href='/career-calendar'">
        📅 Career Calendar
      </div>
      <div class="nav-item" onclick="window.location.href='/career-break'">
        🏖️ Career Break Planner
      </div>
      <div class="nav-item">
        💡 Resources
      </div>
      <div class="nav-item">
        ⚙️ Settings
      </div>
      
      <div style="margin: 20px 0; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
        <div class="nav-item" onclick="window.location.href='/'" style="background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2);">
          🌐 Visit Site
        </div>
      </div>
      
      <div class="logout-container">
        <form method="POST" action="/logout">
          <button type="submit" class="logout-btn">
            🚪 Logout
          </button>
        </form>
      </div>
    </div>
    
    <div class="main-content">        <div class="result-container">
        <a href="/tailor-resume" class="back-link">← Tailor Another Resume</a>
        
        <h2 style="margin-bottom: 10px; color: #333; font-size: 28px;">
          ✅ Your Tailored Resume
        </h2>
        
        <div class="success-badge">
          <span>🎉</span>
          Resume successfully optimized and tailored!
        </div>
        
        <p style="margin-bottom: 25px; color: #666; font-size: 16px; line-height: 1.6;">
          Your resume has been professionally optimized to match the job description. The AI has enhanced keywords, 
          restructured content, and highlighted relevant experience to maximize your chances of getting noticed by recruiters.
        </p>
        
        <div class="action-buttons">
          <button class="btn btn-success" onclick="copyToClipboard()">
            <span>📋</span> Copy to Clipboard
          </button>
          <button class="btn btn-primary" onclick="downloadResume()">
            <span>💾</span> Download as Text
          </button>
          <a href="/tailor-resume" class="btn btn-secondary">
            <span>🔄</span> Tailor Another Resume
          </a>
        </div>
        
        <div class="resume-output" id="resumeContent">{tailored_resume}</div>
        
        <div style="margin-top: 30px; padding: 20px; background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); border-radius: 12px; border-left: 4px solid #2196f3;">
          <h4 style="color: #1976d2; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
            <span>💡</span> Pro Tips for Your Application
          </h4>
          <ul style="color: #424242; line-height: 1.6; margin-left: 20px;">
            <li>Review the tailored resume carefully and make any personal adjustments needed</li>
            <li>Customize your cover letter to complement the optimized resume</li>
            <li>Practice talking about the highlighted experiences during interviews</li>
            <li>Keep the original resume file as a backup for future applications</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
  
  <script>
    function copyToClipboard() {{
      const resumeText = document.getElementById('resumeContent').textContent;
      navigator.clipboard.writeText(resumeText).then(function() {{
        // Show success notification
        const btn = event.target.closest('.btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span>✅</span> Copied!';
        btn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        
        setTimeout(function() {{
          btn.innerHTML = originalText;
          btn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        }}, 2000);
      }}, function(err) {{
        console.error('Could not copy text: ', err);
        alert('Failed to copy to clipboard. Please try selecting and copying manually.');
      }});
    }}
    
    function downloadResume() {{
      const resumeText = document.getElementById('resumeContent').textContent;
      const element = document.createElement('a');
      const file = new Blob([resumeText], {{type: 'text/plain'}});
      element.href = URL.createObjectURL(file);
      element.download = 'tailored_resume_' + new Date().toISOString().split('T')[0] + '.txt';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      
      // Show download feedback
      const btn = event.target.closest('.btn');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>⬇️</span> Downloaded!';
      
      setTimeout(function() {{
        btn.innerHTML = originalText;
      }}, 2000);
    }}
    
    // Add smooth scroll behavior for the resume container
    document.addEventListener('DOMContentLoaded', function() {{
      const resumeContainer = document.getElementById('resumeContent');
      if (resumeContainer) {{
        resumeContainer.style.scrollBehavior = 'smooth';
      }}
    }});
  </script>
</body>
</html>'''
    except Exception as e:
        return f"Error: {str(e)}"

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
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['username'] = username
        return redirect('/app')
    return "Invalid credentials. <a href='/login'>Try again</a>"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html", show_navbar=False)
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return redirect('/login')
    except sqlite3.IntegrityError:
        return "Username already taken. <a href='/signup'>Try again</a>"
    finally:
        conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

# --- Application Page (React) ---

@app.route('/app')
def app_page():
    if not session.get('username'):
        return redirect('/login')
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
  <title>AI Career Planner</title>
  <script crossorigin src="https://unpkg.com/react@17/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }
    .app-container {
      display: flex;
      min-height: 100vh;
    }
    .sidebar {
      width: 250px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
    .sidebar h1 {
      font-size: 24px;
      margin-bottom: 30px;
      text-align: center;
      border-bottom: 2px solid rgba(255,255,255,0.2);
      padding-bottom: 15px;
    }
    .nav-item {
      padding: 12px 15px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(255,255,255,0.1);
    }
    .nav-item:hover {
      background: rgba(255,255,255,0.2);
      transform: translateX(5px);
    }
    .nav-item.active {
      background: rgba(255,255,255,0.3);
      font-weight: bold;
    }
    .main-content {
      flex: 1;
      padding: 30px;
      background-color: white;
      margin: 20px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .form-container {
      max-width: 800px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    .form-group label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      color: #333;
    }
    .form-group input {
      width: 100%;
      padding: 12px 15px;
      border: 2px solid #e1e5e9;
      border-radius: 8px;
      font-size: 16px;
      transition: border-color 0.3s ease;
    }
    .form-group input:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .submit-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 30px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 10px;
    }
    .submit-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    .submit-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .result-container {
      margin-top: 30px;
      background: #f8f9fa;
      border-left: 4px solid #667eea;
      padding: 20px;
      border-radius: 8px;
      white-space: pre-wrap;
      line-height: 1.6;
    }
    .logout-container {
      position: absolute;
      bottom: 20px;
      left: 20px;
      right: 20px;
    }
    .logout-btn {
      background: rgba(220, 53, 69, 0.8);
      color: white;
      padding: 12px 20px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      font-size: 14px;
      font-weight: 500;
    }
    .logout-btn:hover {
      background: rgba(220, 53, 69, 1);
      transform: translateY(-2px);
    }
    .sidebar {
      position: relative;
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    function App() {
      const [formData, setFormData] = React.useState({
        name: '', age: '', country: '', education: '', currentCareer: '', dreamJob: ''
      });
      const [response, setResponse] = React.useState('');
      const [loading, setLoading] = React.useState(false);
      const [activeNav, setActiveNav] = React.useState('career-planner');

      const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
      };

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResponse('');
        const res = await fetch('/generate-path', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        setResponse(data.result || data.error);
        setLoading(false);
      };

      const downloadPDF = async () => {
        if (!response || !formData.name) {
          alert('Please generate a career plan first');
          return;
        }

        try {
          const res = await fetch('/download-career-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              careerPlan: response,
              userName: formData.name
            })
          });

          if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `career_plan_${formData.name.replace(/\s+/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
          } else {
            alert('Failed to generate PDF. Please try again.');
          }
        } catch (error) {
          console.error('Download error:', error);
          alert('Error downloading PDF. Please try again.');
        }
      };

      const navItems = [
        { id: 'career-planner', label: '🎯 Career Planner', active: true },
        { id: 'dashboard', label: '📊 Dashboard' },
        { id: 'resume-tailor', label: '📝 Resume Tailor' },
        { id: 'career-calendar', label: '📅 Career Calendar' },
        { id: 'history', label: '📚 Career Break Planner' },
        { id: 'resources', label: '💡 Resources' },
        { id: 'settings', label: '⚙️ Settings' }
      ];

      const handleNavClick = (navId) => {
        if (navId === 'resume-tailor') {
          window.location.href = '/tailor-resume';
        } else if (navId === 'career-calendar') {
          window.location.href = '/career-calendar';
        } else if (navId === 'history') {
          window.location.href = '/career-break';
        } else {
          setActiveNav(navId);
        }
      };

      return (
        <div className="app-container">
          <div className="sidebar">
            <h1>Caria</h1>
            {navItems.map(item => (
              <div 
                key={item.id}
                className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
                onClick={() => handleNavClick(item.id)}
              >
                {item.label}
              </div>
            ))}
            
            <div style={{ margin: '20px 0', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
              <div 
                className="nav-item"
                onClick={() => window.location.href = '/'}
                style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.2)' }}
              >
                🌐 Visit Site
              </div>
            </div>
            
            <div className="logout-container">
              <form method="POST" action="/logout">
                <button type="submit" className="logout-btn">
                  🚪 Logout
                </button>
              </form>
            </div>
          </div>
          
          <div className="main-content">
            <div className="form-container">
              <h2 style={{ marginBottom: '30px', color: '#333', fontSize: '28px' }}>
                AI Career Path Planner
              </h2>
              <p style={{ marginBottom: '30px', color: '#666', fontSize: '16px' }}>
                Get personalized career guidance powered by AI. Fill out the form below to receive a detailed roadmap to your dream job.
              </p>
              
              <form onSubmit={handleSubmit}>
                {[
                  { field: 'name', label: 'Full Name', type: 'text' },
                  { field: 'age', label: 'Age', type: 'number' },
                  { field: 'country', label: 'Country', type: 'text' },
                  { field: 'education', label: 'Current Education Level', type: 'text' },
                  { field: 'currentCareer', label: 'Current Career/Job', type: 'text' },
                  { field: 'dreamJob', label: 'Dream Job/Career Goal', type: 'text' }
                ].map(({ field, label, type }) => (
                  <div key={field} className="form-group">
                    <label>{label}:</label>
                    <input 
                      name={field} 
                      type={type}
                      value={formData[field]} 
                      onChange={handleChange} 
                      required 
                      placeholder={`Enter your ${label.toLowerCase()}`}
                    />
                  </div>
                ))}
                <button type="submit" className="submit-btn" disabled={loading}>
                  {loading ? "🔄 Generating your career path..." : "✨ Generate Career Path"}
                </button>
              </form>
              
              {response && (
                <div className="result-container">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h4 style={{ color: '#333', fontSize: '20px', margin: 0 }}>
                      🎯 Your Personalized Career Path:
                    </h4>
                    <button 
                      onClick={downloadPDF}
                      className="submit-btn"
                      style={{ 
                        padding: '10px 20px', 
                        fontSize: '14px',
                        background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
                        marginTop: 0
                      }}
                    >
                      📄 Download PDF
                    </button>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                    {response}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }
    ReactDOM.render(<App />, document.getElementById('root'));
  </script>
</body>
</html>'''
    
    return html_content

# --- AI Career Path Generator ---

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

# --- PDF Download for Career Plans ---

@app.route('/download-career-plan', methods=['POST'])
def download_career_plan():
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    career_plan = data.get('careerPlan', '')
    user_name = data.get('userName', 'User')
    
    if not career_plan:
        return jsonify({'error': 'No career plan provided'}), 400
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor='#667eea'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor='#333333'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_LEFT,
        leftIndent=0,
        rightIndent=0
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph(f"AI Career Plan for {user_name}", title_style))
    story.append(Spacer(1, 20))
    
    # Process career plan text
    lines = career_plan.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
            
        # Check if it's a heading (starts with #, **, or is all caps)
        if (line.startswith('#') or 
            (line.startswith('**') and line.endswith('**')) or
            (line.isupper() and len(line) > 5) or
            line.startswith('Career Roadmap')):
            # Clean heading text
            clean_line = line.replace('#', '').replace('**', '').strip()
            story.append(Paragraph(clean_line, heading_style))
        else:
            # Regular content
            # Escape any HTML and convert markdown-style formatting properly
            import html
            clean_line = html.escape(line)  # Escape HTML first
            
            # Convert markdown bold (**text**) to HTML
            clean_line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', clean_line)
            # Convert markdown italic (*text*) to HTML
            clean_line = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', clean_line)
            
            # Handle bullet points
            if clean_line.startswith('- '):
                clean_line = '• ' + clean_line[2:]
            elif re.match(r'^\d+\. ', clean_line):
                # Keep numbered lists as is
                pass
                
            story.append(Paragraph(clean_line, body_style))
    
    # Add footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor='#666666'
    )
    story.append(Paragraph("Generated by AI Career Mapper - Your Path to Success", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Prepare file for download
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"career_plan_{user_name.replace(' ', '_')}.pdf",
        mimetype='application/pdf'
    )

# --- Career Roadmap Calendar Page ---

@app.route('/career-calendar', methods=['GET'])
def career_calendar():
    if not session.get('username'):
        return redirect('/login')
    
    return '''<!DOCTYPE html>
<html>
<head>
  <title>Career Roadmap Calendar - AI Career Planner</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }
    .app-container {
      display: flex;
      min-height: 100vh;
    }
    .sidebar {
      width: 250px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      box-shadow: 2px 0 10px rgba(0,0,0,0.1);
      position: relative;
    }
    .sidebar h1 {
      font-size: 24px;
      margin-bottom: 30px;
      text-align: center;
      border-bottom: 2px solid rgba(255,255,255,0.2);
      padding-bottom: 15px;
    }
    .nav-item {
      padding: 12px 15px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(255,255,255,0.1);
    }
    .nav-item:hover {
      background: rgba(255,255,255,0.2);
      transform: translateX(5px);
    }
    .nav-item.active {
      background: rgba(255,255,255,0.3);
      font-weight: bold;
    }
    .main-content {
      flex: 1;
      padding: 30px;
      background-color: white;
      margin: 20px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .form-container {
      max-width: 900px;
    }
    .form-group {
      margin-bottom: 25px;
    }
    .form-group label {
      display: block;
      margin-bottom: 10px;
      font-weight: 600;
      color: #333;
      font-size: 16px;
    }
    .form-group input, .form-group textarea {
      width: 100%;
      padding: 15px;
      border: 2px solid #e1e5e9;
      border-radius: 8px;
      font-size: 16px;
      transition: border-color 0.3s ease;
      font-family: inherit;
      line-height: 1.5;
    }
    .form-group input:focus, .form-group textarea:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .submit-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 30px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 10px;
    }
    .submit-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    .calendar-container {
      margin-top: 30px;
      background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
      border: 1px solid #e9ecef;
      border-left: 4px solid #667eea;
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .timeline-item {
      display: flex;
      margin-bottom: 20px;
      padding: 20px;
      background: white;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      border-left: 4px solid #28a745;
    }
    .timeline-year {
      min-width: 80px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 10px 15px;
      border-radius: 8px;
      font-weight: bold;
      text-align: center;
      margin-right: 20px;
    }
    .timeline-content {
      flex: 1;
    }
    .timeline-title {
      font-size: 18px;
      font-weight: bold;
      color: #333;
      margin-bottom: 8px;
    }
    .timeline-description {
      color: #666;
      line-height: 1.6;
    }
    .action-buttons {
      margin-top: 25px;
      display: flex;
      gap: 15px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .btn {
      padding: 14px 24px;
      border: none;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .btn-success {
      background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
      color: white;
    }
    .btn-success:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
    }
    .logout-container {
      position: absolute;
      bottom: 20px;
      left: 20px;
      right: 20px;
    }
    .logout-btn {
      background: rgba(220, 53, 69, 0.8);
      color: white;
      padding: 12px 20px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      font-size: 14px;
      font-weight: 500;
    }
    .logout-btn:hover {
      background: rgba(220, 53, 69, 1);
      transform: translateY(-2px);
    }
    .back-link {
      color: #667eea;
      text-decoration: none;
      font-weight: 500;
      margin-bottom: 20px;
      display: inline-block;
      transition: color 0.3s ease;
    }
    .back-link:hover {
      color: #764ba2;
    }
  </style>
</head>
<body>
  <div class="app-container">
    <div class="sidebar">
      <h1>Caria</h1>
      <div class="nav-item" onclick="window.location.href='/app'">
        🎯 Career Planner
      </div>
      <div class="nav-item">
        📊 Dashboard
      </div>
      <div class="nav-item" onclick="window.location.href='/tailor-resume'">
        📝 Resume Tailor
      </div>
      <div class="nav-item active">
        📅 Career Calendar
      </div>
      <div class="nav-item" onclick="window.location.href='/career-break'">
        Career Break Planner
      </div>
      <div class="nav-item">
        💡 Resources
      </div>
      <div class="nav-item">
        ⚙️ Settings
      </div>
      
      <div style="margin: 20px 0; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
        <div class="nav-item" onclick="window.location.href='/'" style="background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2);">
          🌐 Visit Site
        </div>
      </div>
      
      <div class="logout-container">
        <form method="POST" action="/logout">
          <button type="submit" class="logout-btn">
            🚪 Logout
          </button>
        </form>
      </div>
    </div>
    
    <div class="main-content">
      <div class="form-container">
        <a href="/app" class="back-link">← Back to Career Planner</a>
        
        <h2 style="margin-bottom: 10px; color: #333; font-size: 28px;">
          📅 Career Roadmap Calendar
        </h2>
        <p style="margin-bottom: 30px; color: #666; font-size: 16px;">
          Generate a personalized timeline calendar for your career journey. Enter your details below to get a structured roadmap with specific milestones and deadlines.
        </p>
        
        <form id="calendarForm">
          <div class="form-group">
            <label for="name">👤 Full Name:</label>
            <input type="text" name="name" id="name" required placeholder="Enter your full name">
          </div>
          
          <div class="form-group">
            <label for="dreamJob">🎯 Dream Job/Career Goal:</label>
            <input type="text" name="dreamJob" id="dreamJob" required placeholder="e.g., Software Developer, Doctor, Teacher">
          </div>
          
          <div class="form-group">
            <label for="currentStatus">📚 Current Education/Career Status:</label>
            <textarea name="currentStatus" id="currentStatus" rows="3" required placeholder="Describe your current situation (e.g., Grade 12 student, university graduate, career changer)"></textarea>
          </div>
          
          <div class="form-group">
            <label for="timeframe">⏰ Desired Timeframe (Years):</label>
            <input type="number" name="timeframe" id="timeframe" min="1" max="10" required placeholder="e.g., 5" value="5">
          </div>
          
          <button type="submit" class="submit-btn" id="generateBtn">
            ✨ Generate Career Calendar
          </button>
        </form>
        
        <div id="calendarResult" style="display: none;"></div>
      </div>
    </div>
  </div>
  
  <script>
    document.getElementById('calendarForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const formData = new FormData(e.target);
      const data = Object.fromEntries(formData);
      
      const generateBtn = document.getElementById('generateBtn');
      const originalText = generateBtn.textContent;
      generateBtn.textContent = '🔄 Generating Calendar...';
      generateBtn.disabled = true;
      
      try {
        const response = await fetch('/generate-calendar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.calendar) {
          displayCalendar(result.calendar);
        } else {
          alert('Error generating calendar: ' + (result.error || 'Unknown error'));
        }
      } catch (error) {
        alert('Error: ' + error.message);
      } finally {
        generateBtn.textContent = originalText;
        generateBtn.disabled = false;
      }
    });
    
    function displayCalendar(calendarData) {
      const resultDiv = document.getElementById('calendarResult');
      
      let html = `
        <div class="calendar-container">
          <h3 style="color: #333; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
            <span>📅</span> Your Career Roadmap Calendar
          </h3>
          
          <div class="action-buttons" style="margin-bottom: 25px;">
            <button class="btn btn-success" onclick="exportToGoogleCalendar()">
              <span>📅</span> Export to Google Calendar
            </button>
            <button class="btn btn-primary" onclick="downloadCalendar()">
              <span>💾</span> Download Calendar
            </button>
          </div>
      `;
      
      calendarData.forEach(item => {
        html += `
          <div class="timeline-item">
            <div class="timeline-year">${item.year}</div>
            <div class="timeline-content">
              <div class="timeline-title">${item.title}</div>
              <div class="timeline-description">${item.description}</div>
            </div>
          </div>
        `;
      });
      
      html += '</div>';
      
      resultDiv.innerHTML = html;
      resultDiv.style.display = 'block';
      
      // Store calendar data globally for export functions
      window.currentCalendar = calendarData;
    }
    
    function exportToGoogleCalendar() {
      if (!window.currentCalendar) return;
      
      // Create Google Calendar URL for each event
      window.currentCalendar.forEach(item => {
        const startDate = new Date(new Date().getFullYear() + parseInt(item.year.replace('Year ', '')) - 1, 0, 1);
        const endDate = new Date(startDate.getFullYear(), 11, 31);
        
        const googleUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE' +
          '&text=' + encodeURIComponent(item.title) +
          '&dates=' + formatDateForGoogle(startDate) + '/' + formatDateForGoogle(endDate) +
          '&details=' + encodeURIComponent(item.description);
        
        window.open(googleUrl, '_blank');
      });
    }
    
    function formatDateForGoogle(date) {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    }
    
    function downloadCalendar() {
      if (!window.currentCalendar) return;
      
      let content = 'Career Roadmap Calendar\\n\\n';
      window.currentCalendar.forEach(item => {
        content += `${item.year}: ${item.title}\\n${item.description}\\n\\n`;
      });
      
      const element = document.createElement('a');
      const file = new Blob([content], {type: 'text/plain'});
      element.href = URL.createObjectURL(file);
      element.download = 'career_roadmap_calendar.txt';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  </script>
</body>
</html>'''

@app.route('/generate-calendar', methods=['POST'])
def generate_calendar():
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    prompt = """
You are a career planning expert. Based on the following information:

- Name: {name}
- Dream Job: {dreamJob}
- Current Status: {currentStatus}
- Timeframe: {timeframe} years

Create a detailed year-by-year career roadmap calendar. For each year, provide:
1. A clear, actionable title/milestone
2. Specific activities, courses, or achievements for that year

Format your response as a JSON array with this structure:
[
  {{
    "year": "Year 1",
    "title": "Complete High School & Start Foundations",
    "description": "Finish Matric with focus on Mathematics and Science. Begin online programming courses on Codecademy. Volunteer at local tech companies for exposure."
  }},
  {{
    "year": "Year 2", 
    "title": "Higher Education & Skill Development",
    "description": "Enroll in Computer Science Diploma at university. Complete Python for Everybody course on Coursera. Build first portfolio projects."
  }}
]

Make it specific to their dream job ({dreamJob}) and current situation. Include practical steps, educational milestones, skill development, networking, and career progression over {timeframe} years.

Return ONLY the JSON array, no other text.
""".format(
        name=data['name'],
        dreamJob=data['dreamJob'],
        currentStatus=data['currentStatus'],
        timeframe=data['timeframe']
    )

    try:
        response = cohere_client.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=1200,
            temperature=0.7
        )
        result = response.generations[0].text.strip()
        
        # Try to parse as JSON
        import json
        try:
            calendar_data = json.loads(result)
            return jsonify({'calendar': calendar_data})
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback structure
            lines = result.split('\n')
            calendar_data = []
            for i in range(int(data['timeframe'])):
                calendar_data.append({
                    "year": f"Year {i+1}",
                    "title": f"Career Development Milestone {i+1}",
                    "description": f"Continue progress towards becoming a {data['dreamJob']}"
                })
            return jsonify({'calendar': calendar_data})
            
    except Exception as e:
        return jsonify({'error': str(e)})

        

@app.route("/career-break")
def get_break_plan():
  if not session.get('username'):
    return jsonify({'error': 'Unauthorized'}), 401
  html_content = '''<!DOCTYPE html>
<html>
<head>
  <title>Career Break Planner</title>
  <script crossorigin src="https://unpkg.com/react@17/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }
    .app-container {
      display: flex;
      min-height: 100vh;
    }
    .sidebar {
      width: 250px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
    .sidebar h1 {
      font-size: 24px;
      margin-bottom: 30px;
      text-align: center;
      border-bottom: 2px solid rgba(255,255,255,0.2);
      padding-bottom: 15px;
    }
    .nav-item {
      padding: 12px 15px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(255,255,255,0.1);
    }
    .nav-item:hover {
      background: rgba(255,255,255,0.2);
      transform: translateX(5px);
    }
    .nav-item.active {
      background: rgba(255,255,255,0.3);
      font-weight: bold;
    }
    .main-content {
      flex: 1;
      padding: 30px;
      background-color: white;
      margin: 20px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .form-container {
      max-width: 800px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    .form-group label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      color: #333;
    }
    .form-group input {
      width: 100%;
      padding: 12px 15px;
      border: 2px solid #e1e5e9;
      border-radius: 8px;
      font-size: 16px;
      transition: border-color 0.3s ease;
    }
    .form-group input:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .submit-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 30px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 10px;
    }
    .submit-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    .submit-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .result-container {
      margin-top: 30px;
      background: #f8f9fa;
      border-left: 4px solid #667eea;
      padding: 20px;
      border-radius: 8px;
      white-space: pre-wrap;
      line-height: 1.6;
    }
    .logout-container {
      position: absolute;
      bottom: 20px;
      left: 20px;
      right: 20px;
    }
    .logout-btn {
      background: rgba(220, 53, 69, 0.8);
      color: white;
      padding: 12px 20px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      font-size: 14px;
      font-weight: 500;
    }
    .logout-btn:hover {
      background: rgba(220, 53, 69, 1);
      transform: translateY(-2px);
    }
    .sidebar {
      position: relative;
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    function App() {
      const [formData, setFormData] = React.useState({
        name: '', age: '', country: '', education: '', currentJob: ''
      });
      const [response, setResponse] = React.useState('');
      const [loading, setLoading] = React.useState(false);
      const [activeNav, setActiveNav] = React.useState('career-break-planner');

      const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
      };

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResponse('');
        const res = await fetch('/break-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        setResponse(data.result || data.error);
        setLoading(false);
      };

      const downloadPDF = async () => {
        if (!response || !formData.name) {
          alert('Please generate a break plan first');
          return;
        }

        try {
          const res = await fetch('/download-break-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              breakPlan: response,
              userName: formData.name
            })
          });

          if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `break_plan_${formData.name.replace(/\s+/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
          } else {
            alert('Failed to generate PDF. Please try again.');
          }
        } catch (error) {
          console.error('Download error:', error);
          alert('Error downloading PDF. Please try again.');
        }
      };

      const navItems = [
        { id: 'career-planner', label: '🎯 Career Planner', active: true },
        { id: 'dashboard', label: '📊 Dashboard' },
        { id: 'resume-tailor', label: '📝 Resume Tailor' },
        { id: 'career-calendar', label: '📅 Career Calendar' },
        { id: 'career-break-planner', label: '🏖️ Career Break Planner' },
        { id: 'resources', label: '💡 Resources' },
        { id: 'settings', label: '⚙️ Settings' }
      ];

      const handleNavClick = (navId) => {
        if (navId === 'resume-tailor') {
          window.location.href = '/tailor-resume';
        } else if (navId === 'career-calendar') {
          window.location.href = '/career-calendar';
        } else if (navId === 'career-break-planner') {
          window.location.href = '/career-break';
        } else {
          setActiveNav(navId);
        }
      };

      return (
        <div className="app-container">
          <div className="sidebar">
            <h1>Caria</h1>
            {navItems.map(item => (
              <div 
                key={item.id}
                className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
                onClick={() => handleNavClick(item.id)}
              >
                {item.label}
              </div>
            ))}
            
            <div style={{ margin: '20px 0', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
              <div 
                className="nav-item"
                onClick={() => window.location.href = '/'}
                style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.2)' }}
              >
                🌐 Visit Site
              </div>
            </div>
            
            <div className="logout-container">
              <form method="POST" action="/logout">
                <button type="submit" className="logout-btn">
                  🚪 Logout
                </button>
              </form>
            </div>
          </div>
          
          <div className="main-content">
            <div className="form-container">
              <h2 style={{ marginBottom: '30px', color: '#333', fontSize: '28px' }}>
                AI Career Path Planner
              </h2>
              <p style={{ marginBottom: '30px', color: '#666', fontSize: '16px' }}>
                Get personalized career guidance powered by AI. Fill out the form below to receive a detailed roadmap to your dream job.
              </p>
              
              <form onSubmit={handleSubmit}>
                {[
                  { field: 'name', label: 'Full Name', type: 'text' },
                  { field: 'age', label: 'Age', type: 'number' },
                  { field: 'country', label: 'Country', type: 'text' },
                  { field: 'education', label: 'Current Education Level', type: 'text' },
                  { field: 'currentJob', label: 'Current Career/Job', type: 'text' },
                ].map(({ field, label, type }) => (
                  <div key={field} className="form-group">
                    <label>{label}:</label>
                    <input 
                      name={field} 
                      type={type}
                      value={formData[field]} 
                      onChange={handleChange} 
                      required 
                      placeholder={`Enter your ${label.toLowerCase()}`}
                    />
                  </div>
                ))}
                <button type="submit" className="submit-btn" disabled={loading}>
                  {loading ? "🔄 Generating your break plan..." : "✨ Generate Break Plan"}
                </button>
              </form>
              
              {response && (
                <div className="result-container">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h4 style={{ color: '#333', fontSize: '20px', margin: 0 }}>
                      🎯 Your Personalized Career Path:
                    </h4>
                    <button 
                      onClick={downloadPDF}
                      className="submit-btn"
                      style={{ 
                        padding: '10px 20px', 
                        fontSize: '14px',
                        background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
                        marginTop: 0
                      }}
                    >
                      📄 Download PDF
                    </button>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                    {response}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }
    ReactDOM.render(<App />, document.getElementById('root'));
  </script>
</body>
</html>'''
    
  return html_content

    

@app.route("/break-plan", methods=["POST"])
def generate_break_plan():
  if not session.get('username'):
      return jsonify({'error': 'Unauthorized'}), 401
  data = request.json
  prompt = f"""
  You are a professional career advisor. Based on the following user details:

  - Name: {data['name']}
  - Age: {data['age']}
  - Country: {data['country']}
  - Current Education: {data['education']}
  - Current Career Info: {data['currentJob']}

  Generate a detailed, realistic, and country-specific career break plan for {data['name']} that includes the following:

  1. Recommended certifications to take on the break (with local context).
  2. Recommended subjects and practical skills to keep practicing.
  3. Events to keep an eye which are mainly virtual available in {data['country']}.
  4. Online courses and platforms to use (include specific course examples where possible).
  5. Extra tips to stand stay relevant so they're hirable in their chosen field when they return.

  The output must be:
  - Written in plain English
  - Structured with clear headings and bullet points
  - Focused on realistic and actionable steps
  - Free from vague or generic suggestions

  Start your response with a title like: "Career Break Plan to for a {data['currentJob']} in {data['country']}"
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
  

@app.route('/download-break-plan', methods=['POST'])
def download_break_plan():
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    break_plan = data.get('breakPlan', '')
    user_name = data.get('userName', 'User')

    if not break_plan:
        return jsonify({'error': 'No break plan provided'}), 400

    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor='#667eea'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor='#333333'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_LEFT,
        leftIndent=0,
        rightIndent=0
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph(f"AI Career Plan for {user_name}", title_style))
    story.append(Spacer(1, 20))

    # Process break plan text
    lines = break_plan.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
            
        # Check if it's a heading (starts with #, **, or is all caps)
        if (line.startswith('#') or 
            (line.startswith('**') and line.endswith('**')) or
            (line.isupper() and len(line) > 5) or
            line.startswith('Career Break Plan')):
            # Clean heading text
            clean_line = line.replace('#', '').replace('**', '').strip()
            story.append(Paragraph(clean_line, heading_style))
        else:
            # Regular content
            # Escape any HTML and convert markdown-style formatting properly
            import html
            clean_line = html.escape(line)  # Escape HTML first
            
            # Convert markdown bold (**text**) to HTML
            clean_line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', clean_line)
            # Convert markdown italic (*text*) to HTML
            clean_line = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', clean_line)
            
            # Handle bullet points
            if clean_line.startswith('- '):
                clean_line = '• ' + clean_line[2:]
            elif re.match(r'^\d+\. ', clean_line):
                # Keep numbered lists as is
                pass
                
            story.append(Paragraph(clean_line, body_style))
    
    # Add footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor='#666666'
    )
    story.append(Paragraph("Generated by Caria - Your Path to Success", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Prepare file for download
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"career_plan_{user_name.replace(' ', '_')}.pdf",
        mimetype='application/pdf'
    )


career_results = []

@app.route("/career-fit", methods=["POST"])
def career_fit():
    data = request.json
    answers = data.get("answers", [])
    location = data.get("location", "Unknown")

    # Prepare prompt for Cohere
    prompt = f"""
    You are a professional career advisor. 
    Based on the following answers to a career fit questionnaire, 
    suggest 3 ideal career fields that match the person's interests, skills, and preferences.

    Location: {location}
    Answers:
    {answers}

    Please give a short explanation for each career field.
    """

    # Call Cohere
    response = cohere_client.generate(
        model="command-xlarge-nightly",
        prompt=prompt,
        max_tokens=200,
        temperature=0.7
    )

    career_suggestions = response.generations[0].text.strip()

    # Save result for history
    result_entry = {"answers": answers, "location": location, "suggestions": career_suggestions}
    career_results.append(result_entry)

    return jsonify({"suggestions": career_suggestions})


@app.route("/career-fit", methods=["GET"])
def get_career_results():
    return jsonify(career_results)



if __name__ == '__main__':
    app.run(debug=True)
