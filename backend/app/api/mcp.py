from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.models.models import Task, UnitTestRecord, Requirement
from app.schemas.schemas import (
    MCPSyncTasksPayload, MCPUpdateTaskPayload, MCPSubmitTestPayload,
    TaskResponse, UnitTestRecordResponse,
)

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/sync-tasks")
async def sync_tasks(payload: MCPSyncTasksPayload, db: AsyncSession = Depends(get_db)):
    req = await db.execute(select(Requirement).where(Requirement.id == payload.requirement_id))
    requirement = req.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    existing = await db.execute(select(Task).where(Task.requirement_id == payload.requirement_id))
    for t in existing.scalars().all():
        await db.delete(t)

    for i, task_data in enumerate(payload.tasks):
        t = Task(
            requirement_id=payload.requirement_id,
            order=i,
            **task_data.model_dump(),
        )
        db.add(t)

    await db.commit()
    return {"success": True, "requirement_id": payload.requirement_id, "task_count": len(payload.tasks)}


@router.post("/update-task")
async def update_task(payload: MCPUpdateTaskPayload, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == payload.task_id))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True, exclude={"requirement_id", "task_id"})
    if update_data.get('status') == 'completed' and not db_task.completed_at:
        update_data['completed_at'] = datetime.utcnow()
    for key, value in update_data.items():
        setattr(db_task, key, value)

    await db.commit()
    await db.refresh(db_task)
    return {"success": True, "task": db_task}


@router.post("/submit-test-result")
async def submit_test_result(payload: MCPSubmitTestPayload, db: AsyncSession = Depends(get_db)):
    req = await db.execute(select(Requirement).where(Requirement.id == payload.requirement_id))
    if not req.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Requirement not found")

    data = payload.model_dump(exclude={"requirement_id"})
    if not data.get('executed_at'):
        data['executed_at'] = datetime.utcnow()

    record = UnitTestRecord(requirement_id=payload.requirement_id, **data)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"success": True, "test_record_id": record.id}


@router.get("/requirements")
async def mcp_list_requirements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Requirement).where(Requirement.status.in_(["assigned", "claimed", "in_progress"]))
    )
    return result.scalars().all()


@router.get("/requirements/{requirement_id}")
async def mcp_get_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    tasks_result = await db.execute(select(Task).where(Task.requirement_id == requirement_id).order_by(Task.order))
    tasks = tasks_result.scalars().all()

    return {"requirement": req, "tasks": tasks}
