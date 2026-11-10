"""LCEL RAG chain — retrieves reviews and returns a cited answer."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

_store_cache: object = None
_llm_cache: object = None


def _get_cached_store():
    global _store_cache
    if _store_cache is None:
        from src.retrieval import get_store
        _store_cache = get_store()
    return _store_cache


def _get_cached_llm():
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = get_llm()
    return _llm_cache


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "")
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini")
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            api_key=os.getenv("GROQ_API_KEY"),
        )
    if provider == "together":
        from langchain_together import ChatTogether

        return ChatTogether()
    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model="llama3",
        )
    raise ValueError(
        f"Unknown LLM_PROVIDER: '{provider}'. "
        "Set LLM_PROVIDER to 'openai', 'groq', 'together', or 'ollama'."
    )


def format_context(docs: list[dict]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        title = doc.get("title", "")
        title_line = f"Título: {title}\n" if title else ""
        parts.append(f"[{i}] Score: {doc['score']}\n{title_line}Texto: {doc['text']}")
    return "\n\n".join(parts)


def ask(question: str, show_sources: bool = True) -> dict:
    from langchain_core.output_parsers import StrOutputParser

    from src.rag.prompts import build_prompt

    threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
    store = _get_cached_store()
    docs = store.search_above_threshold(question, threshold=threshold)
    if not docs:
        return {
            "answer": "Não encontrei evidências suficientes nos reviews disponíveis.",
            "sources": [],
        }
    context = format_context(docs)
    prompt = build_prompt()
    llm = _get_cached_llm()
    messages = prompt.format_messages(context=context, question=question)
    answer = StrOutputParser().parse(llm.invoke(messages).content)
    return {"answer": answer, "sources": docs}


if __name__ == "__main__":
    questions = [
        "Quais são os principais problemas de entrega relatados pelos clientes?",
        "Como os clientes avaliam a qualidade dos produtos?",
        "Como é o atendimento ao cliente segundo os reviews?",
        "O que os clientes mais elogiam nas compras?",
        "Qual é a capital da França?",
    ]
    for q in questions:
        print(f"\nPergunta: {q}")
        result = ask(q)
        print(f"Resposta: {result['answer']}")
        if result["sources"]:
            print(f"Fontes ({len(result['sources'])}):")
            for s in result["sources"]:
                print(f"  - [{s['similarity']:.2f}] {s['text'][:80]}...")
