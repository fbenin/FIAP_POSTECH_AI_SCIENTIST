"""Embeddings helpers — build and load the ChromaDB vector index."""

from .builder import build, get_embeddings, load_existing

__all__ = [
    "build",
    "get_embeddings",
    "load_existing",
]
