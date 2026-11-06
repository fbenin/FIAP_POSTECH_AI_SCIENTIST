"""Ingestion helpers — load and summarize raw review data."""

from .loader import load_reviews, summarize_reviews

__all__ = [
    "load_reviews",
    "summarize_reviews",
]
