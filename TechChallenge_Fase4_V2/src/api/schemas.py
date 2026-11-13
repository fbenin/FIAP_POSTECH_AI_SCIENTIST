"""Request and response models for the RAG API."""

from __future__ import annotations

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class SourceDocument(BaseModel):
    id: str
    text: str
    score: int
    date: str
    similarity: float
    product_category: str | None = None
    delivery_delta_days: float | None = None
    purchase_year: int | None = None
    purchase_month: int | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    has_evidence: bool


class HealthResponse(BaseModel):
    status: str
