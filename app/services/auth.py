from datetime import UTC, datetime, timedelta

from app.core.settings import settings
from app.database import r_db
from app.schemas.schemas import Token
from app.utils.auth import create_token, decode_token
from fastapi import Response


async def generate_tokens(user_id: str, response: Response) -> Token:
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

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=str(refresh_token_expiry),
        httponly=True,
        secure=True,
    )

    return Token(access_token=access_token, token_type="bearer")


async def logout_user(refresh_token: str) -> None:

    decoded_jwt = decode_token(refresh_token, "refresh")

    jti = decoded_jwt["jti"]
    exp = datetime.fromtimestamp(int(decoded_jwt["exp"]), tz=UTC)
    cur = datetime.now(UTC)
    ttl = int((exp - cur).total_seconds())

    await r_db.set(jti, 1, ex=ttl)


async def is_token_revoked(refresh_token: str):
    decoded_jwt = decode_token(refresh_token, "refresh")

    jti = decoded_jwt["jti"]

    if await r_db.exists(jti) > 0:
        return True

    return False
