from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.models.models import Task, UnitTestRecord, Requirement, Project
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
async def mcp_list_requirements(
    assignee_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Requirement).where(
        Requirement.status.in_(["assigned", "claimed", "in_progress"])
    )
    if assignee_id:
        query = query.where(Requirement.assignee_id == str(assignee_id))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/my-context")
async def mcp_my_context(
    assignee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """聚合返回：当前开发者有未完成需求的【项目 → 迭代】树 + 这些需求列表。
    用于 MCP 在进入 Superpowers 头脑风暴前的项目/迭代/需求三级选择。
    """
    from app.models.models import Iteration

    # 1. 找出开发者有活儿干的项目 id（去重）
    proj_ids_q = await db.execute(
        select(Requirement.project_id)
        .where(
            Requirement.assignee_id == str(assignee_id),
            Requirement.status.in_(["assigned", "claimed", "in_progress"]),
        )
        .distinct()
    )
    project_ids = [row[0] for row in proj_ids_q.all()]

    # 2. 加载这些项目
    projects: list = []
    iterations_by_project: dict = {}
    if project_ids:
        proj_result = await db.execute(
            select(Project).where(Project.id.in_(project_ids)).order_by(Project.name)
        )
        projects = [
            {"id": str(p.id), "name": p.name, "status": p.status.value if hasattr(p.status, 'value') else p.status}
            for p in proj_result.scalars().all()
        ]

        # 3. 一次性拉所有相关迭代，Python 端 groupby
        iter_result = await db.execute(
            select(Iteration)
            .where(Iteration.project_id.in_(project_ids))
            .order_by(Iteration.created_at.desc())
        )
        for it in iter_result.scalars().all():
            pid = str(it.project_id)
            iterations_by_project.setdefault(pid, []).append({
                "id": str(it.id),
                "name": it.name,
                "status": it.status.value if hasattr(it.status, 'value') else it.status,
            })

    # 4. 一次性拉所有可开发需求
    reqs_result = await db.execute(
        select(Requirement)
        .where(
            Requirement.assignee_id == str(assignee_id),
            Requirement.status.in_(["assigned", "claimed", "in_progress"]),
        )
        .order_by(Requirement.priority.asc(), Requirement.due_date.asc())
    )
    assignable_requirements = [
        {
            "id": str(r.id),
            "title": r.title,
            "status": r.status.value if hasattr(r.status, 'value') else r.status,
            "priority": r.priority.value if hasattr(r.priority, 'value') else r.priority,
            "project_id": str(r.project_id),
            "iteration_id": str(r.iteration_id) if r.iteration_id else None,
            "due_date": r.due_date.isoformat() if r.due_date else None,
        }
        for r in reqs_result.scalars().all()
    ]

    return {
        "developer_id": str(assignee_id),
        "projects": projects,
        "iterations_by_project": iterations_by_project,
        "assignable_requirements": assignable_requirements,
    }


@router.get("/requirements/{requirement_id}")
async def mcp_get_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    tasks_result = await db.execute(select(Task).where(Task.requirement_id == requirement_id).order_by(Task.order))
    tasks = tasks_result.scalars().all()

    return {"requirement": req, "tasks": tasks}
