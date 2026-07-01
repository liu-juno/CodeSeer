from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import Project, Iteration, Requirement, ProjectMember, User
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, PaginatedResponse, ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 全局管理员可见全部项目，普通用户只能看到自己参与的项目
    from app.models.models import UserRole
    if current_user.role == UserRole.ADMIN:
        count_q = select(func.count()).select_from(Project)
        data_q = select(Project).order_by(Project.created_at.desc())
    else:
        count_q = (
            select(func.count()).select_from(Project)
            .join(ProjectMember, and_(
                ProjectMember.project_id == Project.id,
                ProjectMember.user_id == current_user.id,
                ProjectMember.status == "approved",
            ))
        )
        data_q = (
            select(Project)
            .join(ProjectMember, and_(
                ProjectMember.project_id == Project.id,
                ProjectMember.user_id == current_user.id,
                ProjectMember.status == "approved",
            ))
            .order_by(Project.created_at.desc())
        )

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    items = (await db.execute(data_q.offset(offset).limit(page_size))).scalars().all()

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if project.identifier:
        existing = await db.execute(select(Project).where(Project.identifier == project.identifier))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"标识符 '{project.identifier}' 已被使用")
    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.flush()
    creator_member = ProjectMember(
        project_id=str(db_project.id),
        user_id=str(current_user.id),
        role="admin",
        status="approved",
    )
    db.add(creator_member)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get("/mine", response_model=List[ProjectResponse])
async def get_my_projects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户参与的所有项目，附带用户在每个项目中的角色"""
    result = await db.execute(
        select(Project, ProjectMember.role)
        .join(ProjectMember, and_(
            ProjectMember.project_id == Project.id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.status == "approved",
        ))
    )
    rows = result.all()
    out = []
    for project, role in rows:
        data = ProjectResponse.model_validate(project)
        data.my_role = role
        out.append(data)
    return out


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
    if "identifier" in update_data and update_data["identifier"]:
        existing = await db.execute(
            select(Project).where(Project.identifier == update_data["identifier"], Project.id != str(project_id))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"标识符 '{update_data['identifier']}' 已被使用")
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
    """列出指派给某用户的、状态为 assigned/in_progress 的需求所在的项目。"""
    req_result = await db.execute(
        select(Requirement.project_id)
        .where(
            Requirement.assignee_id == str(assignee_id),
            Requirement.status.in_(["assigned", "in_progress"]),
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


async def check_project_admin(project_id: str, user_id: str, db: AsyncSession) -> bool:
    """检查用户是否是项目管理员或创建人"""
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project and project.owner_id == user_id:
        return True
    member_result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role == "admin",
                ProjectMember.status == "approved"
            )
        )
    )
    return member_result.scalar_one_or_none() is not None

async def check_project_member(project_id: str, user_id: str, db: AsyncSession) -> bool:
    """检查用户是否是项目成员"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.status == "approved"
            )
        )
    )
    return result.scalar_one_or_none() is not None


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
async def list_project_members(project_id: str, db: AsyncSession = Depends(get_db)):
    """列出项目所有成员"""
    result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    members = result.scalars().all()
    response = []
    for m in members:
        user_result = await db.execute(select(User).where(User.id == m.user_id))
        user = user_result.scalar_one_or_none()
        response.append(ProjectMemberResponse(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            role=m.role,
            status=m.status,
            invited_by=m.invited_by,
            created_at=m.created_at,
            updated_at=m.updated_at,
            user_name=user.name if user else None,
            user_email=user.email if user else None
        ))
    return response

@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(project_id: str, member: ProjectMemberCreate, db: AsyncSession = Depends(get_db)):
    """管理员添加项目成员（直接成为 approved）"""
    user_result = await db.execute(select(User).where(User.id == member.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == member.user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该用户已是项目成员")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=member.user_id,
        role=member.role,
        status="approved",
        invited_by=member.invited_by
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return ProjectMemberResponse(
        id=new_member.id,
        project_id=new_member.project_id,
        user_id=new_member.user_id,
        role=new_member.role,
        status=new_member.status,
        invited_by=new_member.invited_by,
        created_at=new_member.created_at,
        updated_at=new_member.updated_at,
        user_name=user.name,
        user_email=user.email
    )

@router.delete("/{project_id}/members/{user_id}")
async def remove_project_member(project_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """管理员移除项目成员"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    await db.delete(member)
    await db.commit()
    return {"message": "成员已移除"}

@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_project_member(project_id: str, user_id: str, update: ProjectMemberUpdate, db: AsyncSession = Depends(get_db)):
    """更新项目成员角色或状态"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    if update.role is not None:
        member.role = update.role
    if update.status is not None:
        member.status = update.status
    await db.commit()
    await db.refresh(member)
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        invited_by=member.invited_by,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.post("/{project_id}/apply", response_model=ProjectMemberResponse)
async def apply_to_project(project_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """用户申请加入项目"""
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    existing = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已是项目成员")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=current_user.id,
        role="dev",
        status="pending"
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return ProjectMemberResponse(
        id=new_member.id,
        project_id=new_member.project_id,
        user_id=new_member.user_id,
        role=new_member.role,
        status=new_member.status,
        invited_by=new_member.invited_by,
        created_at=new_member.created_at,
        updated_at=new_member.updated_at,
        user_name=current_user.name,
        user_email=current_user.email
    )

@router.post("/{project_id}/approve/{user_id}", response_model=ProjectMemberResponse)
async def approve_project_member(project_id: str, user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """项目创建人或管理员批准申请"""
    if not await check_project_admin(project_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="需要项目管理员权限")

    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="申请不存在")
    member.status = "approved"
    await db.commit()
    await db.refresh(member)
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        invited_by=member.invited_by,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.post("/{project_id}/reject/{user_id}")
async def reject_project_member(project_id: str, user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """项目创建人或管理员拒绝申请"""
    if not await check_project_admin(project_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="需要项目管理员权限")

    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="申请不存在")
    await db.delete(member)
    await db.commit()
    return {"message": "已拒绝申请"}