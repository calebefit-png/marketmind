"""
database.py
Engine e sessão assíncrona do SQLAlchemy 2.0 para PostgreSQL/TimescaleDB.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os models ORM."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI para injetar uma sessão de banco por requisição."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Cria as tabelas no banco (usado em dev; produção usa Alembic/migrations SQL)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
