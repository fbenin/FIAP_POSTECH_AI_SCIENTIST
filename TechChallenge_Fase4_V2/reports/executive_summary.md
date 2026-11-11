# Resumo Executivo — Voice of Customer Intelligence com RAG

**Tech Challenge Fase 4 — Pos Tech FIAP AI Scientist**

---

## Contexto

Empresas de e-commerce acumulam milhares de avaliações escritas por clientes a cada mês.
Embora as notas numéricas (1–5 estrelas) sejam fáceis de monitorar, a maior parte dos insights
estratégicos está nos comentários em texto livre: motivos de insatisfação, elogios específicos,
padrões recorrentes por categoria de produto ou período.

Analisar manualmente esse volume de dados é inviável. Filtros por palavras-chave capturam o
óbvio mas perdem nuances. Dashboards agregados escondem o detalhe que fundamenta uma decisão.

---

## A Solução

Desenvolvemos um sistema de **Voice of Customer Intelligence** baseado em
**Retrieval-Augmented Generation (RAG)** que transforma o acervo de avaliações em uma base de
conhecimento conversacional.

Gestores e analistas fazem perguntas em linguagem natural — o sistema recupera os comentários
mais relevantes e gera respostas estruturadas citando as evidências reais que as sustentam.

**Exemplos de perguntas respondidas:**
- *"Quais são os principais motivos de insatisfação dos clientes?"*
- *"O que os clientes reclamam sobre entrega em produtos de eletrônicos?"*
- *"Quais aspectos os clientes mais elogiam?"*
- *"Existem padrões nas avaliações de clientes que receberam o produto com atraso?"*

---

## Como Funciona

```
Pergunta do gestor
      ↓
Sistema encontra os comentários mais semanticamente relevantes (~37k avaliações indexadas)
      ↓
Filtra por relevância mínima (evita respostas sem fundamento)
      ↓
Envia os comentários + metadados ao modelo de linguagem
      ↓
Resposta estruturada com trechos citados e indicação de evidência
```

Quando não há comentários suficientemente relevantes, o sistema declara isso explicitamente
em vez de fabricar uma resposta — um requisito crítico para uso em contexto de negócios.

---

## Dataset

O sistema foi desenvolvido e validado sobre o **Brazilian E-Commerce Public Dataset by Olist**
(Kaggle), com ~115 mil pedidos realizados entre 2016 e 2018. Após filtragem e deduplicação,
foram indexadas **~37 mil avaliações únicas** com texto.

Cada avaliação pode ser enriquecida com:
- Categoria do produto comprado
- Dias de antecipação ou atraso na entrega
- Mês e ano da compra

---

## Principais Resultados

| Métrica | Resultado |
|---------|-----------|
| Corpus indexado | ~37 mil avaliações únicas |
| Threshold de relevância | 0.75 (validado experimentalmente) |
| Perguntas in-scope com evidência | 100% retornaram documentos relevantes |
| Perguntas fora de escopo | Fallback ativado corretamente |
| Suporte multilingual | Português, inglês e espanhol funcionam sem tradução |

---

## Tecnologias Utilizadas

| Componente | Tecnologia |
|------------|------------|
| Embeddings (indexação e consulta) | `paraphrase-multilingual-MiniLM-L12-v2` — local, sem custo de API |
| Base vetorial | ChromaDB — persistência em disco, sem servidor externo |
| LLM para geração | OpenAI GPT-4o-mini / Groq Llama-3 / Together AI / Ollama |
| Framework | LangChain + FastAPI |
| Containerização | Docker + docker-compose |

---

## Valor Gerado

**Para analistas de CX:** Exploração rápida de padrões sem depender de um time de dados.
Perguntas ad hoc respondem em segundos com evidências rastreáveis.

**Para gestores de produto:** Identificação de problemas recorrentes por categoria antes que
se tornem tendência visível nos KPIs quantitativos.

**Para operações:** Análise de reclamações de entrega correlacionadas com delta de prazo,
permitindo priorização de melhorias logísticas com base em evidências reais de clientes.

**Rastreabilidade:** Cada resposta cita as avaliações que a embasaram. Isso é auditável —
o insight não é uma "caixa preta", é uma síntese verificável de opiniões reais.

---

## Limitações Conhecidas

- O sistema não tem memória de conversa: cada pergunta é independente.
- Queries genéricas (*"bom"*, *"ruim"*) retornam resultados pouco informativos.
- O enriquecimento de metadados requer download e re-indexação completa dos CSVs adicionais.

---

## Próximos Passos Sugeridos

1. **Interface conversacional:** Adicionar histórico de conversa para perguntas de follow-up.
2. **Filtros por metadados:** Permitir filtrar por categoria, período ou faixa de nota diretamente
   na query (ex: *"apenas avaliações com nota ≤ 2 de móveis em 2018"*).
3. **Avaliação automática:** Implementar métricas RAG (faithfulness, answer relevance) com
   frameworks como RAGAS para monitoramento contínuo da qualidade.
