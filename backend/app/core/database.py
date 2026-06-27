from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import quote_plus
from .config import settings

def get_database_url():
    if settings.DB_TYPE == "mysql":
        password = quote_plus(settings.MYSQL_PASSWORD)
        return f"mysql+aiomysql://{settings.MYSQL_USER}:{password}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    return "sqlite+aiosqlite:///./codeseer.db"

engine = create_async_engine(get_database_url(), echo=True)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def init_db():
    """Initialize database and create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()