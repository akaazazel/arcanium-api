from app.settings import settings
from cryptography.fernet import Fernet

cipher = Fernet(key=settings.encryption_key)


def encrypt(plain_text: str) -> str:
    return cipher.encrypt(plain_text.encode()).decode()


def decrypt(encrypted_text: str) -> str:
    return cipher.decrypt(encrypted_text.encode()).decode()
