"""Leitor do COTAHIST da B3 para séries diárias oficiais de fechamento.

O arquivo COTAHIST é histórico publicado pela B3. Ele não deve ser usado nem
rotulado como feed de cotação em tempo real.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import TextIOWrapper
from pathlib import Path
import tempfile
from typing import Iterable
import zipfile

import httpx

from config import settings
from services.data_providers.contracts import (
    AssetIdentity,
    CandlePoint,
    DataStatus,
    ProviderAvailability,
    ProviderStatus,
)


B3_COTAHIST_SOURCE_ID = "b3_cotahist"
B3_COTAHIST_SOURCE_URL = "https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/"
B3_COTAHIST_LICENSE_NOTE = (
    "Arquivo histórico público da B3. Representa preços oficiais de fechamento "
    "publicados e não equivale a cotação em tempo real."
)


def _decimal_cents(raw: str) -> float:
    """Converte número fixo da B3, expresso com duas casas implícitas."""
    value = raw.strip()
    if not value:
        return 0.0
    return int(value) / 100


def _asset_class(symbol: str, specification: str) -> str:
    """Classificação prudente, usada apenas para a navegação; não altera o dado B3."""
    spec = specification.upper()
    if "FII" in spec:
        return "fii"
    if "ETF" in spec:
        return "etf"
    if "BDR" in spec:
        return "bdr"
    if symbol.endswith("11"):
        return "fund_or_etf"
    return "stock"


def parse_cotahist_lines(lines: Iterable[str], symbols: set[str]) -> list[CandlePoint]:
    """Extrai somente ações do mercado à vista e os símbolos solicitados.

    O layout de largura fixa segue a especificação pública do arquivo COTAHIST.
    Linhas de cabeçalho, trailer e instrumentos fora do mercado à vista são
    ignoradas deliberadamente.
    """
    received_at = datetime.now(tz=timezone.utc)
    points: list[CandlePoint] = []

    for line in lines:
        if len(line) < 188 or line[:2] != "01":
            continue
        symbol = line[12:24].strip().upper()
        market_type = line[24:27]
        if symbol not in symbols or market_type != "010":
            continue

        try:
            time = datetime.strptime(line[2:10], "%Y%m%d").replace(tzinfo=timezone.utc)
            name = line[27:39].strip() or None
            specification = line[39:49].strip() or None
            currency = line[52:56].strip() or "BRL"
            open_price = _decimal_cents(line[56:69])
            high_price = _decimal_cents(line[69:82])
            low_price = _decimal_cents(line[82:95])
            close_price = _decimal_cents(line[108:121])
            if min(open_price, high_price, low_price, close_price) <= 0:
                continue
            trades = int(line[147:152].strip() or "0")
            volume = _decimal_cents(line[170:188])
        except (ValueError, IndexError):
            continue

        source_hash = sha256(line.encode("latin-1", errors="ignore")).hexdigest()
        points.append(
            CandlePoint(
                asset=AssetIdentity(
                    symbol=symbol,
                    exchange="B3",
                    asset_class=_asset_class(symbol, specification or ""),
                    name=name,
                    specification=specification,
                    currency=currency,
                ),
                timeframe="1d",
                time=time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                trades=trades or None,
                data_status=DataStatus.CLOSING,
                as_of=time,
                received_at=received_at,
                source_id=B3_COTAHIST_SOURCE_ID,
                source_record_hash=source_hash,
            )
        )
    return points


class B3CotahistProvider:
    """Consulta arquivos anuais COTAHIST e devolve candles de fechamento."""

    name = B3_COTAHIST_SOURCE_ID

    async def status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            availability=ProviderAvailability.AVAILABLE,
            detail="Histórico diário publicado; não é uma fonte de preço B3 ao vivo.",
            source_url=B3_COTAHIST_SOURCE_URL,
        )

    async def _year_points(
        self,
        client: httpx.AsyncClient,
        year: int,
        symbols: set[str],
    ) -> list[CandlePoint]:
        """Baixa em streaming e lê o TXT compactado sem ocupar a RAM do serviço."""
        url = settings.B3_COTAHIST_URL_TEMPLATE.format(year=year)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(prefix=f"marketmind-cotahist-{year}-", suffix=".zip", delete=False) as temporary:
                temporary_path = Path(temporary.name)
                total_bytes = 0
                async with client.stream("GET", url, follow_redirects=True) as response:
                    response.raise_for_status()
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > settings.B3_COTAHIST_MAX_ARCHIVE_BYTES:
                        raise ValueError(f"Arquivo COTAHIST de {year} excede o limite configurado")
                    async for chunk in response.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > settings.B3_COTAHIST_MAX_ARCHIVE_BYTES:
                            raise ValueError(f"Arquivo COTAHIST de {year} excede o limite configurado")
                        temporary.write(chunk)

            with zipfile.ZipFile(temporary_path) as archive:
                members = [member for member in archive.namelist() if member.upper().endswith(".TXT")]
                if len(members) != 1:
                    raise ValueError("Arquivo COTAHIST sem um TXT identificável")
                with archive.open(members[0]) as raw_file:
                    with TextIOWrapper(raw_file, encoding="latin-1") as text_file:
                        return parse_cotahist_lines(text_file, symbols)
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Resposta inválida para o arquivo COTAHIST de {year}") from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    async def candles(
        self,
        *,
        symbols: list[str],
        start: datetime,
        end: datetime,
    ) -> list[CandlePoint]:
        normalized_symbols = {symbol.strip().upper() for symbol in symbols if symbol.strip()}
        if not normalized_symbols:
            return []
        if end < start:
            raise ValueError("O fim do histórico não pode ser anterior ao início")

        points: list[CandlePoint] = []
        timeout = httpx.Timeout(timeout=300.0, connect=20.0)
        headers = {"User-Agent": "MarketMind/1.0 historical-data-client"}
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            for year in range(start.year, end.year + 1):
                year_points = await self._year_points(client, year, normalized_symbols)
                points.extend(point for point in year_points if start <= point.time <= end)
        return sorted(points, key=lambda point: (point.asset.symbol, point.time))
