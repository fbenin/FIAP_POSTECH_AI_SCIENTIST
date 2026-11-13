"""Build and persist the FAISS vector index from processed documents."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
INDEX_FILENAME = "reviews.index"
DOCS_FILENAME = "documents.pkl"


def load_documents(documents_path: str | Path) -> list[dict]:
    """Load the documents.json produced by the ingestion pipeline."""
    with open(Path(documents_path), encoding="utf-8") as f:
        return json.load(f)


def build_index(
    documents_path: str | Path,
    output_dir: str | Path,
    model_name: str = EMBEDDING_MODEL,
    batch_size: int = 256,
) -> tuple[faiss.Index, list[dict]]:
    """Generate embeddings for every document and save a FAISS index.

    Uses IndexFlatIP (inner product) over L2-normalized vectors, which is
    equivalent to cosine similarity and requires no training phase.

    Args:
        documents_path: path to data/processed/documents.json
        output_dir:     folder where the index and document list are saved
        model_name:     sentence-transformers model to use
        batch_size:     encoding batch size (reduce if memory is tight)

    Returns:
        (faiss_index, documents) — already persisted to output_dir
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    documents = load_documents(documents_path)
    texts = [doc["text"] for doc in documents]

    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    print(f"Encoding {len(texts):,} documents…")
    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2-normalize in place → cosine via IndexFlatIP
    )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    index_path = output_dir / INDEX_FILENAME
    docs_path = output_dir / DOCS_FILENAME

    faiss.write_index(index, str(index_path))
    with open(docs_path, "wb") as f:
        pickle.dump(documents, f)

    print(f"Index saved  → {index_path}  ({index.ntotal:,} vectors, dim={dim})")
    print(f"Docs saved   → {docs_path}")

    return index, documents
