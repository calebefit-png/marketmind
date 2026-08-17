"""
api/routes/market.py
Rotas HTTP de mercado: preço BTC em tempo real, Selic, e análise técnica.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candle import Candle
from models.market_data import DataSource, MarketAsset, MarketCandle
from schemas.candle import AnalysisResponse, PriceTick, SelicResponse
from schemas.market_data import (
    DataSourceRead,
    MarketAssetDetailResponse,
    MarketAssetListResponse,
    MarketAssetRead,
    MarketCandleRead,
    MarketHistoryResponse,
    MarketQuoteRead,
)
from services.bcb_service import bcb_service
from services.binance_stream import binance_stream_service
from services.technical_analysis import candles_to_dataframe, compute_indicators
from services.trend_engine import classify_trend

logger = logging.getLogger("marketmind.routes.market")

router = APIRouter(tags=["market"])


def _asset_read(asset: MarketAsset, quote: MarketQuoteRead | None = None) -> MarketAssetRead:
    return MarketAssetRead(
        symbol=asset.symbol,
        exchange=asset.exchange,
        asset_class=asset.asset_class,
        name=asset.name,
        specification=asset.specification,
        currency=asset.currency,
        active=asset.active,
        listed_at=asset.listed_at.isoformat() if asset.listed_at else None,
        delisted_at=asset.delisted_at.isoformat() if asset.delisted_at else None,
        quote=quote,
    )


def _source_read(source: DataSource | None) -> DataSourceRead | None:
    if source is None:
        return None
    return DataSourceRead(
        id=source.id,
        name=source.name,
        source_url=source.source_url,
        license_note=source.license_note,
        update_mode=source.update_mode,
        default_delay_seconds=source.default_delay_seconds,
    )


async def _latest_closing_quote(db: AsyncSession, asset: MarketAsset) -> MarketQuoteRead:
    """Obtém o último fechamento e sua variação, sempre com estado e fonte."""
    candle_result = await db.execute(
        select(MarketCandle, DataSource)
        .join(DataSource, DataSource.id == MarketCandle.source_id)
        .where(MarketCandle.asset_id == asset.id, MarketCandle.timeframe == "1d")
        .order_by(MarketCandle.time.desc())
        .limit(2)
    )
    rows = candle_result.all()
    if not rows:
        return MarketQuoteRead(data_status="unavailable")

    latest, source = rows[0]
    previous_close = rows[1][0].close if len(rows) > 1 else None
    change_percent = None
    if previous_close and previous_close != 0:
        change_percent = ((latest.close / previous_close) - 1) * 100
    return MarketQuoteRead(
        value=latest.close,
        previous_close=previous_close,
        change_percent=change_percent,
        as_of=latest.as_of,
        received_at=latest.received_at,
        data_status=latest.data_status,
        source=_source_read(source),
    )


async def _b3_asset_or_404(db: AsyncSession, symbol: str) -> MarketAsset:
    result = await db.execute(
        select(MarketAsset).where(
            MarketAsset.symbol == symbol.upper(),
            MarketAsset.exchange == "B3",
        )
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Ativo ainda não foi carregado de uma fonte verificável. Sincronize seu histórico primeiro.",
        )
    return asset


@router.get("/market/btc", response_model=PriceTick)
async def get_btc_price() -> PriceTick:
    """
    Retorna o último preço de BTCUSDT recebido pelo stream da Binance.
    Se o stream ainda não tiver recebido nenhum tick, busca via REST como fallback.
    """
    price = binance_stream_service.last_price

    if price is None:
        try:
            tick = await binance_stream_service.fetch_rest_tick()
            price = float(tick["price"])
        except RuntimeError as exc:
            logger.warning("Fallback REST da Binance indisponível: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Cotação BTC indisponível no momento.",
            ) from exc

    last_tick = binance_stream_service.last_tick or {}
    return PriceTick(
        asset="BTCUSDT",
        price=price,
        timestamp=datetime.now(tz=timezone.utc),
        source=last_tick.get("source", "binance"),
    )


@router.get("/macro/selic", response_model=SelicResponse)
async def get_selic() -> SelicResponse:
    """Retorna a taxa Selic atual, data de referência e variação, via API do BCB."""
    try:
        return await bcb_service.get_selic()
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.warning("Falha ao buscar Selic no BCB: %s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar a Selic no BCB.",
        ) from exc


@router.get("/market/assets", response_model=MarketAssetListResponse)
async def list_market_assets(
    query: str | None = None,
    asset_class: str | None = None,
    exchange: str | None = "B3",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> MarketAssetListResponse:
    """Lista ativos já carregados de fontes verificáveis."""
    if not 1 <= limit <= 200:
        raise HTTPException(status_code=422, detail="limit deve estar entre 1 e 200")
    stmt = select(MarketAsset)
    count_stmt = select(func.count()).select_from(MarketAsset)
    filters = []
    if exchange:
        filters.append(MarketAsset.exchange == exchange.upper())
    if asset_class:
        filters.append(MarketAsset.asset_class == asset_class.lower())
    if query:
        normalized = f"%{query.strip().upper()}%"
        filters.append(
            (func.upper(MarketAsset.symbol).like(normalized))
            | (func.upper(func.coalesce(MarketAsset.name, "")).like(normalized))
        )
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
    try:
        result = await db.execute(stmt.order_by(MarketAsset.symbol).limit(limit))
        total_result = await db.execute(count_stmt)
        assets = result.scalars().all()
        items = [
            _asset_read(asset, await _latest_closing_quote(db, asset))
            for asset in assets
        ]
    except SQLAlchemyError as exc:
        logger.exception("Falha ao listar catálogo de ativos")
        raise HTTPException(status_code=503, detail="Catálogo de mercado indisponível no momento.") from exc
    return MarketAssetListResponse(
        items=items,
        total=int(total_result.scalar_one()),
    )


@router.get("/market/assets/{symbol}", response_model=MarketAssetDetailResponse)
async def get_market_asset(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> MarketAssetDetailResponse:
    """Retorna o último fechamento conhecido, sem rotulá-lo como dado ao vivo."""
    asset = await _b3_asset_or_404(db, symbol)
    try:
        quote = await _latest_closing_quote(db, asset)
    except SQLAlchemyError as exc:
        logger.exception("Falha ao consultar detalhe de %s", asset.symbol)
        raise HTTPException(status_code=503, detail="Série do ativo indisponível no momento.") from exc
    return MarketAssetDetailResponse(asset=_asset_read(asset), quote=quote)


@router.get("/market/assets/{symbol}/history", response_model=MarketHistoryResponse)
async def get_market_history(
    symbol: str,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 5000,
    db: AsyncSession = Depends(get_db),
) -> MarketHistoryResponse:
    """Retorna uma série diária histórica para gráficos e análise com fonte explícita."""
    if not 1 <= limit <= 5000:
        raise HTTPException(status_code=422, detail="limit deve estar entre 1 e 5000")
    if start and end and end < start:
        raise HTTPException(status_code=422, detail="end não pode ser anterior a start")
    asset = await _b3_asset_or_404(db, symbol)
    stmt = (
        select(MarketCandle, DataSource)
        .join(DataSource, DataSource.id == MarketCandle.source_id)
        .where(MarketCandle.asset_id == asset.id, MarketCandle.timeframe == "1d")
        .order_by(MarketCandle.time.asc())
        .limit(limit + 1)
    )
    if start:
        stmt = stmt.where(MarketCandle.time >= start)
    if end:
        stmt = stmt.where(MarketCandle.time <= end)
    try:
        result = await db.execute(stmt)
    except SQLAlchemyError as exc:
        logger.exception("Falha ao consultar histórico de %s", asset.symbol)
        raise HTTPException(status_code=503, detail="Histórico do ativo indisponível no momento.") from exc
    rows = result.all()
    truncated = len(rows) > limit
    rows = rows[:limit]
    source = rows[-1][1] if rows else None
    points = [
        MarketCandleRead(
            time=candle.time,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
            trades=candle.trades,
            data_status=candle.data_status,
            as_of=candle.as_of,
            received_at=candle.received_at,
        )
        for candle, _ in rows
    ]
    return MarketHistoryResponse(
        asset=_asset_read(asset),
        requested_start=start,
        requested_end=end,
        points=points,
        source=_source_read(source),
        truncated=truncated,
    )


@router.get("/analysis/btc", response_model=AnalysisResponse)
async def get_btc_analysis(db: AsyncSession = Depends(get_db)) -> AnalysisResponse:
    """
    Calcula indicadores técnicos e classifica a tendência do BTCUSDT
    com base no histórico de candles diários armazenado no banco.
    """
    stmt = (
        select(Candle)
        .where(Candle.asset == "BTCUSDT", Candle.timeframe == "1d")
        .order_by(Candle.time.desc())
        .limit(60)
    )
    try:
        result = await db.execute(stmt)
    except SQLAlchemyError as exc:
        logger.exception("Falha ao consultar candles de BTC")
        raise HTTPException(
            status_code=503,
            detail="Histórico de mercado indisponível no momento.",
        ) from exc

    rows = list(reversed(result.scalars().all()))

    if len(rows) < 21:
        raise HTTPException(
            status_code=422,
            detail=(
                "Histórico insuficiente de candles para análise técnica. "
                "Rode o script seed_btc_history.py primeiro."
            ),
        )

    candles = [
        {
            "time": row.time,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
        }
        for row in rows
    ]

    df = candles_to_dataframe(candles)
    indicators = compute_indicators(df)
    return classify_trend(indicators, asset="BTCUSDT")
