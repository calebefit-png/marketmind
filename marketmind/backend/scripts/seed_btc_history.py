"""
scripts/seed_btc_history.py
Baixa 1 ano de candles diários (klines) do BTCUSDT via API REST da Binance
e grava no banco PostgreSQL/TimescaleDB (tabela `candles`), com upsert.

Execução local:
    cd backend
    python -m scripts.seed_btc_history
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402
from database import AsyncSessionLocal  # noqa: E402
from models.candle import Candle  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("marketmind.seed")

SYMBOL = "BTCUSDT"
INTERVAL = "1d"
TIMEFRAME_LABEL = "1d"
DAYS_BACK = 365
KLINES_LIMIT = 1000  # máximo permitido pela Binance por request


async def fetch_klines(client: httpx.AsyncClient, start_time_ms: int, end_time_ms: int) -> list[list]:
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": KLINES_LIMIT,
    }
    response = await client.get(f"{settings.BINANCE_REST_URL}/klines", params=params)
    response.raise_for_status()
    return response.json()


def kline_to_row(kline: list) -> dict:
    """
    Formato de um kline da Binance:
    [open_time, open, high, low, close, volume, close_time, ...]
    """
    open_time_ms = kline[0]
    return {
        "asset": SYMBOL,
        "timeframe": TIMEFRAME_LABEL,
        "time": datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc),
        "open": float(kline[1]),
        "high": float(kline[2]),
        "low": float(kline[3]),
        "close": float(kline[4]),
        "volume": float(kline[5]),
    }


async def upsert_candles(rows: list[dict]) -> None:
    if not rows:
        return

    async with AsyncSessionLocal() as session:
        stmt = pg_insert(Candle).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["asset", "timeframe", "time"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
            },
        )
        await session.execute(stmt)
        await session.commit()


async def main() -> None:
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=DAYS_BACK)

    logger.info("Baixando candles de %s a %s para %s (%s)", start.date(), end.date(), SYMBOL, INTERVAL)

    async with httpx.AsyncClient(timeout=30.0) as client:
        klines = await fetch_klines(
            client,
            start_time_ms=int(start.timestamp() * 1000),
            end_time_ms=int(end.timestamp() * 1000),
        )

    logger.info("Recebidos %d candles da Binance", len(klines))

    rows = [kline_to_row(k) for k in klines]
    await upsert_candles(rows)

    logger.info("Seed concluído: %d candles gravados/atualizados em `candles`", len(rows))


if __name__ == "__main__":
    asyncio.run(main())
