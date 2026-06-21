import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Requirement, RequirementAttachment

router = APIRouter(prefix="/requirements", tags=["attachments"])

BASE_DIR = "/tmp/codeforge/attachments"
os.makedirs(BASE_DIR, exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    content_type: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{requirement_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    requirement_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Requirement not found")

    file_id = str(uuid.uuid4())
    safe_filename = file.filename or "unknown"
    req_dir = os.path.join(BASE_DIR, requirement_id)
    os.makedirs(req_dir, exist_ok=True)
    storage_path = os.path.join(req_dir, f"{file_id}_{safe_filename}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 100MB)")

    with open(storage_path, 'wb') as f:
        f.write(content)

    attachment = RequirementAttachment(
        id=file_id,
        requirement_id=requirement_id,
        filename=safe_filename,
        file_size=len(content),
        content_type=file.content_type,
        storage_path=storage_path,
        storage_backend="local",
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.get("/{requirement_id}/attachments", response_model=List[AttachmentResponse])
async def list_attachments(requirement_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequirementAttachment)
        .where(RequirementAttachment.requirement_id == requirement_id)
        .order_by(RequirementAttachment.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{requirement_id}/attachments/{attachment_id}/download")
async def download_attachment(
    requirement_id: str,
    attachment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RequirementAttachment)
        .where(
            RequirementAttachment.id == attachment_id,
            RequirementAttachment.requirement_id == requirement_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.storage_path):
        raise HTTPException(status_code=404, detail="File not found on storage")

    with open(attachment.storage_path, 'rb') as f:
        content = f.read()

    return Response(
        content=content,
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=\"{attachment.filename}\""},
    )


@router.delete("/{requirement_id}/attachments/{attachment_id}")
async def delete_attachment(requirement_id: str, attachment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequirementAttachment)
        .where(
            RequirementAttachment.id == attachment_id,
            RequirementAttachment.requirement_id == requirement_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if os.path.exists(attachment.storage_path):
        os.remove(attachment.storage_path)

    await db.delete(attachment)
    await db.commit()
    return {"message": "Attachment deleted"}
