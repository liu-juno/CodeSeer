import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.models import Project, Iteration, Requirement

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
async def test_project(db):
    project = Project(
        id="proj-test-001",
        name="Test Project",
        identifier="test-proj",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_requirement(db, test_project):
    req = Requirement(
        id="req-test-001",
        title="Test Requirement",
        project_id=test_project.id,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@pytest.mark.asyncio
async def test_full_attachment_flow(client, db, test_requirement):
    """完整流程：创建需求 → 上传附件 → 列出附件 → 下载附件 → 删除附件"""
    req_id = test_requirement.id

    # 1. 上传附件
    upload_resp = await client.post(
        f"/api/requirements/{req_id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["filename"] == "test.txt"
    assert upload_data["file_size"] == 11
    att_id = upload_data["id"]

    # 2. 列出附件
    list_resp = await client.get(f"/api/requirements/{req_id}/attachments")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) == 1
    assert list_data[0]["filename"] == "test.txt"

    # 3. 下载附件
    download_resp = await client.get(
        f"/api/requirements/{req_id}/attachments/{att_id}/download"
    )
    assert download_resp.status_code == 200
    assert download_resp.content == b"hello world"
    assert download_resp.headers["content-type"].startswith("text/plain")

    # 4. 删除附件
    delete_resp = await client.delete(
        f"/api/requirements/{req_id}/attachments/{att_id}"
    )
    assert delete_resp.status_code == 200

    # 5. 确认已删除
    list_resp2 = await client.get(f"/api/requirements/{req_id}/attachments")
    assert list_resp2.json() == []
