"""Fontes públicas para o ticker de referência do portal.

Nenhum valor é persistido ou inventado nesta camada. Em falhas de fonte, a API
retorna o estado ``unavailable`` e o frontend conserva o aviso explícito.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
import logging
from typing import Any

import httpx

from schemas.reference_tickers import ReferenceTickerQuote, ReferenceTickerSource

logger = logging.getLogger("marketmind.reference_tickers")

PTAX_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

BCB_SOURCE = ReferenceTickerSource(
    id="bcb-ptax",
    name="BCB PTAX",
    source_url="https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/",
    license_note="Cotação de venda PTAX publicada pelo Banco Central do Brasil.",
    update_mode="Publicação oficial em dias úteis.",
    default_delay_seconds=None,
)

YAHOO_SOURCES: dict[str, ReferenceTickerSource] = {
    "IBOV": ReferenceTickerSource(
        id="yahoo-finance-ibov",
        name="Yahoo Finance",
        source_url="https://finance.yahoo.com/quote/%5EBVSP/",
        license_note="Feed público de mercado; pode apresentar atraso conforme a bolsa.",
        update_mode="Atualização conforme o feed público do provedor.",
        default_delay_seconds=None,
    ),
    "IFIX": ReferenceTickerSource(
        id="yahoo-finance-ifix",
        name="Yahoo Finance",
        source_url="https://finance.yahoo.com/quote/IFIX.SA/",
        license_note="Feed público de mercado; pode apresentar atraso conforme a bolsa.",
        update_mode="Atualização conforme o feed público do provedor.",
        default_delay_seconds=None,
    ),
    "BRENT": ReferenceTickerSource(
        id="yahoo-finance-brent",
        name="Yahoo Finance",
        source_url="https://finance.yahoo.com/quote/BZ%3DF/",
        license_note="Contrato futuro de Brent no feed público; pode apresentar atraso.",
        update_mode="Atualização conforme o feed público do provedor.",
        default_delay_seconds=None,
    ),
}

YAHOO_REFERENCES = (
    ("IBOV", "IBOV", "^BVSP"),
    ("IFIX", "IFIX", "IFIX.SA"),
    ("BRENT", "BRENT", "BZ=F"),
)


class ReferenceTickerService:
    """Agregador assíncrono de referências, com falha isolada por indicador."""

    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout

    @staticmethod
    def _unavailable(symbol: str, label: str, source: ReferenceTickerSource) -> ReferenceTickerQuote:
        return ReferenceTickerQuote(
            symbol=symbol,
            label=label,
            received_at=datetime.now(tz=timezone.utc),
            data_status="unavailable",
            source=source,
        )

    @staticmethod
    def parse_ptax(record: dict[str, Any]) -> tuple[float, datetime]:
        value = float(record["cotacaoVenda"])
        as_of = datetime.fromisoformat(str(record["dataHoraCotacao"]))
        return value, as_of

    @staticmethod
    def ptax_params(reference_date: date) -> dict[str, str]:
        """Monta a consulta OData com a data entre aspas exigida pelo BCB."""
        return {
            "@dataCotacao": f"'{reference_date.strftime('%m-%d-%Y')}'",
            "$top": "100",
            "$format": "json",
        }

    @staticmethod
    def parse_yahoo(payload: dict[str, Any]) -> tuple[float, float | None, str, datetime | None]:
        result = payload.get("chart", {}).get("result") or []
        if not result:
            raise ValueError("Resposta sem resultado do feed de mercado")
        meta = result[0].get("meta") or {}
        value = float(meta["regularMarketPrice"])
        previous = meta.get("chartPreviousClose")
        previous_close = float(previous) if previous not in (None, 0) else None
        raw_time = meta.get("regularMarketTime")
        as_of = datetime.fromtimestamp(int(raw_time), tz=timezone.utc) if raw_time else None
        return value, previous_close, str(meta.get("currency") or ""), as_of

    async def _fetch_ptax(self, client: httpx.AsyncClient) -> ReferenceTickerQuote:
        for offset in range(0, 8):
            refdate = date.today() - timedelta(days=offset)
            response = await client.get(PTAX_URL, params=self.ptax_params(refdate))
            response.raise_for_status()
            records = response.json().get("value") or []
            if records:
                value, as_of = self.parse_ptax(records[-1])
                return ReferenceTickerQuote(
                    symbol="USD/BRL",
                    label="USD",
                    value=value,
                    currency="BRL",
                    as_of=as_of,
                    received_at=datetime.now(tz=timezone.utc),
                    data_status="closing",
                    source=BCB_SOURCE,
                )
        raise ValueError("PTAX não disponível nos últimos sete dias")

    async def _fetch_yahoo(
        self,
        client: httpx.AsyncClient,
        label: str,
        symbol: str,
    ) -> ReferenceTickerQuote:
        response = await client.get(
            YAHOO_CHART_URL.format(symbol=symbol),
            params={"range": "5d", "interval": "1d"},
        )
        response.raise_for_status()
        value, previous_close, currency, as_of = self.parse_yahoo(response.json())
        change_percent = None
        if previous_close:
            change_percent = ((value / previous_close) - 1) * 100
        return ReferenceTickerQuote(
            symbol=label,
            label=label,
            value=value,
            previous_close=previous_close,
            change_percent=change_percent,
            currency=currency,
            as_of=as_of,
            received_at=datetime.now(tz=timezone.utc),
            data_status="delayed",
            source=YAHOO_SOURCES[label],
        )

    async def get_tickers(self) -> list[ReferenceTickerQuote]:
        headers = {"Accept": "application/json", "User-Agent": "MarketMind/1.0 (public-data)"}
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            tasks = [self._fetch_ptax(client)] + [
                self._fetch_yahoo(client, label, symbol) for label, _name, symbol in YAHOO_REFERENCES
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        fallbacks: list[tuple[str, str, ReferenceTickerSource]] = [
            ("USD/BRL", "USD", BCB_SOURCE),
            *( (label, label, YAHOO_SOURCES[label]) for label, _name, _symbol in YAHOO_REFERENCES ),
        ]
        quotes: list[ReferenceTickerQuote] = []
        for result, (symbol, label, source) in zip(results, fallbacks, strict=True):
            if isinstance(result, Exception):
                logger.warning("Indicador %s indisponível: %s", label, type(result).__name__)
                quotes.append(self._unavailable(symbol, label, source))
            else:
                quotes.append(result)
        return quotes


reference_ticker_service = ReferenceTickerService()
