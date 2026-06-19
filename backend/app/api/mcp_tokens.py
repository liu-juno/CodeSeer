import secrets
import string
import hashlib
import hmac as hmac_mod
from datetime import datetime, timedelta, timezone
from typing import Optional, List

UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, AccessToken

router = APIRouter(prefix="/mcp/tokens", tags=["mcp-tokens"])

TOKEN_PREFIX_LEN = 12


def generate_token() -> tuple[str, str, str]:
    """生成 Token，返回 (token, token_hash, prefix)"""
    random_part = "".join(
        secrets.choice(string.ascii_lowercase + string.digits)
        for _ in range(settings.ACCESS_TOKEN_LENGTH)
    )
    token = "codeseer_" + random_part
    prefix = token[:TOKEN_PREFIX_LEN]
    token_hash = hmac_mod.new(settings.ACCESS_TOKEN_SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    return token, token_hash, prefix


async def verify_token(token: str, db: AsyncSession) -> Optional[User]:
    """验证 Token，返回用户或 None"""
    token_hash = hmac_mod.new(settings.ACCESS_TOKEN_SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    result = await db.execute(
        select(AccessToken, User)
        .join(User, AccessToken.user_id == User.id)
        .where(
            AccessToken.token_hash == token_hash,
            AccessToken.is_active == True,
        )
    )
    row = result.first()
    if not row:
        return None
    access_token, user = row
    if access_token.expires_at and access_token.expires_at < _now():
        return None
    access_token.last_used_at = _now()
    await db.commit()
    return user


# ── Schemas ───────────────────────────────────────────────────────────────────

class TokenCreateRequest(BaseModel):
    name: str
    user_id: str
    days: Optional[int] = None


class TokenCreateResponse(BaseModel):
    token_id: str
    token: str
    prefix: str
    name: str
    expires_at: Optional[datetime] = None
    created_at: datetime


class TokenListItem(BaseModel):
    id: str
    name: str
    prefix: str
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class TokenListResponse(BaseModel):
    tokens: List[TokenListItem]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=201, response_model=TokenCreateResponse)
async def create_token(
    body: TokenCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """申请新 Token（明文仅返回一次）"""
    user_result = await db.execute(select(User).where(User.id == body.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token, token_hash, prefix = generate_token()
    days = body.days if body.days is not None else settings.ACCESS_TOKEN_EXPIRY_DAYS
    expires_at = _now() + timedelta(days=days) if days is not None else None

    at = AccessToken(
        user_id=body.user_id,
        token_hash=token_hash,
        token_prefix=prefix,
        name=body.name,
        expires_at=expires_at,
    )
    db.add(at)
    await db.commit()
    await db.refresh(at)

    return TokenCreateResponse(
        token_id=str(at.id),
        token=token,
        prefix=prefix,
        name=at.name,
        expires_at=at.expires_at,
        created_at=at.created_at,
    )


@router.get("", response_model=TokenListResponse)
async def list_tokens(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """查询指定用户的有效 Token 列表（不含明文）"""
    result = await db.execute(
        select(AccessToken)
        .where(AccessToken.user_id == user_id, AccessToken.is_active == True)
        .order_by(AccessToken.created_at.desc())
    )
    tokens = result.scalars().all()
    return TokenListResponse(
        tokens=[
            TokenListItem(
                id=str(t.id),
                name=t.name,
                prefix=t.token_prefix,
                expires_at=t.expires_at,
                last_used_at=t.last_used_at,
                created_at=t.created_at,
            )
            for t in tokens
        ]
    )


@router.delete("/{token_id}")
async def revoke_token(
    token_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """撤销 Token（必须提供 user_id 校验所有权）"""
    result = await db.execute(
        select(AccessToken).where(
            AccessToken.id == token_id,
            AccessToken.user_id == user_id,
        )
    )
    at = result.scalar_one_or_none()
    if not at:
        raise HTTPException(status_code=404, detail="Token not found")
    at.is_active = False
    await db.commit()
    return {"message": "Token revoked"}
