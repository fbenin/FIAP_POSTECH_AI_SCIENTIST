"""LCEL RAG chain — retrieves reviews and returns a cited answer."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "")
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini")
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
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
        parts.append(f"[{i}] Score: {doc['score']}\nTexto: {doc['text']}")
    return "\n\n".join(parts)


def build_chain(store=None):
    from langchain_core.output_parsers import StrOutputParser

    from src.rag.prompts import build_prompt
    from src.retrieval import get_store

    if store is None:
        store = get_store()

    prompt = build_prompt()
    llm = get_llm()
    parser = StrOutputParser()

    def _run(inputs: dict) -> str:
        question = inputs["question"]
        docs = store.search_above_threshold(question)
        context = format_context(docs)
        messages = prompt.format_messages(context=context, question=question)
        return parser.parse(llm.invoke(messages).content)

    return _run


def ask(question: str, show_sources: bool = True) -> dict:
    from langchain_core.output_parsers import StrOutputParser

    from src.rag.prompts import build_prompt
    from src.retrieval import get_store

    store = get_store()
    docs = store.search_above_threshold(question)
    if not docs:
        return {
            "answer": "Não encontrei evidências suficientes nos reviews disponíveis.",
            "sources": [],
        }
    context = format_context(docs)
    prompt = build_prompt()
    llm = get_llm()
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
