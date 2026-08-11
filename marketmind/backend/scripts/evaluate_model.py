"""
scripts/evaluate_model.py
Carrega um modelo já treinado do registry e imprime suas métricas de
walk-forward validation, incluindo a matriz de confusão de cada fold,
sem retreinar. Útil para checar se um modelo em produção ainda atende
aos critérios mínimos de confiabilidade.

Uso:
    cd backend
    python scripts/evaluate_model.py --asset BTCUSDT
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.label_engine import LABEL_CLASSES  # noqa: E402
from services.model_registry import model_registry  # noqa: E402


def print_confusion_matrix(cm: list[list[int]], labels: list[str]) -> None:
    col_width = max(len(l) for l in labels) + 2
    header = " " * (col_width + 2) + "".join(f"{l:>{col_width}}" for l in labels)
    print(header)
    for i, row in enumerate(cm):
        row_str = "".join(f"{v:>{col_width}}" for v in row)
        print(f"{labels[i]:>{col_width}}  {row_str}")


def main(asset: str) -> None:
    loaded = model_registry.load(asset)
    if loaded is None:
        raise SystemExit(
            f"Nenhum modelo encontrado para {asset} em models_store/{asset}/. "
            "Rode scripts/train_model.py primeiro."
        )

    metadata = loaded.metadata
    metrics = loaded.metrics

    print("=" * 60)
    print(f"MODELO: {metadata.get('model_name', asset)}")
    print("=" * 60)
    print(f"Asset:            {metadata.get('asset')}")
    print(f"Timeframe:        {metadata.get('timeframe')}")
    print(f"Horizonte:        {metadata.get('horizon_candles')} candles")
    print(f"Threshold:        {metadata.get('threshold'):.2%}" if metadata.get("threshold") is not None else "Threshold:        n/a")
    print(f"Treinado até:     {metadata.get('trained_until')}")
    print(f"Treinado em:      {metadata.get('trained_at')}")
    print(f"Candles usados:   {metadata.get('n_rows_used')} (brutos: {metadata.get('n_candles_raw')})")
    print(f"Distrib. classes: {metadata.get('label_distribution')}")

    print("\n" + "-" * 60)
    print("MÉTRICAS AGREGADAS (média dos folds de walk-forward)")
    print("-" * 60)
    print(f"Balanced accuracy média:      {metrics.get('avg_balanced_accuracy')}")
    print(f"F1 macro médio:               {metrics.get('avg_f1_macro')}")
    print(f"Retorno médio por sinal:      {metrics.get('avg_mean_return_per_signal')}")
    print(f"Anos out-of-sample cobertos:  {metrics.get('oos_years_covered')}")
    print(f"Critérios mínimos exigidos:   {metrics.get('criteria')}")

    reliable = metrics.get("reliable", False)
    print(f"\nModelo confiável para exibição em produção? {reliable}")

    folds = metrics.get("folds", [])
    if folds:
        print("\n" + "-" * 60)
        print("DETALHE POR FOLD (walk-forward)")
        print("-" * 60)
        for fold in folds:
            print(
                f"\nTreino {fold['train_start']} .. {fold['train_end']}  |  "
                f"Teste {fold['test_start']} .. {fold['test_end']}"
            )
            print(
                f"  bal_acc={fold['balanced_accuracy']}  f1_macro={fold['f1_macro']}  "
                f"roc_auc_ovr={fold['roc_auc_ovr']}  ret_medio_sinal={fold['mean_return_per_signal']}"
            )
            print(f"  n_train={fold['n_train']}  n_test={fold['n_test']}")
            print("  Matriz de confusão (linhas=real, colunas=previsto):")
            print_confusion_matrix(fold["confusion_matrix"], LABEL_CLASSES)
    else:
        print("\nNenhum fold registrado nas métricas.")

    if not reliable:
        print(
            "\nATENÇÃO: este modelo está abaixo do critério mínimo de validação. "
            "O endpoint /prediction/{asset} retornará 'model_not_reliable' em vez de expor previsões."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avalia um modelo já treinado do registry.")
    parser.add_argument("--asset", required=True, help="Ex.: BTCUSDT")
    args = parser.parse_args()
    main(args.asset)
