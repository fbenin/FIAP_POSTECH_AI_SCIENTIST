"""Text cleaning and document preparation for the RAG knowledge base."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


_WHITESPACE = re.compile(r"\s+")
_REPEATED_PUNCT = re.compile(r"([!?,.]){2,}")


def _normalize(text: str) -> str:
    """Normalize unicode (NFKC), collapse whitespace, deduplicate punctuation."""
    text = unicodedata.normalize("NFKC", text)
    text = _WHITESPACE.sub(" ", text).strip()
    text = _REPEATED_PUNCT.sub(r"\1", text)
    return text


def clean_text(text: str | None) -> str | None:
    """Return a cleaned version of a single review text, or None if empty."""
    if not isinstance(text, str):
        return None
    cleaned = _normalize(text)
    return cleaned if cleaned else None


def merge_title_and_message(
    df: pd.DataFrame,
    title_col: str = "review_comment_title",
    message_col: str = "review_comment_message",
    output_col: str = "review_text",
) -> pd.DataFrame:
    """Concatenate title and message into a single text field.

    When both are present: "<title>. <message>"
    When only one is present: whichever is not null
    When neither: None
    """
    def _combine(row: pd.Series) -> str | None:
        title = clean_text(row[title_col])
        message = clean_text(row[message_col])
        if title and message:
            return f"{title}. {message}"
        return title or message

    return df.assign(**{output_col: df.apply(_combine, axis=1)})


def filter_reviews_with_text(
    df: pd.DataFrame,
    text_col: str = "review_text",
) -> pd.DataFrame:
    """Keep only rows that have non-null text content."""
    return df[df[text_col].notna()].reset_index(drop=True)


def prepare_documents(df: pd.DataFrame, text_col: str = "review_text") -> list[dict]:
    """Convert a reviews DataFrame into a list of documents for the vector store.

    Each document has:
        - text: the cleaned review text
        - metadata: review_id, order_id, review_score, review_creation_date,
                    and any enrichment columns present (purchase_year,
                    purchase_month, delivery_delta_days,
                    product_category_name_english)
    """
    metadata_cols = [
        "review_id",
        "order_id",
        "review_score",
        "review_creation_date",
        "purchase_year",
        "purchase_month",
        "delivery_delta_days",
        "product_category_name_english",
    ]
    available = [c for c in metadata_cols if c in df.columns]

    documents = []
    for _, row in df[[text_col] + available].iterrows():
        metadata = {
            col: (None if pd.isna(row[col]) else row[col])
            for col in available
        }
        if isinstance(metadata.get("review_creation_date"), pd.Timestamp):
            metadata["review_creation_date"] = metadata["review_creation_date"].isoformat()

        documents.append({"text": row[text_col], "metadata": metadata})

    return documents


def build_documents(data_dir: str, enriched: bool = True) -> list[dict]:
    """Full pipeline: load → merge text → clean → filter → prepare.

    Args:
        data_dir: path to the folder containing the Olist CSVs
        enriched: if True, attempts to join with orders/products metadata

    Returns:
        List of document dicts ready for embedding.
    """
    from src.ingestion.loader import load_enriched_reviews, load_reviews

    df = load_enriched_reviews(data_dir) if enriched else load_reviews(data_dir)
    df = merge_title_and_message(df)
    df = filter_reviews_with_text(df)
    return prepare_documents(df)
