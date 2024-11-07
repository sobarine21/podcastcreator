import streamlit as st
import os
import io
import qrcode
from zipfile import ZipFile
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from PyPDF2 import PdfReader, PdfWriter

# Helper functions

def generate_key(password: str, key_size: int = 256) -> bytes:
    """Generate AES key from password."""
    salt = os.urandom(16)  # Random salt for key generation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_size // 8,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_pdf_aes(pdf_data: bytes, password: str) -> bytes:
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

def decrypt_pdf_aes(encrypted_data: bytes, password: str) -> bytes:
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

def generate_rsa_keys() -> tuple:
    """Generate RSA public and private keys."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    # Serialize private and public keys to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

def encrypt_pdf_rsa(pdf_data: bytes, public_key: bytes) -> bytes:
    """Encrypt PDF using RSA public key."""
    public_key_obj = serialization.load_pem_public_key(public_key, backend=default_backend())
    encrypted_pdf = public_key_obj.encrypt(pdf_data, asymmetric_padding.OAEP(
        mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    ))
    return encrypted_pdf

def decrypt_pdf_rsa(encrypted_data: bytes, private_key: bytes) -> bytes:
    """Decrypt PDF using RSA private key."""
    private_key_obj = serialization.load_pem_private_key(private_key, password=None, backend=default_backend())
    decrypted_pdf = private_key_obj.decrypt(encrypted_data, asymmetric_padding.OAEP(
        mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    ))
    return decrypted_pdf

# Streamlit UI

st.title("Advanced PDF Encryption & Decryption Tool with Multiple Algorithms")

option = st.selectbox("Choose Operation", ["Encrypt PDF", "Decrypt PDF"])

if option == "Encrypt PDF":
    uploaded_files = st.file_uploader("Upload PDF files to encrypt", type="pdf", accept_multiple_files=True)
    password = st.text_input("Enter password for encryption", type="password")

    # Choose Encryption Algorithm
    encryption_algo = st.selectbox("Choose Encryption Algorithm", ["AES", "RSA"])

    if uploaded_files and password:
        encrypted_files = []
        
        for uploaded_file in uploaded_files:
            pdf_data = uploaded_file.read()
            encrypted_pdf_data = None

            if encryption_algo == "AES":
                encrypted_pdf_data = encrypt_pdf_aes(pdf_data, password)
            
            elif encryption_algo == "RSA":
                private_pem, public_pem = generate_rsa_keys()
                encrypted_pdf_data = encrypt_pdf_rsa(pdf_data, public_pem)

            if encrypted_pdf_data:
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

        # QR Code for decryption password or key
        qr_code_img = generate_qr_code(password if encryption_algo == "AES" else public_pem.decode())
        st.image(qr_code_img, caption="QR Code for Decryption Key", width=150)
        st.download_button("Download QR Code", qr_code_img, "decryption_qr.png", mime="image/png")

elif option == "Decrypt PDF":
    encrypted_file = st.file_uploader("Upload an encrypted PDF", type="pdf")
    password = st.text_input("Enter decryption password", type="password")

    # Choose Encryption Algorithm
    decryption_algo = st.selectbox("Choose Decryption Algorithm", ["AES", "RSA"])

    if encrypted_file and password:
        encrypted_data = encrypted_file.read()

        if decryption_algo == "AES":
            try:
                decrypted_pdf_data = decrypt_pdf_aes(encrypted_data, password)
                st.download_button("Download Decrypted PDF", decrypted_pdf_data, "decrypted_file.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Decryption failed: {e}")

        elif decryption_algo == "RSA":
            try:
                # Assume private_key is provided by the user for RSA decryption
                private_key = st.text_area("Enter your RSA private key (in PEM format)", height=200)
                decrypted_pdf_data = decrypt_pdf_rsa(encrypted_data, private_key.encode())
                st.download_button("Download Decrypted PDF", decrypted_pdf_data, "decrypted_file.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Decryption failed: {e}")
