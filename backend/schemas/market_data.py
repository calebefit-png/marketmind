"""Contratos públicos para ativos, fontes e séries com proveniência."""

from datetime import datetime

from pydantic import BaseModel, Field


class DataSourceRead(BaseModel):
    id: str
    name: str
    source_url: str
    license_note: str
    update_mode: str
    default_delay_seconds: int | None = None


class MarketQuoteRead(BaseModel):
    value: float | None = None
    previous_close: float | None = None
    change_percent: float | None = None
    as_of: datetime | None = None
    received_at: datetime | None = None
    data_status: str
    source: DataSourceRead | None = None


class MarketAssetRead(BaseModel):
    symbol: str
    exchange: str
    asset_class: str
    name: str | None = None
    specification: str | None = None
    currency: str
    active: bool
    listed_at: str | None = None
    delisted_at: str | None = None
    quote: MarketQuoteRead | None = None


class MarketAssetListResponse(BaseModel):
    items: list[MarketAssetRead]
    total: int
    source_note: str = "O catálogo é formado somente por ativos já carregados de fontes verificáveis."


class MarketCandleRead(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int | None = None
    data_status: str
    as_of: datetime
    received_at: datetime


class MarketAssetDetailResponse(BaseModel):
    asset: MarketAssetRead
    quote: MarketQuoteRead


class MarketHistoryResponse(BaseModel):
    asset: MarketAssetRead
    timeframe: str = "1d"
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    points: list[MarketCandleRead]
    source: DataSourceRead | None = None
    truncated: bool = False
    note: str = Field(
        default="Fechamentos B3 publicados são históricos; não representam cotação em tempo real.",
    )
