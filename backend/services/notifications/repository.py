"""Operações transacionais para deduplicar alertas e registrar entregas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from sqlalchemy import select

from database import AsyncSessionLocal
from models.alert import AlertDelivery, AlertEvent, AlertState
from services.notifications.contracts import Alert, NotificationChannel


@dataclass(frozen=True)
class AlertReservation:
    alert_id: str
    created_at: datetime


class AlertRepository:
    """Repositório que persiste cooldown e histórico sem reter dados sensíveis de destino."""

    def _session_factory(self):
        if AsyncSessionLocal is None:
            raise RuntimeError("Banco de dados não configurado para o pipeline de alertas.")
        return AsyncSessionLocal

    @staticmethod
    def _number(details: dict[str, Any], *keys: str) -> float | None:
        for key in keys:
            value = details.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return None

    async def reserve(self, alert: Alert, *, scope_key: str = "owner") -> AlertReservation | None:
        """Cria um evento somente quando a chave não estiver em cooldown."""
        now = datetime.now(tz=timezone.utc)
        payload = dict(alert.details)
        cooldown_until = now + timedelta(seconds=max(alert.cooldown_seconds, 0))
        value = self._number(payload, "value", "price", "current_value")
        previous_value = self._number(payload, "previous_value", "previous_price")
        message_hash = sha256(f"{alert.title}\n{alert.message}".encode("utf-8")).hexdigest()
        session_factory = self._session_factory()

        async with session_factory() as session:
            async with session.begin():
                scoped_dedup_key = f"{scope_key}:{alert.dedup_key}"
                state = await session.scalar(
                    select(AlertState)
                    .where(AlertState.dedup_key == scoped_dedup_key)
                    .with_for_update()
                )
                if state is not None:
                    if now < state.cooldown_until:
                        return None
                    state.last_emitted_at = now
                    state.last_payload = payload
                    state.previous_value = state.last_value
                    state.last_value = value
                    state.last_message_hash = message_hash
                    state.cooldown_until = cooldown_until
                else:
                    state = AlertState(
                        dedup_key=scoped_dedup_key,
                        last_emitted_at=now,
                        last_payload=payload,
                        last_value=value,
                        previous_value=previous_value,
                        last_message_hash=message_hash,
                        cooldown_until=cooldown_until,
                    )
                    session.add(state)

                event = AlertEvent(
                    scope_key=scope_key,
                    dedup_key=alert.dedup_key,
                    asset=alert.asset.upper(),
                    event_type=alert.event_type,
                    severity=alert.severity.value,
                    title=alert.title,
                    message=alert.message,
                    source=alert.source,
                    payload=payload,
                    value=value,
                    previous_value=previous_value,
                    message_hash=message_hash,
                    cooldown_until=cooldown_until,
                )
                session.add(event)
                await session.flush()
                return AlertReservation(alert_id=event.id, created_at=event.created_at)

    async def create_delivery(self, alert_id: str, channel: NotificationChannel) -> str:
        session_factory = self._session_factory()
        async with session_factory() as session:
            delivery = AlertDelivery(alert_id=alert_id, channel=channel.value)
            session.add(delivery)
            await session.commit()
            await session.refresh(delivery)
            return delivery.id

    async def get_observation(self, key: str) -> dict[str, Any] | None:
        """Lê um contexto de comparação persistente, sem gerar uma entrega."""
        session_factory = self._session_factory()
        async with session_factory() as session:
            state = await session.get(AlertState, key)
            return dict(state.last_payload) if state is not None else None

    async def save_observation(self, key: str, payload: dict[str, Any]) -> None:
        """Persiste a última leitura de contexto para sobreviver a reinícios do worker."""
        now = datetime.now(tz=timezone.utc)
        session_factory = self._session_factory()
        async with session_factory() as session:
            state = await session.get(AlertState, key)
            if state is None:
                state = AlertState(
                    dedup_key=key,
                    last_emitted_at=now,
                    last_payload=dict(payload),
                    last_message_hash="observation",
                    cooldown_until=now,
                )
                session.add(state)
            else:
                state.last_payload = dict(payload)
                state.last_emitted_at = now
                state.cooldown_until = now
            await session.commit()

    async def mark_delivery(
        self,
        delivery_id: str,
        *,
        status: str,
        attempts: int,
        provider_message_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        session_factory = self._session_factory()
        async with session_factory() as session:
            delivery = await session.get(AlertDelivery, delivery_id)
            if delivery is None:
                return
            delivery.status = status
            delivery.attempts = attempts
            delivery.provider_message_id = provider_message_id
            delivery.error_code = error_code
            delivery.delivered_at = datetime.now(tz=timezone.utc) if status == "sent" else None
            await session.commit()

    async def set_event_status(self, alert_id: str, status: str) -> None:
        session_factory = self._session_factory()
        async with session_factory() as session:
            event = await session.get(AlertEvent, alert_id)
            if event is not None:
                event.status = status
                await session.commit()
