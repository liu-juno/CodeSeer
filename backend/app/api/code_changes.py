from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.models import CodeChange, CodeChangeStatus
from app.schemas.schemas import CodeChangeCreate, CodeChangeResponse, CodeChangeListResponse
from app.services.code_change_service import CodeChangeService

router = APIRouter(prefix="/code-changes", tags=["code-changes"])


@router.post("", response_model=CodeChangeResponse)
async def create_code_change(
    data: CodeChangeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Query(None),
):
    """上传变更数据"""
    service = CodeChangeService(db)
    try:
        change = await service.upload(data, created_by=current_user)
        return change
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{change_id}")
async def get_code_change(
    change_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取变更详情（含 diff 内容）"""
    service = CodeChangeService(db)
    result = await service.get_with_diff(change_id)
    if not result:
        raise HTTPException(status_code=404, detail="CodeChange not found")
    return result


@router.get("/by-requirement/{requirement_id}", response_model=CodeChangeListResponse)
async def list_code_changes_by_requirement(
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
):
    """按需求查询变更列表"""
    service = CodeChangeService(db)
    changes = await service.list_by_requirement(requirement_id)
    return {
        "requirement_id": requirement_id,
        "changes": changes,
    }


@router.get("")
async def list_code_changes(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """查询所有变更（可选状态过滤）"""
    from sqlalchemy import select
    query = select(CodeChange)
    if status:
        query = query.where(CodeChange.status == status)
    query = query.order_by(CodeChange.created_at.desc())

    result = await db.execute(query)
    changes = result.scalars().all()

    return {
        "changes": changes,
        "total": len(changes),
    }