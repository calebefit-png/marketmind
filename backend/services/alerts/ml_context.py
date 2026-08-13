"""Contexto probabilístico opcional e estritamente condicionado à confiabilidade do modelo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.feature_engineering import build_features, latest_feature_row
from services.model_registry import model_registry
from services.predictive_model import predict_proba_for_row
from services.technical_analysis import candles_to_dataframe


@dataclass(frozen=True)
class ReliablePredictionContext:
    asset: str
    probabilities: dict[str, float]
    model_name: str
    trained_until: str
    balanced_accuracy: float

    def payload(self) -> dict[str, Any]:
        return asdict(self)


def get_reliable_prediction_context(
    asset: str, candles: list[dict[str, Any]]
) -> ReliablePredictionContext | None:
    """Retorna probabilidades somente para um artefato e métricas aprovados."""
    loaded = model_registry.load(asset.upper())
    if loaded is None or not loaded.metrics.get("reliable", False):
        return None
    try:
        features = build_features(candles_to_dataframe(candles))
        probabilities = predict_proba_for_row(
            loaded.model, loaded.label_encoder, latest_feature_row(features)
        )
    except (ValueError, KeyError, TypeError):
        return None
    return ReliablePredictionContext(
        asset=asset.upper(),
        probabilities={key: float(value) for key, value in probabilities.items()},
        model_name=str(loaded.metadata.get("model_name", "unknown")),
        trained_until=str(loaded.metadata.get("trained_until", "unknown")),
        balanced_accuracy=float(loaded.metrics.get("avg_balanced_accuracy", 0.0)),
    )
