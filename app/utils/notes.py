from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if ENCRYPTION_KEY is None:
    raise RuntimeError("ENCRYPTION_KEY env variable is missing!")


cipher = Fernet(key=ENCRYPTION_KEY)


def encrypt(plain_text: str):
    return cipher.encrypt(plain_text.encode()).decode()


def decrypt(encrypted_text: str):
    return cipher.decrypt(encrypted_text.encode()).decode()
