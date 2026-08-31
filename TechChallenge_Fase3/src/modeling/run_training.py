"""Run reproducible model training for the Fase 3 project.

Usage:
    python -m src.modeling.run_training
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

from src.evaluation import evaluate_models, metrics_to_frame
from src.modeling import split_temporal_train_test, split_train_test, train_candidate_models
from src.preprocessing import build_feature_matrix, load_indicator_municipio, summarize_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _format_metric(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _metrics_markdown_table(metrics: pd.DataFrame) -> str:
    columns = ["model", "accuracy", "precision", "recall", "f1", "roc_auc"]
    lines = [
        "| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in metrics[columns].iterrows():
        lines.append(
            "| {model} | {accuracy} | {precision} | {recall} | {f1} | {roc_auc} |".format(
                model=row["model"],
                accuracy=_format_metric(row["accuracy"]),
                precision=_format_metric(row["precision"]),
                recall=_format_metric(row["recall"]),
                f1=_format_metric(row["f1"]),
                roc_auc=_format_metric(row["roc_auc"]),
            )
        )
    return "\n".join(lines)


def _confusion_matrices_section(metrics: dict[str, dict[str, Any]]) -> str:
    lines = [
        "## Matrizes De Confusao",
        "",
        "Formato: `[[TN, FP], [FN, TP]]`.",
        "",
    ]
    for model_name, values in metrics.items():
        lines.append(f"- `{model_name}`: `{values['confusion_matrix']}`")
    return "\n".join(lines)


def _write_report(
    random_metrics: pd.DataFrame,
    temporal_metrics: pd.DataFrame,
    random_raw: dict[str, dict[str, Any]],
    temporal_raw: dict[str, dict[str, Any]],
    feature_info: dict[str, list[str]],
    dataset_summary: dict[str, Any],
    output_path: Path,
) -> None:
    best_random = random_metrics.iloc[0]
    best_temporal = temporal_metrics.iloc[0]
    target_counts = dataset_summary["target_counts"]

    content = f"""# Resultados De Modelagem - Fase 3

Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Base Utilizada

- Registros: {dataset_summary["rows"]}
- Colunas originais: {dataset_summary["columns"]}
- Municipios unicos: {dataset_summary["municipalities"]}
- UFs: {dataset_summary["states"]}
- Anos: {dataset_summary["years"]}
- Classe 0: {target_counts.get(0, 0)} registros
- Classe 1: {target_counts.get(1, 0)} registros
- Taxa da classe positiva: {_format_percent(dataset_summary["target_positive_rate"])}

## Features Do Modelo Principal

Features numericas:

```text
{feature_info["numeric_features"]}
```

Features categoricas:

```text
{feature_info["categorical_features"]}
```

Colunas excluidas por risco de data leakage:

```text
{feature_info["excluded_leakage_columns"]}
```

## Validacao Aleatoria Estratificada

Split: 80% treino e 20% teste, mantendo a proporcao do target.

{_metrics_markdown_table(random_metrics)}

Melhor modelo por F1 nesta validacao: `{best_random["model"]}`.

## Validacao Temporal

Split: treino em 2023 e teste em 2024.

{_metrics_markdown_table(temporal_metrics)}

Melhor modelo por F1 nesta validacao: `{best_temporal["model"]}`.

## Leitura Inicial

O baseline `DummyClassifier` confirma que acuracia sozinha nao e suficiente: como a classe majoritaria representa cerca de 81% da base, um modelo que sempre prediz a classe 0 pode parecer razoavel em accuracy, mas tem recall e F1 iguais a zero para a classe de meta atingida.

Na proxima etapa, a comparacao deve priorizar F1, recall da classe positiva e estabilidade entre validacao aleatoria e temporal. Tambem sera necessario interpretar as variaveis mais relevantes para conectar o resultado com decisoes de politica publica.

Observacao importante: `media_portugues` e um indicador educacional do mesmo ciclo observado. Portanto, as metricas devem ser lidas como desempenho de uma solucao diagnostica com dados contemporaneos. Para uma predicao antecipada antes da avaliacao anual, sera necessario testar uma versao sem essa variavel e enriquecer o modelo com dados socioeconomicos e territoriais externos.

{_confusion_matrices_section(random_raw)}

## Matrizes De Confusao - Validacao Temporal

Formato: `[[TN, FP], [FN, TP]]`.

"""
    for model_name, values in temporal_raw.items():
        content += f"- `{model_name}`: `{values['confusion_matrix']}`\n"

    output_path.write_text(content, encoding="utf-8")


def run(include_level_proportions: bool = False) -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_indicator_municipio()
    dataset_summary = summarize_dataset(df)
    X, y, feature_info = build_feature_matrix(
        df,
        include_level_proportions=include_level_proportions,
    )

    X_train, X_test, y_train, y_test = split_train_test(X, y)
    random_models = train_candidate_models(
        X_train,
        y_train,
        feature_info["numeric_features"],
        feature_info["categorical_features"],
    )
    random_raw = evaluate_models(random_models, X_test, y_test)
    random_metrics = metrics_to_frame(random_raw)

    temporal_X_train, temporal_X_test, temporal_y_train, temporal_y_test = split_temporal_train_test(X, y)
    temporal_models = train_candidate_models(
        temporal_X_train,
        temporal_y_train,
        feature_info["numeric_features"],
        feature_info["categorical_features"],
    )
    temporal_raw = evaluate_models(temporal_models, temporal_X_test, temporal_y_test)
    temporal_metrics = metrics_to_frame(temporal_raw)

    random_metrics.to_csv(REPORTS_DIR / "model_metrics_random.csv", index=False)
    temporal_metrics.to_csv(REPORTS_DIR / "model_metrics_temporal.csv", index=False)

    raw_payload = {
        "dataset_summary": dataset_summary,
        "feature_info": feature_info,
        "random_validation": random_raw,
        "temporal_validation": temporal_raw,
    }
    (REPORTS_DIR / "model_metrics.json").write_text(
        json.dumps(raw_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    _write_report(
        random_metrics=random_metrics,
        temporal_metrics=temporal_metrics,
        random_raw=random_raw,
        temporal_raw=temporal_raw,
        feature_info=feature_info,
        dataset_summary=dataset_summary,
        output_path=REPORTS_DIR / "model_results.md",
    )

    return raw_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Fase 3 model training.")
    parser.add_argument(
        "--include-level-proportions",
        action="store_true",
        help="Include proportion-by-level columns. They are mostly unavailable in 2023.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(include_level_proportions=args.include_level_proportions)
    print(f"Reports saved in: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
