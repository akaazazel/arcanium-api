import jwt, os
from dotenv import load_dotenv
from datetime import datetime, timedelta, UTC
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

load_dotenv()

TOKEN_EXPIRY_MINUTES = os.getenv("TOKEN_EXPIRY_MINUTES") or "30"
ALGORITHM = os.getenv("ALGORITHM") or "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return password_hash.verify(plain_password, hash_password)


def create_access_token(data, expire_delta) -> str:
    to_encode = data.copy()

    if expire_delta:
        expire = datetime.now(UTC) + expire_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=int(TOKEN_EXPIRY_MINUTES))

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    try:
        decoded_jwt = jwt.decode(
            jwt=token,
            key=SECRET_KEY,
            algorithms=ALGORITHM,
            options={"require": ["exp", "sub"]},
        )

    except jwt.InvalidTokenError:
        return None
    else:
        return decoded_jwt.get("sub")
