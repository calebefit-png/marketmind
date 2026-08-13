"""Modelos persistentes do pipeline de alertas e entregas."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class AlertEvent(Base):
    """Um cenário relevante reservado pelo motor de alertas."""

    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scope_key: Mapped[str] = mapped_column(String(80), nullable=False, default="owner", index=True)
    dedup_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    asset: Mapped[str] = mapped_column(String(32), nullable=False, default="MARKET")
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    message_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # O canal principal mantém o histórico legível; entregas detalhadas ficam em AlertDelivery.
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default="telegram")
    cooldown_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    deliveries: Mapped[list["AlertDelivery"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alert_events_scope_asset_created", "scope_key", "asset", "created_at"),
    )


class AlertState(Base):
    """Estado de cooldown, em chave única, preservado entre reinicializações."""

    __tablename__ = "alert_states"

    dedup_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    last_emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_message_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    cooldown_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class AlertDelivery(Base):
    """Tentativa de entrega por canal, sem registrar credenciais ou destinatários."""

    __tablename__ = "alert_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    alert_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("alert_events.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alert: Mapped[AlertEvent] = relationship(back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("alert_id", "channel", name="uq_alert_delivery_alert_channel"),
        Index("ix_alert_deliveries_channel_status_created", "channel", "status", "created_at"),
    )


class AlertPreference(Base):
    """Preferências não sensíveis de um perfil; os destinos permanecem no ambiente seguro."""

    __tablename__ = "alert_preferences"

    scope_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    assets: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    minimum_severity: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=1800)
    paused: Mapped[bool] = mapped_column(nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class WorkerHeartbeat(Base):
    """Estado operacional persistente de cada processo de monitoramento."""

    __tablename__ = "worker_heartbeats"

    worker_name: Mapped[str] = mapped_column(String(80), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="offline")
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(160), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
