from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.models import Document, DocumentVersion, Module, Skill
from app.schemas.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentVersionResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    status: Optional[str] = Query(None),
    module_id: Optional[str] = Query(None),
    requirement_id: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document)
    if status:
        query = query.where(Document.status == status)
    if module_id:
        query = query.where(Document.module_id == module_id)
    if requirement_id:
        query = query.where(Document.requirement_id == requirement_id)
    if document_type:
        query = query.where(Document.document_type == document_type)
    query = query.order_by(Document.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=DocumentResponse)
async def create_document(doc: DocumentCreate, db: AsyncSession = Depends(get_db)):
    data = doc.model_dump()
    if data.get('module_id'):
        data['module_id'] = str(data['module_id'])
    if data.get('requirement_id'):
        data['requirement_id'] = str(data['requirement_id'])
    db_doc = Document(**data, processing_status="pending")
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    # create initial version
    version = DocumentVersion(
        document_id=db_doc.id,
        version=1,
        content=db_doc.content,
        change_note="初版",
    )
    db.add(version)
    await db.commit()
    return db_doc


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, update: DocumentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    db_doc = result.scalar_one_or_none()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # create a new version on content change
    body = update.model_dump(exclude_unset=True)
    content_changed = "content" in body and body["content"] != db_doc.content
    if content_changed:
        body["version"] = db_doc.version + 1
        new_version = DocumentVersion(
            document_id=db_doc.id,
            version=body["version"],
            content=body.get("content"),
            change_note="内容更新",
        )
        db.add(new_version)

    for k, v in body.items():
        setattr(db_doc, k, v)
    await db.commit()
    await db.refresh(db_doc)
    return db_doc


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


@router.post("/{document_id}/archive", response_model=DocumentResponse)
async def archive_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # auto-extract summary if missing
    if not doc.summary and doc.content:
        content = doc.content
        doc.summary = content[:200] + ("..." if len(content) > 200 else "")
        key_points = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "• ")) or (line and len(line) < 80 and line[0].isdigit() and "." in line[:3]):
                key_points.append(line.lstrip("-*•0123456789. "))
        doc.key_points = "\n".join(key_points[:10])
        doc.processing_status = "completed"

    doc.status = "archived"
    doc.archived_at = datetime.utcnow()

    # deprecate older archived docs of same type+module (version superseding)
    if doc.module_id and doc.document_type:
        old_result = await db.execute(
            select(Document).where(
                Document.id != doc.id,
                Document.module_id == doc.module_id,
                Document.document_type == doc.document_type,
                Document.status == "archived",
            )
        )
        for old_doc in old_result.scalars().all():
            old_doc.status = "deprecated"

    await db.commit()
    await db.refresh(doc)

    # dispatch webhook
    try:
        from app.api.webhooks import dispatcher
        await dispatcher.dispatch("document.archived", {
            "document_id": doc.id,
            "title": doc.title,
            "module_id": doc.module_id,
            "requirement_id": doc.requirement_id,
        }, db)
    except Exception:
        pass

    return doc


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """AI 整理文档：生成 summary + key_points"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = "processing"
    await db.commit()

    # 简单模拟：取内容前 200 字作为摘要，按行提取要点
    content = doc.content or ""
    doc.summary = content[:200] + ("..." if len(content) > 200 else "")
    key_points = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(("- ", "* ", "• ")) or (line and len(line) < 80 and line[0].isdigit() and "." in line[:3]):
            key_points.append(line.lstrip("-*•0123456789. "))
    doc.key_points = "\n".join(key_points[:10])
    doc.processing_status = "completed"
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def list_document_versions(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version.desc())
    )
    return result.scalars().all()


# ── 归档草稿文档到模块（迭代发布时调用） ──────────────────────────────────

async def archive_requirement_drafts(requirement_ids: List[str], db: AsyncSession):
    """将一组需求下的草稿文档转为 archived"""
    if not requirement_ids:
        return 0
    result = await db.execute(
        select(Document).where(
            Document.requirement_id.in_(requirement_ids),
            Document.status == "draft",
        )
    )
    docs = result.scalars().all()
    for d in docs:
        d.status = "archived"
        d.archived_at = datetime.utcnow()
    await db.commit()
    return len(docs)
