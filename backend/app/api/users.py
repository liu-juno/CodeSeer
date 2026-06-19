from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.auth import hash_password
from app.models.models import User, UserRole

router = APIRouter(prefix="/users", tags=["users"])


# ── 角色与权限配置 ──────────────────────────────────────────────────────────

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "product_manager": [
        "requirements:create", "requirements:edit_own", "requirements:delete_own",
        "requirements:assign", "modules:view", "documents:view", "iterations:view",
    ],
    "project_manager": [
        "requirements:view", "requirements:edit", "requirements:assign",
        "requirements:view_all", "modules:manage", "users:manage",
        "iterations:manage", "webhooks:manage", "documents:view",
    ],
    "developer": [
        "requirements:view_assigned", "requirements:claim",
        "requirements:update_status", "documents:submit", "modules:view",
        "skills:view", "iterations:view",
    ],
    "viewer": ["requirements:view_public", "modules:view", "iterations:view"],
}


class UserCreate(BaseModel):
    email: str
    name: str
    role: str = "developer"
    password: Optional[str] = None
    avatar_color: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    avatar_color: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar_color: Optional[str] = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at))
    return [{
        "id": u.id, "email": u.email, "name": u.name,
        "role": u.role.value if hasattr(u.role, 'value') else u.role,
        "avatar_color": u.avatar_color, "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else "",
    } for u in result.scalars().all()]


@router.post("", response_model=UserOut)
async def create_user(u: UserCreate, db: AsyncSession = Depends(get_db)):
    # check duplicate
    existing = (await db.execute(select(User).where(User.email == u.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    db_user = User(
        email=u.email,
        name=u.name,
        role=UserRole(u.role),
        password_hash=hash_password(u.password) if u.password else None,
        avatar_color=u.avatar_color or "#6366f1",
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {
        "id": db_user.id, "email": db_user.email, "name": db_user.name,
        "role": db_user.role.value if hasattr(db_user.role, 'value') else db_user.role,
        "avatar_color": db_user.avatar_color, "is_active": db_user.is_active,
        "created_at": db_user.created_at.isoformat() if db_user.created_at else "",
    }


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, u: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = u.model_dump(exclude_unset=True)
    if 'password' in update_data:
        raw = update_data.pop('password')
        update_data['password_hash'] = hash_password(raw) if raw else None
    for k, v in update_data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return {
        "id": user.id, "email": user.email, "name": user.name,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "avatar_color": user.avatar_color, "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


@router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}


# ── 角色权限查询 ──────────────────────────────────────────────────────────

@router.get("/roles/permissions")
async def list_role_permissions():
    """返回所有角色及其权限（用于前端渲染和权限校验）"""
    return ROLE_PERMISSIONS
