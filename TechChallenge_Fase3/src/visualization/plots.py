"""Reusable plotting helpers for notebooks and reports."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")


def save_current_figure(path: str | Path, dpi: int = 160) -> Path:
    """Save the current Matplotlib figure with consistent defaults."""
    import matplotlib.pyplot as plt

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    return output_path


def plot_target_distribution(
    y: pd.Series,
    title: str = "Distribuicao do target binario",
):
    """Plot the binary target distribution."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, ax = plt.subplots(figsize=(7, 4))
    counts = y.value_counts().sort_index().rename(index={0: "Em risco", 1: "Meta atingida"})
    sns.barplot(x=counts.index.astype(str), y=counts.values, ax=ax, color="#4C78A8")
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("Registros")
    return fig, ax


def plot_feature_importance(
    feature_importance: pd.DataFrame,
    feature_column: str = "feature",
    importance_column: str = "importance",
    top_n: int = 20,
    title: str = "Importancia das variaveis",
):
    """Plot the top feature importances from a prepared DataFrame."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    plot_data = (
        feature_importance[[feature_column, importance_column]]
        .sort_values(importance_column, ascending=False)
        .head(top_n)
        .sort_values(importance_column)
    )

    height = max(3.5, 0.45 * len(plot_data) + 1.5)
    fig, ax = plt.subplots(figsize=(10, height))
    sns.barplot(data=plot_data, y=feature_column, x=importance_column, ax=ax, color="#F58518")
    ax.set_title(title)
    ax.set_xlabel("Importancia")
    ax.set_ylabel("")
    return fig, ax
