# Tech Challenge - Fase 4: Voice of Customer Intelligence com RAG

## Contexto

Empresas de e-commerce recebem diariamente milhares de avaliacoes contendo percepcoes, elogios, reclamacoes e relatos sobre diferentes etapas da jornada de compra. Analisar manualmente esse volume de dados e uma tarefa complexa e pouco escalavel.

Este projeto desenvolve uma solucao de **Voice of Customer Intelligence** baseada em **Retrieval-Augmented Generation (RAG)**, capaz de permitir a exploracao inteligente das avaliacoes de clientes presentes na base **Brazilian E-Commerce Public Dataset by Olist** (Kaggle).

## Objetivo

Construir um sistema que permite a gestores e analistas realizarem perguntas em linguagem natural como:

- "Quais sao os principais problemas relatados pelos clientes?"
- "O que os clientes mais elogiam em sua experiencia de compra?"
- "Quais reclamacoes relacionadas a entrega aparecem com maior frequencia?"
- "Quais padroes podem ser identificados nas avaliacoes de clientes insatisfeitos?"

A solucao deve recuperar avaliacoes relevantes da base de conhecimento e utiliza-las como evidencia para fundamentar cada resposta, evitando alucinacoes e permitindo rastreabilidade dos insights.

## Base de Dados

- **Fonte**: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data)
- **Volume**: ~100 mil pedidos (2016-2018)
- **Foco**: Conteudos textuais das avaliacoes dos clientes (`review_comment_title`, `review_comment_message`)
- **Enriquecimento opcional**: nota da avaliacao, periodo da compra, categoria do produto, informacoes de entrega

## Arquitetura RAG

```
Pergunta do usuario
       |
       v
Preprocessamento da pergunta
       |
       v
Geracao de embedding da query
       |
       v
Busca semantica no vector store
       |
       v
Selecao das avaliacoes mais relevantes
       |
       v
Construcao do contexto para o LLM
       |
       v
Geracao da resposta com evidencias
       |
       v
Resposta fundamentada nas avaliacoes recuperadas
```

## Estrutura do Projeto

```
TechChallenge_Fase4/
├── data/
│   ├── raw/           # CSVs originais do Kaggle (gitignored)
│   └── processed/     # Base preprocessada e indexes vetoriais (gitignored)
├── notebooks/
│   ├── 01_exploracao.ipynb      # EDA das avaliacoes
│   ├── 02_base_conhecimento.ipynb  # Construcao da knowledge base
│   └── 03_experimentos_rag.ipynb   # Experimentos com o pipeline RAG
├── src/
│   ├── ingestion/         # Carga e limpeza dos dados Olist
│   ├── knowledge_base/    # Preprocessamento de texto e geracao de embeddings
│   ├── retrieval/         # Vector store e busca semantica
│   ├── rag/               # Pipeline RAG: contexto + geracao
│   └── evaluation/        # Metricas de avaliacao do RAG
├── reports/               # Relatorios e documentacao tecnica
├── images/                # Graficos e diagramas
├── requirements.txt
└── README.md
```

## Roadmap de Desenvolvimento

| PR | Descricao |
|---|---|
| #1 | Scaffold inicial do projeto (este PR) |
| #2 | Carga e exploracao dos dados Olist (EDA das avaliacoes) |
| #3 | Construcao da base de conhecimento (preprocessamento + embeddings + vector store) |
| #4 | Pipeline RAG (recuperacao semantica + geracao de respostas com evidencias) |
| #5 | Interface de consulta (CLI ou aplicacao web) |
| #6 | Avaliacao do sistema RAG + documentacao final |

## Como Executar

> Instrucoes serao detalhadas ao longo do desenvolvimento.

```bash
# Instalar dependencias
pip install -r requirements.txt

# Construir a base de conhecimento
python -m src.knowledge_base.build

# Executar o pipeline RAG
python -m src.rag.pipeline
```

## Tecnologias (planejadas)

- Python 3.11+
- Embeddings: sentence-transformers ou OpenAI Embeddings
- Vector Store: FAISS ou ChromaDB
- LLM: OpenAI GPT ou modelo open-source via HuggingFace
- Orquestracao: LangChain ou implementacao customizada

## Equipe

Projeto desenvolvido como parte da pos-graduacao em Inteligencia Artificial para Cientistas (POSTECH / FIAP).
