from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from app.core.settings import settings
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return password_hash.verify(plain_password, hash_password)


def create_token(data: dict[str, Any], expire_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()

    if expire_delta:
        expire = datetime.now(UTC) + expire_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=int(settings.token_expiry_minutes)
        )

    to_encode.update(
        {
            "exp": expire,
            "type": token_type,
        }
    )

    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def verify_token(token: str | None, token_type: str) -> str | None:
    if token is None:
        return None

    try:
        decoded_jwt = jwt.decode(
            jwt=token,
            key=settings.secret_key,
            algorithms=settings.algorithm,
            options={"require": ["exp", "sub", "type"]},
        )

        if not (token_type == decoded_jwt.get("type")):
            raise jwt.InvalidTokenError("Invalid token type!")

    except jwt.InvalidTokenError:
        return None
    else:
        return decoded_jwt.get("sub")
