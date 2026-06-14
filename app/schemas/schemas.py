from pydantic import BaseModel, EmailStr, Field

# User Schemas


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)


class UserResponse(UserBase):
    id: int


# Note Schemas


class NoteBase(BaseModel):
    title: str
    content: str = ""


class NoteCreate(NoteBase):
    pass


class NoteResponse(NoteBase):
    id: int


# Token Schemas


class Token(BaseModel):
    access_token: str
    token_type: str
