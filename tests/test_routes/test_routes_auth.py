import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
import pytest_asyncio
from app.core.settings import settings
from app.database import get_db
from app.main import app
from app.schemas.schemas import Token, UserCreate, UserResponse
from fastapi.testclient import TestClient
from tests.test_services.fixtures import db, init_db
from app.core.exceptions import UnauthorizedError

client = TestClient(app=app)


@pytest.fixture
def override_db(db):
    def give_db():
        yield db

    app.dependency_overrides[get_db] = give_db


def create_mock_token(type: str):
    return jwt.encode(
        payload={
            "sub": "user",
            "exp": datetime.now(UTC) + timedelta(days=10),
            "type": type,
        },
        key=settings.secret_key,
        algorithm=settings.algorithm,
    )


@pytest.mark.asyncio
async def test_register(override_db):
    user_data = UserCreate(
        name="akshay",
        email="akshay@gmail.com",
        password="unsettling",
    )

    response = client.post(
        "/auth/register",
        json=user_data.model_dump(),
    )
    res_user_data = response.json()

    assert response.status_code == 200
    assert res_user_data["name"] == user_data.name


@pytest.mark.asyncio
async def test_register_duplicate_user(override_db):
    user_data = UserCreate(
        name="akshay",
        email="akshay@gmail.com",
        password="unsettling",
    )

    client.post(
        "/auth/register",
        json=user_data.model_dump(),
    )
    response = client.post(
        "/auth/register",
        json=user_data.model_dump(),
    )

    assert response.status_code == 409


@pytest.mark.asyncio
@patch("app.routes.auth.login_user", new_callable=AsyncMock)
async def test_login_user(mock_login_user, override_db):

    access = Token(
        access_token=create_mock_token("access"),
        token_type="access",
    )
    refresh = create_mock_token("refresh")

    mock_login_user.return_value = (access, refresh)

    response = client.post(
        "/auth/login",
        data={
            "username": "user1@gmail.com",
            "password": "user1password",
        },
    )

    assert response.status_code == 200
    assert response.cookies.get("refresh_token") == refresh
    assert response.json()["access_token"] == access.access_token


@pytest.mark.asyncio
@patch("app.routes.auth.login_user", new_callable=AsyncMock)
async def test_login_exception(mock_login_user):

    mock_login_user.side_effect = UnauthorizedError

    response = client.post(
        "/auth/login",
        data={
            "username": "user1@gmail.com",
            "password": "user1password",
        },
    )

    assert response.status_code == 401
