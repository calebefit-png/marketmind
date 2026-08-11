"""
services/label_engine.py
Gera o target (rótulo) de classificação multiclasse ALTA/BAIXA/LATERAL,
a partir do retorno futuro do preço N candles à frente.

Regra de threshold (parametrizável):
    retorno_futuro > +threshold  -> ALTA
    retorno_futuro < -threshold  -> BAIXA
    caso contrário                -> LATERAL

O rótulo de uma linha no tempo t depende de close em t+horizon, portanto as
últimas `horizon` linhas do dataset não têm rótulo válido (ficam NaN) e devem
ser descartadas do conjunto de treino/teste, mas são exatamente as linhas
usadas para inferência em produção (não temos o futuro ainda).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_HORIZON = 24
DEFAULT_THRESHOLD = 0.015  # 1.5%

LABEL_ALTA = "ALTA"
LABEL_BAIXA = "BAIXA"
LABEL_LATERAL = "LATERAL"

LABEL_CLASSES = [LABEL_BAIXA, LABEL_LATERAL, LABEL_ALTA]  # ordem estável p/ encoding


def add_labels(
    df: pd.DataFrame,
    horizon: int = DEFAULT_HORIZON,
    threshold: float = DEFAULT_THRESHOLD,
) -> pd.DataFrame:
    """
    Acrescenta as colunas `future_return` e `label` ao DataFrame.
    `df` deve estar ordenado cronologicamente e conter a coluna `close`.
    """
    out = df.copy()
    future_close = out["close"].shift(-horizon)
    out["future_return"] = (future_close - out["close"]) / out["close"]

    conditions = [
        out["future_return"] > threshold,
        out["future_return"] < -threshold,
    ]
    choices = [LABEL_ALTA, LABEL_BAIXA]
    out["label"] = np.select(conditions, choices, default=LABEL_LATERAL)

    # linhas sem futuro suficiente (últimas `horizon`) não têm rótulo válido
    out.loc[future_close.isna(), "label"] = np.nan

    return out


def label_distribution(df_with_labels: pd.DataFrame) -> dict[str, int]:
    """Contagem de classes, útil para checar balanceamento antes do treino."""
    return df_with_labels["label"].value_counts(dropna=True).to_dict()
