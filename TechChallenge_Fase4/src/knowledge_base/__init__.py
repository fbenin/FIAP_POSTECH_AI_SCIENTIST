"""Knowledge base: embedding generation and FAISS index construction."""

from src.knowledge_base.builder import (
    DOCS_FILENAME,
    EMBEDDING_MODEL,
    INDEX_FILENAME,
    build_index,
    load_documents,
)

__all__ = [
    "DOCS_FILENAME",
    "EMBEDDING_MODEL",
    "INDEX_FILENAME",
    "build_index",
    "load_documents",
]
