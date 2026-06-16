from datetime import timedelta
from app.core.settings import settings
from app.utils.auth import create_token
from fastapi import Response
from app.schemas.schemas import Token


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

    refresh_token_expiry = timedelta(minutes=int(settings.token_expiry_days))
    refresh_token = create_token({"sub": user_id}, refresh_token_expiry, "refresh")

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=str(refresh_token_expiry),
        httponly=True,
        secure=True,
    )

    return Token(access_token=access_token, token_type="bearer")
