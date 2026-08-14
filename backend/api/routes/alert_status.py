"""Leituras públicas, sem segredos, para o radar operacional de alertas."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from database import AsyncSessionLocal
from models.alert import AlertEvent
from services.alerts.worker_status import WorkerStatusService
from services.data_providers import provider_registry
from services.model_registry import model_registry
from services.notifications.preferences import AlertPreferenceService
from services.notifications.telegram_service import get_telegram_service

router = APIRouter(tags=["alerts"])


@router.get("/alerts/status")
async def get_alert_status() -> dict[str, object]:
    heartbeat = await WorkerStatusService().snapshot()
    model = model_registry.load("BTCUSDT")
    return {
        "telegram_configured": get_telegram_service().is_configured(),
        "worker": {
            "status": heartbeat.status if heartbeat else "offline",
            "last_run": heartbeat.last_run.isoformat() if heartbeat and heartbeat.last_run else None,
            "last_success": heartbeat.last_success.isoformat() if heartbeat and heartbeat.last_success else None,
            "processed_events": heartbeat.processed_events if heartbeat else 0,
            "sent_alerts": heartbeat.sent_alerts if heartbeat else 0,
            "last_error": heartbeat.last_error if heartbeat else None,
        },
        "model": {
            "asset": "BTCUSDT",
            "available": model is not None,
            "reliable": bool(model and model.metrics.get("reliable", False)),
            "name": model.metadata.get("model_name") if model else None,
        },
        "providers": [status.__dict__ for status in await provider_registry.statuses()],
    }


@router.get("/alerts/recent")
async def get_recent_alerts(
    limit: int = 10,
    asset: str | None = None,
    severity: str | None = None,
    channel: str | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict[str, object]]:
    if AsyncSessionLocal is None:
        return []
    safe_limit = min(max(limit, 1), 50)
    statement = select(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(safe_limit)
    if asset:
        statement = statement.where(AlertEvent.asset == asset.strip().upper())
    if severity:
        statement = statement.where(AlertEvent.severity == severity.strip().upper())
    if channel:
        statement = statement.where(AlertEvent.channel == channel.strip().lower())
    if status:
        statement = statement.where(AlertEvent.status == status.strip().lower())
    if date_from:
        statement = statement.where(AlertEvent.created_at >= date_from)
    if date_to:
        statement = statement.where(AlertEvent.created_at <= date_to)
    async with AsyncSessionLocal() as session:
        result = await session.scalars(statement)
        return [
            {
                "id": event.id,
                "asset": event.asset,
                "event_type": event.event_type,
                "severity": event.severity,
                "title": event.title,
                "message": event.message,
                "status": event.status,
                "channel": event.channel,
                "created_at": event.created_at.isoformat(),
            }
            for event in result.all()
        ]


@router.get("/alerts/preferences")
async def get_global_alert_preferences() -> dict[str, object]:
    """Retorna somente a configuração global não sensível consumida pelo dashboard."""
    preference = await AlertPreferenceService().get("owner")
    return {
        "scope_key": preference.scope_key,
        "assets": preference.assets,
        "channels": preference.channels,
        "minimum_severity": preference.minimum_severity,
        "cooldown_seconds": preference.cooldown_seconds,
        "paused": preference.paused,
        "managed_via": "ADMIN_NOTIFICATION_SECRET",
    }
