import streamlit as st
import PyPDF2
from gtts import gTTS
from io import BytesIO
import random
import re
import json
import csv
from pydub import AudioSegment
from pydub.playback import play
import langid
import os
import time
from transformers import pipeline
from googletrans import Translator
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from collections import Counter
import shutil
import tempfile

# Initialize NLTK resources
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Helper functions
def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def summarize_text(text, max_length=300):
    """Summarize text to fit into a shorter format."""
    sentences = text.split('. ')
    summary = '. '.join(sentences[:max_length]) + '.'
    return summary

def convert_text_to_audio(text, language="en", speed="normal", pitch="normal", volume="normal", accent="neutral", background_music=False):
    """Convert text to audio using gTTS and add custom features."""
    tts = gTTS(text=text, lang=language, slow=(speed == "slow"))
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    
    # If background music is enabled
    if background_music:
        try:
            sound_effect = AudioSegment.from_file("background_music.mp3")
            audio_segment = AudioSegment.from_mp3(audio_file)
            audio_segment = audio_segment + sound_effect
            audio_segment.export(audio_file, format="mp3")
            audio_file.seek(0)
        except Exception as e:
            st.warning(f"Could not add background music: {e}")
    
    return audio_file

def create_quiz(text):
    """Generate a quiz based on extracted text."""
    questions = [
        {"question": "What is the main idea of the text?", "answer": "The main idea is..."},
        {"question": "Can you mention one key detail from the text?", "answer": "A key detail is..."},
        {"question": "Summarize the text in a few words.", "answer": "Summary: ..."}
    ]
    return random.choice(questions)

def highlight_text(text, keyword="important"):
    """Highlight important words in the text."""
    highlighted_text = re.sub(rf"(\b{keyword}\b)", r"**\1**", text, flags=re.IGNORECASE)
    return highlighted_text

def detect_entities(text):
    """Detect key entities like names, dates, locations, etc."""
    # Placeholder, replace with actual NLP entity extraction model
    entities = {'names': ['John Doe'], 'dates': ['2024-11-06'], 'locations': ['New York']}
    return entities

def summarize_pdf(text):
    """Use AI model for text summarization."""
    summarizer = pipeline("summarization")
    summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def detect_sentiment(text):
    """Perform sentiment analysis on text."""
    sentiment_analyzer = pipeline("sentiment-analysis")
    sentiment = sentiment_analyzer(text)
    return sentiment[0]['label']

def translate_text(text, target_language='en'):
    """Translate text to another language."""
    translator = Translator()
    translated_text = translator.translate(text, dest=target_language).text
    return translated_text

def generate_audio_with_effects(text, effect_type="echo"):
    """Apply speech effects like echo, reverb to the generated podcast."""
    tts = gTTS(text=text, lang="en")
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    
    if effect_type == "echo":
        audio_segment = AudioSegment.from_mp3(audio_file)
        audio_segment = audio_segment + audio_segment.reverse()  # Echo effect
        audio_segment.export(audio_file, format="mp3")
        audio_file.seek(0)
    
    return audio_file

def export_pdf_data(text, format_type='json'):
    """Export extracted PDF text to JSON, CSV, or TXT."""
    if format_type == 'json':
        return json.dumps({"text": text})
    elif format_type == 'csv':
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerow([text])
        return csv_file.getvalue()
    else:
        return text

def generate_video_from_text(text):
    """Generate a simple video from the text (using basic slides)."""
    # Placeholder for future implementation
    return "Video created successfully."

# Word Cloud Generation
def generate_wordcloud(text):
    """Generate a word cloud from the text."""
    wordcloud = WordCloud(stopwords=stopwords.words('english'), background_color="white").generate(text)
    plt.figure(figsize=(10, 8))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    st.pyplot()

def plot_word_frequencies(text):
    """Plot word frequency distribution."""
    words = word_tokenize(text)
    filtered_words = [word.lower() for word in words if word.lower() not in stopwords.words('english') and word.isalpha()]
    fdist = FreqDist(filtered_words)
    plt.figure(figsize=(10, 6))
    fdist.plot(30, cumulative=False)
    st.pyplot()

def plot_sentiment_analysis(text):
    """Generate a sentiment analysis chart."""
    sentiment = detect_sentiment(text)
    sentiments = ['Positive', 'Negative'] if sentiment == 'NEGATIVE' else ['Positive']
    counts = [1, 0] if sentiment == 'NEGATIVE' else [1]
    sns.barplot(x=sentiments, y=counts)
    st.pyplot()

def create_podcast_segments(text, segment_length=500):
    """Split the text into segments for podcast."""
    segments = [text[i:i+segment_length] for i in range(0, len(text), segment_length)]
    return segments

def export_podcast_as_zip(audio_files):
    """Export multiple podcasts into a ZIP file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_file_path = os.path.join(temp_dir, "podcast.zip")
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for i, audio_file in enumerate(audio_files):
                zipf.write(audio_file, os.path.basename(audio_file))
        return zip_file_path

def create_pdf_preview(pdf_file):
    """Create a preview of the PDF file content."""
    text = extract_text_from_pdf(pdf_file)
    return text[:1000]

# Main app code
st.title("Enhanced PDF to Podcast Generator")
st.write("Upload a PDF to generate a podcast, create quizzes, and more.")

# PDF Upload
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file)

    st.subheader("Extracted Text")
    st.write(pdf_text)
    
    # Highlight important terms in the text
    highlighted_text = highlight_text(pdf_text, keyword="important")
    st.subheader("Highlighted Text")
    st.write(highlighted_text)

    # Text summarization
    summarized_text = summarize_text(pdf_text, max_length=3)
    st.subheader("Summarized Text")
    st.write(summarized_text)

    # Sentiment analysis
    sentiment = detect_sentiment(pdf_text)
    st.subheader("Sentiment Analysis")
    st.write(f"Sentiment: {sentiment}")
    
    # Entities detection
    entities = detect_entities(pdf_text)
    st.subheader("Detected Entities")
    st.json(entities)

    # Language Translation
    translated_text = translate_text(pdf_text, target_language='es')
    st.subheader("Translated Text (Spanish)")
    st.write(translated_text)

    # Generate Podcast Settings
    st.subheader("Generate Podcast Settings")
    language = st.selectbox("Choose language", ("en", "es", "fr", "de"))
    speed = st.radio("Select speed", ("normal", "slow"))
    pitch = st.radio("Select pitch", ("normal", "high", "low"))
    volume = st.slider("Set volume", 0.5, 2.0, 1.0)
    accent = st.selectbox("Choose accent", ("neutral", "british", "american"))
    background_music = st.checkbox("Add background music")

    # Generate Podcast Button
    if st.button("Generate Podcast Audio"):
        with st.spinner("Converting text to audio..."):
            audio_file = convert_text_to_audio(summarized_text, language=language, speed=speed, pitch=pitch, volume=volume, accent=accent, background_music=background_music)
        
        st.audio(audio_file, format="audio/mp3")
        
        # Add download button to download the podcast
        st.download_button("Download Podcast", audio_file, file
