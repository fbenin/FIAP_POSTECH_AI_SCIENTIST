# Tech Challenge — Fase 4

**Sistema de inteligência sobre voz do cliente com RAG sobre avaliações de e-commerce**

**Pos Tech FIAP — AI Scientist**

---

## Objetivo

Implementar um sistema de Retrieval-Augmented Generation (RAG) que permita consultores e gestores formularem perguntas em linguagem natural sobre os ~115 mil reviews de clientes do Olist, recebendo respostas contextualizadas com citação dos depoimentos relevantes. O sistema indexa vetorialmente os textos de avaliações, recupera os mais similares à pergunta e os utiliza como contexto para geração de respostas via LLM.

---

## Dataset

O dataset é o **Brazilian E-Commerce Public Dataset by Olist**, disponível no Kaggle. Contém avaliações estruturadas de clientes com scores (1-5), comentários em texto livre, datas e outros metadados relacionados a pedidos de e-commerce.

**Nota:** O arquivo CSV é gitignored e deve ser baixado manualmente pelo usuário (veja `data/README.md` para instruções).

---

## Estrutura do Projeto

```text
TechChallenge_Fase4/
├── .gitignore
├── .env.example
├── README.md
├── requirements.txt
├── data/
│   ├── .gitkeep
│   └── README.md                    # Instruções de download do dataset
├── images/
│   └── .gitkeep                     # Gráficos e visualizações (EDA)
├── notebooks/
│   ├── .gitkeep
│   ├── 01_eda_reviews.ipynb         # Exploração e análise inicial dos dados
│   └── 02_experimentos_rag.ipynb    # Testes do pipeline RAG
├── reports/
│   ├── .gitkeep
│   ├── technical_report.md          # Relatório técnico
│   ├── executive_summary.md         # Resumo executivo
│   └── video_script.md              # Roteiro da apresentação (7 min)
└── src/
    ├── __init__.py
    ├── ingestion/
    │   ├── __init__.py
    │   └── loader.py                # Carregamento e normalização do CSV
    ├── embeddings/
    │   ├── __init__.py
    │   └── builder.py               # Construção do índice vetorial (ChromaDB)
    ├── retrieval/
    │   ├── __init__.py
    │   └── store.py                 # Wrapper para busca por similaridade
    └── rag/
        ├── __init__.py
        ├── prompts.py               # Templates de prompts em português
        └── chain.py                 # Cadeia LCEL end-to-end
```

---

## Instalação

### 1. Preparar ambiente

```bash
cd /Users/i540522/Documents/POS\ TECH/Challenges/Repositorio\ do\ grupo/FIAP_POSTECH_AI_SCIENTIST/TechChallenge_Fase4
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` para informar:
- `LLM_PROVIDER`: `openai`, `together`, ou `ollama`
- Chave da API correspondente (`OPENAI_API_KEY`, `TOGETHER_AI_API_KEY`, etc.)

### 3. Baixar e colocar o dataset

Siga as instruções em `data/README.md` para:
- Baixar `olist_order_reviews_dataset.csv` do Kaggle
- Colocar em `data/raw/olist_order_reviews_dataset.csv`

### 4. Construir o índice vetorial

```bash
python -m src.embeddings.builder
```

Este comando carrega o CSV, gera embeddings com a HuggingFace (modelo local, sem API), e persiste o índice em `data/chroma_db/`.

---

## Uso

### Consultar via Python

```bash
python -m src.rag.chain
```

Este comando executa 5 perguntas de teste e exibe as respostas junto com os reviews citados.

### Consultar programaticamente

```python
from src.rag import ask

resultado = ask(question="Quais sao os principais problemas de entrega mencionados pelos clientes?", show_sources=True)
print(resultado["answer"])
print(resultado["sources"])
```

---

## Próximos Passos

- **Fase 2:** API FastAPI com endpoint `POST /query`
- **Fase 3:** Enriquecimento de metadados (categoria de produto, período temporal, filtros)
