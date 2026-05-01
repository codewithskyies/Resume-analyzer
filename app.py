import streamlit as st
import os
import PyPDF2
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

if not GROQ_API_KEY:
    st.error("⚠️ No Groq API key found. Set GROQ_API_KEY in your .env file.")
    st.stop()

API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# 📄 Extract text from PDF
def input_pdf_text(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text.strip()

# 🤖 Groq API call
def query_groq(prompt):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert ATS (Applicant Tracking System) analyst. Be specific and concise."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 600,
        "temperature": 0.5
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        elif response.status_code == 401:
            return "❌ Invalid Groq API key."
        else:
            return f"❌ Error {response.status_code}: {response.text}"

    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Try again."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# 🎯 Streamlit UI
st.set_page_config(page_title="ATS Resume Analyzer", page_icon="📄")
st.title("📄 ATS Resume Analyzer")
st.caption("Powered by Groq + Llama 3")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste Job Description", height=200)

if st.button("🔍 Analyze Resume", use_container_width=True):
    if not uploaded_file:
        st.warning("Please upload a resume PDF.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        with st.spinner("Analyzing your resume..."):
            resume_text = input_pdf_text(uploaded_file)

            if not resume_text:
                st.error("Could not extract text from PDF. Make sure it's not a scanned image.")
                st.stop()

            prompt = f"""Compare this resume with the job description and provide:
1. Match Percentage (0-100%)
2. Missing Keywords (list them)
3. Top 3 suggestions to improve the resume

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:1500]}"""

            result = query_groq(prompt)

        st.subheader("📊 Analysis Result")
        st.write(result)