"""Normalização de códigos monetários recebidos de fontes de mercado."""

from __future__ import annotations


_CURRENCY_ALIASES = {"R$": "BRL", "US$": "USD"}


def normalize_currency_code(currency: str | None, fallback: str = "BRL") -> str:
    """Retorna um código ISO 4217, incluindo marcadores históricos do COTAHIST."""
    normalized = (currency or "").strip().upper()
    resolved = _CURRENCY_ALIASES.get(normalized, normalized)
    return resolved if len(resolved) == 3 and resolved.isalpha() else fallback
