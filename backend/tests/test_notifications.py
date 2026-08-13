"""Testes do motor de alertas e dos provedores sem chamadas externas reais."""

from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from config import Settings
from services.alerts.alert_engine import MarketAlertEngine
from services.notifications.contracts import Alert, AlertSeverity, DeliveryReceipt, NotificationChannel
from services.notifications.notification_service import NotificationService
from services.notifications.preferences import PreferenceSnapshot
from services.notifications.repository import AlertReservation
from services.notifications.telegram_service import TelegramConfigurationError, TelegramService


def notification_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "TELEGRAM_BOT_TOKEN": "123456:test-token",
        "TELEGRAM_CHAT_ID": "12345",
        "TELEGRAM_MIN_SEND_INTERVAL_SECONDS": 0,
        "ALERT_PRICE_WINDOW_SECONDS": 900,
        "ALERT_PRICE_MOVE_THRESHOLD_PCT": 2.5,
        "ALERT_RSI_OVERBOUGHT": 70.0,
        "ALERT_RSI_OVERSOLD": 30.0,
        "ALERT_VOLUME_SPIKE_MULTIPLIER": 2.0,
    }
    values.update(overrides)
    return Settings(**values)


class TelegramServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_requires_token_and_destination(self) -> None:
        service = TelegramService(notification_settings(TELEGRAM_BOT_TOKEN=""))
        with self.assertRaises(TelegramConfigurationError):
            service.assert_configured()

    async def test_fragments_long_message_and_returns_provider_ids(self) -> None:
        service = TelegramService(notification_settings())
        service._post_message = AsyncMock(side_effect=["1", "2"])  # type: ignore[method-assign]
        result = await service.send_telegram_message("a" * 4_200)
        self.assertEqual(result.message_ids, ("1", "2"))
        self.assertEqual(service._post_message.await_count, 2)  # type: ignore[attr-defined]

    async def test_formats_alert_with_escaped_content_and_disclaimer(self) -> None:
        alert = Alert(
            asset="BTCUSDT",
            event_type="price_move_up",
            severity=AlertSeverity.WARNING,
            title="<movimento>",
            message="Texto & contexto",
            source="Binance",
        )
        message = TelegramService.format_alert(alert)
        self.assertIn("&lt;movimento&gt;", message)
        self.assertIn("Texto &amp; contexto", message)
        self.assertIn("não é recomendação de investimento", message)


class AlertEngineTestCase(unittest.TestCase):
    def test_detects_material_price_move_inside_window(self) -> None:
        engine = MarketAlertEngine(notification_settings())
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(
            engine.evaluate_tick({"asset": "BTCUSDT", "price": 100, "timestamp": start.isoformat(), "source": "binance"}),
            [],
        )
        alerts = engine.evaluate_tick(
            {
                "asset": "BTCUSDT",
                "price": 103,
                "timestamp": (start + timedelta(minutes=5)).isoformat(),
                "source": "binance",
            }
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].event_type, "price_move_up")
        self.assertIn("Condição de invalidação", alerts[0].message)

    def test_detects_rsi_overbought_with_real_candle_series(self) -> None:
        engine = MarketAlertEngine(notification_settings())
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        candles = [
            {
                "time": start + timedelta(days=index),
                "open": 100 + index,
                "high": 101 + index,
                "low": 99 + index,
                "close": 100 + index,
                "volume": 10,
            }
            for index in range(35)
        ]
        event_types = {alert.event_type for alert in engine.evaluate_candles(candles)}
        self.assertIn("rsi_overbought", event_types)


class _FakeRepository:
    def __init__(self) -> None:
        self.statuses: list[str] = []

    async def reserve(self, alert: Alert, *, scope_key: str = "owner") -> AlertReservation:
        return AlertReservation(alert_id="alert-1", created_at=datetime.now(tz=timezone.utc))

    async def create_delivery(self, alert_id: str, channel: NotificationChannel) -> str:
        return f"delivery-{channel.value}"

    async def mark_delivery(self, delivery_id: str, *, status: str, **kwargs: object) -> None:
        self.statuses.append(status)

    async def set_event_status(self, alert_id: str, status: str) -> None:
        self.statuses.append(status)


class _FakeProvider:
    channel = NotificationChannel.TELEGRAM

    async def send(self, alert: Alert) -> DeliveryReceipt:
        return DeliveryReceipt(provider_message_id="telegram-1")


class NotificationServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_records_success_without_real_provider_or_database(self) -> None:
        repository = _FakeRepository()
        service = NotificationService([_FakeProvider()], repository=repository)  # type: ignore[arg-type]
        sent = await service.send_alert(
            Alert(
                asset="BTCUSDT",
                event_type="test",
                severity=AlertSeverity.INFO,
                title="Teste",
                message="Mensagem",
                source="teste",
            ),
            [NotificationChannel.TELEGRAM],
        )
        self.assertTrue(sent)
        self.assertEqual(repository.statuses, ["sent", "sent"])

    def test_preference_filters_by_asset_and_severity(self) -> None:
        preference = PreferenceSnapshot(
            scope_key="owner",
            assets=("BTCUSDT",),
            channels=(NotificationChannel.TELEGRAM,),
            minimum_severity=AlertSeverity.WARNING,
            cooldown_seconds=1800,
            paused=False,
        )
        warning = Alert("BTCUSDT", "test", AlertSeverity.WARNING, "t", "m", "source")
        info = Alert("BTCUSDT", "test", AlertSeverity.INFO, "t", "m", "source")
        self.assertTrue(preference.matches(warning))
        self.assertFalse(preference.matches(info))
