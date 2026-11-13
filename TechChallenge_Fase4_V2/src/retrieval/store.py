"""Thin wrapper around ChromaDB for similarity search."""

from __future__ import annotations

_ENRICHMENT_KEYS = ("product_category", "delivery_delta_days", "purchase_year", "purchase_month")


class ReviewStore:
    def __init__(self, vectorstore) -> None:
        self._vectorstore = vectorstore

    def search(self, query: str, k: int = 5) -> list[dict]:
        # similarity_search_with_score returns (doc, cosine_distance) where
        # cosine_distance = 1 - cosine_similarity, in range [0, 2].
        # We convert to a [0, 1] similarity score via 1 - distance/2.
        results = self._vectorstore.similarity_search_with_score(query, k=k)
        docs = []
        for doc, distance in results:
            similarity = max(0.0, 1.0 - distance / 2.0)
            entry = {
                "text": doc.page_content,
                "score": doc.metadata.get("score"),
                "date": doc.metadata.get("date"),
                "id": doc.metadata.get("id"),
                "similarity": float(similarity),
            }
            for key in _ENRICHMENT_KEYS:
                val = doc.metadata.get(key)
                if val is not None:
                    entry[key] = val
            docs.append(entry)
        return sorted(docs, key=lambda x: x["similarity"], reverse=True)

    def search_above_threshold(
        self, query: str, k: int = 5, threshold: float = 0.4
    ) -> list[dict]:
        return [r for r in self.search(query, k=k) if r["similarity"] >= threshold]


def get_store() -> ReviewStore:
    from src.embeddings import load_existing

    return ReviewStore(load_existing())
