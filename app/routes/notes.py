from datetime import datetime
from typing import Annotated, Literal

from app.database import get_db
from app.routes.auth import get_current_user
from app.schemas.schemas import (
    CreatedResponse,
    GenericResponse,
    NoteCreate,
    NoteResponse,
    UserResponse,
)
from app.services import notes
from app.utils.notes import decrypt
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NoteNotFoundError

router = APIRouter(tags=["notes"])


@router.post("/notes", response_model=CreatedResponse)
async def create_note(
    note_data: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):

    response = await notes.create_note(note_data=note_data, user_id=user.id, db=db)

    return CreatedResponse(
        message="Note created",
        id=response,
    )


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):
    try:
        result = await notes.get_note(note_id=note_id, user_id=user.id, db=db)
    except NoteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return NoteResponse(
        id=result.id,
        title=decrypt(result.title),
        content=decrypt(result.content),
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("/notes", response_model=list[NoteResponse])
async def get_notes(
    user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sort: Literal["date_created", "date_updated"] = "date_created",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(gt=0, lt=101, default=100),
    offset_id: int | None = None,
    offset_date: datetime | None = None,
):

    return await notes.get_notes(
        user.id,
        db,
        sort,
        order,
        limit,
        offset_id,
        offset_date,
    )


@router.put("/notes/{note_id}", response_model=GenericResponse)
async def update_notes(
    note_data: NoteCreate,
    note_id: int,
    user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):

    try:
        result = await notes.update_note(
            user_id=user.id, note_id=note_id, note_data=note_data, db=db
        )
    except NoteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return GenericResponse(message="Note updated")


@router.delete("/notes/{note_id}", response_model=GenericResponse)
async def delete_note(
    note_id: int,
    user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):

    try:
        result = await notes.delete_note(
            note_id=note_id,
            user_id=user.id,
            db=db,
        )
    except NoteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return GenericResponse(message="Note deleted")
