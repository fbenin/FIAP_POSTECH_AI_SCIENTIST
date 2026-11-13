"""RAG pipeline: grounded response generation from retrieved reviews."""

from __future__ import annotations

from openai import OpenAI

from src.retrieval.searcher import ReviewSearcher

# Minimum cosine similarity to accept a document as evidence
MIN_SCORE = 0.30
# Minimum number of relevant documents before we attempt a response
MIN_EVIDENCE_COUNT = 2

SYSTEM_PROMPT = """\
Você é um analista especializado em experiência do cliente para uma empresa de e-commerce brasileiro.

Sua tarefa é responder perguntas sobre as avaliações de clientes utilizando EXCLUSIVAMENTE \
as avaliações fornecidas como contexto. Siga estas regras:

1. Baseie cada afirmação em pelo menos uma das avaliações fornecidas.
2. Ao identificar padrões ou problemas, cite trechos concretos das avaliações.
3. Se as avaliações não contiverem informações suficientes para responder à pergunta, \
diga isso claramente — não invente informações.
4. Organize a resposta de forma objetiva e estruturada.
5. Responda em português.\
"""


def build_context(docs: list[dict]) -> str:
    """Format retrieved documents into a numbered context block for the LLM."""
    lines = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get("metadata", {})
        score = meta.get("review_score", "?")
        sim = doc.get("similarity_score", 0)
        lines.append(
            f"[Avaliação {i} | Nota: {score}/5 | Similaridade: {sim:.2f}]\n{doc['text']}"
        )
    return "\n\n---\n\n".join(lines)


def answer(
    question: str,
    searcher: ReviewSearcher,
    k: int = 15,
    min_score: float = MIN_SCORE,
    model: str = "gpt-4o-mini",
    client: OpenAI | None = None,
) -> dict:
    """Answer a question grounded in semantically retrieved reviews.

    Args:
        question:  natural-language question from the user
        searcher:  loaded ReviewSearcher instance
        k:         number of candidate reviews to retrieve
        min_score: cosine similarity threshold; reviews below this are excluded
        model:     OpenAI chat model name
        client:    optional pre-configured OpenAI client (created if None)

    Returns:
        dict with keys:
            answer       — generated response (str)
            evidence     — list of retrieved document dicts used as context
            has_evidence — False when fewer than MIN_EVIDENCE_COUNT reviews
                           were found; the answer will state this explicitly
    """
    if client is None:
        client = OpenAI()

    retrieved = searcher.search(question, k=k, min_score=min_score)

    if len(retrieved) < MIN_EVIDENCE_COUNT:
        return {
            "answer": (
                "Não foram encontradas avaliações suficientemente relevantes na base de "
                "conhecimento para responder a esta pergunta com evidências confiáveis. "
                "Tente reformular ou faça uma pergunta relacionada aos temas presentes "
                "nas avaliações de clientes do e-commerce (entrega, produto, atendimento, etc.)."
            ),
            "evidence": retrieved,
            "has_evidence": False,
        }

    context = build_context(retrieved)

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Pergunta: {question}\n\n"
                    f"Avaliações recuperadas:\n\n{context}"
                ),
            },
        ],
    )

    return {
        "answer": response.choices[0].message.content,
        "evidence": retrieved,
        "has_evidence": True,
    }
