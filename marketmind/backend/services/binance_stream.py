"""
services/binance_stream.py
Cliente WebSocket para o stream público da Binance (BTCUSDT trade stream).
Mantém o último preço em memória e repassa ticks para um broadcaster de
WebSocket local (clientes conectados ao nosso backend).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import websockets
from websockets.exceptions import ConnectionClosed

from config import settings

logger = logging.getLogger("marketmind.binance")

TickCallback = Callable[[dict], Awaitable[None]]


class BinanceStreamService:
    """
    Gerencia a conexão persistente com o WebSocket público da Binance
    e distribui os ticks recebidos para callbacks registrados
    (ex.: broadcast para clientes conectados ao nosso próprio WS).
    """

    def __init__(self, symbol: str = "btcusdt") -> None:
        self.symbol = symbol.lower()
        self.stream_url = f"{settings.BINANCE_WS_URL}/{self.symbol}@trade"
        self._last_price: float | None = None
        self._subscribers: list[TickCallback] = []
        self._task: asyncio.Task | None = None
        self._running = False

    @property
    def last_price(self) -> float | None:
        return self._last_price

    def subscribe(self, callback: TickCallback) -> None:
        """Registra um callback assíncrono chamado a cada novo tick recebido."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: TickCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def _notify(self, payload: dict) -> None:
        for callback in list(self._subscribers):
            try:
                await callback(payload)
            except Exception:
                logger.exception("Erro ao notificar subscriber do Binance stream")

    async def _run(self) -> None:
        backoff = 1
        while self._running:
            try:
                async with websockets.connect(self.stream_url, ping_interval=20) as ws:
                    logger.info("Conectado ao stream Binance: %s", self.stream_url)
                    backoff = 1
                    async for raw_message in ws:
                        if not self._running:
                            break
                        data = json.loads(raw_message)
                        price = float(data.get("p", 0.0))
                        self._last_price = price

                        payload = {
                            "asset": data.get("s", self.symbol.upper()),
                            "price": price,
                            "timestamp": datetime.fromtimestamp(
                                data.get("T", 0) / 1000, tz=timezone.utc
                            ).isoformat(),
                            "source": "binance",
                        }
                        print(f"[Binance] {payload['asset']} = {price}")
                        await self._notify(payload)
            except (ConnectionClosed, OSError) as exc:
                logger.warning("Conexão Binance perdida (%s). Reconectando em %ss", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
            except Exception:
                logger.exception("Erro inesperado no stream Binance")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("BinanceStreamService iniciado para %s", self.symbol)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("BinanceStreamService parado")


# Instância única compartilhada pela aplicação
binance_stream_service = BinanceStreamService(symbol="btcusdt")
