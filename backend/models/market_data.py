"""Modelos normalizados para catálogo, proveniência e séries de mercado."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class DataSource(Base):
    """Cadastro público de origem, licença e comportamento de atualização."""

    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    license_note: Mapped[str] = mapped_column(Text, nullable=False)
    update_mode: Mapped[str] = mapped_column(String(24), nullable=False)
    default_delay_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketAsset(Base):
    """Ativo canônico sem inferir uma classe financeira que a fonte não confirmou."""

    __tablename__ = "market_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False)
    exchange: Mapped[str] = mapped_column(String(40), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(40), nullable=False, default="unclassified")
    name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    specification: Mapped[str | None] = mapped_column(String(80), nullable=True)
    currency: Mapped[str] = mapped_column(String(12), nullable=False, default="BRL")
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    listed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    delisted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "exchange", name="uq_market_assets_symbol_exchange"),
        Index("ix_market_assets_class_exchange", "asset_class", "exchange"),
    )


class MarketCandle(Base):
    """OHLCV com estado e proveniência suficientes para auditoria de cada ponto."""

    __tablename__ = "market_candles"

    asset_id: Mapped[int] = mapped_column(ForeignKey("market_assets.id", ondelete="CASCADE"), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(12), primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_status: Mapped[str] = mapped_column(String(20), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_record_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_market_candles_asset_timeframe_time", "asset_id", "timeframe", "time"),
        Index("ix_market_candles_source_time", "source_id", "time"),
    )


class IngestionRun(Base):
    """Auditoria de cada carga: fonte, escopo, volume, checksum e erro resumido."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    job_name: Mapped[str] = mapped_column(String(120), nullable=False)
    requested_scope: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_ingestion_runs_source_started", "source_id", "started_at"),)
