import json
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
