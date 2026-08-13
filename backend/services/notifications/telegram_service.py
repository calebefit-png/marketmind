"""Provedor Telegram Bot API para entrega segura de alertas do MarketMind."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import httpx

from config import Settings, settings
from services.notifications.contracts import Alert, DeliveryReceipt, NotificationChannel

logger = logging.getLogger("marketmind.telegram")

TELEGRAM_TEXT_LIMIT = 4096
MAX_RETRY_ATTEMPTS = 3


class TelegramError(RuntimeError):
    """Erro base sem token, chat ID ou conteúdo sensível na mensagem."""


class TelegramConfigurationError(TelegramError):
    """O ambiente não tem as credenciais mínimas do bot configuradas."""


class TelegramDeliveryError(TelegramError):
    """A Telegram Bot API recusou ou não concluiu uma entrega."""


@dataclass(frozen=True)
class TelegramSendResult:
    """Identificadores de mensagens enviadas, sem persistir conteúdo ou destino."""

    message_ids: tuple[str, ...]


class TelegramService:
    """Cliente assíncrono com fragmentação, espera de limite e retentativa limitada."""

    channel = NotificationChannel.TELEGRAM

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings
        self._rate_lock = asyncio.Lock()
        self._next_send_at = 0.0

    def is_configured(self) -> bool:
        """Indica somente se as duas variáveis obrigatórias existem, sem expô-las."""
        return bool(
            self._settings.TELEGRAM_BOT_TOKEN.strip()
            and self._settings.TELEGRAM_CHAT_ID.strip()
        )

    def assert_configured(self) -> None:
        if self.is_configured():
            return
        missing = [
            name
            for name, value in {
                "TELEGRAM_BOT_TOKEN": self._settings.TELEGRAM_BOT_TOKEN,
                "TELEGRAM_CHAT_ID": self._settings.TELEGRAM_CHAT_ID,
            }.items()
            if not value.strip()
        ]
        raise TelegramConfigurationError(
            "Configuração Telegram incompleta: defina " + ", ".join(missing) + "."
        )

    async def send(self, alert: Alert) -> DeliveryReceipt:
        result = await self.send_telegram_message(self.format_alert(alert), parse_mode="HTML")
        return DeliveryReceipt(provider_message_id=result.message_ids[-1] if result.message_ids else None)

    async def send_telegram_message(
        self,
        message: str,
        *,
        parse_mode: Literal["HTML", "MarkdownV2"] = "HTML",
    ) -> TelegramSendResult:
        """Envia texto em partes válidas para Telegram, respeitando rate limiting local."""
        self.assert_configured()
        if parse_mode not in {"HTML", "MarkdownV2"}:
            raise TelegramDeliveryError("Formato Telegram não suportado.")

        message_ids: list[str] = []
        for chunk in self._split_message(message):
            await self._wait_for_rate_limit()
            message_id = await self._post_message(chunk, parse_mode=parse_mode)
            message_ids.append(message_id)
        logger.info("Telegram entregou %d parte(s) de alerta", len(message_ids))
        return TelegramSendResult(message_ids=tuple(message_ids))

    @staticmethod
    def format_alert(alert: Alert) -> str:
        """Formata um alerta curto e profissional com hipótese e dados de origem."""
        import html

        emoji = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "CRITICAL": "🚨",
        }.get(alert.severity.value, "ℹ️")
        return (
            f"{emoji} <b>MARKETMIND ALERT</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"<b>{html.escape(alert.asset.upper())}</b> · {html.escape(alert.severity.value)}\n\n"
            f"<b>{html.escape(alert.title)}</b>\n"
            f"{html.escape(alert.message)}\n\n"
            "<i>Informação analítica, não é recomendação de investimento.</i>\n"
            f"Fonte: {html.escape(alert.source)}"
        )

    async def _wait_for_rate_limit(self) -> None:
        interval = max(float(self._settings.TELEGRAM_MIN_SEND_INTERVAL_SECONDS), 0.0)
        async with self._rate_lock:
            now = time.monotonic()
            if self._next_send_at > now:
                await asyncio.sleep(self._next_send_at - now)
            self._next_send_at = time.monotonic() + interval

    async def _post_message(self, text: str, *, parse_mode: str) -> str:
        endpoint = f"https://api.telegram.org/bot{self._settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": self._settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        timeout = httpx.Timeout(timeout=12.0, connect=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
                try:
                    response = await client.post(endpoint, json=payload)
                    body = response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    if attempt == MAX_RETRY_ATTEMPTS:
                        raise TelegramDeliveryError("Não foi possível alcançar a Telegram Bot API.") from exc
                    await asyncio.sleep(2 ** (attempt - 1))
                    continue

                if response.is_success and body.get("ok") is True:
                    result = body.get("result") or {}
                    message_id = result.get("message_id")
                    if message_id is None:
                        raise TelegramDeliveryError("Telegram não retornou o identificador da mensagem.")
                    return str(message_id)

                retry_after = self._retry_after_seconds(body)
                should_retry = response.status_code == 429 or response.status_code >= 500
                if should_retry and attempt < MAX_RETRY_ATTEMPTS:
                    await asyncio.sleep(retry_after if retry_after is not None else 2 ** (attempt - 1))
                    continue
                if response.status_code in {401, 403}:
                    raise TelegramConfigurationError("A Telegram Bot API recusou a credencial ou o destino configurado.")
                raise TelegramDeliveryError("A Telegram Bot API recusou a mensagem ou está indisponível.")

        raise TelegramDeliveryError("Não foi possível concluir a entrega Telegram.")

    @staticmethod
    def _retry_after_seconds(body: object) -> float | None:
        if not isinstance(body, dict):
            return None
        parameters = body.get("parameters")
        if not isinstance(parameters, dict):
            return None
        retry_after = parameters.get("retry_after")
        if isinstance(retry_after, (int, float)) and retry_after >= 0:
            return float(retry_after)
        return None

    @staticmethod
    def _split_message(message: str) -> list[str]:
        if not isinstance(message, str) or not message.strip():
            raise TelegramDeliveryError("A mensagem Telegram é obrigatória.")
        remaining = message.strip()
        chunks: list[str] = []
        while len(remaining) > TELEGRAM_TEXT_LIMIT:
            cut = remaining.rfind("\n", 0, TELEGRAM_TEXT_LIMIT + 1)
            if cut < TELEGRAM_TEXT_LIMIT // 2:
                cut = remaining.rfind(" ", 0, TELEGRAM_TEXT_LIMIT + 1)
            if cut <= 0:
                cut = TELEGRAM_TEXT_LIMIT
            chunks.append(remaining[:cut].strip())
            remaining = remaining[cut:].lstrip()
        if remaining:
            chunks.append(remaining)
        return chunks


@lru_cache
def get_telegram_service() -> TelegramService:
    return TelegramService()


async def send_telegram_message(message: str) -> TelegramSendResult:
    """Atalho de compatibilidade para o envio de texto HTML pelo provedor singleton."""
    return await get_telegram_service().send_telegram_message(message)
