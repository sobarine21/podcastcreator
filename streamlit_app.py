import streamlit as st
import fitz  # PyMuPDF for PDF handling
from gtts import gTTS
import tempfile
import os
from transformers import pipeline
import numpy as np
from pydub import AudioSegment
import random

# Initialize pipelines
summarizer = pipeline("summarization")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    return text

# Function to create audio from text using gTTS
def text_to_audio(text, lang='en', slow=False):
    tts = gTTS(text=text, lang=lang, slow=slow)
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio_file.name)
    return temp_audio_file.name

# Function to generate a placeholder image
def generate_image(content):
    # Placeholder for image generation
    return "image_placeholder.png"  # Replace with image generation logic

# Streamlit UI
st.title("Advanced PDF to Podcast Generator 🎙️")
st.subheader("Upload a PDF and experience an interactive audio adventure!")

# PDF File Upload
pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])

if pdf_file:
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_file)

    # Summarize PDF content
    summary = summarizer(pdf_text, max_length=150, min_length=50, do_sample=False)[0]['summary_text']
    st.write("### Summary of the PDF Content")
    st.write(summary)

    # Language selection
    lang = st.selectbox("Select Language", ['en', 'es', 'fr', 'de'])
    
    # Narration speed selection
    slow = st.checkbox("Slow Narration")

    # Background music selection
    background_music = st.selectbox("Select Background Music", ["None", "Cheerful Jingle", "Suspense Music"])
    
    # Mood-based narration
    mood = st.selectbox("Select Mood for Narration", ["Neutral", "Cheerful", "Dramatic", "Serious"])

    # Convert PDF Text to Audio
    if st.button("Convert PDF to Podcast Audio"):
        audio_file = text_to_audio(pdf_text, lang=lang, slow=slow)

        # Display audio player
        with open(audio_file, "rb") as file:
            st.audio(file.read(), format="audio/mp3")

        # Provide download option
        with open(audio_file, "rb") as file:
            btn = st.download_button(
                label="Download Podcast Audio",
                data=file,
                file_name="podcast_audio.mp3",
                mime="audio/mp3"
            )
        os.remove(audio_file)  # Clean up temporary audio file

    # Interactive Quizzes
    if st.button("Take a Quiz"):
        st.write("### Quiz Section")
        st.write("Question: What is the main topic of the PDF?")
        answer = st.text_input("Your Answer")
        if st.button("Submit Answer"):
            st.write("Thanks for your answer!")

    # User Comments Section
    st.write("### Comments Section")
    comment = st.text_area("Leave your comments:")
    if st.button("Submit Comment"):
        st.write("Comment submitted!")

    # Podcast Rating System
    st.write("### Rate this Podcast")
    rating = st.slider("Rate this Podcast", 1, 5)
    if st.button("Submit Rating"):
        st.write(f"Thank you for rating this podcast: {rating} stars!")

    # Custom Intro/Outro
    intro = st.text_input("Enter your custom intro:")
    outro = st.text_input("Enter your custom outro:")
    if st.button("Generate Podcast with Intro/Outro"):
        combined_audio = AudioSegment.from_mp3(audio_file)
        if intro:
            intro_audio = text_to_audio(intro, lang=lang, slow=slow)
            combined_audio = combined_audio + AudioSegment.from_mp3(intro_audio)
        if outro:
            outro_audio = text_to_audio(outro, lang=lang, slow=slow)
            combined_audio = combined_audio + AudioSegment.from_mp3(outro_audio)

        combined_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        combined_audio.export(combined_audio_path.name, format="mp3")
        
        st.audio(combined_audio_path.name)

        # Provide download option for combined audio
        with open(combined_audio_path.name, "rb") as file:
            btn = st.download_button(
                label="Download Podcast with Intro/Outro",
                data=file,
                file_name="podcast_with_intro_outro.mp3",
                mime="audio/mp3"
            )
        os.remove(combined_audio_path.name)  # Clean up temporary audio file

    # Mood Music Synchronization
    if mood == "Cheerful":
        st.write("Playing cheerful music...")
        # Implement cheerful background music logic here
    elif mood == "Suspense":
        st.write("Playing suspenseful music...")
        # Implement suspenseful music logic here

    # Feedback Mechanism
    feedback = st.text_area("Your Feedback:")
    if st.button("Submit Feedback"):
        st.write("Thank you for your feedback!")

    # Progress Tracking
    st.write("### Your Progress")
    progress = st.slider("Progress", 0, 100, 50)
    
    # Export to Social Media
    if st.button("Share on Social Media"):
        st.write("Sharing feature coming soon!")

    # Visual Content Generation
    if st.button("Generate Visual Content"):
        image = generate_image(pdf_text)
        st.image(image, caption="Generated Visual Content")

# Interactive Story Ending Choices
st.write("### Create an Interactive Story Ending")
ending_choice = st.selectbox("Choose your ending:", ["Happy Ending", "Sad Ending", "Unexpected Twist"])
if st.button("Generate Story Ending"):
    st.write(f"The story ends with a {ending_choice}!")

# Podcast Reminders
reminder = st.checkbox("Set a reminder for creating new podcasts")
if reminder:
    st.write("You will receive reminders for new podcasts!")

# Collaboration Feature
collaborator_email = st.text_input("Invite a collaborator by email:")
if st.button("Send Invite"):
    st.write("Invite sent!")

st.write("#### Enjoy creating your podcasts!")
