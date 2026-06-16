from typing import Annotated

from app.database import get_db
from app.models import models
from app.schemas.schemas import Token, UserCreate, UserResponse
from app.services.auth import generate_tokens
from app.utils.auth import hash_password, oauth2_scheme, verify_password, verify_token
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
            detail="Incorrect email or password",
        )

    return await generate_tokens(user_id=str(user.id), response=response)


@router.get("/refresh", response_model=Token)
async def refresh(
    refresh_token: Annotated[str | None, Cookie()],
    response: Response,
):
    user_id = verify_token(refresh_token, "refresh")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return await generate_tokens(user_id=str(user_id), response=response)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = verify_token(token, "access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
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
