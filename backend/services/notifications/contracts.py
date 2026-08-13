"""Contratos independentes de provedor para o pipeline de alertas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    EMAIL = "email"


@dataclass(frozen=True)
class Alert:
    """Evento aprovado pelo motor, pronto para reserva e distribuição."""

    asset: str
    event_type: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    details: dict[str, Any] = field(default_factory=dict)
    cooldown_seconds: int = 1800

    @property
    def dedup_key(self) -> str:
        return f"{self.asset.upper()}:{self.event_type.lower()}"


@dataclass(frozen=True)
class DeliveryReceipt:
    provider_message_id: str | None = None


class NotificationProvider(Protocol):
    channel: NotificationChannel

    async def send(self, alert: Alert) -> DeliveryReceipt:
        """Entrega um alerta aprovado e retorna somente o identificador do provedor."""
