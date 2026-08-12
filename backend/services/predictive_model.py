"""
services/predictive_model.py
Motor de treino e validação do modelo preditivo (GradientBoostingClassifier)
com walk-forward validation (janelas expansivas, sem embaralhar dados).

Critérios mínimos de confiabilidade (aplicados no fold final de teste):
    - balanced accuracy > 0.52
    - F1 macro > 0.50
    - retorno médio por sinal positivo (ALTA/BAIXA acionáveis) > 0
    - pelo menos 3 anos de teste out-of-sample cobertos pelos folds

Se os critérios não forem atingidos, o modelo ainda é salvo (para
inspeção/histórico), mas marcado como `reliable = False` no metadata —
é essa flag que o endpoint de predição usa para decidir se expõe a
previsão ou retorna `model_not_reliable`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder

from services.feature_engineering import FEATURE_COLUMNS
from services.label_engine import LABEL_CLASSES

MIN_BALANCED_ACCURACY = 0.52
MIN_F1_MACRO = 0.50
MIN_OOS_YEARS = 3

RELIABILITY_CRITERIA = {
    "min_balanced_accuracy": MIN_BALANCED_ACCURACY,
    "min_f1_macro": MIN_F1_MACRO,
    "min_oos_years": MIN_OOS_YEARS,
}


@dataclass
class FoldResult:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    balanced_accuracy: float
    f1_macro: float
    roc_auc_ovr: float | None
    confusion_matrix: list[list[int]]
    mean_return_per_signal: float
    n_train: int
    n_test: int


@dataclass
class TrainingResult:
    model: GradientBoostingClassifier
    label_encoder: LabelEncoder
    folds: list[FoldResult] = field(default_factory=list)
    final_metrics: dict = field(default_factory=dict)
    reliable: bool = False


def _yearly_walk_forward_splits(df: pd.DataFrame, min_train_years: int = 5) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    """
    Gera splits de janela expansiva por ano civil:
    treino = [início, fim do ano Y), teste = [ano Y+1 inteiro).
    Requer histórico mínimo de `min_train_years` antes do primeiro teste.
    """
    years = sorted(df["time"].dt.year.unique())
    splits = []
    for i in range(min_train_years, len(years)):
        test_year = years[i]
        train_years = years[:i]
        train_start = df["time"].min()
        train_end = pd.Timestamp(year=test_year, month=1, day=1, tz=train_start.tz)
        test_start = train_end
        test_end = pd.Timestamp(year=test_year + 1, month=1, day=1, tz=train_start.tz)
        splits.append((train_start, train_end, test_start, test_end))
    return splits


def _mean_return_per_signal(y_true_return: pd.Series, y_pred: np.ndarray, label_encoder: LabelEncoder) -> float:
    """
    Retorno médio realizado (future_return) apenas nas linhas onde o modelo
    sinalizou ALTA ou BAIXA (sinais acionáveis, LATERAL é "ficar de fora").
    Para BAIXA, inverte o sinal (retorno positivo = acerto de uma posição vendida).
    """
    pred_labels = label_encoder.inverse_transform(y_pred)
    mask_alta = pred_labels == "ALTA"
    mask_baixa = pred_labels == "BAIXA"

    if not (mask_alta.any() or mask_baixa.any()):
        return 0.0

    returns = []
    if mask_alta.any():
        returns.append(y_true_return[mask_alta].mean())
    if mask_baixa.any():
        returns.append(-y_true_return[mask_baixa].mean())

    return float(np.nanmean(returns)) if returns else 0.0


def train_walk_forward_model(
    df_features_labeled: pd.DataFrame,
    min_train_years: int = 5,
) -> TrainingResult:
    """
    Treina e valida o modelo com walk-forward validation em janelas anuais
    expansivas. O `df_features_labeled` deve conter FEATURE_COLUMNS, `label`,
    `future_return` e `time`, já sem NaN nas linhas usadas.
    """
    data = df_features_labeled.dropna(subset=FEATURE_COLUMNS + ["label", "future_return"]).copy()
    data = data.sort_values("time").reset_index(drop=True)

    label_encoder = LabelEncoder()
    label_encoder.fit(LABEL_CLASSES)

    splits = _yearly_walk_forward_splits(data, min_train_years=min_train_years)

    folds: list[FoldResult] = []
    last_model: GradientBoostingClassifier | None = None

    for train_start, train_end, test_start, test_end in splits:
        train_mask = (data["time"] >= train_start) & (data["time"] < train_end)
        test_mask = (data["time"] >= test_start) & (data["time"] < test_end)

        train_df = data.loc[train_mask]
        test_df = data.loc[test_mask]

        if len(train_df) < 100 or len(test_df) < 20:
            continue

        X_train = train_df[FEATURE_COLUMNS]
        y_train = label_encoder.transform(train_df["label"])
        X_test = test_df[FEATURE_COLUMNS]
        y_test = label_encoder.transform(test_df["label"])

        model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )
        model.fit(X_train, y_train)
        last_model = model

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        bal_acc = balanced_accuracy_score(y_test, y_pred)
        f1_macro = f1_score(y_test, y_pred, average="macro")

        try:
            roc_auc = roc_auc_score(y_test, y_proba, multi_class="ovr")
        except ValueError:
            roc_auc = None

        cm = confusion_matrix(y_test, y_pred, labels=range(len(LABEL_CLASSES))).tolist()
        mean_return = _mean_return_per_signal(test_df["future_return"], y_pred, label_encoder)

        folds.append(
            FoldResult(
                train_start=str(train_start.date()),
                train_end=str(train_end.date()),
                test_start=str(test_start.date()),
                test_end=str(test_end.date()),
                balanced_accuracy=round(float(bal_acc), 4),
                f1_macro=round(float(f1_macro), 4),
                roc_auc_ovr=round(float(roc_auc), 4) if roc_auc is not None else None,
                confusion_matrix=cm,
                mean_return_per_signal=round(mean_return, 6),
                n_train=len(train_df),
                n_test=len(test_df),
            )
        )

    if not folds or last_model is None:
        raise ValueError(
            "Histórico insuficiente para gerar ao menos um fold de walk-forward "
            f"(mínimo {min_train_years} anos de treino + 1 ano de teste)."
        )

    # Treina o modelo final com TODO o histórico disponível (produção usa o máximo de dado).
    X_all = data[FEATURE_COLUMNS]
    y_all = label_encoder.transform(data["label"])
    final_model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )
    final_model.fit(X_all, y_all)

    avg_bal_acc = float(np.mean([f.balanced_accuracy for f in folds]))
    avg_f1_macro = float(np.mean([f.f1_macro for f in folds]))
    avg_mean_return = float(np.mean([f.mean_return_per_signal for f in folds]))
    oos_years_covered = len(folds)

    reliable = (
        avg_bal_acc > MIN_BALANCED_ACCURACY
        and avg_f1_macro > MIN_F1_MACRO
        and avg_mean_return > 0
        and oos_years_covered >= MIN_OOS_YEARS
    )

    final_metrics = {
        "avg_balanced_accuracy": round(avg_bal_acc, 4),
        "avg_f1_macro": round(avg_f1_macro, 4),
        "avg_mean_return_per_signal": round(avg_mean_return, 6),
        "oos_years_covered": oos_years_covered,
        "criteria": RELIABILITY_CRITERIA,
        "reliable": reliable,
        "folds": [f.__dict__ for f in folds],
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    return TrainingResult(
        model=final_model,
        label_encoder=label_encoder,
        folds=folds,
        final_metrics=final_metrics,
        reliable=reliable,
    )


def predict_proba_for_row(
    model: GradientBoostingClassifier,
    label_encoder: LabelEncoder,
    feature_row: pd.DataFrame,
) -> dict[str, float]:
    """Retorna probabilidades por classe para uma única linha de features."""
    X = feature_row[FEATURE_COLUMNS]
    proba = model.predict_proba(X)[0]
    classes = label_encoder.inverse_transform(model.classes_)
    return {str(cls): round(float(p), 4) for cls, p in zip(classes, proba)}


# Alias retrocompatível — nome anterior da função pública de treino.
train_with_walk_forward = train_walk_forward_model
