from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    minio_endpoint: str = "http://localhost:9000"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/coverocr"
    allowed_origins: list[str] = ["http://localhost:5173"]

    model_config = {
        "env_prefix": "COVEROCR_",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
