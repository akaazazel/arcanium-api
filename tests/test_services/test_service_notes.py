import pytest
from typing import Callable, Any
import pytest_asyncio
from datetime import datetime, UTC
from app.database import Base
from app.models.models import *
from app.schemas.schemas import NoteCreate, UserCreate
from app.services.notes import create_note, get_note
from app.utils.auth import hash_password
from app.utils.notes import decrypt
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy_utils import create_database, database_exists

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


def user_factory(name: str = "user0") -> UserCreate:
    return UserCreate(
        name=name,
        email=f"{name}@gmail.com",
        password=f"{name}_password",
    )


def note_factory(note_no: int = 1, no_content: bool = False) -> NoteCreate:
    content = f"Note {note_no} content" if no_content == False else ""

    return NoteCreate(
        title=f"Note {note_no} title.",
        content=content,
    )


def get_note_model(note_schema: NoteCreate, owner: int) -> Note:
    return Note(
        title=note_schema.title,
        content=note_schema.content,
        owner=owner,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def get_user_model(user_schema: UserCreate) -> User:
    return User(
        name=user_schema.name,
        email=user_schema.email,
        password_hash=hash_password(user_schema.password),
    )


@pytest.mark.asyncio
async def add_to_db(db: AsyncSession, data: list[Any]) -> None:
    for models in data:
        db.add(models)

    await db.commit()

    for models in data:
        await db.refresh(models)


@pytest.mark.asyncio
async def test_create_notes(db: AsyncSession):
    user = get_user_model(user_factory("user01"))

    await add_to_db(db, [user])  # creates user

    note = note_factory(1)

    # test: Create a new note
    note_id = await create_note(note_data=note, user_id=user.id, db=db)

    # verify: Fetch created note
    result = await db.execute(select(Note).where(Note.id == note_id))
    fetched_note = result.scalar_one_or_none()

    assert fetched_note is not None
    assert decrypt(fetched_note.title) == note.title
    assert decrypt(fetched_note.content) == note.content
    assert fetched_note.owner == 1
    assert fetched_note.created_at is not None
    assert fetched_note.updated_at is not None
    assert fetched_note.updated_at == fetched_note.created_at


@pytest.mark.asyncio
async def test_create_notes_no_user(db):
    note = note_factory(1)

    with pytest.raises(IntegrityError):
        await create_note(note_data=note, user_id=1, db=db)
