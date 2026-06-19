from datetime import UTC, datetime

from app.core.exceptions import DuplicateUserError, InvalidUserError, UnauthorizedError
from app.database import r_db
from app.models import models
from app.models.models import User
from app.schemas.schemas import Token, UserCreate
from app.utils.auth import (
    decode_token,
    generate_tokens,
    hash_password,
    is_token_revoked,
    verify_password,
    verify_token,
)
from fastapi import Response
from jwt.exceptions import InvalidTokenError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(user_data: UserCreate, db: AsyncSession) -> models.User:
    select_response = await db.execute(
        select(models.User.email).where(
            func.lower(models.User.email) == user_data.email.lower()
        )
    )

    if select_response.scalars().first():
        raise DuplicateUserError

    new_user = models.User(
        name=user_data.name,
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login_user(
    username: str,
    password: str,
    db: AsyncSession,
    response: Response,
) -> Token:
    select_response = await db.execute(
        select(models.User).where(func.lower(models.User.email) == username.lower())
    )

    user = select_response.scalars().first()

    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError

    access_token, refresh_token = generate_tokens(user_id=str(user.id))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
    )

    return access_token


async def logout_user(refresh_token: str) -> None:

    decoded_jwt = decode_token(refresh_token, "refresh")

    jti = decoded_jwt["jti"]
    exp = datetime.fromtimestamp(int(decoded_jwt["exp"]), tz=UTC)
    cur = datetime.now(UTC)
    ttl = int((exp - cur).total_seconds())

    await r_db.set(jti, 1, ex=ttl)


async def refresh_user_token(refresh_token: str, response: Response) -> Token:
    if await is_token_revoked(refresh_token):
        raise InvalidTokenError

    user_id = verify_token(refresh_token, "refresh")

    access_token, refresh_token = generate_tokens(user_id=str(user_id))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
    )

    return access_token


async def get_current_user_data(token: str, db: AsyncSession) -> User:

    user_id = verify_token(token, "access")
    user_id_int = int(user_id)

    select_result = await db.execute(
        select(models.User).where(models.User.id == user_id_int)
    )
    user = select_result.scalars().first()

    if not user:
        raise InvalidUserError("User does not exist")

    return user
