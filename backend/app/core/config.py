from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeSeer"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # Database - SQLite for development, PostgreSQL for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeseer.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()