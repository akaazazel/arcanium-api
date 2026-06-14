import os
from datetime import timedelta
from typing import Annotated

from app.database import get_db
from app.models import models
from app.schemas.schemas import Token, UserCreate, UserResponse
from app.utils.auth import (
    create_token,
    hash_password,
    oauth2_scheme,
    verify_password,
    verify_token,
)
from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

TOKEN_EXPIRY_MINUTES = os.getenv("TOKEN_EXPIRY_MINUTES") or "30"
TOKEN_EXPIRY_DAYS = os.getenv("TOKEN_EXPIRY_DAYS") or "28"

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
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
async def login(
    user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
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
        )

    access_token_expiry = timedelta(minutes=int(TOKEN_EXPIRY_MINUTES))
    access_token = create_token({"sub": str(user.id)}, access_token_expiry, "access")

    refresh_token_expiry = timedelta(minutes=int(TOKEN_EXPIRY_MINUTES))
    refresh_token = create_token({"sub": str(user.id)}, refresh_token_expiry, "refresh")

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=str(refresh_token_expiry),
        httponly=True,
        secure=True,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/refresh")
async def refresh(refresh_token: Annotated[str | None, Cookie()]):
    user_id = verify_token(refresh_token, "refresh")

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    access_token_expiry = timedelta(minutes=int(TOKEN_EXPIRY_MINUTES))
    new_access_token = create_token({"sub": user_id}, access_token_expiry, "access")

    return Token(access_token=new_access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = verify_token(token, "access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
        )

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    select_result = await db.execute(
        select(models.User).where(models.User.id == user_id_int)
    )

    user = select_result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User don't exist",
        )

    return user
