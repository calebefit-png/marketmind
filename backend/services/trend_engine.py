"""
services/trend_engine.py
Motor de classificação de tendência (ALTA / BAIXA / LATERAL) com score 0-100,
baseado em cruzamento de médias móveis (SMA9 x SMA21) e força do RSI14.

O sistema é probabilístico, não determinístico: o score expressa confiança
relativa do modelo, nunca uma previsão garantida.
"""

from __future__ import annotations

from schemas.candle import AnalysisResponse, TechnicalIndicators, TrendEnum


def _sma_gap_score(sma9: float, sma21: float) -> float:
    """
    Distância percentual entre SMA9 e SMA21, normalizada em uma escala de
    contribuição de até 50 pontos para o score final.
    """
    if sma21 == 0:
        return 0.0
    gap_pct = (sma9 - sma21) / sma21 * 100
    # satura em +/-3% de gap como contribuição máxima de +/-50 pontos
    clamped = max(min(gap_pct, 3.0), -3.0)
    return (clamped / 3.0) * 50.0


def _rsi_score(rsi: float) -> float:
    """
    Contribuição do RSI para o score, centrada em 50 (neutro).
    RSI 70+ = força compradora; RSI 30- = força vendedora.
    Contribui até +/-50 pontos.
    """
    return (rsi - 50.0)


def classify_trend(indicators: TechnicalIndicators, asset: str) -> AnalysisResponse:
    """
    Classifica a tendência do ativo combinando SMA9/SMA21 e RSI14.
    score = 50 (neutro) + contribuição de gap de médias + contribuição de RSI,
    limitado a [0, 100].
    """
    sma9 = indicators.sma9
    sma21 = indicators.sma21
    rsi = indicators.rsi

    if sma9 is None or sma21 is None or rsi is None:
        return AnalysisResponse(
            asset=asset,
            trend=TrendEnum.LATERAL,
            score=50,
            indicators=indicators,
            explanation=(
                "Dados insuficientes para calcular tendência com confiança; "
                "aguardando histórico mínimo de candles."
            ),
        )

    raw_score = 50.0 + (_sma_gap_score(sma9, sma21) * 0.6) + (_rsi_score(rsi) * 0.4)
    score = int(max(0, min(100, round(raw_score))))

    sma_diff_pct = ((sma9 - sma21) / sma21 * 100) if sma21 else 0.0

    if score >= 60:
        trend = TrendEnum.ALTA
    elif score <= 40:
        trend = TrendEnum.BAIXA
    else:
        trend = TrendEnum.LATERAL

    explanation = _build_explanation(trend, sma_diff_pct, rsi)

    return AnalysisResponse(
        asset=asset,
        trend=trend,
        score=score,
        indicators=indicators,
        explanation=explanation,
    )


def _build_explanation(trend: TrendEnum, sma_diff_pct: float, rsi: float) -> str:
    sma_desc = (
        f"SMA9 {'acima' if sma_diff_pct > 0 else 'abaixo'} da SMA21 em "
        f"{abs(sma_diff_pct):.2f}%"
    )

    if rsi >= 70:
        rsi_desc = "RSI em zona de sobrecompra"
    elif rsi >= 55:
        rsi_desc = "RSI em zona de força compradora"
    elif rsi <= 30:
        rsi_desc = "RSI em zona de sobrevenda"
    elif rsi <= 45:
        rsi_desc = "RSI em zona de força vendedora"
    else:
        rsi_desc = "RSI em zona neutra"

    if trend == TrendEnum.ALTA:
        veredito = "Cenário favorável a continuidade de alta, mas sem garantia de movimento."
    elif trend == TrendEnum.BAIXA:
        veredito = "Cenário favorável a pressão vendedora, mas sem garantia de movimento."
    else:
        veredito = "Mercado sem direção clara; sinais mistos entre médias e momentum."

    return f"{sma_desc}. {rsi_desc}. {veredito}"
