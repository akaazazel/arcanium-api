import pytest
import pytest_asyncio
from app.database import Base
from app.models.models import *
from app.schemas.schemas import NoteCreate, UserCreate
from app.services.notes import create_note, decrypt, get_note
from app.utils.auth import hash_password
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy_utils import create_database, database_exists

postgre_url = "postgresql+psycopg://postgres:unsettled@postgres:5432/arcanium_test_db"
engine = create_async_engine(postgre_url)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db():
    if not database_exists(postgre_url):
        create_database(postgre_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def user_data():
    return UserCreate(name="akshay", email="akshay@gmail.com", password="unsettling")


@pytest.fixture
def note_data():
    return NoteCreate(title="Note title 01", content="Note content 01")


@pytest.mark.asyncio
async def test_create_note(db, user_data, note_data):
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    note_id = await create_note(note_data=note_data, user_id=user.id, db=db)

    fetched_note = await get_note(note_id=note_id, user_id=user.id, db=db)

    assert fetched_note.id == note_id
    assert decrypt(fetched_note.title) == note_data.title
    assert decrypt(fetched_note.content) == note_data.content
