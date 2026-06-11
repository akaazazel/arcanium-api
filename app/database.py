import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DB_URL = os.getenv("POSTGRES_DB_URL")

if DB_URL is None:
    raise RuntimeError("POSTGRES_DB_URL env variable is required!")

engine = create_async_engine(DB_URL)
SessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db
