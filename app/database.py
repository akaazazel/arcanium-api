from app.core.settings import settings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# PostgreSQL

engine = create_async_engine(settings.postgres_url)
SessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db


# Redis


r_db = Redis.from_url(
    url=f"{settings.redis_url}/{settings.redis_token_db}",
    decode_responses=True,
)
