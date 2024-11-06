import streamlit as st
import PyPDF2
from gtts import gTTS
from io import BytesIO
import random

# Helper functions
def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def convert_text_to_audio(text, language="en", speed="normal"):
    """Convert text to audio using gTTS."""
    tts = gTTS(text=text, lang=language, slow=(speed == "slow"))
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file

def create_quiz(text):
    """Create a simple quiz based on the text."""
    questions = [
        "What is the main idea of the text?",
        "Can you mention one key detail from the text?",
        "Summarize the text in a few words."
    ]
    return random.choice(questions)

# Main app code
st.title("PDF to Podcast Generator")
st.write("Upload a PDF to generate a podcast and explore unique features.")

# PDF Upload
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
    
    st.subheader("Extracted Text")
    st.write(pdf_text)

    # Convert text to audio
    st.subheader("Generate Podcast")
    language = st.selectbox("Choose language", ("en", "es", "fr", "de"))
    speed = st.radio("Select speed", ("normal", "slow"))
    
    if st.button("Generate Podcast Audio"):
        with st.spinner("Converting text to audio..."):
            audio_file = convert_text_to_audio(pdf_text, language=language, speed=speed)
        
        st.audio(audio_file, format="audio/mp3")

        # Add download button to download the podcast
        st.download_button("Download Podcast", audio_file, file_name="podcast.mp3", mime="audio/mp3")

    # Generate a quiz
    if st.button("Generate Quiz"):
        quiz_question = create_quiz(pdf_text)
        st.subheader("Quiz Question")
        st.write(quiz_question)

    # Feedback and comments
    st.subheader("Feedback")
    st.text_area("Leave a comment about your podcast experience")

    st.subheader("Rate the App")
    rating = st.slider("Rate from 1 to 5", 1, 5)
    if st.button("Submit Rating"):
        st.write(f"Thank you for rating the app {rating}/5!")
