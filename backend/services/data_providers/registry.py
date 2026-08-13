"""Catálogo honesto de conectores disponíveis e planejados."""

from __future__ import annotations

from services.data_providers.contracts import ProviderAvailability, ProviderStatus


class StaticProvider:
    def __init__(self, status: ProviderStatus) -> None:
        self.name = status.name
        self._status = status

    async def status(self) -> ProviderStatus:
        return self._status


class ProviderRegistry:
    """Expõe contratos estáveis sem acionar fontes não autorizadas ou não integradas."""

    def __init__(self) -> None:
        self._providers = {
            "binance": StaticProvider(
                ProviderStatus(
                    name="binance",
                    availability=ProviderAvailability.AVAILABLE,
                    detail="Stream e candles BTCUSDT integrados ao worker.",
                    source_url="https://api.binance.com",
                )
            ),
            "bcb": StaticProvider(
                ProviderStatus(
                    name="bcb",
                    availability=ProviderAvailability.AVAILABLE,
                    detail="Série Selic do SGS integrada ao worker.",
                    source_url="https://api.bcb.gov.br",
                )
            ),
            "b3": StaticProvider(ProviderStatus("b3", ProviderAvailability.NOT_AVAILABLE, "Conector B3 ainda não integrado.")),
            "btg_research": StaticProvider(ProviderStatus("btg_research", ProviderAvailability.NOT_AVAILABLE, "Pesquisa pública BTG ainda não integrada ao radar.")),
            "news": StaticProvider(ProviderStatus("news", ProviderAvailability.NOT_AVAILABLE, "Conector de notícias verificadas ainda não integrado.")),
            "whales": StaticProvider(ProviderStatus("whales", ProviderAvailability.NOT_AVAILABLE, "Conector de grandes movimentações on-chain ainda não integrado.")),
        }

    async def statuses(self) -> list[ProviderStatus]:
        return [await provider.status() for provider in self._providers.values()]


provider_registry = ProviderRegistry()
