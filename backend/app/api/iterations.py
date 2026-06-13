from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.models import Iteration, Requirement
from app.schemas.schemas import IterationCreate, IterationUpdate, IterationResponse
from app.api.documents import archive_requirement_drafts

router = APIRouter(prefix="/iterations", tags=["iterations"])


@router.get("", response_model=List[IterationResponse])
async def list_iterations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Iteration).order_by(Iteration.created_at.desc()))
    iterations = result.scalars().all()
    return iterations


@router.post("", response_model=IterationResponse)
async def create_iteration(iteration: IterationCreate, db: AsyncSession = Depends(get_db)):
    data = iteration.model_dump()
    data['project_id'] = str(data['project_id'])
    db_iteration = Iteration(**data)
    db.add(db_iteration)
    await db.commit()
    await db.refresh(db_iteration)
    return db_iteration


@router.get("/by-project/{project_id}", response_model=List[IterationResponse])
async def list_iterations_by_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Iteration)
        .where(Iteration.project_id == project_id)
        .order_by(Iteration.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{iteration_id}", response_model=IterationResponse)
async def get_iteration(iteration_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Iteration).where(Iteration.id == iteration_id))
    iteration = result.scalar_one_or_none()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")
    return iteration


@router.put("/{iteration_id}", response_model=IterationResponse)
async def update_iteration(iteration_id: UUID, iteration: IterationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Iteration).where(Iteration.id == iteration_id))
    db_iteration = result.scalar_one_or_none()
    if not db_iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    update_data = iteration.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_iteration, key, value)

    await db.commit()
    await db.refresh(db_iteration)
    return db_iteration


@router.delete("/{iteration_id}")
async def delete_iteration(iteration_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Iteration).where(Iteration.id == iteration_id))
    iteration = result.scalar_one_or_none()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    await db.delete(iteration)
    await db.commit()
    return {"message": "Iteration deleted successfully"}


@router.post("/{iteration_id}/release")
async def release_iteration(iteration_id: UUID, db: AsyncSession = Depends(get_db)):
    """发布迭代：归档所有该迭代下需求的草稿文档"""
    result = await db.execute(select(Iteration).where(Iteration.id == iteration_id))
    iteration = result.scalar_one_or_none()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    # Get all requirements under this iteration
    reqs = (await db.execute(
        select(Requirement).where(Requirement.iteration_id == str(iteration_id))
    )).scalars().all()
    req_ids = [r.id for r in reqs]

    # Archive all draft documents
    archived_count = await archive_requirement_drafts(req_ids, db)

    # Update iteration status
    iteration.status = "released"
    iteration.actual_release_date = datetime.utcnow()
    await db.commit()
    await db.refresh(iteration)

    # dispatch webhook
    try:
        from app.api.webhooks import dispatcher
        await dispatcher.dispatch("iteration.released", {
            "iteration_id": str(iteration_id),
            "name": iteration.name,
            "archived_documents": archived_count,
        }, db)
    except Exception:
        pass

    return {
        "success": True,
        "iteration_id": str(iteration_id),
        "status": iteration.status,
        "archived_documents": archived_count,
        "requirement_count": len(req_ids),
    }


@router.get("/{iteration_id}/statistics")
async def iteration_statistics(iteration_id: UUID, db: AsyncSession = Depends(get_db)):
    """迭代统计：总需求、按状态分布、完成率"""
    iteration = (await db.execute(select(Iteration).where(Iteration.id == iteration_id))).scalar_one_or_none()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    reqs = (await db.execute(
        select(Requirement).where(Requirement.iteration_id == str(iteration_id))
    )).scalars().all()

    status_counts = {}
    for r in reqs:
        s = r.status.value if hasattr(r.status, 'value') else r.status
        status_counts[s] = status_counts.get(s, 0) + 1

    total = len(reqs)
    completed = status_counts.get('completed', 0)
    return {
        "iteration_id": str(iteration_id),
        "total_requirements": total,
        "completed": completed,
        "in_progress": status_counts.get('in_progress', 0),
        "pending": total - completed - status_counts.get('in_progress', 0),
        "progress_pct": round((completed / total) * 100) if total else 0,
        "status_distribution": status_counts,
    }