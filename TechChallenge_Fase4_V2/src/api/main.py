"""FastAPI app — exposes the RAG pipeline as a REST API."""

from fastapi import FastAPI, HTTPException

from src.api.schemas import HealthResponse, QueryRequest, QueryResponse
from src.rag.chain import ask

app = FastAPI(
    title="Olist Reviews RAG API",
    description="Responde perguntas sobre reviews de clientes da Olist usando RAG.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="question não pode ser vazia")
    return ask(request.question)
