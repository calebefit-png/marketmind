"""Orquestra a distribuição multi-canal e mantém o histórico de cada tentativa."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from services.notifications.contracts import Alert, NotificationChannel, NotificationProvider
from services.notifications.repository import AlertRepository

logger = logging.getLogger("marketmind.notifications")


class NotificationService:
    """Reserva o alerta uma vez, entrega por canal e nunca registra destinatários em logs."""

    def __init__(
        self,
        providers: Iterable[NotificationProvider],
        repository: AlertRepository | None = None,
    ) -> None:
        self._providers = {provider.channel: provider for provider in providers}
        self._repository = repository or AlertRepository()

    async def send_alert(
        self,
        alert: Alert,
        channels: Iterable[NotificationChannel],
        *,
        scope_key: str = "owner",
    ) -> bool:
        reservation = await self._repository.reserve(alert, scope_key=scope_key)
        if reservation is None:
            logger.info("Alerta suprimido por cooldown: %s", alert.dedup_key)
            return False

        delivered = False
        for channel in channels:
            delivery_id = await self._repository.create_delivery(reservation.alert_id, channel)
            provider = self._providers.get(channel)
            if provider is None:
                await self._repository.mark_delivery(
                    delivery_id, status="skipped", attempts=0, error_code="provider_not_configured"
                )
                continue

            try:
                receipt = await provider.send(alert)
                await self._repository.mark_delivery(
                    delivery_id,
                    status="sent",
                    attempts=1,
                    provider_message_id=receipt.provider_message_id,
                )
                delivered = True
            except Exception as exc:
                logger.warning("Falha de entrega no canal %s: %s", channel.value, type(exc).__name__)
                await self._repository.mark_delivery(
                    delivery_id, status="failed", attempts=1, error_code=type(exc).__name__[:64]
                )

        await self._repository.set_event_status(reservation.alert_id, "sent" if delivered else "failed")
        return delivered
