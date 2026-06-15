from datetime import UTC, datetime
from typing import Sequence

from app.models.models import Note
from app.schemas.schemas import NoteCreate, NoteResponse
from app.utils.notes import decrypt, encrypt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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
    sort: str,
    order: str,
    limit: int,
    offset_id: int | None,
    offset_date: datetime | None,
) -> Sequence:

    is_asc = True if order == "asc" else False

    date_stmt = Note.created_at if sort == "date_created" else Note.updated_at
    order_stmt = date_stmt.asc() if is_asc else date_stmt.desc()

    # The below code is used for pagination
    # The program uses date (created/updated) and id of the last note from the list of notes sent.
    # The date and id is given by client, to order and choose the next list of notes to be send.
    # 1. Basically, client requests a limited number of notes.
    # 2. Then they sent us the id and date of the last note in the list we sent.
    # 3. Then we sent them the next notes coming after that date and id.
    offset_stmt = None

    if offset_id is not None and offset_date is not None:
        # Why we using both date and id. date is already enough right????
        # Nuh uh...
        # If offset date and note date are different, just choose it based on the order (asc/desc)
        # But sometimes different notes can have same dates. It makes the offset date and note date same.
        # if we're just comparing dates and sending the notes after a specific date, then the notes with same date might be misssed during the filtering
        # Thats were we use note id to find difference.
        offset_stmt_diff_date = (
            (date_stmt > offset_date) if is_asc else (date_stmt < offset_date)
        )

        offset_stmt_same_date = (date_stmt == offset_date) & (
            (Note.id > offset_id) if is_asc else (Note.id < offset_id)
        )

        offset_stmt = offset_stmt_same_date | offset_stmt_diff_date
    else:
        offset_stmt = True

    stmt = (
        select(Note)
        .where((Note.owner == user_id) & offset_stmt)
        .order_by(
            order_stmt,
            Note.id,
        )
        .limit(limit)
    )

    response = await db.execute(stmt)
    notes = response.scalars().all()

    decrypted_notes: list[NoteResponse] = []

    for note in notes:
        decrypted_notes.append(
            NoteResponse(
                id=note.id,
                title=decrypt(note.title),
                content=decrypt(note.content),
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
        )

    return decrypted_notes


async def create_note(
    note_data: NoteCreate,
    user_id: int,
    db: AsyncSession,
) -> int:
    cur_time = datetime.now(UTC)
    new_note = Note(
        title=encrypt(note_data.title),
        content=encrypt(note_data.content),
        owner=user_id,
        created_at=cur_time,
        updated_at=cur_time,
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
    result.updated_at = datetime.now(UTC)

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
