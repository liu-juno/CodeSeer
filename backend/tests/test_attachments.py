import pytest
import pytest_asyncio
from app.models.models import RequirementAttachment, Project, Iteration, Requirement


def test_requirement_attachment_model_exists():
    assert hasattr(RequirementAttachment, '__tablename__')
    assert RequirementAttachment.__tablename__ == 'requirement_attachments'


def test_requirement_attachment_fields():
    columns = [c.name for c in RequirementAttachment.__table__.columns]
    required_fields = [
        'id', 'requirement_id', 'filename', 'file_size',
        'content_type', 'storage_path', 'storage_backend', 'created_at'
    ]
    for field in required_fields:
        assert field in columns, f"Missing field: {field}"


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
async def test_upload_attachment_to_existing_requirement(client, db, test_requirement):
    """上传附件到已存在的需求应返回201并创建附件记录"""
    resp = await client.post(
        f"/api/requirements/{test_requirement.id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "test.txt"
    assert data["file_size"] == 11


@pytest.mark.asyncio
async def test_list_attachments_returns_array(client, db, test_requirement):
    """列出已存在需求的附件应返回数组"""
    resp = await client.get(f"/api/requirements/{test_requirement.id}/attachments")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_download_attachment_returns_content(client, db, test_requirement):
    """下载已上传的附件应返回二进制内容"""
    # first upload
    upload_resp = await client.post(
        f"/api/requirements/{test_requirement.id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    attachment_id = upload_resp.json()["id"]

    # then download
    resp = await client.get(
        f"/api/requirements/{test_requirement.id}/attachments/{attachment_id}/download"
    )
    assert resp.status_code == 200
    assert resp.content == b"hello world"


@pytest.mark.asyncio
async def test_delete_attachment_removes_file(client, db, test_requirement):
    """删除附件应返回200并物理删除文件"""
    # first upload
    upload_resp = await client.post(
        f"/api/requirements/{test_requirement.id}/attachments",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    attachment_id = upload_resp.json()["id"]

    # then delete
    resp = await client.delete(
        f"/api/requirements/{test_requirement.id}/attachments/{attachment_id}"
    )
    assert resp.status_code == 200
