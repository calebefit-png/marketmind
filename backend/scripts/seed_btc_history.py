"""Baixa e grava candles históricos do BTCUSDT em PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402
from database import AsyncSessionLocal  # noqa: E402
from models.candle import Candle  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("marketmind.seed")

SYMBOL = "BTCUSDT"
INTERVAL = "1d"
TIMEFRAME_LABEL = "1d"
DEFAULT_DAYS_BACK = 8 * 365
KLINES_LIMIT = 1000
DAY_MS = 24 * 60 * 60 * 1000


async def fetch_klines(
    client: httpx.AsyncClient,
    start_time_ms: int,
    end_time_ms: int,
) -> list[list]:
    response = await client.get(
        f"{settings.BINANCE_REST_URL}/klines",
        params={
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "startTime": start_time_ms,
            "endTime": end_time_ms,
            "limit": KLINES_LIMIT,
        },
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Resposta inesperada da Binance para klines")
    return data


async def fetch_historical_klines(
    client: httpx.AsyncClient,
    start_time_ms: int,
    end_time_ms: int,
) -> list[list]:
    """Percorre a janela em páginas de até 1.000 candles."""
    cursor = start_time_ms
    all_klines: list[list] = []

    while cursor < end_time_ms:
        batch = await fetch_klines(client, cursor, end_time_ms)
        if not batch:
            break

        all_klines.extend(batch)
        last_open_time = int(batch[-1][0])
        next_cursor = last_open_time + DAY_MS
        if next_cursor <= cursor:
            raise RuntimeError("Paginação da Binance não avançou")
        cursor = next_cursor

        if len(batch) < KLINES_LIMIT:
            break
        await asyncio.sleep(0.15)

    # Remove duplicatas e o candle diário ainda não encerrado.
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    unique = {int(kline[0]): kline for kline in all_klines if int(kline[6]) <= now_ms}
    return [unique[key] for key in sorted(unique)]


def kline_to_row(kline: list) -> dict:
    """Converte o formato OHLCV da Binance para o modelo Candle."""
    return {
        "asset": SYMBOL,
        "timeframe": TIMEFRAME_LABEL,
        "time": datetime.fromtimestamp(int(kline[0]) / 1000, tz=timezone.utc),
        "open": float(kline[1]),
        "high": float(kline[2]),
        "low": float(kline[3]),
        "close": float(kline[4]),
        "volume": float(kline[5]),
    }


async def upsert_candles(rows: list[dict]) -> None:
    if not rows:
        return
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada; não é possível gravar candles")

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


async def main(days_back: int = DEFAULT_DAYS_BACK) -> None:
    if days_back < 365:
        raise ValueError("Use pelo menos 365 dias para manter um histórico mínimo útil")
    if AsyncSessionLocal is None:
        raise SystemExit("DATABASE_URL não configurada; defina a variável antes de executar o seed.")

    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days_back)
    logger.info("Baixando %d dias de candles para %s (%s)", days_back, SYMBOL, INTERVAL)

    async with httpx.AsyncClient(timeout=30.0) as client:
        klines = await fetch_historical_klines(
            client,
            start_time_ms=int(start.timestamp() * 1000),
            end_time_ms=int(end.timestamp() * 1000),
        )

    rows = [kline_to_row(kline) for kline in klines]
    logger.info("Recebidos %d candles encerrados da Binance", len(rows))
    await upsert_candles(rows)
    logger.info("Seed concluído: %d candles gravados/atualizados em `candles`", len(rows))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baixa candles históricos do BTCUSDT.")
    parser.add_argument("--days-back", type=int, default=DEFAULT_DAYS_BACK)
    args = parser.parse_args()
    asyncio.run(main(days_back=args.days_back))
