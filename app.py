
import streamlit as st
import pdfplumber
import pandas as pd
import os
import smtplib
import speech_recognition as sr
import pyttsx3
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Constants
RESULT_FILE = "data/interview_results.xlsx"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
EMAIL_SENDER = "youremail@gmail.com"
EMAIL_PASS = "yourpassword"

keywords = ['python', 'team', 'remote', 'ai', 'ml', 'developer', 'project', 'leader']
questions = [
    "Tell me about yourself.",
    "What are your strengths?",
    "Why do you want this job?",
    "Do you have experience with Python?",
    "Are you comfortable with remote work?"
]

if not os.path.exists(RESULT_FILE):
    pd.DataFrame(columns=['Name', 'Score', 'Responses', 'Resume Summary', 'Interview Date']).to_excel(RESULT_FILE, index=False)

def parse_resume(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()
    return text

def evaluate_answers(answers):
    score = 0
    for ans in answers:
        for word in keywords:
            if word in ans.lower():
                score += 10
                break
    return score

def summarize_resume(text):
    lines = text.split('\n')
    summary = [line.strip() for line in lines if any(kw in line.lower() for kw in ['experience', 'education', 'skills', 'project', 'work'])]
    return " | ".join(summary[:5]) if summary else "No summary available."

def load_data():
    return pd.read_excel(RESULT_FILE)

def save_result(data):
    df = pd.read_excel(RESULT_FILE)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_excel(RESULT_FILE, index=False)

def send_email(name, email_to, result):
    subject = f"Interview Result for {name}"
    body = generate_email(name, result)
    
    message = MIMEMultipart()
    message['From'] = EMAIL_SENDER
    message['To'] = email_to
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_SENDER, EMAIL_PASS)
    server.send_message(message)
    server.quit()

def generate_email(name, result):
    if result >= 50:
        return f"Dear {name},\n\nCongratulations! You’ve been shortlisted.\nWe’ll contact you with further rounds.\n\nRegards,\nHR Team"
    else:
        return f"Dear {name},\n\nThank you for your interest. Unfortunately, you are not selected this time.\n\nRegards,\nHR Team"

def voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙 Speak now...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        st.success(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        st.error("Could not understand audio")
    return ""

# UI
st.set_page_config(page_title="Smart HR Chatbot", layout="wide")
st.markdown("<h1 style='color:#4CAF50;'>🤖 AI Recruitment Assistant</h1>", unsafe_allow_html=True)

mode = st.sidebar.radio("Choose Mode:", ["Candidate", "Admin Login"])

if mode == "Candidate":
    name = st.text_input("👤 Your Full Name")
    email = st.text_input("📧 Your Email Address")
    interview_date = st.date_input("📅 Select Interview Date")
    uploaded_resume = st.file_uploader("📄 Upload Resume", type=['pdf'])
    use_voice = st.checkbox("🎙 Use Voice Input for Questions")

    if uploaded_resume:
        resume_text = parse_resume(uploaded_resume)
        st.success("✅ Resume uploaded successfully!")
        with st.expander("📄 Resume Preview"):
            st.write(resume_text)

    if name and uploaded_resume:
        st.subheader("🧠 Answer Interview Questions")
        responses = []
        for q in questions:
            if use_voice:
                if st.button(f"🎤 Answer: {q}"):
                    responses.append(voice_input())
            else:
                responses.append(st.text_input(q))

        if st.button("🚀 Submit & Evaluate"):
            score = evaluate_answers(responses)
            resume_summary = summarize_resume(resume_text)
            result = {
                "Name": name,
                "Score": score,
                "Responses": " | ".join(responses),
                "Resume Summary": resume_summary,
                "Interview Date": interview_date.strftime("%Y-%m-%d")
            }
            save_result(result)

            st.success(f"✅ Score: {score}/100")
            st.write("📝 Resume Summary:", resume_summary)
            st.code(generate_email(name, score), language='text')

            if st.button("📧 Send Result Email"):
                try:
                    send_email(name, email, score)
                    st.success("Email sent successfully!")
                except Exception as e:
                    st.error(f"Error sending email: {e}")

elif mode == "Admin Login":
    username = st.text_input("👤 Admin Username")
    password = st.text_input("🔒 Password", type='password')

    if st.button("🔓 Login"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.success("✅ Access Granted!")
            data = load_data()
            st.subheader("📊 All Interview Data")
            st.dataframe(data, use_container_width=True)

            st.subheader("🔍 Filter Candidates")
            name_search = st.text_input("Search Name")
            min_score, max_score = st.slider("Filter Score", 0, 100, (0, 100))

            filtered = data[
                data['Name'].str.contains(name_search, case=False, na=False) &
                data['Score'].between(min_score, max_score)
            ]
            st.write(f"Showing {len(filtered)} candidate(s)")
            st.dataframe(filtered, use_container_width=True)

            st.download_button("⬇ Download Full Data", data.to_excel(index=False), file_name="candidates.xlsx")
        else:
            st.error("❌ Invalid credentials")
