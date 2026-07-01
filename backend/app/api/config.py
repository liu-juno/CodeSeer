import json
import os
import re
import shutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import (
    StateMachineConfig, CustomField, CustomFieldType,
)
from app.schemas.schemas import (
    StateMachineConfigCreate, StateMachineConfigUpdate, StateMachineConfigResponse,
    CustomFieldCreate, CustomFieldUpdate, CustomFieldResponse,
)

router = APIRouter(prefix="/config", tags=["config"])


# ── State Machine ──────────────────────────────────────────────────────────

DEFAULT_TRANSITIONS = {
    "draft": ["assigned"],
    "assigned": ["in_progress"],
    "in_progress": ["pending_review"],
    "pending_review": ["review_approved", "review_rejected"],
    "review_approved": ["completed"],
    "review_rejected": ["in_progress"],
    "completed": [],
}


STATE_NAMES = {
    "draft": "草稿", "assigned": "已指派", "in_progress": "开发中",
    "pending_review": "待评审", "review_approved": "评审通过",
    "review_rejected": "评审驳回", "completed": "已完成",
}


@router.get("/state-machine")
async def get_state_machine(db: AsyncSession = Depends(get_db)):
    """返回完整状态机配置（如果数据库为空则用默认值初始化）"""
    result = await db.execute(select(StateMachineConfig).order_by(StateMachineConfig.order))
    items = result.scalars().all()

    if not items:
        for i, (state, transitions) in enumerate(DEFAULT_TRANSITIONS.items()):
            cfg = StateMachineConfig(
                state=state,
                name=STATE_NAMES.get(state, state),
                allowed_transitions=json.dumps(transitions),
                is_initial=(state == "draft"),
                is_terminal=(state == "completed"),
                order=i,
            )
            db.add(cfg)
        await db.commit()
        items = (await db.execute(select(StateMachineConfig).order_by(StateMachineConfig.order))).scalars().all()

    return [{
        "id": c.id, "state": c.state, "name": c.name, "description": c.description,
        "allowed_transitions": json.loads(c.allowed_transitions or "[]"),
        "is_initial": c.is_initial, "is_terminal": c.is_terminal,
        "order": c.order,
    } for c in items]


@router.put("/state-machine")
async def update_state_machine(states: List[dict], db: AsyncSession = Depends(get_db)):
    """整体更新状态机配置"""
    # 简单策略：清空再插入
    existing = (await db.execute(select(StateMachineConfig))).scalars().all()
    for e in existing:
        await db.delete(e)
    await db.commit()

    for i, s in enumerate(states):
        cfg = StateMachineConfig(
            state=s["state"],
            name=s.get("name", s["state"]),
            description=s.get("description"),
            allowed_transitions=json.dumps(s.get("allowed_transitions", [])),
            is_initial=s.get("is_initial", False),
            is_terminal=s.get("is_terminal", False),
            order=s.get("order", i),
        )
        db.add(cfg)
    await db.commit()
    return await get_state_machine(db)


# ── Custom Fields ──────────────────────────────────────────────────────────

@router.get("/custom-fields")
async def list_custom_fields(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomField).order_by(CustomField.order))
    items = result.scalars().all()
    return [{
        "id": f.id, "field_key": f.field_key, "field_name": f.field_name,
        "field_type": f.field_type.value if hasattr(f.field_type, 'value') else f.field_type,
        "required": f.required,
        "options": json.loads(f.options or "[]") if f.options else [],
        "default_value": f.default_value, "order": f.order,
    } for f in items]


@router.post("/custom-fields")
async def create_custom_field(f: CustomFieldCreate, db: AsyncSession = Depends(get_db)):
    # check duplicate
    existing = (await db.execute(select(CustomField).where(CustomField.field_key == f.field_key))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="字段 key 已存在")

    data = f.model_dump()
    if isinstance(data.get("options"), list):
        data["options"] = json.dumps(data["options"])
    field = CustomField(**data)
    db.add(field)
    await db.commit()
    await db.refresh(field)
    return {
        "id": field.id, "field_key": field.field_key, "field_name": field.field_name,
        "field_type": field.field_type.value if hasattr(field.field_type, 'value') else field.field_type,
        "required": field.required, "options": json.loads(field.options or "[]"),
        "default_value": field.default_value, "order": field.order,
    }


@router.put("/custom-fields/{field_id}")
async def update_custom_field(field_id: str, f: CustomFieldUpdate, db: AsyncSession = Depends(get_db)):
    field = (await db.execute(select(CustomField).where(CustomField.id == field_id))).scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")
    body = f.model_dump(exclude_unset=True)
    if "options" in body and isinstance(body["options"], list):
        body["options"] = json.dumps(body["options"])
    for k, v in body.items():
        setattr(field, k, v)
    await db.commit()
    await db.refresh(field)
    return {
        "id": field.id, "field_key": field.field_key, "field_name": field.field_name,
        "field_type": field.field_type.value if hasattr(field.field_type, 'value') else field.field_type,
        "required": field.required, "options": json.loads(field.options or "[]"),
        "default_value": field.default_value, "order": field.order,
    }


@router.delete("/custom-fields/{field_id}")
async def delete_custom_field(field_id: str, db: AsyncSession = Depends(get_db)):
    field = (await db.execute(select(CustomField).where(CustomField.id == field_id))).scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")
    await db.delete(field)
    await db.commit()
    return {"message": "字段已删除"}


# ── .env 配置管理 ──────────────────────────────────────────────────────────────

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
ENV_SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.example")


# 允许通过后台管理的配置项
MANAGED_KEYS = [
    # AI / LLM
    "LLM_PROVIDER", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_MAX_TOKENS", "LLM_TEMPERATURE",
    # Storage
    "STORAGE_TYPE", "FTP_HOST", "FTP_PORT", "FTP_USERNAME", "FTP_PASSWORD", "FTP_REMOTE_BASE_PATH",
    "OSS_ENDPOINT", "OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET", "OSS_BUCKET_NAME",
    # 其他可运行时修改的
    "ACCESS_TOKEN_EXPIRY_DAYS",
]

# 敏感字段，写入时脱敏显示
SENSITIVE_KEYS = {"LLM_API_KEY", "FTP_PASSWORD", "OSS_ACCESS_KEY_SECRET"}


def _read_env() -> dict:
    """读取 .env 文件为 key-value dict"""
    vars_ = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                vars_[k.strip()] = v.strip().strip('"').strip("'")
    return vars_


def _write_env(vars_: dict):
    """写入 .env 文件"""
    lines = [f'{k}="{v}"' if v else f"{k}=" for k, v in vars_.items()]
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


@router.get("/env")
async def get_env_config():
    """获取所有配置项（敏感字段脱敏）"""
    vars_ = _read_env()
    result = {}
    for k in MANAGED_KEYS:
        v = vars_.get(k, "")
        if k in SENSITIVE_KEYS and v and "****" not in v:
            v = v[:6] + "****" + v[-4:] if len(v) > 10 else "****"
        result[k] = v
    return result


class EnvConfigUpdate(BaseModel):
    # 支持部分更新
    LLM_PROVIDER: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    LLM_MAX_TOKENS: Optional[int] = None
    LLM_TEMPERATURE: Optional[float] = None
    STORAGE_TYPE: Optional[str] = None
    FTP_HOST: Optional[str] = None
    FTP_PORT: Optional[int] = None
    FTP_USERNAME: Optional[str] = None
    FTP_PASSWORD: Optional[str] = None
    FTP_REMOTE_BASE_PATH: Optional[str] = None
    OSS_ENDPOINT: Optional[str] = None
    OSS_ACCESS_KEY_ID: Optional[str] = None
    OSS_ACCESS_KEY_SECRET: Optional[str] = None
    OSS_BUCKET_NAME: Optional[str] = None
    ACCESS_TOKEN_EXPIRY_DAYS: Optional[int] = None


@router.put("/env")
async def update_env_config(body: EnvConfigUpdate):
    """更新配置项（写入 .env）"""
    vars_ = _read_env()
    data = body.model_dump(exclude_unset=True)

    for k, v in data.items():
        # 忽略脱敏占位符
        if k in SENSITIVE_KEYS and isinstance(v, str) and "****" in v:
            continue
        vars_[k] = str(v) if v is not None else ""

    _write_env(vars_)

    # 同步到运行时 settings
    from app.core.config import settings
    mapping = {
        "LLM_PROVIDER": "LLM_PROVIDER", "LLM_BASE_URL": "LLM_BASE_URL",
        "LLM_API_KEY": "LLM_API_KEY", "LLM_MODEL": "LLM_MODEL",
        "LLM_MAX_TOKENS": "LLM_MAX_TOKENS", "LLM_TEMPERATURE": "LLM_TEMPERATURE",
        "STORAGE_TYPE": "STORAGE_TYPE", "FTP_HOST": "FTP_HOST", "FTP_PORT": "FTP_PORT",
        "FTP_USERNAME": "FTP_USERNAME", "FTP_PASSWORD": "FTP_PASSWORD",
        "FTP_REMOTE_BASE_PATH": "FTP_REMOTE_BASE_PATH", "OSS_ENDPOINT": "OSS_ENDPOINT",
        "OSS_ACCESS_KEY_ID": "OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET": "OSS_ACCESS_KEY_SECRET",
        "OSS_BUCKET_NAME": "OSS_BUCKET_NAME", "ACCESS_TOKEN_EXPIRY_DAYS": "ACCESS_TOKEN_EXPIRY_DAYS",
    }
    for env_key, setting_key in mapping.items():
        if env_key in data:
            setattr(settings, setting_key, data[env_key])

    return await get_env_config()
