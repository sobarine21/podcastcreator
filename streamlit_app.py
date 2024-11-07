import streamlit as st
import os
import hashlib
import base64
import random
import string
import io
import qrcode
from zipfile import ZipFile
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from PyPDF2 import PdfReader, PdfWriter

# Helper functions

def generate_key(password: str, key_size: int = 256) -> bytes:
    """Generate an AES key from a password using PBKDF2 with a secure salt."""
    salt = os.urandom(16)  # 16-byte salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_size // 8,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_pdf(pdf_data: bytes, password: str, key_size: int = 256) -> bytes:
    """Encrypt PDF data using AES in CBC mode with a derived key."""
    key, salt = generate_key(password, key_size)
    iv = os.urandom(16)  # 16-byte IV for AES-CBC
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the PDF data to make its length a multiple of the block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(pdf_data) + padder.finalize()

    # Encrypt the padded PDF content
    encrypted_pdf = encryptor.update(padded_data) + encryptor.finalize()

    # Return the salt, IV, and encrypted data as a combined output
    return salt + iv + encrypted_pdf

def decrypt_pdf(encrypted_data: bytes, password: str, key_size: int = 256) -> bytes:
    """Decrypt PDF data using AES in CBC mode with the derived key."""
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_pdf = encrypted_data[32:]

    # Derive the key using the same method
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_size // 8,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the data
    decrypted_pdf = decryptor.update(encrypted_pdf) + decryptor.finalize()

    # Unpad the decrypted data
    unpadder = padding.PKCS7(128).unpadder()
    unpadded_data = unpadder.update(decrypted_pdf) + unpadder.finalize()

    return unpadded_data

def add_watermark(pdf_data: bytes, watermark_text: str) -> bytes:
    """Add watermark text to each page of the PDF."""
    pdf_reader = PdfReader(io.BytesIO(pdf_data))
    pdf_writer = PdfWriter()

    for page in pdf_reader.pages:
        # Adding watermark text to each page
        page.merge_text(watermark_text)
        pdf_writer.add_page(page)

    output_pdf = io.BytesIO()
    pdf_writer.write(output_pdf)
    return output_pdf.getvalue()

def generate_qr_code(data: str) -> bytes:
    """Generate a QR code image for given data."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img_byte = io.BytesIO()
    img.save(img_byte, format="PNG")
    img_byte.seek(0)
    return img_byte

# Streamlit UI

st.title("Advanced PDF Encryption & Decryption Tool with QR Decryption")

option = st.selectbox("Choose Operation", ["Encrypt PDF", "Decrypt PDF"])

if option == "Encrypt PDF":
    uploaded_files = st.file_uploader("Upload PDF files to encrypt", type="pdf", accept_multiple_files=True)
    password = st.text_input("Enter password for encryption", type="password")
    key_size = st.selectbox("Select AES Key Size", [128, 192, 256])

    watermark_text = st.text_input("Optional: Add watermark text to PDF pages")
    if uploaded_files and password:
        encrypted_files = []
        
        for uploaded_file in uploaded_files:
            # Reading PDF content
            pdf_data = uploaded_file.read()

            # Add watermark if specified
            if watermark_text:
                pdf_data = add_watermark(pdf_data, watermark_text)

            # Encrypt the PDF data
            encrypted_pdf_data = encrypt_pdf(pdf_data, password, key_size)

            # Store encrypted file and its name for later download
            encrypted_files.append((encrypted_pdf_data, f"{uploaded_file.name}_encrypted.pdf"))

        # Option to download each encrypted PDF or as a ZIP
        download_as_zip = st.checkbox("Download all encrypted files as ZIP")

        if download_as_zip:
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                for encrypted_pdf_data, file_name in encrypted_files:
                    zip_file.writestr(file_name, encrypted_pdf_data)
            zip_buffer.seek(0)
            st.download_button("Download Encrypted PDFs as ZIP", zip_buffer, "encrypted_pdfs.zip", mime="application/zip")
        else:
            for encrypted_pdf_data, file_name in encrypted_files:
                st.download_button(f"Download {file_name}", encrypted_pdf_data, file_name)

        # QR code for decryption information
        if password:
            qr_code_img = generate_qr_code(password)
            st.image(qr_code_img, caption="QR Code for Decryption Key", width=150)
            st.download_button("Download QR Code", qr_code_img, "decryption_qr.png", mime="image/png")

elif option == "Decrypt PDF":
    encrypted_file = st.file_uploader("Upload an encrypted PDF", type="pdf")
    password = st.text_input("Enter decryption password", type="password")

    if encrypted_file and password:
        encrypted_data = encrypted_file.read()
        
        try:
            decrypted_pdf_data = decrypt_pdf(encrypted_data, password)
            st.download_button("Download Decrypted PDF", decrypted_pdf_data, "decrypted_file.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Decryption failed: {e}")
