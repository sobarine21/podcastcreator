import streamlit as st
import os
import io
import qrcode
from zipfile import ZipFile
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from PyPDF2 import PdfReader, PdfWriter

# Helper Functions

def generate_key(password: str) -> bytes:
    """Generate AES key from password."""
    salt = os.urandom(16)  # Random salt for key generation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_pdf(pdf_data: bytes, password: str) -> bytes:
    """Encrypt PDF using AES."""
    key, salt = generate_key(password)
    iv = os.urandom(16)  # 16-byte IV
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the PDF data
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(pdf_data) + padder.finalize()

    encrypted_pdf = encryptor.update(padded_data) + encryptor.finalize()

    return salt + iv + encrypted_pdf

def decrypt_pdf(encrypted_data: bytes, password: str) -> bytes:
    """Decrypt AES encrypted PDF."""
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_pdf = encrypted_data[32:]

    key, _ = generate_key(password)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_pdf = decryptor.update(encrypted_pdf) + decryptor.finalize()

    # Unpad the data
    unpadder = padding.PKCS7(128).unpadder()
    unpadded_data = unpadder.update(decrypted_pdf) + unpadder.finalize()

    return unpadded_data

def generate_qr_code(data: str) -> bytes:
    """Generate a QR code for a password."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img_byte = io.BytesIO()
    img.save(img_byte, format="PNG")
    img_byte.seek(0)
    return img_byte

# Streamlit UI

st.title("PDF Encryption & Decryption Tool with QR Code")

option = st.selectbox("What do you want to do?", ["Encrypt PDF", "Decrypt PDF"])

if option == "Encrypt PDF":
    uploaded_files = st.file_uploader("Upload PDF files to encrypt", type="pdf", accept_multiple_files=True)
    password = st.text_input("Enter password for encryption", type="password")
    
    if uploaded_files and password:
        encrypted_files = []
        
        for uploaded_file in uploaded_files:
            pdf_data = uploaded_file.read()
            
            # Encrypt the PDF
            encrypted_pdf_data = encrypt_pdf(pdf_data, password)
            encrypted_files.append((encrypted_pdf_data, f"{uploaded_file.name}_encrypted.pdf"))

        # Option to download all PDFs as a ZIP
        download_as_zip = st.checkbox("Download as ZIP")

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

        # QR Code for decryption password
        qr_code_img = generate_qr_code(password)
        st.image(qr_code_img, caption="QR Code for Decryption Password", width=150)
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
