from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeSeer"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # Database - MySQL for production, SQLite for development
    # MySQL: mysql+aiomysql://user:password@host:port/dbname
    # SQLite: sqlite+aiosqlite:///./codeseer.db
    DB_TYPE: str = "mysql"  # "mysql" or "sqlite"
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeseer.db"
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "ljb0916@"
    MYSQL_DATABASE: str = "codeseer"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Access Token
    ACCESS_TOKEN_SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRY_DAYS: int = 30
    ACCESS_TOKEN_LENGTH: int = 32

    # LLM (AI) Configuration for document merge
    LLM_PROVIDER: str = "openai"  # "openai" / "anthropic" / "ollama"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MAX_TOKENS: int = 8192
    LLM_TEMPERATURE: float = 0.3

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