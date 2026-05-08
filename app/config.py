from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:secret@localhost:5432/library_db"
    DATABASE_URL_TEST: str = "sqlite+aiosqlite:///:memory:"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Security
    JWT_SECRET_KEY: str = "super-secret-key-for-local-dev-change-in-production"
    SECRET_KEY: str | None = None  # Docker env fallback
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Business Logic
    DUE_DAYS: int = 14
    FINE_PER_DAY: float = 0.50
    MAX_BORROWS_PER_USER: int = 5

    # ✅ Pydantic V2 Settings Config
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def model_post_init(self, __context):
        # Prioritize SECRET_KEY from Docker environment if it exists
        if self.SECRET_KEY:
            self.JWT_SECRET_KEY = self.SECRET_KEY

settings = Settings()