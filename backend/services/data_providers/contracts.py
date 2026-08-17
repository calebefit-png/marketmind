"""Interface comum e estados explícitos para conectores de dados."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, Sequence


class ProviderAvailability(StrEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    DEGRADED = "degraded"


class DataStatus(StrEnum):
    """Estado que a interface deve exibir sem tentar inferir tempo real."""

    LIVE = "live"
    DELAYED = "delayed"
    CLOSING = "closing"
    REGULATORY = "regulatory"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    availability: ProviderAvailability
    detail: str
    source_url: str | None = None


@dataclass(frozen=True)
class AssetIdentity:
    symbol: str
    exchange: str
    asset_class: str = "unclassified"
    name: str | None = None
    specification: str | None = None
    currency: str = "BRL"


@dataclass(frozen=True)
class QuotePoint:
    asset: AssetIdentity
    value: float | None
    as_of: datetime | None
    received_at: datetime
    data_status: DataStatus
    source_id: str


@dataclass(frozen=True)
class CandlePoint:
    asset: AssetIdentity
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int | None
    data_status: DataStatus
    as_of: datetime
    received_at: datetime
    source_id: str
    source_record_hash: str | None = None


class DataProvider(Protocol):
    """Contrato de baixo acoplamento para fontes atuais e futuras."""

    name: str

    async def status(self) -> ProviderStatus: ...


class HistoricalProvider(DataProvider, Protocol):
    """Contrato para downloads paginados ou arquivos históricos oficiais."""

    async def candles(
        self,
        *,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
    ) -> list[CandlePoint]: ...
