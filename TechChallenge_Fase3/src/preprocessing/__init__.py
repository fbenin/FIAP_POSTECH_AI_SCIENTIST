"""Data loading and feature preparation helpers."""

from .features import (
    CANDIDATE_CATEGORICAL_FEATURES,
    CANDIDATE_NUMERIC_FEATURES,
    LEAKAGE_COLUMNS,
    TARGET_COLUMN,
    build_feature_matrix,
    create_binary_target,
    get_feature_columns,
    load_gold_tables,
    load_indicator_municipio,
    summarize_dataset,
)

__all__ = [
    "CANDIDATE_CATEGORICAL_FEATURES",
    "CANDIDATE_NUMERIC_FEATURES",
    "LEAKAGE_COLUMNS",
    "TARGET_COLUMN",
    "build_feature_matrix",
    "create_binary_target",
    "get_feature_columns",
    "load_gold_tables",
    "load_indicator_municipio",
    "summarize_dataset",
]
