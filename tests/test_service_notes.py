import pytest
import pytest_asyncio
from app.database import Base
from app.models.models import *
from app.schemas.schemas import NoteCreate, UserCreate
from app.services.notes import create_note, decrypt, get_note
from app.utils.auth import hash_password
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

postgre_url = "postgresql+psycopg://postgres:unsettled@postgres:5432/arcanium_test_db"
engine = create_async_engine(postgre_url)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


# fixtures


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


@pytest_asyncio.fixture  # creates tables and yields a db session, lastly drops tables
async def db(init_db):
    async with Session() as session:
        yield session

    await session.execute(
        text('TRUNCATE TABLE "note", "user" RESTART IDENTITY CASCADE')
    )
    await session.commit()


@pytest.fixture  # returns user data
def user_data():
    return UserCreate(name="akshay", email="akshay@gmail.com", password="unsettling")


@pytest.fixture  # returns note data
def note_data():
    return NoteCreate(title="Note title 01", content="Note content 01")


@pytest_asyncio.fixture  # adds a dummy user to database and returns the db object of user
async def added_user(user_data, db):
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


# tests


@pytest.mark.asyncio  # test valid note
async def test_create_note(db: AsyncSession, note_data, added_user):
    user = added_user

    # create a note
    note_id = await create_note(note_data=note_data, user_id=user.id, db=db)

    # fetch the note
    result = await db.execute(select(Note).where(Note.id == note_id))
    fetched_note = result.scalars().first()

    assert fetched_note is not None
    assert fetched_note.id == note_id
    assert decrypt(fetched_note.title) == note_data.title
    assert decrypt(fetched_note.content) == note_data.content
    assert fetched_note.owner == user.id
    assert fetched_note.created_at is not None
    assert fetched_note.updated_at is not None
    assert fetched_note.updated_at == fetched_note.created_at


@pytest.mark.asyncio  # create note without a user
async def test_create_note_no_user(db: AsyncSession, note_data):

    with pytest.raises(IntegrityError):
        await create_note(note_data=note_data, user_id=100, db=db)
