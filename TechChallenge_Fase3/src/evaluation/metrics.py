"""Evaluation metrics for binary classification."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _positive_scores(model: Any, X_test: pd.DataFrame):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_test)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(X_test)
    return None


def evaluate_classifier(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    """Evaluate one fitted classifier with standard binary metrics."""
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    y_pred = model.predict(X_test)
    scores = _positive_scores(model, X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    if scores is not None and y_test.nunique() == 2:
        metrics["roc_auc"] = roc_auc_score(y_test, scores)
    else:
        metrics["roc_auc"] = None

    return metrics


def evaluate_models(
    models: dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, dict[str, Any]]:
    """Evaluate multiple fitted models."""
    return {
        name: evaluate_classifier(model, X_test, y_test)
        for name, model in models.items()
    }


def metrics_to_frame(metrics: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Convert the metrics dictionary to a sorted DataFrame."""
    rows = []
    for model_name, values in metrics.items():
        row = {"model": model_name}
        row.update({k: v for k, v in values.items() if k != "confusion_matrix"})
        rows.append(row)

    return pd.DataFrame(rows).sort_values(["f1", "recall"], ascending=False)
