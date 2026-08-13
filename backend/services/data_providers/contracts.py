"""Interface comum e estados explícitos para conectores de dados."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ProviderAvailability(StrEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    availability: ProviderAvailability
    detail: str
    source_url: str | None = None


class DataProvider(Protocol):
    """Contrato de baixo acoplamento para fontes atuais e futuras."""

    name: str

    async def status(self) -> ProviderStatus: ...
