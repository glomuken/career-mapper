from gtts import gTTS

text = """
In today’s world, many women still face limited access to career guidance, mentorship, and real economic opportunities.
We built something to change that.

Introducing our AI-powered career empowerment platform — a web-based tool built with Python and Flask, designed specifically to help women take charge of their future.
Whether you’re a student, a job seeker, a mother, or a woman returning to work after a break — this tool was built for you.

It all starts with a simple form. You enter your name, age, country, your education and career background, and your dream job.
Then, our AI analyzes your data and builds a customized, country-specific roadmap to help you get there.

You’ll see which qualifications you need, the best subjects to focus on, internships to apply for, local or online events to attend, and even how long it might take to reach your goal.
It’s more than a plan — it’s a pathway to independence.

But we didn’t stop there. We’ve added:
A WhatsApp, Instagram, and Messenger chatbot — so you can access your career planner anytime, anywhere.
A built-in calendar planner, to keep your goals organized and on track.
A career break planner, especially for women returning to work after time away.
A powerful career mapper, to visualize your journey from today to your dream job.
And a resume tailor, to help you craft the perfect CV for any opportunity.

This isn’t just another career tool.
This is a full empowerment suite, designed to break down the barriers women face in the workforce.
Whether it's lack of mentorship, flexible options, confidence, or access to resources — we’re tackling them all, with technology and intention.

Because when women are empowered economically, they gain the freedom to choose their own path, support their families, and uplift their communities.
And that ripple effect? It changes economies.

This is more than an app.
This is a movement — for women, with women, powered by AI, and built for change.
Start mapping your future today.
"""

# Generate speech
speech = gTTS(text=text, lang='en')

# Save to file
speech.save("career_empowerment_intro.mp3")

print("✅ Audio file saved as career_empowerment_intro.mp3")
