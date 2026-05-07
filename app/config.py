from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:secret@localhost:5432/library_db"
    DATABASE_URL_TEST: str = "sqlite+aiosqlite:///:memory:"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "super-secret-key-for-local-dev-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    DUE_DAYS: int = 14
    FINE_PER_DAY: float = 0.50
    MAX_BORROWS_PER_USER: int = 5

    # ✅ Pydantic V2 Standard Config (replaces class Config)
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()