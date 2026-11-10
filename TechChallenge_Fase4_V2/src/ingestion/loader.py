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


def load_reviews(path=DEFAULT_CSV, deduplicate: bool = True) -> list[dict]:
    df = pd.read_csv(path)
    df = df[df["review_comment_message"].notna()]
    df = df[df["review_comment_message"].str.strip() != ""]
    df["_text_norm"] = df["review_comment_message"].apply(_normalize_text)
    if deduplicate:
        df = df.drop_duplicates(subset="_text_norm", keep="first")
    records = []
    for _, row in df.iterrows():
        records.append({
            "id": row["review_id"],
            "title": str(row.get("review_comment_title") or ""),
            "text": row["_text_norm"],
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
