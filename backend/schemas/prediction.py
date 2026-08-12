"""
schemas/prediction.py
Schemas de resposta do endpoint de predição estatística.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    trained_until: str
    backtest_balanced_accuracy: float
    backtest_f1_macro: float
    oos_years_covered: int


class ConfidenceBand(BaseModel):
    lower: float
    upper: float


class PredictionResponse(BaseModel):
    asset: str
    horizon_candles: int
    generated_at: str
    prediction: str
    probabilities: dict[str, float]
    model: ModelInfo
    confidence_band: ConfidenceBand
    disclaimer: str = (
        "Probabilidades estatísticas baseadas em histórico; "
        "não constituem recomendação de investimento."
    )


class ModelNotReliableResponse(BaseModel):
    status: str = "model_not_reliable"
    message: str
    metrics: dict = Field(default_factory=dict)
    criteria: dict = Field(default_factory=dict)
