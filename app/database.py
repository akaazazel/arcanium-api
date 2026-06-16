from app.core.settings import settings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# PostgreSQL

engine = create_async_engine(settings.postgres_db_url)
SessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db


# Redis

r_db = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
