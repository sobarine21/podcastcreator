import streamlit as st
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import PyPDF2
from PIL import Image
import qrcode
import base64
import io
import random
import string
import hashlib
import os
import sys
from io import BytesIO
from cryptography.hazmat.primitives import hashes


# Utility to generate a random key
def generate_random_key(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# Hash function for file integrity check (SHA-256)
def generate_file_hash(file_data):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_data)
    return sha256_hash.hexdigest()


# Encrypt the PDF file using AES (Password-based encryption)
def encrypt_pdf_aes(file, password):
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=os.urandom(16), iterations=100000, backend=default_backend()).derive(password.encode())
    cipher = Cipher(algorithms.AES(key), modes.CBC(os.urandom(16)), backend=default_backend())
    encryptor = cipher.encryptor()
    
    pdf_writer = PyPDF2.PdfWriter()
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        pdf_writer.add_page(page)
    
    output_pdf = io.BytesIO()
    pdf_writer.write(output_pdf)
    encrypted_data = encryptor.update(output_pdf.getvalue()) + encryptor.finalize()
    
    return encrypted_data, key


# Decrypt the PDF file using AES
def decrypt_pdf_aes(encrypted_data, key):
    cipher = Cipher(algorithms.AES(key), modes.CBC(os.urandom(16)), backend=default_backend())
    decryptor = cipher.decryptor()
    
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    return decrypted_data


# Generate a decryption script
def generate_decryption_script(key):
    script = f"""
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import PyPDF2

# The decryption key
key = {key}

# Decrypt the PDF data
def decrypt_pdf(encrypted_data, key):
    cipher = Cipher(algorithms.AES(key), modes.CBC(os.urandom(16)), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    return decrypted_data

# Example encrypted data (replace with actual encrypted PDF content)
encrypted_data = b"YOUR_ENCRYPTED_PDF_CONTENT"

# Decrypt and print the result
print(decrypt_pdf(encrypted_data, key))
"""
    return script


# Create a QR code for the decryption key or script
def create_qr_code(data):
    qr = qrcode.make(data)
    img = io.BytesIO()
    qr.save(img, 'PNG')
    img.seek(0)
    return img


# Streamlit UI
st.title("Advanced PDF Encryption & Decryption Tool")

option = st.selectbox("Select Action", ["Encrypt", "Decrypt"])

if option == "Encrypt":
    uploaded_file = st.file_uploader("Upload a PDF to encrypt", type="pdf")
    
    if uploaded_file:
        # Select Encryption Algorithm
        encryption_algorithm = st.selectbox("Choose encryption algorithm", ["AES", "RSA", "Blowfish"])
        
        if encryption_algorithm == "AES":
            password = st.text_input("Enter a password for AES encryption")
            
            if password:
                st.text("Encrypting PDF...")
                encrypted_pdf, encryption_key = encrypt_pdf_aes(uploaded_file, password)
                
                # Show encrypted PDF base64 data
                st.write("Encrypted PDF content (Base64):")
                st.text(base64.b64encode(encrypted_pdf).decode('utf-8'))
                
                # Generate and display QR code for decryption
                decryption_script = generate_decryption_script(encryption_key)
                qr_code_image = create_qr_code(decryption_script)
                
                st.image(qr_code_image, caption="Scan this QR code to get the decryption script.")
                
                # Allow the user to download the encrypted PDF
                st.download_button("Download Encrypted PDF", base64.b64encode(encrypted_pdf), "encrypted_pdf.pdf", mime="application/pdf")
                
                # Provide a downloadable decryption script
                st.download_button("Download Decryption Script", decryption_script, "decryption_script.py")
                
        # Add more encryption algorithms if needed

elif option == "Decrypt":
    encrypted_file = st.file_uploader("Upload Encrypted PDF for decryption", type="pdf")
    
    if encrypted_file:
        decryption_key = st.text_input("Enter decryption key (or scan QR code)")
        
        if decryption_key:
            decrypted_pdf = decrypt_pdf_aes(encrypted_file, decryption_key)
            st.write("Decrypted content:")
            st.text(decrypted_pdf.decode('utf-8'))
        
        # File integrity check (SHA-256)
        file_hash = generate_file_hash(encrypted_file.getvalue())
        st.write(f"File Integrity Hash: {file_hash}")

