"""Semantic search over the FAISS review index."""

from __future__ import annotations

import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.knowledge_base.builder import DOCS_FILENAME, EMBEDDING_MODEL, INDEX_FILENAME


class ReviewSearcher:
    """Load a pre-built FAISS index and run semantic queries against it.

    Usage:
        searcher = ReviewSearcher("data/processed")
        results = searcher.search("produto chegou com defeito", k=10)
    """

    def __init__(self, index_dir: str | Path, model_name: str = EMBEDDING_MODEL) -> None:
        index_dir = Path(index_dir)
        self.index = faiss.read_index(str(index_dir / INDEX_FILENAME))
        with open(index_dir / DOCS_FILENAME, "rb") as f:
            self.documents: list[dict] = pickle.load(f)
        self.model = SentenceTransformer(model_name)

    def search(
        self,
        query: str,
        k: int = 10,
        min_score: float = 0.30,
    ) -> list[dict]:
        """Return up to k documents semantically similar to query.

        Args:
            query:     natural-language question or keyword
            k:         maximum number of candidates to retrieve
            min_score: cosine similarity threshold (0–1); documents below
                       this threshold are discarded to avoid weak evidence

        Returns:
            List of document dicts, each augmented with a ``similarity_score``
            key, sorted by descending similarity.
        """
        embedding: np.ndarray = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        scores, indices = self.index.search(embedding, k)

        results = []
        for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
            if idx < 0:
                continue
            if score < min_score:
                continue
            doc = dict(self.documents[idx])
            doc["similarity_score"] = round(score, 4)
            results.append(doc)

        return results
