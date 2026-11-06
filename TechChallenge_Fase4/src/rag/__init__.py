"""RAG chain — build and query the retrieval-augmented generation pipeline."""

from .chain import ask, build_chain

__all__ = [
    "ask",
    "build_chain",
]
