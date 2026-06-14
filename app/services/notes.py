from typing import Sequence
from app.models.models import Note
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schemas import NoteResponse, NoteCreate
from app.utils.notes import decrypt, encrypt
from datetime import datetime, UTC


async def get_note(
    note_id: int,
    user_id: int,
    db: AsyncSession,
) -> Note:
    result = await db.execute(
        select(Note).where(
            (Note.id == note_id) & (Note.owner == user_id),
        )
    )

    note = result.scalars().first()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The note is not found!",
        )

    return note


async def get_notes(
    user_id: int,
    db: AsyncSession,
) -> Sequence:
    response = await db.execute(select(Note).where(Note.owner == user_id))
    notes = response.scalars().all()

    decrypted_notes: list[NoteResponse] = []

    for note in notes:
        decrypted_notes.append(
            NoteResponse(
                id=note.id,
                title=decrypt(note.title),
                content=decrypt(note.content),
            )
        )

    return decrypted_notes


async def create_note(
    note_data: NoteCreate,
    user_id: int,
    db: AsyncSession,
) -> int:
    new_note = Note(
        title=encrypt(note_data.title),
        content=encrypt(note_data.content),
        owner=user_id,
        created_at=datetime.now(UTC),
    )

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return new_note.id


async def update_note(
    user_id: int,
    note_id: int,
    note_data: NoteCreate,
    db: AsyncSession,
) -> None:
    result = await get_note(note_id=note_id, user_id=user_id, db=db)

    result.title = encrypt(note_data.title)
    result.content = encrypt(note_data.content)

    await db.commit()
    await db.refresh(result)


async def delete_note(
    note_id: int,
    user_id: int,
    db: AsyncSession,
) -> None:
    result = await get_note(note_id=note_id, user_id=user_id, db=db)

    await db.delete(result)
    await db.commit()
