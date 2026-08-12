"""
services/feature_engineering.py
Gera o conjunto de features tabulares por candle usado pelo modelo preditivo:
retorno/momentum, tendência (SMA9/21/50), osciladores (RSI, MACD, estocástico),
volatilidade (ATR, desvio padrão, vol. anualizada), volume (relativo, z-score)
e regime (inclinação da SMA50, tendência de volume).

Todas as features são calculadas apenas com dados até o candle corrente
(sem lookahead), pré-requisito para qualquer validação walk-forward válida.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, SMAIndicator
from ta.volatility import AverageTrueRange

FEATURE_COLUMNS: list[str] = [
    "ret_1", "ret_3", "ret_5", "ret_10",
    "momentum_5", "momentum_10",
    "sma9", "sma21", "sma50",
    "dist_close_sma21",
    "sma_cross_9_21",
    "rsi14",
    "macd", "macd_signal", "macd_hist",
    "stoch_k", "stoch_d",
    "atr14",
    "std20",
    "vol_annualized",
    "volume_rel20",
    "volume_zscore20",
    "sma50_slope",
    "volume_trend",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe um DataFrame OHLCV ordenado cronologicamente (colunas:
    time, open, high, low, close, volume) e retorna o mesmo DataFrame
    acrescido de todas as colunas de FEATURE_COLUMNS.

    Linhas iniciais sem histórico suficiente para uma feature ficam com NaN
    e devem ser descartadas pelo chamador (dropna) antes do treino/inferência.
    """
    out = df.copy().reset_index(drop=True)
    close = out["close"]
    high = out["high"]
    low = out["low"]
    volume = out["volume"]

    # --- Retorno e momentum ---
    out["ret_1"] = close.pct_change(1)
    out["ret_3"] = close.pct_change(3)
    out["ret_5"] = close.pct_change(5)
    out["ret_10"] = close.pct_change(10)
    out["momentum_5"] = close - close.shift(5)
    out["momentum_10"] = close - close.shift(10)

    # --- Tendência ---
    sma9 = SMAIndicator(close=close, window=9).sma_indicator()
    sma21 = SMAIndicator(close=close, window=21).sma_indicator()
    sma50 = SMAIndicator(close=close, window=50).sma_indicator()
    out["sma9"] = sma9
    out["sma21"] = sma21
    out["sma50"] = sma50
    out["dist_close_sma21"] = (close - sma21) / sma21
    out["sma_cross_9_21"] = (sma9 - sma21) / sma21

    # --- Osciladores ---
    out["rsi14"] = RSIIndicator(close=close, window=14).rsi()

    macd_calc = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    out["macd"] = macd_calc.macd()
    out["macd_signal"] = macd_calc.macd_signal()
    out["macd_hist"] = macd_calc.macd_diff()

    stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    out["stoch_k"] = stoch.stoch()
    out["stoch_d"] = stoch.stoch_signal()

    # --- Volatilidade ---
    atr = AverageTrueRange(high=high, low=low, close=close, window=14)
    out["atr14"] = atr.average_true_range()
    out["std20"] = close.rolling(window=20).std()
    daily_ret = close.pct_change(1)
    out["vol_annualized"] = daily_ret.rolling(window=20).std() * np.sqrt(365)

    # --- Volume ---
    vol_sma20 = volume.rolling(window=20).mean()
    vol_std20 = volume.rolling(window=20).std()
    out["volume_rel20"] = volume / vol_sma20
    out["volume_zscore20"] = (volume - vol_sma20) / vol_std20.replace(0, np.nan)

    # --- Regime ---
    out["sma50_slope"] = (sma50 - sma50.shift(5)) / sma50.shift(5)
    out["volume_trend"] = volume.rolling(window=10).mean() / volume.rolling(window=30).mean()

    return out


def latest_feature_row(df_with_features: pd.DataFrame) -> pd.DataFrame:
    """Retorna a última linha válida (sem NaN nas FEATURE_COLUMNS) para inferência."""
    valid = df_with_features.dropna(subset=FEATURE_COLUMNS)
    if valid.empty:
        raise ValueError("Nenhuma linha com features completas disponível para inferência.")
    return valid.tail(1)
