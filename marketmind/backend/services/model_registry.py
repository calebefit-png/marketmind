"""
services/model_registry.py
Registry de modelos treinados em disco: cada ativo tem uma pasta em
`models_store/<ASSET>/` contendo `model.joblib`, `label_encoder.joblib`,
`metadata.json` e `metrics.json`.

O registry é a única porta de entrada para carregar um modelo em produção —
o endpoint de predição nunca treina nem acessa joblib diretamente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

MODELS_STORE_DIR = Path(__file__).resolve().parent.parent / "models_store"


@dataclass
class LoadedModel:
    model: Any
    label_encoder: Any
    metadata: dict
    metrics: dict


class ModelRegistry:
    def __init__(self, store_dir: Path = MODELS_STORE_DIR) -> None:
        self.store_dir = store_dir

    def _asset_dir(self, asset: str) -> Path:
        # Nome exato do ativo (ex.: BTCUSDT), sem normalização de case —
        # o caminho no disco deve corresponder ao usado na CLI.
        return self.store_dir / asset

    def save(
        self,
        asset: str,
        model: Any,
        label_encoder: Any,
        metadata: dict,
        metrics: dict,
    ) -> Path:
        asset_dir = self._asset_dir(asset)
        asset_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, asset_dir / "model.joblib")
        joblib.dump(label_encoder, asset_dir / "label_encoder.joblib")
        (asset_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        (asset_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False)
        )
        return asset_dir

    def load(self, asset: str) -> LoadedModel | None:
        asset_dir = self._asset_dir(asset)
        model_path = asset_dir / "model.joblib"
        encoder_path = asset_dir / "label_encoder.joblib"
        metadata_path = asset_dir / "metadata.json"
        metrics_path = asset_dir / "metrics.json"

        if not (
            model_path.exists()
            and encoder_path.exists()
            and metadata_path.exists()
            and metrics_path.exists()
        ):
            return None

        model = joblib.load(model_path)
        label_encoder = joblib.load(encoder_path)
        metadata = json.loads(metadata_path.read_text())
        metrics = json.loads(metrics_path.read_text())

        return LoadedModel(
            model=model,
            label_encoder=label_encoder,
            metadata=metadata,
            metrics=metrics,
        )

    def exists(self, asset: str) -> bool:
        return (self._asset_dir(asset) / "model.joblib").exists()


model_registry = ModelRegistry()
