from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from app.core.settings import settings
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from fastapi import Response
from app.schemas.schemas import Token
from app.database import r_db

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return password_hash.verify(plain_password, hash_password)


def create_token(data: dict[str, Any], expire_delta: timedelta, token_type: str) -> str:
    """Generates a single JWT Token

    Args:
        data (dict[str, Any]): Base payload data. Usually contains { sub: user_id }
        expire_delta (timedelta): expiration of the token
        token_type (str): token type (refresh / access)

    Returns:
        str: JWT Token string
    """
    to_encode = data.copy()

    if expire_delta:
        expire = datetime.now(UTC) + expire_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=int(settings.token_expiry_days),
        )

    to_encode.update(
        {
            "exp": expire,
            "type": token_type,
        }
    )

    if token_type == "refresh":
        to_encode.update(
            {
                "jti": str(uuid4()),
            }
        )

    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def generate_tokens(user_id: str) -> tuple[Token, str]:
    """Generates access token and refresh tokens.\n
    Puts refresh token into the response cookie and returns the access token

    Args:
        user_id (str): user id from the database
        response (Response): response object

    Returns:
        Token: access token
    """

    access_token_expiry = timedelta(minutes=int(settings.token_expiry_minutes))
    access_token = create_token({"sub": user_id}, access_token_expiry, "access")

    refresh_token_expiry = timedelta(days=int(settings.token_expiry_days))
    refresh_token = create_token({"sub": user_id}, refresh_token_expiry, "refresh")

    return (Token(access_token=access_token, token_type="bearer"), refresh_token)


def decode_token(token: str, token_type: str) -> dict[str, str]:
    if token_type == "access":
        options = ["exp", "sub", "type"]
    else:
        options = ["exp", "sub", "type", "jti"]

    # Raises InvalidTokenError
    return jwt.decode(
        jwt=token,
        key=settings.secret_key,
        algorithms=settings.algorithm,
        options={"require": options},
    )


def verify_token(token: str, token_type: str) -> str:
    decoded_jwt = decode_token(token, token_type)

    if not (token_type == decoded_jwt.get("type")):
        raise InvalidTokenError("Invalid token type!")

    return decoded_jwt["sub"]


async def is_token_revoked(refresh_token: str):
    decoded_jwt = decode_token(refresh_token, "refresh")

    jti = decoded_jwt["jti"]

    if await r_db.exists(jti) > 0:
        return True

    return False
