from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import json
from datetime import datetime

from app.core.database import get_db
from app.models.models import Task, UnitTestRecord, Requirement
from app.schemas.schemas import (
    TaskCreate, TaskUpdate, TaskResponse,
    UnitTestRecordCreate, UnitTestRecordResponse,
)

router = APIRouter(tags=["tasks"])


@router.get("/requirements/{requirement_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(requirement_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.requirement_id == str(requirement_id)).order_by(Task.order)
    )
    return result.scalars().all()


@router.post("/requirements/{requirement_id}/tasks", response_model=TaskResponse)
async def create_task(requirement_id: UUID, task: TaskCreate, db: AsyncSession = Depends(get_db)):
    db_task = Task(requirement_id=str(requirement_id), **task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.put("/requirements/{requirement_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(requirement_id: UUID, task_id: UUID, task: TaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == str(task_id), Task.requirement_id == str(requirement_id)))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = task.model_dump(exclude_unset=True)
    if update_data.get('status') == 'completed' and not db_task.completed_at:
        update_data['completed_at'] = datetime.utcnow()
    for key, value in update_data.items():
        setattr(db_task, key, value)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.delete("/requirements/{requirement_id}/tasks/{task_id}")
async def delete_task(requirement_id: UUID, task_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == str(task_id)))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(db_task)
    await db.commit()
    return {"message": "Task deleted"}


@router.get("/requirements/{requirement_id}/test-records", response_model=List[UnitTestRecordResponse])
async def list_test_records(requirement_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UnitTestRecord)
        .where(UnitTestRecord.requirement_id == str(requirement_id))
        .order_by(UnitTestRecord.executed_at.desc())
    )
    return result.scalars().all()


@router.post("/requirements/{requirement_id}/test-records", response_model=UnitTestRecordResponse)
async def create_test_record(requirement_id: UUID, record: UnitTestRecordCreate, db: AsyncSession = Depends(get_db)):
    data = record.model_dump()
    if data.get('task_id'):
        data['task_id'] = str(data['task_id'])
    if not data.get('executed_at'):
        data['executed_at'] = datetime.utcnow()
    db_record = UnitTestRecord(requirement_id=str(requirement_id), **data)
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)
    return db_record
