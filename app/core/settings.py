from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    postgres_password: str
    postgres_db: str
    postgres_db_url: str

    redis_host: str
    redis_port: int

    secret_key: str
    encryption_key: str
    algorithm: str
    token_expiry_minutes: int
    token_expiry_days: int


@lru_cache
def get_settings():
    return Settings()  # type: ignore


settings = get_settings()
