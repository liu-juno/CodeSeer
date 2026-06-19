from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import verify_password, create_access_token, get_current_user
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar_color: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")

    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token({"sub": str(user.id), "role": role})
    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=role,
            avatar_color=user.avatar_color,
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=role,
        avatar_color=current_user.avatar_color,
    )
