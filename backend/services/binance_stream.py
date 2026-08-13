"""
Cliente de mercado da Binance para BTCUSDT.

Mantém o stream WebSocket como fonte principal e usa o endpoint REST público como
fallback. Isso mantém a API e os clientes WebSocket utilizáveis quando uma rede
de hospedagem bloqueia ou atrasa a conexão WebSocket de saída.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from config import settings

logger = logging.getLogger("marketmind.binance")

TickCallback = Callable[[dict], Awaitable[None]]
_FALLBACK_REST_BASES = (
    "https://data-api.binance.vision/api/v3",
    "https://api1.binance.com/api/v3",
)


class BinanceStreamService:
    """Conexão de mercado única, com fan-out para os consumidores internos."""

    def __init__(self, symbol: str = "btcusdt") -> None:
        self.symbol = symbol.lower()
        self.stream_url = f"{settings.BINANCE_WS_URL.rstrip('/')}/{self.symbol}@trade"
        configured_rest = settings.BINANCE_REST_URL.rstrip("/")
        self.rest_bases = tuple(dict.fromkeys((configured_rest, *_FALLBACK_REST_BASES)))
        self._last_price: float | None = None
        self._last_tick: dict | None = None
        self._subscribers: list[TickCallback] = []
        self._task: asyncio.Task | None = None
        self._running = False

    @property
    def last_price(self) -> float | None:
        return self._last_price

    @property
    def last_tick(self) -> dict | None:
        return self._last_tick.copy() if self._last_tick else None

    def subscribe(self, callback: TickCallback) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: TickCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _make_tick(self, price: float, source: str = "binance") -> dict:
        return {
            "asset": self.symbol.upper(),
            "price": price,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "source": source,
        }

    def _remember_tick(self, payload: dict) -> None:
        self._last_price = float(payload["price"])
        self._last_tick = payload

    async def _notify(self, payload: dict) -> None:
        for callback in list(self._subscribers):
            try:
                await callback(payload)
            except Exception:
                logger.exception("Erro ao notificar subscriber do Binance stream")

    async def fetch_rest_tick(self) -> dict:
        """Busca cotação por REST, testando mirrors públicos oficiais em sequência."""
        timeout = httpx.Timeout(timeout=8.0, connect=4.0)
        errors: list[str] = []
        async with httpx.AsyncClient(timeout=timeout) as client:
            for base_url in self.rest_bases:
                try:
                    response = await client.get(
                        f"{base_url}/ticker/price",
                        params={"symbol": self.symbol.upper()},
                    )
                    response.raise_for_status()
                    price = float(response.json()["price"])
                    if price <= 0:
                        raise ValueError("preço não positivo")
                    payload = self._make_tick(price, source="binance_rest")
                    self._remember_tick(payload)
                    return payload
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    errors.append(f"{base_url}: {type(exc).__name__}")
        raise RuntimeError("; ".join(errors) or "fallback REST indisponível")

    async def _run(self) -> None:
        backoff = 2
        while self._running:
            try:
                async with websockets.connect(
                    self.stream_url,
                    ping_interval=20,
                    open_timeout=10,
                    close_timeout=5,
                ) as ws:
                    logger.info("Conectado ao stream Binance: %s", self.stream_url)
                    backoff = 2
                    async for raw_message in ws:
                        if not self._running:
                            break
                        data = json.loads(raw_message)
                        price = float(data.get("p", 0.0))
                        if price <= 0:
                            continue
                        payload = {
                            "asset": data.get("s", self.symbol.upper()),
                            "price": price,
                            "timestamp": datetime.fromtimestamp(
                                data.get("T", 0) / 1000, tz=timezone.utc
                            ).isoformat(),
                            "source": "binance",
                        }
                        self._remember_tick(payload)
                        await self._notify(payload)
            except (ConnectionClosed, OSError, asyncio.TimeoutError) as exc:
                logger.warning("Stream Binance indisponível (%s); usando REST temporariamente", type(exc).__name__)
            except Exception:
                logger.exception("Erro inesperado no stream Binance; usando REST temporariamente")

            if not self._running:
                break
            try:
                fallback_tick = await self.fetch_rest_tick()
                await self._notify(fallback_tick)
                backoff = 2
            except Exception as exc:
                logger.warning("Fallback REST Binance indisponível: %s", type(exc).__name__)
                backoff = min(backoff * 2, 30)
            await asyncio.sleep(backoff)

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


binance_stream_service = BinanceStreamService(symbol="btcusdt")
