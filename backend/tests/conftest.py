import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db):
    from app.models.models import User, UserRole
    user = User(
        id="test-user-001",
        email="dev@example.com",
        name="Test Developer",
        role=UserRole.DEVELOPER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def token_and_user(client, test_user):
    """创建一个有效 Token，返回 (token_str, user)"""
    resp = await client.post(
        "/api/mcp/tokens",
        json={"name": "Test Token", "user_id": test_user.id},
    )
    return resp.json()["token"], test_user
