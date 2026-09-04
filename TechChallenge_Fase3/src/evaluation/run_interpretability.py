"""Run model interpretability analysis for the Fase 3 project.

Usage:
    python -m src.evaluation.run_interpretability
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / "tmp"))

from src.evaluation import (  # noqa: E402
    get_linear_coefficients,
    get_model_feature_importance,
    get_permutation_importance,
)
from src.modeling import split_temporal_train_test, split_train_test, train_candidate_models  # noqa: E402
from src.preprocessing import build_feature_matrix, load_indicator_municipio  # noqa: E402
from src.visualization import plot_feature_importance, save_current_figure  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGES_DIR = PROJECT_ROOT / "images"


def _write_report(
    logistic_coefficients,
    random_forest_importance,
    permutation_importance,
    output_path: Path,
) -> None:
    top_permutation = permutation_importance.head(5)
    top_rf = random_forest_importance.head(5)
    top_logistic = logistic_coefficients.head(8)

    content = f"""# Interpretabilidade Dos Modelos - Fase 3

Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Objetivo

Esta etapa busca entender quais variaveis mais influenciam a classificacao de risco/cumprimento de meta em nivel municipal/agregado.

## Importancia Por Permutacao

A importancia por permutacao foi calculada sobre a validacao temporal, usando o modelo de regressao logistica e a metrica F1. Essa leitura mede quanto o desempenho cai quando uma variavel e embaralhada.

| Feature | Importancia media | Desvio |
|---|---:|---:|
"""
    for _, row in top_permutation.iterrows():
        content += f"| {row['feature']} | {row['importance_mean']:.4f} | {row['importance_std']:.4f} |\n"

    content += """
## Coeficientes Da Regressao Logistica

Os coeficientes indicam a direcao da associacao depois do preprocessamento. Valores positivos aumentam a probabilidade estimada de meta atingida; valores negativos reduzem essa probabilidade.

| Feature | Coeficiente | Peso absoluto |
|---|---:|---:|
"""
    for _, row in top_logistic.iterrows():
        content += f"| {row['feature']} | {row['coefficient']:.4f} | {row['abs_coefficient']:.4f} |\n"

    content += """
## Importancia Da Random Forest

A Random Forest ajuda a enxergar variaveis relevantes por reducao de impureza nas arvores.

| Feature | Importancia |
|---|---:|
"""
    for _, row in top_rf.iterrows():
        content += f"| {row['feature']} | {row['importance']:.4f} |\n"

    content += """
## Leitura Executiva

- `media_portugues` aparece como a variavel mais forte do modelo, o que e coerente com o problema: melhor desempenho em lingua portuguesa esta associado a maior chance de cumprimento da meta.
- `sigla_uf` tambem aparece com peso relevante, indicando que fatores territoriais e contextuais diferenciam bastante os municipios.
- `rede` contribui para a classificacao, mas deve ser interpretada com cuidado porque a base usa codigos numericos sem dicionario oficial no repositorio.
- `ano` ajuda a capturar a diferenca entre 2023 e 2024, mas nao substitui uma serie historica mais longa.

Como `media_portugues` pertence ao ciclo educacional analisado, ela deve ser usada com cautela em narrativas preditivas. O resultado mostra forte associacao diagnostica; para antecipacao operacional antes da avaliacao, a recomendacao e criar um experimento sem essa variavel.

## Cuidados De Interpretacao

- A interpretabilidade confirma associacoes no nivel agregado da base, nao causalidade individual.
- As colunas diretamente derivadas da taxa de alfabetizacao e das metas foram excluidas do modelo principal para evitar data leakage.
- `media_portugues` pode nao estar disponivel antes da avaliacao anual, entao nao deve ser vendida como variavel plenamente ex-ante.
- Como ha apenas dois anos disponiveis, a validacao temporal e util, mas ainda limitada para afirmar estabilidade futura.
"""
    output_path.write_text(content, encoding="utf-8")


def run() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_indicator_municipio()
    X, y, feature_info = build_feature_matrix(df)

    X_train, X_test, y_train, y_test = split_train_test(X, y)
    random_models = train_candidate_models(
        X_train,
        y_train,
        feature_info["numeric_features"],
        feature_info["categorical_features"],
    )

    temporal_X_train, temporal_X_test, temporal_y_train, temporal_y_test = split_temporal_train_test(X, y)
    temporal_models = train_candidate_models(
        temporal_X_train,
        temporal_y_train,
        feature_info["numeric_features"],
        feature_info["categorical_features"],
    )

    logistic_coefficients = get_linear_coefficients(temporal_models["logistic_regression"])
    random_forest_importance = get_model_feature_importance(random_models["random_forest"])
    permutation = get_permutation_importance(
        temporal_models["logistic_regression"],
        temporal_X_test,
        temporal_y_test,
    )

    logistic_coefficients.to_csv(REPORTS_DIR / "logistic_coefficients.csv", index=False)
    random_forest_importance.to_csv(REPORTS_DIR / "random_forest_feature_importance.csv", index=False)
    permutation.to_csv(REPORTS_DIR / "permutation_importance_temporal.csv", index=False)

    fig, _ = plot_feature_importance(
        permutation.rename(columns={"importance_mean": "importance"}),
        importance_column="importance",
        title="Importancia por permutacao - validacao temporal",
    )
    save_current_figure(IMAGES_DIR / "model_permutation_importance_temporal.png")

    _write_report(
        logistic_coefficients=logistic_coefficients,
        random_forest_importance=random_forest_importance,
        permutation_importance=permutation,
        output_path=REPORTS_DIR / "interpretability.md",
    )

    print(f"Reports saved in: {REPORTS_DIR}")
    print(f"Figures saved in: {IMAGES_DIR}")


if __name__ == "__main__":
    run()
