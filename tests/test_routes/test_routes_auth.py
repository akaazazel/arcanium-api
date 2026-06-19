import asyncio

import pytest
import pytest_asyncio
from app.database import get_db
from app.main import app
from app.schemas.schemas import UserCreate, UserResponse
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tests.test_services.fixtures import db, init_db

client = TestClient(app=app)


@pytest.fixture
def override_db(db):
    def give_db():
        yield db

    app.dependency_overrides[get_db] = give_db


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
