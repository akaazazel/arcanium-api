from typing import Annotated

from app.core.rate_limit import limiter
from app.database import get_db
from app.models import models
from app.schemas.schemas import GenericResponse, Token, UserCreate, UserResponse
from app.services.auth import generate_tokens, is_token_revoked, logout_user
from app.utils.auth import hash_password, oauth2_scheme, verify_password, verify_token
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    select_response = await db.execute(
        select(models.User.email).where(
            func.lower(models.User.email) == user_data.email.lower()
        )
    )
    if select_response.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists!",
        )

    new_user = models.User(
        name=user_data.name,
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    response: Response,
):
    select_response = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == user_data.username.lower()
        )
    )

    user = select_response.scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Incorrect email or password",
        )

    return await generate_tokens(user_id=str(user.id), response=response)


@router.post("/logout")
@limiter.limit("5/minute")
async def logout(
    request: Request,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    try:
        await logout_user(refresh_token)

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return GenericResponse(message="User logged out")


@router.post("/refresh", response_model=Token)
@limiter.limit("5/minute")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    try:
        if await is_token_revoked(refresh_token):
            raise InvalidTokenError

        user_id = verify_token(refresh_token, "refresh")
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return await generate_tokens(user_id=str(user_id), response=response)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
):

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not provided",
        )

    user_id = verify_token(token, "access")

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    select_result = await db.execute(
        select(models.User).where(models.User.id == user_id_int)
    )

    user = select_result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
        )

    return user
