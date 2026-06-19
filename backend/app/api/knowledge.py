from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.core.database import get_db
from app.models.models import Document

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# 知识库文件存储路径（可配置）
KNOWLEDGE_BASE_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "/tmp/knowledge")


@router.get("/{doc_id}")
async def download_knowledge_file(doc_id: str, db: AsyncSession = Depends(get_db)):
    """根据文档 ID 下载知识库文件"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "archived":
        raise HTTPException(status_code=403, detail="Document is not archived")

    # 假设文件存储在 KNOWLEDGE_BASE_PATH/{doc_id}/ 目录
    file_dir = os.path.join(KNOWLEDGE_BASE_PATH, doc_id)

    if not os.path.exists(file_dir):
        # 如果文件不存在，返回文档内容作为文本
        return {
            "document_id": doc_id,
            "title": doc.title,
            "content": doc.content,
            "format": "text"
        }

    # 查找目录中的文件
    files = os.listdir(file_dir)
    if not files:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(file_dir, files[0])
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=files[0]
    )