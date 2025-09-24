from flask import render_template, request, session, redirect
from supabase_client import supabase
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Onboarding route
@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if not session.get('username'):
        return redirect('/login')
    if request.method == 'GET':
        return render_template('onboarding.html', show_navbar=False)
    # POST: Save life stage and resume
    life_stage = request.form['life_stage']
    resume_file = request.files['resume']
    resume_path = None
    if resume_file:
        filename = secure_filename(resume_file.filename)
        resume_path = os.path.join(UPLOAD_FOLDER, filename)
        resume_file.save(resume_path)
    # Save to Supabase (update user row)
    supabase.table('users').update({
        'life_stage': life_stage,
        'resume_path': resume_path
    }).eq('username', session['username']).execute()
    return redirect('/app')
