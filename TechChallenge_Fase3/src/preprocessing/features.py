"""Feature preparation for the Fase 3 modeling problem.

The Gold layer is aggregated by municipality, year, grade and school network.
The binary target uses `categoria_risco` as a proxy for whether the educational
goal was reached in that aggregate record.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLD_DATA_DIR = PROJECT_ROOT / "data" / "gold"
TARGET_COLUMN = "target"

LEAKAGE_COLUMNS = (
    "taxa_alfabetizacao",
    "gap_meta_municipio_2030",
    "gap_meta_uf_2030",
    "atingiu_meta_uf",
    "categoria_risco",
)

CANDIDATE_NUMERIC_FEATURES = (
    "ano",
    "media_portugues",
    "meta_mun_2030",
    "meta_uf_2030",
    "meta_brasil_2030",
)

LEVEL_PROPORTION_FEATURES = (
    "proporcao_aluno_nivel_0",
    "proporcao_aluno_nivel_1",
    "proporcao_aluno_nivel_2",
    "proporcao_aluno_nivel_3",
)

CANDIDATE_CATEGORICAL_FEATURES = (
    "sigla_uf",
    "serie",
    "rede",
)


def load_gold_tables(data_dir: str | Path = GOLD_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load every single-file Parquet table from the local Gold directory."""
    data_dir = Path(data_dir)
    tables: dict[str, pd.DataFrame] = {}

    for table_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        parquet_files = sorted(table_dir.glob("*.parquet"))
        if not parquet_files:
            continue
        tables[table_dir.name] = pd.read_parquet(parquet_files[0])

    return tables


def load_indicator_municipio(data_dir: str | Path = GOLD_DATA_DIR) -> pd.DataFrame:
    """Load the main modeling table."""
    path = Path(data_dir) / "indicador_municipio" / "indicador_municipio.parquet"
    return pd.read_parquet(path)


def create_binary_target(
    df: pd.DataFrame,
    source_column: str = "categoria_risco",
    positive_label: str = "meta_atingida",
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Create a binary target where 1 means the goal was reached."""
    if source_column not in df.columns:
        raise KeyError(f"Column not found for target creation: {source_column}")

    result = df.copy()
    result[target_column] = (result[source_column] == positive_label).astype(int)
    return result


def _existing_columns(df: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    return [column for column in columns if column in df.columns]


def get_feature_columns(
    df: pd.DataFrame,
    include_level_proportions: bool = False,
    drop_constant: bool = True,
) -> tuple[list[str], list[str]]:
    """Return numeric and categorical feature columns without leakage columns."""
    numeric_features = list(CANDIDATE_NUMERIC_FEATURES)
    if include_level_proportions:
        numeric_features.extend(LEVEL_PROPORTION_FEATURES)

    numeric_features = _existing_columns(df, numeric_features)
    categorical_features = _existing_columns(df, CANDIDATE_CATEGORICAL_FEATURES)

    if drop_constant:
        numeric_features = [
            column for column in numeric_features if df[column].nunique(dropna=True) > 1
        ]
        categorical_features = [
            column for column in categorical_features if df[column].nunique(dropna=True) > 1
        ]

    return numeric_features, categorical_features


def build_feature_matrix(
    df: pd.DataFrame,
    include_level_proportions: bool = False,
    drop_constant: bool = True,
) -> tuple[pd.DataFrame, pd.Series, dict[str, list[str]]]:
    """Create X, y and feature metadata for the first predictive model."""
    modeled = create_binary_target(df)
    numeric_features, categorical_features = get_feature_columns(
        modeled,
        include_level_proportions=include_level_proportions,
        drop_constant=drop_constant,
    )
    feature_columns = numeric_features + categorical_features

    X = modeled[feature_columns].copy()
    y = modeled[TARGET_COLUMN].copy()
    feature_info = {
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "excluded_leakage_columns": [c for c in LEAKAGE_COLUMNS if c in modeled.columns],
    }

    return X, y, feature_info


def summarize_dataset(df: pd.DataFrame) -> dict[str, object]:
    """Return compact metadata used by notebooks and reports."""
    if "categoria_risco" in df.columns:
        target = (df["categoria_risco"] == "meta_atingida").astype(int)
        positive_rate = float(target.mean())
        target_counts = target.value_counts().sort_index().to_dict()
    else:
        positive_rate = None
        target_counts = {}

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "years": sorted(df["ano"].dropna().unique().tolist()) if "ano" in df else [],
        "municipalities": int(df["id_municipio"].nunique()) if "id_municipio" in df else None,
        "states": int(df["sigla_uf"].nunique()) if "sigla_uf" in df else None,
        "target_positive_rate": positive_rate,
        "target_counts": target_counts,
    }
