from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Defect, DefectComment, DefectLog, DefectStatus
from app.schemas.schemas import (
    DefectCreate, DefectUpdate, DefectResponse,
    DefectCommentCreate, DefectCommentResponse, DefectLogResponse
)
from datetime import datetime

router = APIRouter(prefix="/defects", tags=["defects"])


@router.post("", response_model=DefectResponse, status_code=201)
async def create_defect(data: DefectCreate, db: AsyncSession = Depends(get_db)):
    defect = Defect(**data.model_dump())
    db.add(defect)

    log = DefectLog(
        defect_id=defect.id,
        action="created",
        new_value=f"status={data.severity.value}"
    )
    db.add(log)

    await db.commit()
    await db.refresh(defect)
    return defect


@router.get("", response_model=List[DefectResponse])
async def list_defects(
    project_id: Optional[str] = None,
    status: Optional[DefectStatus] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    creator_id: Optional[str] = None,
    module_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Defect).order_by(desc(Defect.created_at))

    if project_id:
        query = query.where(Defect.project_id == project_id)
    if status:
        query = query.where(Defect.status == status)
    if severity:
        query = query.where(Defect.severity == severity)
    if priority:
        query = query.where(Defect.priority == priority)
    if assignee:
        query = query.where(Defect.assignees.contains(assignee))
    if creator_id:
        query = query.where(Defect.creator_id == creator_id)
    if module_id:
        query = query.where(Defect.module_id == module_id)
    if requirement_id:
        query = query.where(Defect.requirement_id == requirement_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{defect_id}", response_model=DefectResponse)
async def get_defect(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@router.patch("/{defect_id}", response_model=DefectResponse)
async def update_defect(defect_id: str, data: DefectUpdate, db: AsyncSession = Depends(get_db), user_id: Optional[str] = None):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    old_status = defect.status.value if hasattr(defect.status, 'value') else str(defect.status)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(defect, field, value)

    new_status = defect.status.value if hasattr(defect.status, 'value') else str(defect.status)

    if old_status != new_status:
        log = DefectLog(
            defect_id=defect_id,
            user_id=user_id,
            action="status_changed",
            old_value=old_status,
            new_value=new_status
        )
        db.add(log)

    await db.commit()
    await db.refresh(defect)
    return defect


@router.delete("/{defect_id}", status_code=204)
async def delete_defect(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    await db.delete(defect)
    await db.commit()


@router.post("/{defect_id}/comments", response_model=DefectCommentResponse, status_code=201)
async def create_comment(defect_id: str, data: DefectCommentCreate, db: AsyncSession = Depends(get_db), user_id: Optional[str] = None):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Defect not found")

    comment = DefectComment(defect_id=defect_id, user_id=user_id, content=data.content)
    db.add(comment)

    log = DefectLog(defect_id=defect_id, user_id=user_id, action="commented", new_value=data.content[:100])
    db.add(log)

    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/{defect_id}/comments", response_model=List[DefectCommentResponse])
async def list_comments(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DefectComment).where(DefectComment.defect_id == defect_id).order_by(DefectComment.created_at)
    )
    return result.scalars().all()


@router.get("/{defect_id}/logs", response_model=List[DefectLogResponse])
async def list_logs(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DefectLog).where(DefectLog.defect_id == defect_id).order_by(DefectLog.created_at)
    )
    return result.scalars().all()