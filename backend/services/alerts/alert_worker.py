"""Processo isolado e contínuo para avaliar alertas do MarketMind no Render."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import time

from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal, dispose_db, init_db
from models.candle import Candle
from services.alerts.alert_engine import MarketAlertEngine
from services.alerts.ml_context import get_reliable_prediction_context
from services.alerts.worker_status import WorkerStatusService
from services.bcb_service import bcb_service
from services.binance_stream import BinanceStreamService
from services.notifications.factory import configured_channels, create_notification_service
from services.notifications.preferences import AlertPreferenceService
from services.notifications.queue import NotificationQueue
from services.notifications.repository import AlertRepository
from services.notifications.telegram_service import get_telegram_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("marketmind.alert_worker")


class AlertWorker:
    """Isola o monitoramento de mercado da API HTTP e preserva estado no PostgreSQL."""

    def __init__(self) -> None:
        self._stop_event = asyncio.Event()
        self._engine = MarketAlertEngine()
        self._notifications = create_notification_service()
        self._queue = NotificationQueue(self._notifications, on_delivery=self._record_delivery)
        self._channels = configured_channels()
        self._preferences = AlertPreferenceService()
        self._repository = AlertRepository()
        self._stream = BinanceStreamService(symbol="btcusdt")
        self._next_technical_run = 0.0
        self._next_macro_run = 0.0
        self._status = WorkerStatusService()

    async def run(self) -> None:
        database_ready = await init_db()
        if not database_ready:
            raise RuntimeError("O processo de alertas exige DATABASE_URL disponível.")
        if not self._channels:
            logger.warning("Nenhum canal de alerta reconhecido em ALERT_DEFAULT_CHANNELS.")
        logger.info("Telegram configured: %s", get_telegram_service().is_configured())
        await self._status.heartbeat()
        await self._queue.start()

        self._stream.subscribe(self._on_tick)
        self._stream.start()
        logger.info("Worker de alertas iniciado; canais configurados: %s", [channel.value for channel in self._channels])
        try:
            while not self._stop_event.is_set():
                now = time.monotonic()
                if now >= self._next_technical_run:
                    await self._run_cycle(self._evaluate_technical)
                    self._next_technical_run = now + settings.ALERT_WORKER_TECHNICAL_INTERVAL_SECONDS
                if now >= self._next_macro_run:
                    await self._run_cycle(self._evaluate_macro)
                    self._next_macro_run = now + settings.ALERT_WORKER_MACRO_INTERVAL_SECONDS
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
                except TimeoutError:
                    pass
        finally:
            await self._stream.stop()
            await self._queue.stop()
            await self._status.mark_offline()
            await dispose_db()
            logger.info("Worker de alertas encerrado")

    async def run_once(self) -> None:
        """Executa uma varredura completa e encerra, apropriada para agendamentos pontuais."""
        database_ready = await init_db()
        if not database_ready:
            raise RuntimeError("A execução agendada exige DATABASE_URL disponível.")
        if not self._channels:
            logger.warning("Nenhum canal de alerta reconhecido em ALERT_DEFAULT_CHANNELS.")
        logger.info("Execução agendada iniciada; Telegram configured: %s", get_telegram_service().is_configured())
        await self._status.heartbeat()
        await self._queue.start()
        try:
            await self._run_cycle(self._evaluate_technical)
            await self._run_cycle(self._evaluate_macro)
            await self._queue.wait_until_idle()
        finally:
            await self._queue.stop()
            await self._status.mark_scheduled()
            await dispose_db()
            logger.info("Execução agendada de alertas concluída")

    async def stop(self) -> None:
        self._stop_event.set()

    async def _on_tick(self, tick: dict) -> None:
        try:
            await self._emit(self._engine.evaluate_tick(tick))
        except Exception as exc:
            logger.warning("Tick não avaliado pelo motor de alertas: %s", type(exc).__name__)

    async def _run_cycle(self, operation) -> None:
        try:
            sent = await operation()
            await self._status.heartbeat(processed_increment=1, sent_increment=int(bool(sent)))
        except Exception as exc:
            logger.warning("Ciclo de alertas falhou: %s", type(exc).__name__)
            await self._status.heartbeat(error=exc)

    async def _evaluate_technical(self) -> bool:
        if AsyncSessionLocal is None:
            return False
        async with AsyncSessionLocal() as session:
            result = await session.scalars(
                select(Candle)
                .where(Candle.asset == "BTCUSDT", Candle.timeframe == "1d")
                .order_by(Candle.time.desc())
                .limit(100)
            )
            rows = list(reversed(result.all()))
        candles = [
            {"time": row.time, "open": row.open, "high": row.high, "low": row.low, "close": row.close, "volume": row.volume}
            for row in rows
        ]
        alerts = self._engine.evaluate_candles(candles, asset="BTCUSDT")
        regime = self._engine.classify_regime(candles)
        if regime is not None:
            regime_key = "owner:BTCUSDT:technical_regime"
            previous_regime = await self._repository.get_observation(regime_key)
            alerts.extend(self._engine.evaluate_regime_change("BTCUSDT", regime, previous_regime))
            await self._repository.save_observation(regime_key, regime)
        context = get_reliable_prediction_context("BTCUSDT", candles)
        if context is not None:
            observation_key = "owner:BTCUSDT:reliable_model_probability"
            previous = await self._repository.get_observation(observation_key)
            previous_probabilities = previous.get("probabilities") if previous else None
            alerts.extend(
                self._engine.evaluate_probability_change(
                    "BTCUSDT",
                    context.probabilities,
                    previous_probabilities if isinstance(previous_probabilities, dict) else None,
                    model_name=context.model_name,
                    balanced_accuracy=context.balanced_accuracy,
                )
            )
            await self._repository.save_observation(observation_key, context.payload())
        return await self._emit(alerts)

    async def _evaluate_macro(self) -> bool:
        try:
            selic = await bcb_service.get_selic()
        except Exception as exc:
            logger.warning("Não foi possível consultar a série Selic: %s", type(exc).__name__)
            return False
        return await self._emit(
            self._engine.evaluate_selic(selic.valor_atual, selic.valor_anterior, selic.data)
        )

    async def _emit(self, alerts) -> bool:
        queued_any = False
        preference = await self._preferences.get_or_create_owner()
        for alert in alerts:
            if not preference.matches(alert):
                continue
            alert = alert.__class__(
                asset=alert.asset,
                event_type=alert.event_type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                details=alert.details,
                cooldown_seconds=preference.cooldown_seconds,
            )
            try:
                queued = await self._queue.enqueue(
                    alert, preference.channels, scope_key=preference.scope_key
                )
                queued_any = queued_any or queued
            except RuntimeError as exc:
                logger.warning("Alerta não enfileirado: %s", str(exc))
        return queued_any

    async def _record_delivery(self, delivered: bool) -> None:
        """Atualiza o contador somente depois da conclusão no provedor."""
        await self._status.heartbeat(sent_increment=int(delivered))


async def main() -> None:
    worker = AlertWorker()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signum, lambda: asyncio.create_task(worker.stop()))
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
