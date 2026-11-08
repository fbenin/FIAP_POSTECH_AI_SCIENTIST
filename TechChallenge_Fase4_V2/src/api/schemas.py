"""Request and response models for the RAG API."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class SourceDocument(BaseModel):
    id: str
    text: str
    score: int
    date: str
    similarity: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]


class HealthResponse(BaseModel):
    status: str
