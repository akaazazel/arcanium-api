from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str
    postgres_db: str = "arcanium_db"

    redis_password: str
    redis_url: str
    redis_token_db: str = ""
    redis_limiter_db: str = ""

    secret_key: str
    encryption_key: str
    algorithm: str
    token_expiry_minutes: int = 5
    token_expiry_days: int = 30

    @property
    def postgres_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings():
    return Settings()  # type: ignore


settings = get_settings()
