"""Build and persist the ChromaDB vector index from review data."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
CHROMA_PERSIST_DIR = PROJECT_ROOT / os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "olist_reviews")


def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


def build(reviews: list[dict]):
    from langchain_chroma import Chroma
    from langchain_core.documents import Document

    docs = []
    for r in reviews:
        metadata = {
            "id": r["id"],
            "score": r["score"],
            "date": r["date"],
        }
        for key in ("product_category", "delivery_delta_days", "purchase_year", "purchase_month"):
            if key in r:
                metadata[key] = r[key]
        docs.append(Document(page_content=r["text"], metadata=metadata))

    print(f"Indexing {len(docs)} documents...")
    vectorstore = Chroma.from_documents(
        docs,
        get_embeddings(),
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(CHROMA_PERSIST_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
    print("Done.")
    return vectorstore


def load_existing():
    from langchain_chroma import Chroma

    if not CHROMA_PERSIST_DIR.exists():
        raise FileNotFoundError(
            f"ChromaDB directory not found at {CHROMA_PERSIST_DIR}. "
            "Run `python -m src.embeddings.builder` first."
        )
    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_PERSIST_DIR),
    )


if __name__ == "__main__":
    from src.ingestion import load_reviews

    reviews = load_reviews(enrich=True)
    build(reviews)
