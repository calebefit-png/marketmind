"""
schemas/candle.py
Schemas Pydantic v2 para serialização de candles, indicadores técnicos e análises.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CandleBase(BaseModel):
    asset: str = Field(..., examples=["BTCUSDT"])
    timeframe: str = Field(..., examples=["1d"])
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class CandleRead(CandleBase):
    model_config = ConfigDict(from_attributes=True)


class CandleCreate(CandleBase):
    pass


class PriceTick(BaseModel):
    """Payload de preço em tempo real transmitido via WebSocket."""

    asset: str
    price: float
    timestamp: datetime
    source: str = "binance"


class TrendEnum(str, Enum):
    ALTA = "ALTA"
    BAIXA = "BAIXA"
    LATERAL = "LATERAL"


class TechnicalIndicators(BaseModel):
    rsi: float | None = None
    sma9: float | None = None
    sma21: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    bb_middle: float | None = None


class AnalysisResponse(BaseModel):
    asset: str
    trend: TrendEnum
    score: int = Field(..., ge=0, le=100)
    indicators: TechnicalIndicators
    explanation: str


class SelicResponse(BaseModel):
    valor_atual: float
    data: str
    valor_anterior: float | None = None
    variacao: float | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    env: str
    version: str
    database: str
