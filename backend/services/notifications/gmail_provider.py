"""Adaptador assíncrono do Gmail OAuth para o contrato comum de notificações."""

from __future__ import annotations

import asyncio
import html

from config import Settings, settings
from services.email.gmail_service import GmailConfigurationError, GmailService, get_gmail_service
from services.notifications.contracts import Alert, DeliveryReceipt, NotificationChannel


class GmailNotificationProvider:
    """Entrega alertas por Gmail sem expor destinatários fora do ambiente do servidor."""

    channel = NotificationChannel.EMAIL

    def __init__(
        self,
        app_settings: Settings | None = None,
        gmail_service: GmailService | None = None,
    ) -> None:
        self._settings = app_settings or settings
        self._gmail_service = gmail_service or get_gmail_service()

    async def send(self, alert: Alert) -> DeliveryReceipt:
        recipients = self._settings.alert_email_recipients_list
        if not recipients:
            raise GmailConfigurationError(
                "ALERT_EMAIL_RECIPIENTS não foi configurada para a entrega de alertas."
            )
        subject = f"[MarketMind {alert.severity.value}] {alert.asset.upper()} — {alert.title}"
        text_body = (
            f"{alert.title}\n\n{alert.message}\n\n"
            "Informação analítica; não é recomendação de investimento.\n"
            f"Fonte: {alert.source}"
        )
        html_body = (
            "<h2>MarketMind Alert</h2>"
            f"<p><strong>{html.escape(alert.asset.upper())}</strong> · "
            f"{html.escape(alert.severity.value)}</p>"
            f"<h3>{html.escape(alert.title)}</h3>"
            f"<p>{html.escape(alert.message).replace(chr(10), '<br>')}</p>"
            "<p><em>Informação analítica; não é recomendação de investimento.</em></p>"
            f"<p>Fonte: {html.escape(alert.source)}</p>"
        )
        result = await asyncio.to_thread(
            self._gmail_service.send_email,
            recipients,
            subject,
            text_body,
            html_body,
        )
        return DeliveryReceipt(provider_message_id=result.message_id)
