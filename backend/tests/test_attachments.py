import pytest
from app.models.models import RequirementAttachment


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
