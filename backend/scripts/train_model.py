"""
scripts/train_model.py
Pipeline de treino offline do modelo preditivo:
1. Lê candles do PostgreSQL/TimescaleDB (filtrando asset e timeframe via CLI)
2. Aplica build_features
3. Aplica add_labels
4. Remove NaNs
5. Treina com train_walk_forward_model (walk-forward validation)
6. Salva modelo com model_registry.save (model.joblib + label_encoder.joblib)
7. Salva métricas em JSON (metrics.json) e metadata em JSON (metadata.json)
8. Exibe resumo no terminal

Uso:
    cd backend
    python scripts/train_model.py --asset BTCUSDT --timeframe 1d --horizon 24

Arquivos gerados:
    backend/models_store/BTCUSDT/model.joblib
    backend/models_store/BTCUSDT/label_encoder.joblib
    backend/models_store/BTCUSDT/metrics.json
    backend/models_store/BTCUSDT/metadata.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from database import AsyncSessionLocal, dispose_db, init_db  # noqa: E402
from models.candle import Candle  # noqa: E402
from services.feature_engineering import FEATURE_COLUMNS, build_features  # noqa: E402
from services.label_engine import DEFAULT_THRESHOLD, add_labels, label_distribution  # noqa: E402
from services.model_registry import model_registry  # noqa: E402
from services.predictive_model import (
    MIN_OOS_YEARS,
    train_walk_forward_model,
)  # noqa: E402
from services.technical_analysis import candles_to_dataframe  # noqa: E402


async def load_candles(asset: str, timeframe: str) -> list[dict]:
    """Lê candles do PostgreSQL/TimescaleDB filtrando por asset e timeframe."""
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada")

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Candle)
            .where(Candle.asset == asset, Candle.timeframe == timeframe)
            .order_by(Candle.time.asc())
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

    return [
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


def print_summary(asset: str, timeframe: str, horizon: int, saved_dir: Path, result) -> None:
    print("\n" + "=" * 60)
    print(f"RESUMO DO TREINO — {asset} ({timeframe}, horizon={horizon})")
    print("=" * 60)
    print(f"Folds de walk-forward: {len(result.folds)}")
    for fold in result.folds:
        print(
            f"  [{fold.test_start} .. {fold.test_end}] "
            f"bal_acc={fold.balanced_accuracy:.4f}  "
            f"f1_macro={fold.f1_macro:.4f}  "
            f"ret_medio_sinal={fold.mean_return_per_signal:.4%}"
        )

    m = result.final_metrics
    print("-" * 60)
    print(f"Balanced accuracy média:      {m['avg_balanced_accuracy']:.4f}")
    print(f"F1 macro médio:               {m['avg_f1_macro']:.4f}")
    print(f"Retorno médio por sinal:      {m['avg_mean_return_per_signal']:.4%}")
    print(f"Anos out-of-sample cobertos:  {m['oos_years_covered']}")
    print(f"Modelo confiável (critérios): {result.reliable}")
    print("-" * 60)
    print(f"Arquivos salvos em: {saved_dir}")
    print("  - model.joblib")
    print("  - label_encoder.joblib")
    print("  - metrics.json")
    print("  - metadata.json")
    print("=" * 60 + "\n")


async def main(
    asset: str,
    timeframe: str,
    horizon: int,
    threshold: float,
    min_train_years: int,
) -> None:
    if AsyncSessionLocal is None:
        raise SystemExit("DATABASE_URL não configurada; defina a variável antes de treinar.")

    if not await init_db():
        raise SystemExit("Não foi possível inicializar/validar o banco antes do treino.")

    print(f"[1/6] Lendo candles de {asset} ({timeframe}) do PostgreSQL/TimescaleDB...")
    candles = await load_candles(asset.upper(), timeframe)
    minimum_expected = 365 * (min_train_years + MIN_OOS_YEARS)
    if len(candles) < minimum_expected:
        raise SystemExit(
            f"Histórico insuficiente ({len(candles)} candles) para {asset}/{timeframe}. "
            f"São necessários aproximadamente {minimum_expected} candles "
            f"({min_train_years} anos de treino + {MIN_OOS_YEARS} folds OOS). "
            "Rode scripts/seed_btc_history.py --days-back 2920."
        )
    print(f"       {len(candles)} candles carregados.")

    print("[2/6] Aplicando build_features...")
    df = candles_to_dataframe(candles)
    df_feat = build_features(df)

    print(f"[3/6] Aplicando add_labels (horizon={horizon} candles, threshold={threshold:.2%})...")
    df_labeled = add_labels(df_feat, horizon=horizon, threshold=threshold)

    print("[4/6] Removendo NaNs (features incompletas e labels sem futuro suficiente)...")
    before = len(df_labeled)
    df_clean = df_labeled.dropna(subset=FEATURE_COLUMNS + ["label", "future_return"]).reset_index(drop=True)
    after = len(df_clean)
    print(f"       {before} -> {after} linhas após remoção de NaNs.")
    dist = label_distribution(df_clean)
    print(f"       Distribuição de classes: {dist}")

    print(f"[5/6] Treinando com train_walk_forward_model (min_train_years={min_train_years})...")
    result = train_walk_forward_model(df_clean, min_train_years=min_train_years)

    print("[6/6] Salvando modelo com model_registry.save...")
    metadata = {
        "asset": asset,
        "timeframe": timeframe,
        "model_name": f"{asset.lower()}_gbm_v1",
        "horizon_candles": horizon,
        "threshold": threshold,
        "min_train_years": min_train_years,
        "feature_columns": FEATURE_COLUMNS,
        "trained_until": df_clean["time"].max().isoformat(),
        "trained_at": datetime.now(tz=timezone.utc).isoformat(),
        "n_candles_raw": len(candles),
        "n_rows_used": after,
        "label_distribution": dist,
        "reliable": result.reliable,
    }

    saved_dir = model_registry.save(
        asset=asset,
        model=result.model,
        label_encoder=result.label_encoder,
        metadata=metadata,
        metrics=result.final_metrics,
    )

    print_summary(asset.upper(), timeframe, horizon, saved_dir, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Treina o modelo preditivo MarketMind AI.")
    parser.add_argument("--asset", required=True, help="Ex.: BTCUSDT")
    parser.add_argument("--timeframe", required=True, help="Ex.: 1d")
    parser.add_argument("--horizon", type=int, required=True, help="Candles à frente para o rótulo, ex.: 24")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Threshold de retorno para ALTA/BAIXA, ex.: 0.015")
    parser.add_argument("--min-train-years", type=int, default=5, help="Anos mínimos de treino antes do 1º fold de teste")
    args = parser.parse_args()

    async def run() -> None:
        try:
            await main(
                asset=args.asset,
                timeframe=args.timeframe,
                horizon=args.horizon,
                threshold=args.threshold,
                min_train_years=args.min_train_years,
            )
        finally:
            await dispose_db()

    asyncio.run(run())
