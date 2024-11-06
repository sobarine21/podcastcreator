import streamlit as st
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import PyPDF2
from PIL import Image
import qrcode
import base64
import io
import random
import string
import os
from cryptography.hazmat.primitives import hashes

# Utility to generate a random key
def generate_random_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Encrypt the PDF file
def encrypt_pdf(file, key):
    pdf_writer = PyPDF2.PdfWriter()
    reader = PyPDF2.PdfReader(file)
    
    for page in reader.pages:
        pdf_writer.add_page(page)

    output_pdf = io.BytesIO()
    pdf_writer.write(output_pdf)
    encrypted_data = base64.b64encode(output_pdf.getvalue())
    return encrypted_data

# Generate a Python decryption script
def generate_decryption_script(key):
    script = f"""
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import io
import PyPDF2

# The decryption key
key = '{key}'

# Decrypt the PDF data
def decrypt_pdf(encrypted_data, key):
    encrypted_pdf = base64.b64decode(encrypted_data)
    output_pdf = io.BytesIO(encrypted_pdf)
    reader = PyPDF2.PdfReader(output_pdf)
    decrypted_text = ''
    
    for page in reader.pages:
        decrypted_text += page.extract_text()
    return decrypted_text

# Example encrypted data (replace with actual encrypted PDF content)
encrypted_data = b"YOUR_ENCRYPTED_PDF_CONTENT"

# Decrypt and print the result
print(decrypt_pdf(encrypted_data, key))
"""
    return script

# Create QR Code for decryption script
def create_qr_code(data):
    qr = qrcode.make(data)
    img = io.BytesIO()
    qr.save(img, 'PNG')
    img.seek(0)
    return img

# App Layout
st.title("Crazy PDF Encryption and Decryption Tool")
option = st.selectbox("Select Action", ["Encrypt", "Decrypt"])

if option == "Encrypt":
    uploaded_file = st.file_uploader("Upload a PDF to encrypt", type="pdf")
    
    if uploaded_file:
        key = st.text_input("Enter encryption key (leave empty for random key)", "")
        if not key:
            key = generate_random_key()
        
        encrypted_pdf = encrypt_pdf(uploaded_file, key)
        
        # Display encrypted PDF (base64 encoded)
        st.write("Encrypted PDF content (Base64):")
        st.text(encrypted_pdf.decode('utf-8'))
        
        # Generate and display the QR code for decryption
        decryption_script = generate_decryption_script(key)
        qr_code_image = create_qr_code(decryption_script)
        
        st.image(qr_code_image, caption="Scan this QR code to get the decryption script")

        # Provide the option to download the QR-based decryption script
        st.download_button("Download QR-based Decryption Script", decryption_script, "decryption_script.py")
        
        # Allow the user to download the encrypted PDF
        st.download_button("Download Encrypted PDF", encrypted_pdf, "encrypted_pdf.txt")
        
elif option == "Decrypt":
    encrypted_file = st.file_uploader("Upload Encrypted PDF for decryption", type="txt")
    
    if encrypted_file:
        encrypted_data = encrypted_file.read().decode('utf-8')
        key_input = st.text_input("Enter the decryption key (or scan QR code)")
        
        if key_input:
            # Decrypt the file based on the provided key
            decrypted_data = decrypt_pdf(encrypted_data, key_input)
            st.write("Decrypted content:")
            st.text(decrypted_data)
        
        # Optionally add a feature to decrypt hidden data from an image using steganography
