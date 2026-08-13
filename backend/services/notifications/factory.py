"""Composição dos provedores habilitados no processo de alertas."""

from __future__ import annotations

from config import settings
from services.notifications.contracts import NotificationChannel
from services.notifications.gmail_provider import GmailNotificationProvider
from services.notifications.notification_service import NotificationService
from services.notifications.telegram_service import get_telegram_service


def configured_channels() -> list[NotificationChannel]:
    """Converte a configuração em canais conhecidos, ignorando valores inválidos."""
    channels: list[NotificationChannel] = []
    for configured in settings.alert_channels_list:
        try:
            channel = NotificationChannel(configured)
        except ValueError:
            continue
        if channel not in channels:
            channels.append(channel)
    return channels


def create_notification_service() -> NotificationService:
    """Cria o serviço multi-canal; cada provedor valida a própria credencial no envio."""
    return NotificationService(
        providers=[get_telegram_service(), GmailNotificationProvider()],
    )
