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

    # Storage backend type: ftp / oss
    STORAGE_TYPE: str = "ftp"

    # FTP configuration
    FTP_HOST: str = "ftp.example.com"
    FTP_PORT: int = 21
    FTP_USERNAME: str = "admin"
    FTP_PASSWORD: str = "password"
    FTP_REMOTE_BASE_PATH: str = "/code-changes"

    # OSS (S3-compatible) configuration
    OSS_ENDPOINT: str = "https://s3.amazonaws.com"
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = "codeseer-changes"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()