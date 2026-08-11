"""
api/routes/prediction.py
Endpoint de predição estatística. Nunca retorna "vai subir" — retorna
probabilidades calibradas por classe, sempre acompanhadas das métricas de
backtest do modelo. Se o modelo não atingir os critérios mínimos de
confiabilidade (ver services/predictive_model.py), a rota retorna
explicitamente `model_not_reliable` em vez de expor uma previsão.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candle import Candle
from schemas.prediction import (
    ConfidenceBand,
    ModelInfo,
    ModelNotReliableResponse,
    PredictionResponse,
)
from services.feature_engineering import build_features, latest_feature_row
from services.model_registry import model_registry
from services.predictive_model import predict_proba_for_row
from services.technical_analysis import candles_to_dataframe

router = APIRouter(tags=["prediction"])


@router.get(
    "/prediction/{asset}",
    response_model=PredictionResponse,
    responses={422: {"model": ModelNotReliableResponse}},
)
async def get_prediction(
    asset: str,
    horizon: int = Query(default=24, ge=1, le=90),
    timeframe: str = Query(default="1d"),
    db: AsyncSession = Depends(get_db),
):
    asset_upper = asset.upper()
    loaded = model_registry.load(asset_upper)

    if loaded is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nenhum modelo treinado para {asset_upper}. "
                "Rode scripts/train_model.py antes de consultar predições."
            ),
        )

    reliable = loaded.metrics.get("reliable", False)
    if not reliable:
        return _model_not_reliable_response(loaded.metrics)

    stmt = (
        select(Candle)
        .where(Candle.asset == asset_upper, Candle.timeframe == timeframe)
        .order_by(Candle.time.desc())
        .limit(120)
    )
    result = await db.execute(stmt)
    rows = list(reversed(result.scalars().all()))

    if len(rows) < 60:
        raise HTTPException(
            status_code=422,
            detail="Histórico insuficiente de candles recentes para gerar features de inferência.",
        )

    candles = [
        {
            "time": row.time,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
        }
        for row in rows
    ]

    df = candles_to_dataframe(candles)
    df_feat = build_features(df)

    try:
        feature_row = latest_feature_row(df_feat)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    model = loaded.model
    label_encoder = loaded.label_encoder

    probabilities = predict_proba_for_row(model, label_encoder, feature_row)
    prediction = max(probabilities, key=probabilities.get)

    sorted_probs = sorted(probabilities.values(), reverse=True)
    top_prob = sorted_probs[0]
    second_prob = sorted_probs[1] if len(sorted_probs) > 1 else 0.0

    metrics = loaded.metrics
    metadata = loaded.metadata

    return PredictionResponse(
        asset=asset_upper,
        horizon_candles=metadata.get("horizon_candles", horizon),
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        prediction=prediction,
        probabilities=probabilities,
        model=ModelInfo(
            name=metadata.get("model_name", f"{asset_upper.lower()}_gbm_v1"),
            trained_until=metadata.get("trained_until", "unknown"),
            backtest_balanced_accuracy=metrics.get("avg_balanced_accuracy", 0.0),
            backtest_f1_macro=metrics.get("avg_f1_macro", 0.0),
            oos_years_covered=metrics.get("oos_years_covered", 0),
        ),
        confidence_band=ConfidenceBand(
            lower=round(max(0.0, top_prob - (top_prob - second_prob) / 2), 4),
            upper=round(min(1.0, top_prob + (top_prob - second_prob) / 2), 4),
        ),
    )


def _model_not_reliable_response(metrics: dict) -> ModelNotReliableResponse:
    return ModelNotReliableResponse(
        status="model_not_reliable",
        message="Modelo abaixo do critério mínimo de validação.",
        metrics={
            "avg_balanced_accuracy": metrics.get("avg_balanced_accuracy"),
            "avg_f1_macro": metrics.get("avg_f1_macro"),
            "avg_mean_return_per_signal": metrics.get("avg_mean_return_per_signal"),
            "oos_years_covered": metrics.get("oos_years_covered"),
        },
        criteria=metrics.get("criteria", {}),
    )
