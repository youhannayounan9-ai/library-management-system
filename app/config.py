from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./library.db"
    SECRET_KEY: str = "super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REDIS_URL: str = "redis://localhost:6379"
    MAX_BORROW_LIMIT: int = 5
    model_config = {"env_file": ".env", "case_sensitive": True}


@lru_cache()
def get_settings():
    return Settings()
