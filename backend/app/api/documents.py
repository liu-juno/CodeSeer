from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

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
    data['module_id'] = str(data['module_id']) if data.get('module_id') else None
    data['requirement_id'] = str(data['requirement_id']) if data.get('requirement_id') else None
    # 处理 source_document_ids 列表
    if data.get('source_document_ids'):
        data['source_document_ids'] = json.dumps(data['source_document_ids'])
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
    change_note = body.pop("change_note", None)
    content_changed = "content" in body and body["content"] != db_doc.content
    if content_changed:
        body["version"] = db_doc.version + 1
        new_version = DocumentVersion(
            document_id=db_doc.id,
            version=body["version"],
            content=body.get("content"),
            change_note=change_note or "内容更新",
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


# ── AI 合并文档 ───────────────────────────────────────────────────────────────

class MergeRequest(BaseModel):
    title: str
    source_document_ids: List[str]
    module_id: Optional[str] = None


def _build_merge_prompt(docs: List[Document]) -> str:
    """构造 AI 合并提示词"""
    sections = []
    for i, d in enumerate(docs, 1):
        dt = d.document_type.value if hasattr(d.document_type, "value") else str(d.document_type)
        sections.append(f"## 文档 {i}：{d.title} [{dt}]\n{d.content or '(无内容)'}")
    return "\n\n".join(sections) + """

## 任务
请将以上所有文档内容整合为一份完整的模块设计文档：
1. 去重：相同内容只保留最新的描述
2. 合并：将不同来源的内容有机整合，按逻辑顺序组织
3. 标注：在文档开头列出"本文档整合自：[文档1名称]、[文档2名称]..."
4. 输出格式：完整 Markdown，结构清晰（建议包含概述、详细设计、接口说明等章节）

只输出合并后的完整 Markdown 内容，不要解释过程。"""


async def _call_ai_merge(prompt: str) -> str:
    """调用 AI 生成合并文档"""
    import os as _os

    env_path = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))),
        ".env"
    )
    cfg = {}
    if _os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip().strip('"').strip("'")

    api_key = cfg.get("LLM_API_KEY", "")
    if not api_key or "****" in api_key:
        return "【未配置 AI 服务】请前往「设置 → AI / LLM」配置 API Key 后重试。"

    model = cfg.get("LLM_MODEL", "gpt-4o-mini")
    base_url = cfg.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    provider = cfg.get("LLM_PROVIDER", "openai")
    max_tokens = int(cfg.get("LLM_MAX_TOKENS", "8192"))
    temperature = float(cfg.get("LLM_TEMPERATURE", "0.3"))

    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            if provider == "anthropic":
                headers = {
                    "x-api-key": api_key,
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01",
                }
                body = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                }
                resp = await client.post(
                    f"{base_url}/messages",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
            else:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "content-type": "application/json",
                }
                body = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                }
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        return f"【AI 调用失败】HTTP {e.response.status_code}：{e.response.text[:200]}"
    except Exception as e:
        return f"【AI 调用失败】{str(e)}"


@router.post("/merge", response_model=DocumentResponse)
async def merge_documents(req: MergeRequest, db: AsyncSession = Depends(get_db)):
    """将多份文档合并生成一份新的完整设计文档"""
    # 1. 获取源文档
    result = await db.execute(
        select(Document).where(Document.id.in_(req.source_document_ids))
    )
    source_docs = list(result.scalars().all())
    if len(source_docs) != len(req.source_document_ids):
        found_ids = {str(d.id) for d in source_docs}
        missing = set(req.source_document_ids) - found_ids
        raise HTTPException(status_code=404, detail=f"文档不存在: {missing}")

    # 2. 构造 prompt 调用 AI
    prompt = _build_merge_prompt(source_docs)
    merged_content = await _call_ai_merge(prompt)

    # 3. 创建合并文档
    merged_doc = Document(
        title=req.title,
        document_type="design",
        content=merged_content,
        module_id=req.module_id,
        status="draft",
        processing_status="pending",
        source_document_ids=json.dumps(req.source_document_ids),
    )
    db.add(merged_doc)
    await db.commit()
    await db.refresh(merged_doc)

    # 4. 创建版本记录
    version = DocumentVersion(
        document_id=merged_doc.id,
        version=1,
        content=merged_content,
        change_note=f"由 {len(source_docs)} 份文档合并生成",
    )
    db.add(version)
    await db.commit()
    await db.refresh(merged_doc)
    return merged_doc


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
