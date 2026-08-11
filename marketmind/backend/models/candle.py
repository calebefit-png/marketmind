"""
models/candle.py
Modelo ORM da tabela `candles`, convertida em hypertable do TimescaleDB.
Chave primária composta (asset, timeframe, time) para permitir particionamento eficiente.
"""

from datetime import datetime

from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Candle(Base):
    __tablename__ = "candles"

    asset: Mapped[str] = mapped_column(String(20), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(10), primary_key=True)
    time: Mapped[datetime] = mapped_column(primary_key=True)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("ix_candles_asset_timeframe_time", "asset", "timeframe", "time"),
    )

    def __repr__(self) -> str:
        return f"<Candle {self.asset} {self.timeframe} {self.time} close={self.close}>"
