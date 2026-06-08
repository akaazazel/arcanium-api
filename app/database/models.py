from app.database.database import Base
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    password: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )


class Note(Base):
    __tablename__ = "note"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    owner: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
