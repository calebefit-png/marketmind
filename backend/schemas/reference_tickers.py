"""Contratos públicos para indicadores de referência com proveniência explícita."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReferenceTickerSource(BaseModel):
    id: str
    name: str
    source_url: str
    license_note: str
    update_mode: str
    default_delay_seconds: int | None = None


class ReferenceTickerQuote(BaseModel):
    symbol: str
    label: str
    value: float | None = None
    previous_close: float | None = None
    change_percent: float | None = None
    currency: str | None = None
    as_of: datetime | None = None
    received_at: datetime
    data_status: str
    source: ReferenceTickerSource


class ReferenceTickerResponse(BaseModel):
    items: list[ReferenceTickerQuote]
