import hashlib
import hmac
import json
import asyncio
import aiohttp
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Webhook, WebhookDelivery
from app.schemas.schemas import WebhookCreate, WebhookUpdate, WebhookResponse, WebhookDeliveryResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ── 事件分发器（全局单例） ──────────────────────────────────────────────────

class WebhookDispatcher:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def sign(self, secret: str, payload: str) -> str:
        return "sha256=" + hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    async def dispatch(self, event: str, data: dict, db: AsyncSession):
        """向所有订阅该事件的 webhook 投递"""
        result = await db.execute(
            select(Webhook).where(Webhook.enabled == True)
        )
        webhooks = result.scalars().all()
        for wh in webhooks:
            events = json.loads(wh.events or "[]")
            if events and event not in events and "*" not in events:
                continue
            # 异步发送，不阻塞
            asyncio.create_task(self._deliver(wh.id, event, data))


    async def _deliver(self, webhook_id: str, event: str, data: dict):
        from app.core.database import async_session
        async with async_session() as session:
            wh = (await session.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
            if not wh:
                return

            payload_str = json.dumps({
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }, default=str)

            headers = {"Content-Type": "application/json", "X-CodeSeer-Event": event}
            if wh.secret:
                headers["X-CodeSeer-Signature"] = self.sign(wh.secret, payload_str)

            try:
                s = await self.get_session()
                timeout = aiohttp.ClientTimeout(total=wh.timeout or 10)
                async with s.post(wh.url, data=payload_str, headers=headers, timeout=timeout) as resp:
                    body = await resp.text()
                    delivery = WebhookDelivery(
                        webhook_id=webhook_id,
                        event=event,
                        payload=payload_str[:2000],
                        response_status=resp.status,
                        response_body=body[:1000],
                        success=200 <= resp.status < 300,
                        attempt=1,
                    )
                    session.add(delivery)
                    await session.commit()
            except Exception as e:
                delivery = WebhookDelivery(
                    webhook_id=webhook_id,
                    event=event,
                    payload=payload_str[:2000],
                    success=False,
                    error=str(e)[:500],
                    attempt=1,
                )
                session.add(delivery)
                await session.commit()


dispatcher = WebhookDispatcher()


# ── CRUD 端点 ──────────────────────────────────────────────────────────────

@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).order_by(Webhook.created_at.desc()))
    items = result.scalars().all()
    return [{
        "id": w.id, "name": w.name, "url": w.url, "secret": w.secret,
        "events": w.events, "enabled": w.enabled, "max_retries": w.max_retries,
        "retry_interval": w.retry_interval, "timeout": w.timeout,
        "created_at": w.created_at, "updated_at": w.updated_at,
    } for w in items]


@router.post("", response_model=WebhookResponse)
async def create_webhook(wh: WebhookCreate, db: AsyncSession = Depends(get_db)):
    data = wh.model_dump()
    if data.get("events") and isinstance(data["events"], list):
        data["events"] = json.dumps(data["events"])
    elif data.get("events") and isinstance(data["events"], str):
        pass  # already string
    db_wh = Webhook(**data)
    db.add(db_wh)
    await db.commit()
    await db.refresh(db_wh)
    return {
        "id": db_wh.id, "name": db_wh.name, "url": db_wh.url, "secret": db_wh.secret,
        "events": db_wh.events, "enabled": db_wh.enabled, "max_retries": db_wh.max_retries,
        "retry_interval": db_wh.retry_interval, "timeout": db_wh.timeout,
        "created_at": db_wh.created_at, "updated_at": db_wh.updated_at,
    }


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: str, db: AsyncSession = Depends(get_db)):
    w = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {
        "id": w.id, "name": w.name, "url": w.url, "secret": w.secret,
        "events": w.events, "enabled": w.enabled, "max_retries": w.max_retries,
        "retry_interval": w.retry_interval, "timeout": w.timeout,
        "created_at": w.created_at, "updated_at": w.updated_at,
    }


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: str, update: WebhookUpdate, db: AsyncSession = Depends(get_db)):
    w = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Webhook not found")
    body = update.model_dump(exclude_unset=True)
    if "events" in body and isinstance(body["events"], list):
        body["events"] = json.dumps(body["events"])
    for k, v in body.items():
        setattr(w, k, v)
    await db.commit()
    await db.refresh(w)
    return {
        "id": w.id, "name": w.name, "url": w.url, "secret": w.secret,
        "events": w.events, "enabled": w.enabled, "max_retries": w.max_retries,
        "retry_interval": w.retry_interval, "timeout": w.timeout,
        "created_at": w.created_at, "updated_at": w.updated_at,
    }


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str, db: AsyncSession = Depends(get_db)):
    w = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(w)
    await db.commit()
    return {"message": "Webhook deleted"}


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: str, db: AsyncSession = Depends(get_db)):
    """发送测试事件"""
    await dispatcher.dispatch("webhook.test", {"message": "This is a test event"}, db)
    return {"message": "Test event queued"}


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def list_deliveries(webhook_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
    )
    items = result.scalars().all()
    return [{
        "id": d.id, "webhook_id": d.webhook_id, "event": d.event,
        "response_status": d.response_status, "success": d.success,
        "attempt": d.attempt, "error": d.error, "created_at": d.created_at,
    } for d in items]
