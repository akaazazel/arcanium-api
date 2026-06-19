import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
import pytest_asyncio
from app.core.exceptions import UnauthorizedError, InvalidUserError
from app.core.settings import settings
from app.database import get_db
from app.main import app
from app.schemas.schemas import Token, UserCreate, UserResponse
from fastapi.testclient import TestClient
from jwt.exceptions import InvalidTokenError
from tests.test_services.fixtures import db, init_db

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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "refresh_token",
    [
        None,
        create_mock_token("refresh"),
    ],
)
@patch("app.routes.auth.logout_user")
async def test_logout_user(mock_logout_user, refresh_token):
    mock_logout_user.return_value = None

    client.cookies.set("refresh_token", refresh_token)
    response = client.post("/auth/logout")

    if refresh_token is None:
        assert response.status_code == 401
        assert response.json()["message"] == "Refresh token not provided"
    else:
        assert response.status_code == 200

    client.cookies.clear()


@pytest.mark.asyncio
@patch("app.routes.auth.logout_user")
async def test_logout_user_invalid_refresh_token(mock_logout_user):
    mock_logout_user.side_effect = InvalidTokenError

    client.cookies.set("refresh_token", create_mock_token("refresh"))
    response = client.post("/auth/logout")

    assert response.status_code == 401

    client.cookies.clear()


@pytest.mark.asyncio
@patch("app.routes.auth.refresh_user_token")
async def test_refresh(mock_refresh_user_token):
    refresh = create_mock_token("refresh")

    mock_refresh_user_token.return_value = (
        Token(
            access_token=create_mock_token("access"),
            token_type="bearer",
        ),
        refresh,
    )

    client.cookies.set("refresh_token", create_mock_token("refresh"))
    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert response.cookies.get("refresh_token") == refresh

    client.cookies.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("refresh", [None, create_mock_token("refresh")])
@patch("app.routes.auth.refresh_user_token")
async def test_refresh_invalid_token(mock_refresh_user_token, refresh):
    mock_refresh_user_token.side_effect = InvalidTokenError

    client.cookies.set("refresh_token", create_mock_token("refresh"))
    response = client.post("/auth/refresh")

    assert response.status_code == 401

    client.cookies.clear()


@pytest.mark.asyncio
@patch("app.routes.auth.get_current_user_data")
async def test_get_current_user(mock_get_current_user_data):
    user_id = 1
    token = create_mock_token("access")

    mock_get_current_user_data.return_value = UserResponse(
        name="user01", email="user01@gmail.com", id=user_id
    )

    response = (
        client.get(
            "/auth/me",
            headers={"Authorization": f"bearer {token}"},
        )
    ).json()

    assert response["id"] == user_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token",
    [
        None,
        create_mock_token("access"),
    ],
)
@pytest.mark.parametrize(
    "errors",
    [
        ValueError,
        TypeError,
        InvalidUserError,
    ],
)
@patch("app.routes.auth.get_current_user_data")
async def test_get_current_user_exceptions(
    mock_get_current_user_data,
    errors,
    token,
):
    mock_get_current_user_data.side_effect = errors

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"bearer {token}"},
    )

    assert response.status_code == 401
