"""
services/bcb_service.py
Cliente HTTP para a API de Séries Temporais (SGS) do Banco Central do Brasil.
Documentação: https://dadosabertos.bcb.gov.br/dataset/4-taxa-de-juros---selic
Código da série Selic (meta diária): 432 (taxa Selic acumulada mensal), usamos 11
(taxa Selic diária) por ser a série de referência mais granular.
"""

from __future__ import annotations

import logging

import httpx

from config import settings
from schemas.candle import SelicResponse

logger = logging.getLogger("marketmind.bcb")

SELIC_SERIES_CODE = 11  # Taxa Selic - fator diário


class BCBService:
    """Busca séries oficiais do Banco Central via API SGS (JSON público)."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def _series_url(self, code: int, last_n: int = 5) -> str:
        base = settings.BCB_SGS_URL.format(code=code)
        return f"{base}/ultimos/{last_n}?formato=json"

    async def get_selic(self) -> SelicResponse:
        """
        Retorna o valor atual da Selic, a data de referência e a variação
        em relação ao valor anterior disponível na série.
        """
        url = self._series_url(SELIC_SERIES_CODE, last_n=5)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if not data:
            raise ValueError("Série Selic retornou vazia do BCB")

        # data vem em ordem cronológica crescente: [{"data": "dd/mm/aaaa", "valor": "0.123456"}]
        ultimo = data[-1]
        penultimo = data[-2] if len(data) > 1 else None

        valor_atual = float(ultimo["valor"])
        valor_anterior = float(penultimo["valor"]) if penultimo else None
        variacao = (
            round(valor_atual - valor_anterior, 6) if valor_anterior is not None else None
        )

        return SelicResponse(
            valor_atual=valor_atual,
            data=ultimo["data"],
            valor_anterior=valor_anterior,
            variacao=variacao,
        )


bcb_service = BCBService()
