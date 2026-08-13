"""Endpoints administrativos para validar provedores de notificação."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies.notification_admin import require_notification_admin
from services.notifications.telegram_service import TelegramError, get_telegram_service
from services.notifications.preferences import AlertPreferenceService, PreferenceSnapshot

router = APIRouter(tags=["notifications"], include_in_schema=False)


class TelegramTestRequest(BaseModel):
    message: str = Field(
        default="<b>MarketMind AI</b> — teste administrativo de conexão Telegram.",
        min_length=1,
        max_length=20_000,
    )
    parse_mode: str = Field(default="HTML", pattern="^(HTML|MarkdownV2)$")


class AlertPreferenceRequest(BaseModel):
    assets: list[str] = Field(min_length=1, max_length=50)
    channels: list[str] = Field(min_length=1, max_length=2)
    minimum_severity: str = Field(default="INFO", pattern="^(INFO|WARNING|CRITICAL)$")
    cooldown_seconds: int = Field(default=1800, ge=60, le=86_400)
    paused: bool = False


def _preference_response(preference: PreferenceSnapshot) -> dict[str, object]:
    return {
        "scope_key": preference.scope_key,
        "assets": list(preference.assets),
        "channels": [channel.value for channel in preference.channels],
        "minimum_severity": preference.minimum_severity.value,
        "cooldown_seconds": preference.cooldown_seconds,
        "paused": preference.paused,
    }


@router.post("/notifications/test/telegram", dependencies=[Depends(require_notification_admin)])
async def send_telegram_test(payload: TelegramTestRequest) -> dict[str, str | int]:
    """Testa Telegram com o segredo administrativo exclusivo de notificações."""
    try:
        result = await get_telegram_service().send_telegram_message(
            payload.message,
            parse_mode=payload.parse_mode,  # type: ignore[arg-type]
        )
    except TelegramError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "sent", "message_parts": len(result.message_ids)}


@router.get("/notifications/preferences/{scope_key}", dependencies=[Depends(require_notification_admin)])
async def get_alert_preference(scope_key: str) -> dict[str, object]:
    try:
        preference = await AlertPreferenceService().get_or_create(scope_key)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _preference_response(preference)


@router.put("/notifications/preferences/{scope_key}", dependencies=[Depends(require_notification_admin)])
async def update_alert_preference(
    scope_key: str, payload: AlertPreferenceRequest
) -> dict[str, object]:
    try:
        preference = await AlertPreferenceService().update(scope_key, **payload.model_dump())
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _preference_response(preference)
