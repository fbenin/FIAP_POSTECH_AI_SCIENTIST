"""Prompt templates in Portuguese for the RAG chain."""

from __future__ import annotations


RAG_SYSTEM_PROMPT = (
    "Você é um analista de experiência do cliente. Responda APENAS com base nos depoimentos de clientes fornecidos abaixo.\n"
    "Se os depoimentos não contiverem informações suficientes para responder, diga exatamente: "
    '"Não encontrei evidências suficientes nos reviews disponíveis."\n'
    "Não invente informações. Cite os depoimentos relevantes ao final da resposta.\n"
    "\n"
    "Depoimentos:\n"
    "{context}"
)

RAG_HUMAN_TEMPLATE = "Pergunta: {question}"


def build_prompt():
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_HUMAN_TEMPLATE),
        ]
    )
