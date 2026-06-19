import pytest_asyncio
from app.database import Base
from app.models.models import Note, User
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy_utils import create_database, database_exists
from tests.test_services.utils import (
    add_to_db,
    get_note_model,
    get_user_model,
    note_factory,
    user_factory,
)

postgre_url = "postgresql+psycopg://postgres:unsettled@postgres:5432/arcanium_test_db"
engine = create_async_engine(postgre_url)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def init_db():
    if not database_exists(postgre_url):
        create_database(postgre_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db(init_db):
    async with Session() as session:
        yield session

    await session.execute(
        text('TRUNCATE TABLE "note", "user" RESTART IDENTITY CASCADE')
    )
    await session.commit()


@pytest_asyncio.fixture
async def insert_user_and_note_factory():
    async def insert_user_and_note(
        user_id: int, note_id: int, db: AsyncSession
    ) -> tuple[User, Note]:
        user = get_user_model(user_factory(), user_id)
        note = get_note_model(note_factory(), user_id, True, note_id)
        await add_to_db(db=db, data=[user, note])

        return (user, note)

    return insert_user_and_note
