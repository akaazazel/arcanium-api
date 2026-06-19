from tests.test_services.fixtures import db, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_services.utils import user_factory, get_user_model, add_to_db
from app.services.auth import create_user, login_user, get_current_user_data
from app.utils.auth import verify_password
import pytest, pytest_asyncio
import asyncio
from app.core.exceptions import DuplicateUserError, UnauthorizedError, InvalidUserError
from sqlalchemy import select
from app.models.models import User


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


@pytest.mark.asyncio
async def test_login_user(db: AsyncSession):
    user = user_factory()
    user_model = get_user_model(user, 1)
    await add_to_db(db=db, data=[user_model])

    access, refresh = await login_user(
        username=user.email, password=user.password, db=db
    )

    assert access is not None
    assert refresh is not None


@pytest.mark.asyncio
async def test_login_invalid_user(db: AsyncSession):
    user = user_factory()

    with pytest.raises(UnauthorizedError):
        await login_user(username=user.email, password=user.password, db=db)


@pytest.mark.asyncio
async def test_login_invalid_password(db: AsyncSession):
    user = user_factory()
    user_model = get_user_model(user, 1)
    await add_to_db(db=db, data=[user_model])

    wrong_pass = "random_pass"

    with pytest.raises(UnauthorizedError):
        await login_user(username=user.email, password=wrong_pass, db=db)


@pytest.mark.asyncio
async def test_get_current_user(db: AsyncSession):
    name = "user01"
    user_id = 1
    user = user_factory(name)
    user_model = get_user_model(user, user_id)
    await add_to_db(db=db, data=[user_model])

    access, refresh = await login_user(
        username=user.email, password=user.password, db=db
    )

    cur_user = await get_current_user_data(token=access.access_token, db=db)

    assert cur_user.id == user_id
    assert cur_user.name == name


@pytest.mark.asyncio
async def test_get_current_user_invalid(db: AsyncSession):
    name = "user01"
    user_id = 1
    user = user_factory(name)
    user_model = get_user_model(user, user_id)
    await add_to_db(db=db, data=[user_model])

    access, refresh = await login_user(
        username=user.email, password=user.password, db=db
    )

    result = await db.execute(select(User).where(User.id == user_id))
    fetched_user = result.scalar_one_or_none()
    await db.delete(fetched_user)
    await db.commit()

    with pytest.raises(InvalidUserError):
        await get_current_user_data(token=access.access_token, db=db)
