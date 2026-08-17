"""Persistência idempotente de catálogo, fontes e candles com proveniência."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database import AsyncSessionLocal
from models.market_data import DataSource, IngestionRun, MarketAsset, MarketCandle
from services.data_providers.b3_cotahist import (
    B3_COTAHIST_LICENSE_NOTE,
    B3_COTAHIST_SOURCE_ID,
    B3_COTAHIST_SOURCE_URL,
)
from services.data_providers.contracts import CandlePoint


async def ensure_b3_source() -> None:
    """Registra a proveniência da B3 de forma repetível."""
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada")
    now = datetime.now(tz=timezone.utc)
    async with AsyncSessionLocal() as session:
        stmt = pg_insert(DataSource).values(
            id=B3_COTAHIST_SOURCE_ID,
            name="B3 COTAHIST",
            source_url=B3_COTAHIST_SOURCE_URL,
            license_note=B3_COTAHIST_LICENSE_NOTE,
            update_mode="published_file",
            default_delay_seconds=None,
            enabled=True,
            last_checked_at=now,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "source_url": stmt.excluded.source_url,
                "license_note": stmt.excluded.license_note,
                "update_mode": stmt.excluded.update_mode,
                "last_checked_at": stmt.excluded.last_checked_at,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await session.execute(stmt)
        await session.commit()


async def _asset_id(session, point: CandlePoint) -> int:
    result = await session.execute(
        select(MarketAsset).where(
            MarketAsset.symbol == point.asset.symbol,
            MarketAsset.exchange == point.asset.exchange,
        )
    )
    asset = result.scalar_one_or_none()
    now = datetime.now(tz=timezone.utc)
    if asset is None:
        asset = MarketAsset(
            symbol=point.asset.symbol,
            exchange=point.asset.exchange,
            asset_class=point.asset.asset_class,
            name=point.asset.name,
            specification=point.asset.specification,
            currency=point.asset.currency,
            active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(asset)
        await session.flush()
        return asset.id

    asset.asset_class = point.asset.asset_class
    asset.name = point.asset.name or asset.name
    asset.specification = point.asset.specification or asset.specification
    asset.currency = point.asset.currency or asset.currency
    asset.updated_at = now
    return asset.id


async def upsert_candles(points: list[CandlePoint]) -> int:
    """Grava candles em lotes sem duplicar pontos já carregados."""
    if not points:
        return 0
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada")

    rows: list[dict] = []
    async with AsyncSessionLocal() as session:
        asset_ids: dict[tuple[str, str], int] = {}
        for point in points:
            key = (point.asset.symbol, point.asset.exchange)
            if key not in asset_ids:
                asset_ids[key] = await _asset_id(session, point)
            rows.append(
                {
                    "asset_id": asset_ids[key],
                    "timeframe": point.timeframe,
                    "time": point.time,
                    "source_id": point.source_id,
                    "open": point.open,
                    "high": point.high,
                    "low": point.low,
                    "close": point.close,
                    "volume": point.volume,
                    "trades": point.trades,
                    "data_status": point.data_status.value,
                    "as_of": point.as_of,
                    "received_at": point.received_at,
                    "source_record_hash": point.source_record_hash,
                }
            )

        stmt = pg_insert(MarketCandle).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["asset_id", "timeframe", "time", "source_id"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "trades": stmt.excluded.trades,
                "data_status": stmt.excluded.data_status,
                "as_of": stmt.excluded.as_of,
                "received_at": stmt.excluded.received_at,
                "source_record_hash": stmt.excluded.source_record_hash,
            },
        )
        await session.execute(stmt)
        await session.commit()
    return len(rows)


async def start_ingestion_run(*, source_id: str, job_name: str, requested_scope: str) -> int:
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada")
    async with AsyncSessionLocal() as session:
        run = IngestionRun(
            source_id=source_id,
            job_name=job_name,
            requested_scope=requested_scope,
            status="running",
            started_at=datetime.now(tz=timezone.utc),
            records_seen=0,
            records_written=0,
        )
        session.add(run)
        await session.commit()
        return run.id


async def finish_ingestion_run(
    run_id: int,
    *,
    status: str,
    records_seen: int,
    records_written: int,
    error_summary: str | None = None,
) -> None:
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada")
    async with AsyncSessionLocal() as session:
        run = await session.get(IngestionRun, run_id)
        if run is None:
            return
        run.status = status
        run.finished_at = datetime.now(tz=timezone.utc)
        run.records_seen = records_seen
        run.records_written = records_written
        run.error_summary = error_summary
        await session.commit()
