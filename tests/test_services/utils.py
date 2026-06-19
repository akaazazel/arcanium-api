from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.models import Note, User
from app.schemas.schemas import NoteCreate, UserCreate
from app.utils.auth import hash_password
from app.utils.notes import encrypt
from sqlalchemy.ext.asyncio import AsyncSession


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


def get_note_model(
    note_schema: NoteCreate,
    owner: int,
    is_encrypt: bool = False,
    id: int | None = None,
    time_delta_day: int | None = None,
) -> Note:
    date_time = datetime.now(UTC)

    if time_delta_day is not None:
        date_time = date_time + timedelta(days=time_delta_day)

    if is_encrypt is True:
        note_schema.title = encrypt(note_schema.title)
        note_schema.content = encrypt(note_schema.content)

    new_note = Note(
        title=note_schema.title,
        content=note_schema.content,
        owner=owner,
        created_at=date_time,
        updated_at=date_time,
    )

    if id is not None:
        new_note.id = id

    return new_note


def get_user_model(user_schema: UserCreate, id: int | None = None) -> User:
    user = User(
        name=user_schema.name,
        email=user_schema.email,
        password_hash=hash_password(user_schema.password),
    )

    if id is not None:
        user.id = id

    return user


async def add_to_db(db: AsyncSession, data: list[Any]) -> None:
    for models in data:
        db.add(models)

    await db.commit()

    for models in data:
        await db.refresh(models)
