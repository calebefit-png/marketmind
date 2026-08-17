"""Carga seletiva e idempotente de até quinze anos do COTAHIST da B3.

Exemplo:
    python -m scripts.sync_b3_history --symbols PETR4,VALE3,HGLG11
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402
from database import AsyncSessionLocal, init_db  # noqa: E402
from services.data_providers.b3_cotahist import B3_COTAHIST_SOURCE_ID, B3CotahistProvider  # noqa: E402
from services.market_data_store import (  # noqa: E402
    ensure_b3_source,
    finish_ingestion_run,
    start_ingestion_run,
    upsert_candles,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("marketmind.sync_b3")


async def main(symbols: list[str], years: int) -> None:
    if AsyncSessionLocal is None:
        raise SystemExit("DATABASE_URL não configurada; não é possível gravar o histórico.")
    if years < 1 or years > 15:
        raise ValueError("O modo gratuito permite entre 1 e 15 anos por execução.")

    initialized = await init_db()
    if not initialized:
        raise RuntimeError("Não foi possível inicializar as tabelas de dados de mercado.")
    await ensure_b3_source()

    normalized = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})
    if not normalized:
        raise ValueError("Informe pelo menos um ticker B3.")

    scope = f"symbols={','.join(normalized)};years={years}"
    run_id = await start_ingestion_run(
        source_id=B3_COTAHIST_SOURCE_ID,
        job_name="sync_b3_history",
        requested_scope=scope,
    )
    now = datetime.now(tz=timezone.utc)
    start = now.replace(year=now.year - years)
    try:
        provider = B3CotahistProvider()
        points = await provider.candles(symbols=normalized, start=start, end=now)
        written = await upsert_candles(points)
    except Exception as exc:
        await finish_ingestion_run(
            run_id,
            status="failed",
            records_seen=0,
            records_written=0,
            error_summary=f"{type(exc).__name__}: {exc}",
        )
        raise
    else:
        await finish_ingestion_run(
            run_id,
            status="completed",
            records_seen=len(points),
            records_written=written,
        )
        logger.info("Carga B3 concluída: %d registros para %s", written, ", ".join(normalized))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza histórico COTAHIST selecionado da B3.")
    parser.add_argument(
        "--symbols",
        default=",".join(settings.market_data_b3_watchlist),
        help="Tickers B3 separados por vírgula; por padrão usa a lista gratuita configurada.",
    )
    parser.add_argument("--years", type=int, default=settings.MARKET_DATA_DEFAULT_LOOKBACK_YEARS)
    args = parser.parse_args()
    asyncio.run(main(args.symbols.split(","), args.years))
