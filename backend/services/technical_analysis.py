"""
services/technical_analysis.py
Módulo de análise técnica: calcula SMA9, SMA21, RSI14, MACD e Bandas de Bollinger
a partir de uma série de candles, usando pandas + biblioteca `ta`.
"""

from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from schemas.candle import TechnicalIndicators


def candles_to_dataframe(candles: list[dict]) -> pd.DataFrame:
    """
    Converte uma lista de candles (dicts com open/high/low/close/volume/time)
    em um DataFrame ordenado cronologicamente, pronto para cálculo de indicadores.
    """
    df = pd.DataFrame(candles)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_indicators(df: pd.DataFrame) -> TechnicalIndicators:
    """
    Calcula o conjunto completo de indicadores técnicos sobre o fechamento (close).
    Retorna apenas o último valor válido de cada indicador.
    Requer no mínimo ~26 candles para MACD ser significativo.
    """
    if df.empty or len(df) < 2:
        return TechnicalIndicators()

    close = df["close"]

    sma9 = SMAIndicator(close=close, window=9).sma_indicator()
    sma21 = SMAIndicator(close=close, window=21).sma_indicator()
    rsi14 = RSIIndicator(close=close, window=14).rsi()

    macd_calc = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    macd_line = macd_calc.macd()
    macd_signal = macd_calc.macd_signal()
    macd_hist = macd_calc.macd_diff()

    bb = BollingerBands(close=close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband()
    bb_lower = bb.bollinger_lband()
    bb_middle = bb.bollinger_mavg()

    def last_valid(series: pd.Series) -> float | None:
        series = series.dropna()
        if series.empty:
            return None
        return round(float(series.iloc[-1]), 6)

    return TechnicalIndicators(
        rsi=last_valid(rsi14),
        sma9=last_valid(sma9),
        sma21=last_valid(sma21),
        macd=last_valid(macd_line),
        macd_signal=last_valid(macd_signal),
        macd_hist=last_valid(macd_hist),
        bb_upper=last_valid(bb_upper),
        bb_lower=last_valid(bb_lower),
        bb_middle=last_valid(bb_middle),
    )
