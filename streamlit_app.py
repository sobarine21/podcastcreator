import streamlit as st
import os
import random
import string
import hashlib
import PyPDF2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import qrcode
import zipfile
import io


# Helper functions

def generate_random_key(length=16):
    """Generate a random encryption key."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_file_hash(file_data):
    """Generate a hash (SHA-256) for file integrity check."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_data)
    return sha256_hash.hexdigest()

def encrypt_pdf_aes(file, password, key_length=256):
    """Encrypt PDF file using AES encryption with valid key size."""
    
    # Ensure the key length is valid for AES
    if key_length not in [128, 192, 256]:
        raise ValueError("Invalid key size for AES. Valid sizes are 128, 192, or 256 bits.")
    
    # Derive the encryption key from the password
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=key_length // 8, salt=os.urandom(16), iterations=100000, backend=default_backend()).derive(password.encode())
    
    # Encryption using AES (CBC mode)
    cipher = Cipher(algorithms.AES(key), modes.CBC(os.urandom(16)), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Writing the encrypted PDF
    pdf_writer = PyPDF2.PdfWriter()
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        pdf_writer.add_page(page)
    
    output_pdf = io.BytesIO()
    pdf_writer.write(output_pdf)
    encrypted_data = encryptor.update(output_pdf.getvalue()) + encryptor.finalize()
    
    return encrypted_data, key

def create_qr_code(data):
    """Generate a QR code for the decryption script."""
    qr = qrcode.make(data)
    img = io.BytesIO()
    qr.save(img, 'PNG')
    img.seek(0)
    return img

def create_watermarked_pdf(file, watermark_text="Confidential"):
    """Add watermark to PDF before encryption."""
    pdf_writer = PyPDF2.PdfWriter()
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        # Add watermark
        page.merge_text(watermark_text)
        pdf_writer.add_page(page)
    output_pdf = io.BytesIO()
    pdf_writer.write(output_pdf)
    return output_pdf.getvalue()

def zip_files(file_list, zip_filename="encrypted_files.zip"):
    """Zip the encrypted files for batch download."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_data, file_name in file_list:
            zf.writestr(file_name, file_data)
    zip_buffer.seek(0)
    return zip_buffer


# Streamlit UI

st.title("Advanced PDF Encryption & Decryption Tool")

option = st.selectbox("Select Action", ["Encrypt", "Decrypt"])

if option == "Encrypt":
    uploaded_file = st.file_uploader("Upload a PDF to encrypt", type="pdf", accept_multiple_files=True)
    
    if uploaded_file:
        # Select Encryption Algorithm and other options
        encryption_algorithm = st.selectbox("Choose encryption algorithm", ["AES", "RSA"])
        key_length = st.selectbox("Select AES key length", [128, 192, 256], index=2)  # Default to 256 bits
        
        # Watermark Option
        watermark_text = st.text_input("Enter watermark text (Optional)", "Confidential")
        
        # Encrypt File
        password = st.text_input("Enter password for AES encryption", "")
        if password:
            st.text("Encrypting PDF...")
            encrypted_pdfs = []
            
            for file in uploaded_file:
                encrypted_pdf, encryption_key = encrypt_pdf_aes(file, password, key_length)
                
                # Add watermark if selected
                if watermark_text:
                    encrypted_pdf = create_watermarked_pdf(file, watermark_text)
                
                encrypted_pdfs.append((encrypted_pdf, f"{file.name}_encrypted.pdf"))
            
            # Option to compress and download
            zip_option = st.checkbox("Compress and download encrypted files as ZIP", False)
            if zip_option:
                zip_buffer = zip_files(encrypted_pdfs)
                st.download_button("Download Encrypted ZIP", zip_buffer, "encrypted_files.zip", mime="application/zip")
            else:
                for encrypted_pdf, file_name in encrypted_pdfs:
                    st.download_button(f"Download {file_name}", encrypted_pdf, file_name, mime="application/pdf")

elif option == "Decrypt":
    uploaded_file = st.file_uploader("Upload an encrypted PDF", type="pdf")
    
    if uploaded_file:
        decryption_key = st.text_input("Enter decryption key")
        
        if decryption_key:
            decrypted_pdf = decrypt_pdf_aes(uploaded_file, decryption_key)
            st.write("Decrypted PDF content:")
            st.text(decrypted_pdf.decode('utf-8'))
