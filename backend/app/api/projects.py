from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.models import Project, Iteration, Requirement
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return projects


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, project: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    db_project = result.scalar_one_or_none()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)

    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.delete("/{project_id}")
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted successfully"}


@router.get("/by-assignee/{assignee_id}", response_model=List[ProjectResponse])
async def list_projects_by_assignee(assignee_id: UUID, db: AsyncSession = Depends(get_db)):
    """列出指派给某用户的、状态为 assigned/claimed/in_progress 的需求所在的项目。"""
    req_result = await db.execute(
        select(Requirement.project_id)
        .where(
            Requirement.assignee_id == str(assignee_id),
            Requirement.status.in_(["assigned", "claimed", "in_progress"]),
        )
        .distinct()
    )
    project_ids = [row[0] for row in req_result.all()]
    if not project_ids:
        return []
    result = await db.execute(
        select(Project).where(Project.id.in_(project_ids)).order_by(Project.name)
    )
    return result.scalars().all()


@router.get("/{project_id}/statistics")
async def project_statistics(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    iterations = (await db.execute(
        select(Iteration).where(Iteration.project_id == str(project_id))
    )).scalars().all()

    reqs = (await db.execute(
        select(Requirement).where(Requirement.project_id == str(project_id))
    )).scalars().all()

    status_counts = {}
    for r in reqs:
        s = r.status.value if hasattr(r.status, 'value') else r.status
        status_counts[s] = status_counts.get(s, 0) + 1

    total = len(reqs)
    completed = status_counts.get('completed', 0)
    return {
        "project_id": str(project_id),
        "iteration_count": len(iterations),
        "total_requirements": total,
        "completed": completed,
        "in_progress": status_counts.get('in_progress', 0),
        "progress_pct": round((completed / total) * 100) if total else 0,
        "status_distribution": status_counts,
    }