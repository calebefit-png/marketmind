"""Camada comum de provedores, histórico e entrega de notificações."""

from services.notifications.contracts import Alert, AlertSeverity, NotificationChannel
from services.notifications.factory import create_notification_service
from services.notifications.notification_service import NotificationService

__all__ = [
    "Alert",
    "AlertSeverity",
    "NotificationChannel",
    "NotificationService",
    "create_notification_service",
]
