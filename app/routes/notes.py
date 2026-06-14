from typing import Annotated

from app.database import get_db
from app.routes.auth import get_current_user
from app.schemas.schemas import NoteCreate, NoteResponse, UserResponse
from app.services import notes
from app.utils.notes import decrypt
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["notes"])


@router.post("/notes")
async def create_note(
    note_data: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):

    response = await notes.create_note(note_data=note_data, user_id=user.id, db=db)

    return {
        "message": "Note created",
        "id": response,
    }


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):
    result = await notes.get_note(note_id=note_id, user_id=user.id, db=db)

    return NoteResponse(
        id=result.id,
        title=decrypt(result.title),
        content=decrypt(result.content),
    )


@router.get("/notes", response_model=list[NoteResponse])
async def get_notes(
    user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):

    return await notes.get_notes(user.id, db)


@router.put("/notes/{note_id}")
async def update_notes(
    note_data: NoteCreate,
    note_id: int,
    user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await notes.update_note(
        user_id=user.id, note_id=note_id, note_data=note_data, db=db
    )

    return {"message": "Note updated!"}


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await notes.delete_note(
        note_id=note_id,
        user_id=user.id,
        db=db,
    )

    return {"message": "Note deleted!"}
