from tests.test_services.fixtures import db, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_services.utils import user_factory
from app.services.auth import create_user, login_user
from app.utils.auth import verify_password
import pytest, pytest_asyncio
import asyncio
from app.core.exceptions import DuplicateUserError


@pytest.mark.asyncio
async def test_creating_user(db: AsyncSession):
    name = "username_001"
    user_data = user_factory(name)

    new_user = await create_user(user_data=user_data, db=db)

    assert new_user is not None
    assert new_user.name == user_data.name
    assert new_user.email == user_data.email
    assert verify_password(user_data.password, new_user.password_hash) == True


@pytest.mark.asyncio
async def test_creating_duplicate_user(db: AsyncSession):
    name = "username_001"
    user_data_1 = user_factory(name)

    await create_user(user_data=user_data_1, db=db)

    with pytest.raises(DuplicateUserError):
        await create_user(user_data=user_data_1, db=db)
