from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)


class UserResponse(UserBase):
    id: int


class NoteBase(BaseModel):
    title: str
    content: str


class NoteCreate(NoteBase):
    created_at: datetime = datetime.now(timezone.utc)


class NoteResponse(NoteBase):
    note_id: int


class Token(BaseModel):
    access_token: str
    token_type: str
