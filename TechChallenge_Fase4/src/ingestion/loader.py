"""Load and normalize raw Olist review CSV into a list of dicts."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_CSV = RAW_DATA_DIR / "olist_order_reviews_dataset.csv"


def _normalize_text(raw: str) -> str:
    text = raw.lower().strip()
    return re.sub(r"[\x00-\x1f]", " ", text)


def load_reviews(path=DEFAULT_CSV) -> list[dict]:
    df = pd.read_csv(path)
    df = df[df["review_comment_message"].notna()]
    df = df[df["review_comment_message"].str.strip() != ""]
    records = []
    for _, row in df.iterrows():
        records.append({
            "id": row["review_id"],
            "text": _normalize_text(row["review_comment_message"]),
            "score": int(row["review_score"]),
            "date": str(row["review_creation_date"]),
        })
    return records


def summarize_reviews(reviews: list[dict]) -> dict:
    scores = [r["score"] for r in reviews]
    dates = [r["date"] for r in reviews]
    score_distribution = {s: scores.count(s) for s in range(1, 6)}
    return {
        "total": len(reviews),
        "score_distribution": score_distribution,
        "date_range": {"min": min(dates), "max": max(dates)},
    }
