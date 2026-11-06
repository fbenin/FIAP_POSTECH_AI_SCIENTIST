"""Thin wrapper around ChromaDB for similarity search."""

from __future__ import annotations


class ReviewStore:
    def __init__(self, vectorstore) -> None:
        self._vectorstore = vectorstore

    def search(self, query: str, k: int = 5) -> list[dict]:
        # similarity_search_with_score retorna (doc, cosine_distance)
        # onde 0 = idêntico e 2 = oposto. Convertemos para similaridade [0, 1].
        results = self._vectorstore.similarity_search_with_score(query, k=k)
        docs = []
        for doc, distance in results:
            similarity = max(0.0, 1.0 - distance / 2.0)
            docs.append({
                "text": doc.page_content,
                "score": doc.metadata.get("score"),
                "date": doc.metadata.get("date"),
                "id": doc.metadata.get("id"),
                "similarity": float(similarity),
            })
        return sorted(docs, key=lambda x: x["similarity"], reverse=True)

    def search_above_threshold(
        self, query: str, k: int = 5, threshold: float = 0.4
    ) -> list[dict]:
        return [r for r in self.search(query, k=k) if r["similarity"] >= threshold]


def get_store() -> ReviewStore:
    from src.embeddings import load_existing

    return ReviewStore(load_existing())
