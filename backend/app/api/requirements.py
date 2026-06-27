from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.api.projects import check_project_member
from app.models.models import (
    Requirement, RequirementPhase, RequirementHistory, HistoryAction, PhaseStatus, PhaseType,
)
from app.schemas.schemas import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
    RequirementAssign,
    StatusTransition,
    PaginatedResponse,
)

router = APIRouter(prefix="/requirements", tags=["requirements"])

DEFAULT_TRANSITIONS = {
    "draft":           ["assigned"],
    "assigned":        ["in_progress"],
    "in_progress":     ["pending_review"],
    "pending_review":  ["review_approved", "review_rejected"],
    "review_approved": ["completed"],
    "review_rejected": ["in_progress"],
    "completed":       [],
}

TRANSITIONS = DEFAULT_TRANSITIONS


async def load_transitions(db: AsyncSession):
    """从数据库加载状态机配置，如果为空则用默认值"""
    global TRANSITIONS
    from app.models.models import StateMachineConfig
    import json
    result = await db.execute(select(StateMachineConfig))
    items = result.scalars().all()
    if items:
        TRANSITIONS = {c.state: json.loads(c.allowed_transitions or "[]") for c in items}
    return TRANSITIONS


@router.get("/status-config")
async def get_status_config(db: AsyncSession = Depends(get_db)):
    """返回当前生效的状态机配置"""
    transitions = await load_transitions(db)
    return {
        "transitions": transitions,
        "states": list(transitions.keys()),
    }


@router.get("", response_model=PaginatedResponse[RequirementResponse])
async def list_requirements(
    project_id: Optional[UUID] = Query(None),
    iteration_id: Optional[UUID] = Query(None),
    assignee_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if project_id:
        if not await check_project_member(str(project_id), current_user.id, db):
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    query = select(Requirement)
    count_query = select(func.count()).select_from(Requirement)

    if project_id:
        query = query.where(Requirement.project_id == str(project_id))
        count_query = count_query.where(Requirement.project_id == str(project_id))
    if iteration_id:
        query = query.where(Requirement.iteration_id == str(iteration_id))
        count_query = count_query.where(Requirement.iteration_id == str(iteration_id))
    if assignee_id:
        query = query.where(Requirement.assignee_id == str(assignee_id))
        count_query = count_query.where(Requirement.assignee_id == str(assignee_id))
    if status:
        query = query.where(Requirement.status == status)
        count_query = count_query.where(Requirement.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Requirement.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=RequirementResponse)
async def create_requirement(requirement: RequirementCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if requirement.project_id:
        if not await check_project_member(str(requirement.project_id), current_user.id, db):
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    data = requirement.model_dump()
    data['project_id'] = str(data['project_id'])
    data['iteration_id'] = str(data['iteration_id']) if data.get('iteration_id') else None
    if data.get('assignee_id'):
        data['assignee_id'] = str(data['assignee_id'])
    db_requirement = Requirement(**data)
    db.add(db_requirement)
    await db.commit()
    await db.refresh(db_requirement)
    # log history
    h = RequirementHistory(
        requirement_id=db_requirement.id,
        action=HistoryAction.CREATED,
        field_name="title",
        new_value=db_requirement.title,
    )
    db.add(h)
    await db.commit()

    # dispatch webhook
    try:
        from app.api.webhooks import dispatcher
        await dispatcher.dispatch("requirement.created", {
            "requirement_id": db_requirement.id,
            "title": db_requirement.title,
            "priority": db_requirement.priority.value if hasattr(db_requirement.priority, 'value') else db_requirement.priority,
        }, db)
    except Exception:
        pass

    return db_requirement


@router.get("/by-iteration/{iteration_id}", response_model=List[RequirementResponse])
async def list_requirements_by_iteration(iteration_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Requirement)
        .where(Requirement.iteration_id == str(iteration_id))
        .order_by(Requirement.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Requirement).where(Requirement.id == str(requirement_id)))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if requirement.project_id:
        if not await check_project_member(requirement.project_id, current_user.id, db):
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    return requirement


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: UUID, requirement: RequirementUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Requirement).where(Requirement.id == str(requirement_id)))
    db_requirement = result.scalar_one_or_none()
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if db_requirement.project_id:
        if not await check_project_member(db_requirement.project_id, current_user.id, db):
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    for key, value in requirement.model_dump(exclude_unset=True).items():
        setattr(db_requirement, key, value)
    await db.commit()
    await db.refresh(db_requirement)
    return db_requirement


@router.delete("/{requirement_id}")
async def delete_requirement(requirement_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Requirement).where(Requirement.id == str(requirement_id)))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if requirement.project_id:
        if not await check_project_member(requirement.project_id, current_user.id, db):
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    await db.delete(requirement)
    await db.commit()
    return {"message": "Requirement deleted successfully"}


@router.post("/{requirement_id}/assign", response_model=RequirementResponse)
async def assign_requirement(requirement_id: UUID, assignment: RequirementAssign, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Requirement).where(Requirement.id == str(requirement_id)))
    db_requirement = result.scalar_one_or_none()
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    old_assignee = db_requirement.assignee_id
    db_requirement.assignee_id = assignment.assignee_id
    db_requirement.status = "assigned"
    history = RequirementHistory(
        requirement_id=str(requirement_id),
        action=HistoryAction.ASSIGNED,
        field_name="assignee_id",
        old_value=old_assignee,
        new_value=assignment.assignee_id,
        comment=assignment.comment,
    )
    db.add(history)
    await db.commit()
    await db.refresh(db_requirement)
    return db_requirement


@router.post("/{requirement_id}/transition", response_model=RequirementResponse)
async def transition_requirement(
    requirement_id: UUID, transition: StatusTransition, db: AsyncSession = Depends(get_db)
):
    transitions = await load_transitions(db)
    result = await db.execute(select(Requirement).where(Requirement.id == str(requirement_id)))
    db_requirement = result.scalar_one_or_none()
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    current = db_requirement.status.value if hasattr(db_requirement.status, 'value') else db_requirement.status
    allowed = transitions.get(current, [])
    if transition.action not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{transition.action}'. Allowed: {allowed}"
        )

    old_status = current
    db_requirement.status = transition.action
    history = RequirementHistory(
        requirement_id=str(requirement_id),
        action=HistoryAction.STATUS_CHANGED,
        field_name="status",
        old_value=old_status,
        new_value=transition.action,
        actor=transition.actor if hasattr(transition, 'actor') else None,
        comment=transition.comment,
    )
    db.add(history)
    await db.commit()
    await db.refresh(db_requirement)

    # dispatch webhook
    try:
        from app.api.webhooks import dispatcher
        await dispatcher.dispatch("requirement.status_changed", {
            "requirement_id": str(requirement_id),
            "title": db_requirement.title,
            "from": old_status,
            "to": transition.action,
        }, db)
    except Exception:
        pass

    return db_requirement


# ── 阶段 (Phases) ────────────────────────────────────────────────────────────

class PhaseUpdate(BaseModel):
    status: str  # pending | in_progress | completed
    notes: Optional[str] = None


class PhaseInit(BaseModel):
    actor: Optional[str] = None


_PHASE_ORDER = ["clarification", "planning", "execution", "testing", "review"]


@router.get("/{requirement_id}/phases")
async def list_phases(requirement_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取需求的 5 个开发阶段；如不存在则按需初始化。"""
    req = (await db.execute(select(Requirement).where(Requirement.id == str(requirement_id)))).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    existing = (await db.execute(
        select(RequirementPhase)
        .where(RequirementPhase.requirement_id == str(requirement_id))
    )).scalars().all()

    if not existing:
        for p in PhaseType:
            db.add(RequirementPhase(
                requirement_id=str(requirement_id),
                phase=p,
                status=PhaseStatus.PENDING,
            ))
        await db.commit()
        existing = (await db.execute(
            select(RequirementPhase)
            .where(RequirementPhase.requirement_id == str(requirement_id))
        )).scalars().all()

    def _phase_key(p):
        v = p.phase.value if hasattr(p.phase, 'value') else p.phase
        try:
            return _PHASE_ORDER.index(v)
        except ValueError:
            return 99

    return [{
        "id": p.id,
        "phase": p.phase.value if hasattr(p.phase, 'value') else p.phase,
        "status": p.status.value if hasattr(p.status, 'value') else p.status,
        "notes": p.notes,
        "started_at": p.started_at,
        "completed_at": p.completed_at,
    } for p in sorted(existing, key=_phase_key)]


@router.put("/{requirement_id}/phases/{phase_id}")
async def update_phase(requirement_id: UUID, phase_id: UUID, body: PhaseUpdate, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(
        select(RequirementPhase)
        .where(RequirementPhase.id == str(phase_id), RequirementPhase.requirement_id == str(requirement_id))
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Phase not found")

    old_status = p.status.value if hasattr(p.status, 'value') else p.status
    p.status = body.status
    if body.status == "in_progress" and not p.started_at:
        p.started_at = datetime.utcnow()
    if body.status == "completed":
        if not p.started_at:
            p.started_at = datetime.utcnow()
        p.completed_at = datetime.utcnow()
    if body.notes is not None:
        p.notes = body.notes

    history = RequirementHistory(
        requirement_id=str(requirement_id),
        action=HistoryAction.UPDATED,
        field_name=f"phase.{p.phase.value if hasattr(p.phase, 'value') else p.phase}",
        old_value=old_status,
        new_value=body.status,
        comment=body.notes,
    )
    db.add(history)
    await db.commit()
    return {
        "id": p.id,
        "phase": p.phase.value if hasattr(p.phase, 'value') else p.phase,
        "status": body.status,
        "notes": p.notes,
        "started_at": p.started_at,
        "completed_at": p.completed_at,
    }


# ── 活动日志 ────────────────────────────────────────────────────────────────

@router.get("/{requirement_id}/history")
async def list_history(requirement_id: UUID, db: AsyncSession = Depends(get_db)):
    items = (await db.execute(
        select(RequirementHistory)
        .where(RequirementHistory.requirement_id == str(requirement_id))
        .order_by(RequirementHistory.created_at.desc())
    )).scalars().all()
    return [{
        "id": i.id,
        "action": i.action.value if hasattr(i.action, 'value') else i.action,
        "field_name": i.field_name,
        "old_value": i.old_value,
        "new_value": i.new_value,
        "actor": i.actor,
        "comment": i.comment,
        "created_at": i.created_at,
    } for i in items]


@router.post("/{requirement_id}/history", include_in_schema=False)
async def log_history(requirement_id: UUID, action: str, field_name: Optional[str] = None, old_value: Optional[str] = None, new_value: Optional[str] = None, actor: Optional[str] = None, comment: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """内部使用的日志记录端点"""
    h = RequirementHistory(
        requirement_id=str(requirement_id),
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        actor=actor,
        comment=comment,
    )
    db.add(h)
    await db.commit()
    return {"id": h.id}
