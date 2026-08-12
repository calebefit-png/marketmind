"""
api/routes/market.py
Rotas HTTP de mercado: preço BTC em tempo real, Selic, e análise técnica.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.candle import Candle
from schemas.candle import AnalysisResponse, PriceTick, SelicResponse
from services.bcb_service import bcb_service
from services.binance_stream import binance_stream_service
from services.technical_analysis import candles_to_dataframe, compute_indicators
from services.trend_engine import classify_trend

logger = logging.getLogger("marketmind.routes.market")

router = APIRouter(tags=["market"])


@router.get("/market/btc", response_model=PriceTick)
async def get_btc_price() -> PriceTick:
    """
    Retorna o último preço de BTCUSDT recebido pelo stream da Binance.
    Se o stream ainda não tiver recebido nenhum tick, busca via REST como fallback.
    """
    price = binance_stream_service.last_price

    if price is None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.BINANCE_REST_URL}/ticker/price",
                    params={"symbol": "BTCUSDT"},
                )
                response.raise_for_status()
                data = response.json()
                price = float(data["price"])
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            logger.warning("Binance REST indisponível: %s", type(exc).__name__)
            raise HTTPException(
                status_code=503,
                detail="Cotação BTC indisponível no momento.",
            ) from exc

    return PriceTick(
        asset="BTCUSDT",
        price=price,
        timestamp=datetime.now(tz=timezone.utc),
        source="binance",
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
