"""Scikit-learn pipelines and training helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _build_one_hot_encoder() -> Any:
    from sklearn.preprocessing import OneHotEncoder

    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> Any:
    """Build a ColumnTransformer with imputation, scaling and encoding."""
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", _build_one_hot_encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def build_model_pipeline(
    model: Any,
    numeric_features: list[str],
    categorical_features: list[str],
) -> Any:
    """Combine preprocessing and estimator in one reproducible pipeline."""
    from sklearn.pipeline import Pipeline

    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(numeric_features, categorical_features)),
            ("model", model),
        ]
    )


def get_candidate_models(random_state: int = 42) -> dict[str, Any]:
    """Return baseline and first-pass supervised models."""
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    return {
        "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=1,
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            random_state=random_state,
        ),
    }


def split_train_test(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Create a reproducible train/test split."""
    from sklearn.model_selection import train_test_split

    stratify_values = y if stratify else None
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_values,
    )


def split_temporal_train_test(
    X: pd.DataFrame,
    y: pd.Series,
    year_column: str = "ano",
    train_year: int = 2023,
    test_year: int = 2024,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Create a temporal split using one year for train and one for test."""
    if year_column not in X.columns:
        raise KeyError(f"Temporal split requires feature column: {year_column}")

    train_mask = X[year_column] == train_year
    test_mask = X[year_column] == test_year

    if not train_mask.any():
        raise ValueError(f"No rows found for train_year={train_year}")
    if not test_mask.any():
        raise ValueError(f"No rows found for test_year={test_year}")

    return X.loc[train_mask], X.loc[test_mask], y.loc[train_mask], y.loc[test_mask]


def train_candidate_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
) -> dict[str, Any]:
    """Fit every candidate model and return trained pipelines."""
    trained_models: dict[str, Any] = {}

    for name, model in get_candidate_models(random_state=random_state).items():
        pipeline = build_model_pipeline(model, numeric_features, categorical_features)
        pipeline.fit(X_train, y_train)
        trained_models[name] = pipeline

    return trained_models
