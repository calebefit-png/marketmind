"""Utilitários puros para escrita escalável de dados de mercado."""

from __future__ import annotations

from typing import TypeVar


T = TypeVar("T")

# PostgreSQL aceita no máximo 65.535 parâmetros por statement. Cada candle
# utiliza 14 colunas nesta inserção; 2.000 linhas mantêm ampla folga.
MARKET_CANDLE_UPSERT_BATCH_SIZE = 2_000


def batches(items: list[T], batch_size: int = MARKET_CANDLE_UPSERT_BATCH_SIZE) -> list[list[T]]:
    """Divide uma lista em grupos determinísticos com tamanho seguro."""
    if batch_size < 1:
        raise ValueError("batch_size deve ser positivo")
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]
