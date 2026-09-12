"""Interpretability helpers for fitted Scikit-learn pipelines."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _clean_feature_name(name: str) -> str:
    return (
        name.replace("numeric__", "")
        .replace("categorical__", "")
        .replace("remainder__", "")
    )


def get_transformed_feature_names(pipeline: Any) -> list[str]:
    """Return transformed feature names from a fitted preprocessing pipeline."""
    preprocessor = pipeline.named_steps["preprocessor"]
    return [_clean_feature_name(name) for name in preprocessor.get_feature_names_out()]


def get_linear_coefficients(pipeline: Any) -> pd.DataFrame:
    """Extract coefficients from a fitted linear model pipeline."""
    model = pipeline.named_steps["model"]
    if not hasattr(model, "coef_"):
        raise TypeError("The fitted model does not expose coef_.")

    coefficients = model.coef_[0]
    return (
        pd.DataFrame(
            {
                "feature": get_transformed_feature_names(pipeline),
                "coefficient": coefficients,
                "abs_coefficient": abs(coefficients),
            }
        )
        .sort_values("abs_coefficient", ascending=False)
        .reset_index(drop=True)
    )


def get_model_feature_importance(pipeline: Any) -> pd.DataFrame:
    """Extract feature importances from a fitted tree-based model pipeline."""
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        raise TypeError("The fitted model does not expose feature_importances_.")

    return (
        pd.DataFrame(
            {
                "feature": get_transformed_feature_names(pipeline),
                "importance": model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def get_permutation_importance(
    pipeline: Any,
    X: pd.DataFrame,
    y: pd.Series,
    scoring: str = "f1",
    n_repeats: int = 10,
    random_state: int = 42,
) -> pd.DataFrame:
    """Calculate permutation importance on the original feature columns."""
    from sklearn.inspection import permutation_importance

    result = permutation_importance(
        pipeline,
        X,
        y,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=1,
    )

    return (
        pd.DataFrame(
            {
                "feature": X.columns,
                "importance_mean": result.importances_mean,
                "importance_std": result.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )
