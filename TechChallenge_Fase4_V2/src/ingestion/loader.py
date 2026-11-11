"""Load and normalize raw Olist review CSV into a list of dicts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_CSV = RAW_DATA_DIR / "olist_order_reviews_dataset.csv"


def _normalize_text(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw).strip()
    text = re.sub(r"([!?,.]){2,}", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _coerce(val) -> str:
    """Convert a None/NaN/float value from pandas to a plain string."""
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val).strip()


def _build_text(title: str, message: str) -> str | None:
    title = title.strip()
    message = message.strip()
    if title and message:
        return f"{title}. {message}"
    return title or message or None


def _load_enrichment(data_dir: Path) -> pd.DataFrame | None:
    """Joins orders + items + products to add delivery and category metadata.

    Returns a DataFrame with order_id as key and enrichment columns, or None
    if any of the required CSVs are missing from data_dir.
    """
    try:
        orders = pd.read_csv(
            data_dir / "olist_orders_dataset.csv",
            usecols=[
                "order_id",
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
            parse_dates=[
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        )
        items = pd.read_csv(
            data_dir / "olist_order_items_dataset.csv",
            usecols=["order_id", "product_id"],
        ).drop_duplicates("order_id")
        products = pd.read_csv(
            data_dir / "olist_products_dataset.csv",
            usecols=["product_id", "product_category_name"],
        )
        translation = pd.read_csv(data_dir / "product_category_name_translation.csv")
        products = products.merge(translation, on="product_category_name", how="left")
        enrichment = (
            orders
            .merge(items, on="order_id", how="left")
            .merge(
                products[["product_id", "product_category_name_english"]],
                on="product_id",
                how="left",
            )
        )
        enrichment["delivery_delta_days"] = (
            (
                enrichment["order_delivered_customer_date"]
                - enrichment["order_estimated_delivery_date"]
            ).dt.days
        )
        enrichment["purchase_year"] = enrichment["order_purchase_timestamp"].dt.year
        enrichment["purchase_month"] = enrichment["order_purchase_timestamp"].dt.month
        return enrichment[[
            "order_id",
            "purchase_year",
            "purchase_month",
            "delivery_delta_days",
            "product_category_name_english",
        ]]
    except FileNotFoundError:
        return None


def load_reviews(
    path=DEFAULT_CSV,
    deduplicate: bool = True,
    enrich: bool = True,
) -> list[dict]:
    path = Path(path)
    df = pd.read_csv(path)

    enrichment = _load_enrichment(path.parent) if enrich else None
    if enrichment is not None:
        df = df.merge(enrichment, on="order_id", how="left")

    df["_text"] = df.apply(
        lambda r: _build_text(
            _coerce(r.get("review_comment_title")),
            _coerce(r.get("review_comment_message")),
        ),
        axis=1,
    )
    df = df[df["_text"].notna() & (df["_text"].str.strip() != "")]
    df["_text"] = df["_text"].apply(_normalize_text)
    df = df[df["_text"].str.strip() != ""]

    if deduplicate:
        df = df.drop_duplicates(subset="_text", keep="first")

    records = []
    for _, row in df.iterrows():
        record = {
            "id": str(row["review_id"]),
            "text": row["_text"],
            "score": int(row["review_score"]),
            "date": str(row["review_creation_date"]),
        }
        if enrichment is not None:
            if pd.notna(row.get("delivery_delta_days")):
                record["delivery_delta_days"] = float(row["delivery_delta_days"])
            if pd.notna(row.get("product_category_name_english")):
                record["product_category"] = str(row["product_category_name_english"])
            if pd.notna(row.get("purchase_year")):
                record["purchase_year"] = int(row["purchase_year"])
            if pd.notna(row.get("purchase_month")):
                record["purchase_month"] = int(row["purchase_month"])
        records.append(record)

    return records


def summarize_reviews(reviews: list[dict]) -> dict:
    scores = [r["score"] for r in reviews]
    dates = [r["date"] for r in reviews]
    score_distribution = {s: scores.count(s) for s in range(1, 6)}
    categories = {r["product_category"] for r in reviews if "product_category" in r}
    return {
        "total": len(reviews),
        "score_distribution": score_distribution,
        "date_range": {"min": min(dates), "max": max(dates)},
        "enriched_with_metadata": sum(1 for r in reviews if "product_category" in r),
        "unique_categories": len(categories),
    }
