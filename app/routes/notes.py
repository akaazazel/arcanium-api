from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.routes.auth import get_current_user
from app.schemas.schemas import NoteCreate, NoteResponse, UserResponse
from app.models.models import Note
from app.database import get_db
from datetime import datetime, UTC
from app.utils.notes import encrypt, decrypt

router = APIRouter(tags=["notes"])


@router.post("/note")
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


@router.get("/note/{note_id}")
async def get_note():
    pass


@router.get("/note")
async def get_notes():
    pass


@router.put("/note/{note_id}")
async def update_notes():
    pass


@router.delete("/note/{note_id}")
async def delete_note():
    pass
