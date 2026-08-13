"""Engine assíncrono e ciclo de vida do PostgreSQL/TimescaleDB."""

from collections.abc import AsyncGenerator
import asyncio
import logging

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger("marketmind.database")


class Base(DeclarativeBase):
    """Base declarativa para os models ORM."""


engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None
DB_HEALTH_TIMEOUT_SECONDS = 5
DB_INIT_TIMEOUT_SECONDS = 10


def _async_database_url(url: str) -> str:
    """Normalize Render/PostgreSQL URLs for SQLAlchemy's psycopg3 async dialect."""
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized.removeprefix("postgres://")
    if normalized.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + normalized.removeprefix("postgresql+psycopg2://")
    if normalized.startswith("postgresql://"):
        return "postgresql+psycopg://" + normalized.removeprefix("postgresql://")
    return normalized


if settings.DATABASE_URL:
    engine = create_async_engine(
        _async_database_url(settings.DATABASE_URL),
        echo=settings.APP_DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
else:
    logger.warning("DATABASE_URL não configurada; rotas de banco ficarão indisponíveis")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI para uma sessão de banco por requisição."""
    if AsyncSessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados não configurado; defina DATABASE_URL no ambiente.",
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_database() -> tuple[bool, str]:
    """Executa um ping sem registrar a URL ou qualquer credencial."""
    if engine is None:
        return False, "not_configured"

    async def ping() -> None:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    try:
        await asyncio.wait_for(ping(), timeout=DB_HEALTH_TIMEOUT_SECONDS)
        return True, "connected"
    except (SQLAlchemyError, TimeoutError) as exc:
        logger.warning("Healthcheck do PostgreSQL indisponível (%s)", type(exc).__name__)
        return False, "unavailable"


async def init_db() -> bool:
    """Cria tabelas básicas quando o banco está configurado."""
    if engine is None:
        return False

    # Importações tardias evitam ciclos entre database e os modelos ORM.
    from models.candle import Candle  # noqa: F401
    from models.alert import AlertDelivery, AlertEvent, AlertPreference, AlertState  # noqa: F401

    async def create_tables() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    try:
        await asyncio.wait_for(create_tables(), timeout=DB_INIT_TIMEOUT_SECONDS)
        logger.info("Banco inicializado; tabelas presentes: %s", list(Base.metadata.tables))
        return True
    except (SQLAlchemyError, TimeoutError) as exc:
        logger.warning("Falha ao inicializar tabelas do banco (%s)", type(exc).__name__)
        return False


async def dispose_db() -> None:
    if engine is not None:
        await engine.dispose()
