from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.routes.auth import get_current_user
from app.schemas.schemas import NoteCreate, NoteResponse, UserResponse
from app.models.models import Note
from app.database import get_db
from datetime import datetime, UTC
from app.utils.notes import encrypt, decrypt
from sqlalchemy import select

router = APIRouter(tags=["notes"])


@router.post("/notes")
async def create_note(
    note_data: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):

    new_note = Note(
        title=encrypt(note_data.title),
        content=encrypt(note_data.content),
        owner=user.id,
        created_at=datetime.now(UTC),
    )

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return {
        "message": "Note created",
        "id": new_note.id,
    }


@router.get("/notes/{note_id}")
async def get_note(
    note_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):
    result = await db.execute(
        select(Note).where(
            (Note.id == note_id) & (Note.owner == user.id),
        )
    )
    note = result.scalars().first()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The note is not found!",
        )

    return NoteResponse(
        id=note.id,
        title=decrypt(note.title),
        content=decrypt(note.content),
    )


@router.get("/notes")
async def get_notes():
    pass


@router.put("/notes/{note_id}")
async def update_notes():
    pass


@router.delete("/notes/{note_id}")
async def delete_note():
    pass
