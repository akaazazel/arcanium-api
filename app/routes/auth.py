from typing import Annotated

from app.core.exceptions import DuplicateUserError, InvalidUserError, UnauthorizedError
from app.core.rate_limit import limiter
from app.database import get_db
from app.schemas.schemas import GenericResponse, Token, UserCreate, UserResponse
from app.services.auth import (
    create_user,
    get_current_user_data,
    login_user,
    logout_user,
    refresh_user_token,
)
from app.utils.auth import oauth2_scheme
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    try:
        new_user = await create_user(user_data=user_data, db=db)
    except DuplicateUserError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists!",
        )

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    response: Response,
):
    try:
        access_token, refresh_token = await login_user(
            username=user_data.username,
            password=user_data.password,
            db=db,
        )

    except UnauthorizedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Incorrect email or password",
        )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
    )

    return access_token


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
        new_access_token, new_refreh_token = await refresh_user_token(
            refresh_token=refresh_token,
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    response.set_cookie(
        key="refresh_token",
        value=new_refreh_token,
        httponly=True,
        secure=True,
    )

    return new_access_token


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

    try:
        user_data = await get_current_user_data(token=token, db=db)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )
    except InvalidUserError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
        )

    return user_data
