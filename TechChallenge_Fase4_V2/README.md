# Tech Challenge — Fase 4

**Voice of Customer Intelligence com RAG sobre avaliações de e-commerce**

**Pos Tech FIAP — AI Scientist**

---

## Objetivo

Construir um sistema de **Retrieval-Augmented Generation (RAG)** que permite a gestores e analistas
fazerem perguntas em linguagem natural sobre as avaliações de clientes do dataset Olist, recebendo
respostas fundamentadas nos comentários reais com citação das evidências utilizadas.

---

## Arquitetura

```
Pergunta do usuário
        │
        ▼
┌──────────────────────────┐
│  Embedding da pergunta   │
│  (multilingual MiniLM)   │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│   Busca por similaridade │  threshold=0.75 │ top_k=5
│   ChromaDB (cosine HNSW) │
└──────────┬───────────────┘
           │
    ┌──────┴──────┐
    │ sem docs    │ com docs
    ▼             ▼
 Fallback   ┌──────────────────────────────┐
            │  Contexto estruturado        │
            │  [Avaliação N | Nota: X/5    │
            │   Categoria | Delta entrega] │
            └──────────────┬───────────────┘
                           │
                           ▼
               ┌──────────────────────┐
               │  LLM (OpenAI / Groq  │
               │  / Together / Ollama)│
               │  Prompt PT-BR        │
               │  evidence-only rules │
               └──────────┬───────────┘
                          │
                          ▼
          Resposta + evidências citadas + has_evidence
```

**Componentes:**

| Módulo | Responsabilidade |
|--------|-----------------|
| `src/ingestion/loader.py` | Carrega CSVs, normaliza texto (NFKC), concatena título+mensagem, faz join com metadados |
| `src/embeddings/builder.py` | Gera embeddings e persiste índice ChromaDB |
| `src/retrieval/store.py` | Busca semântica com filtro por threshold de similaridade |
| `src/rag/prompts.py` | Templates de prompt em português com regras de evidência |
| `src/rag/chain.py` | Orquestra recuperação → contexto → geração |
| `src/api/main.py` | API REST FastAPI com endpoint `POST /query` |

---

## Dataset

**Brazilian E-Commerce Public Dataset by Olist** — disponível no
[Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data).

Contém ~115 mil avaliações de pedidos entre 2016 e 2018. O pipeline usa o arquivo de reviews
como base obrigatória, e opcionalmente enriquece cada documento com categoria de produto e
`delivery_delta_days` (dias antes/após o prazo de entrega).

Veja `data/README.md` para instruções de download e lista completa de arquivos.

---

## Estrutura do Projeto

```
TechChallenge_Fase4_V2/
├── .env.example              # Variáveis de ambiente (copie para .env)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/
│   ├── README.md             # Instruções de download do dataset
│   └── raw/                  # CSVs do Kaggle (gitignored)
├── images/                   # Gráficos gerados pelo EDA
├── scripts/
│   └── download_data.py      # Download automático do dataset via Kaggle API
├── notebooks/
│   ├── 01_eda_reviews.ipynb  # Exploração e análise dos dados
│   └── 02_experimentos_rag.ipynb  # Testes de threshold, top_k e edge cases
├── reports/
│   ├── technical_report.md
│   └── executive_summary.md
└── src/
    ├── ingestion/loader.py   # Carregamento, limpeza e enriquecimento
    ├── embeddings/builder.py # Construção do índice ChromaDB
    ├── retrieval/store.py    # Busca por similaridade
    └── rag/
        ├── prompts.py        # Templates de prompt
        ├── chain.py          # Pipeline RAG ponta a ponta
    └── api/
        ├── main.py           # FastAPI app
        └── schemas.py        # Modelos Pydantic
```

---

## Instalação

```bash
# 1. Clone o repositório e entre no diretório do projeto
cd TechChallenge_Fase4_V2

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env: defina LLM_PROVIDER e a chave da API correspondente
```

---

## Configuração

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `LLM_PROVIDER` | Provider LLM: `openai`, `groq`, `together`, `ollama` | — (obrigatório) |
| `OPENAI_API_KEY` | Chave OpenAI (se `LLM_PROVIDER=openai`) | — |
| `GROQ_API_KEY` | Chave Groq (se `LLM_PROVIDER=groq`) | — |
| `GROQ_MODEL` | Modelo Groq | `openai/gpt-oss-20b` |
| `EMBEDDING_MODEL` | Modelo sentence-transformers | `paraphrase-multilingual-MiniLM-L12-v2` |
| `CHROMA_PERSIST_DIR` | Diretório do índice ChromaDB | `data/chroma_db` |
| `RETRIEVAL_TOP_K` | Número de documentos recuperados | `5` |
| `SIMILARITY_THRESHOLD` | Threshold mínimo de similaridade | `0.75` |

---

## Construir o índice vetorial

### 1. Baixar o dataset

**Opção A — Download automático via Kaggle API** *(recomendado)*

Crie um token em [kaggle.com/settings/account](https://www.kaggle.com/settings/account) → **Create New Token** → salve em `~/.kaggle/kaggle.json`:

```bash
chmod 600 ~/.kaggle/kaggle.json
python scripts/download_data.py
```

**Opção B — Download manual**

Acesse [kaggle.com/datasets/olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data) e extraia os CSVs em `data/raw/`.

Arquivo obrigatório: `olist_order_reviews_dataset.csv`
Opcionais (enriquecimento): `olist_orders_dataset.csv`, `olist_order_items_dataset.csv`, `olist_products_dataset.csv`, `product_category_name_translation.csv`

### 2. Indexar

```bash
python -m src.embeddings.builder
```

O comando lê os reviews, aplica normalização, faz join com metadados opcionais, gera embeddings
com o modelo multilingual (sem API — roda localmente) e persiste o índice em `data/chroma_db/`.

---

## Preparação da Base de Conhecimento

### Seleção dos dados

Fonte: `olist_order_reviews_dataset.csv`. Os campos `review_comment_title` e `review_comment_message`
contêm os textos das avaliações. Avaliações sem qualquer texto (apenas nota numérica) são descartadas.

### Limpeza e normalização

1. **Normalização Unicode (NFKC):** uniformiza caracteres especiais — comum em textos digitados via mobile.
2. **Colapso de espaços em branco:** remove múltiplos espaços, tabs e quebras de linha internas.
3. **Deduplicação de pontuação:** `!!!` → `!`, `...` → `.`
4. **Concatenação título + mensagem:** quando ambos existem, o documento final é `"<título>. <mensagem>"`. Quando só um está presente, usa-se o disponível.

### Tratamento de valores ausentes

Campos ausentes ou NaN são detectados com `pd.isna()` e convertidos para string vazia antes de qualquer
operação — evita que `float('nan')` seja tratado como string `"nan"` no texto final.

### Estrutura de cada documento indexado

```json
{
  "text": "Produto chegou bem embalado e dentro do prazo.",
  "metadata": {
    "id": "e64fb393e7b32834bb789ff8bb30750e",
    "score": 5,
    "date": "2018-03-15 00:00:00",
    "product_category": "housewares",
    "delivery_delta_days": -2,
    "purchase_year": 2018,
    "purchase_month": 3
  }
}
```

Os campos de enriquecimento (`product_category`, `delivery_delta_days`, `purchase_year`, `purchase_month`)
são opcionais — presentes apenas quando os CSVs adicionais estão em `data/raw/`.

---

## Uso

### CLI (consulta rápida)

```bash
python -m src.rag.chain
```

Executa 5 perguntas de teste e exibe respostas com as avaliações citadas.

### Python

```python
from src.rag import ask

resultado = ask("Quais são os principais problemas de entrega?")
print(resultado["answer"])
print(resultado["has_evidence"])   # False quando não há evidências suficientes
for src in resultado["sources"]:
    print(f"[{src['similarity']:.2f}] {src['text'][:100]}")
```

### API REST

```bash
uvicorn src.api.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação interativa em `http://localhost:8000/docs`.

**POST /query**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "O que os clientes reclamam sobre entrega?"}'
```

Resposta:
```json
{
  "answer": "Os clientes relatam principalmente atrasos...",
  "has_evidence": true,
  "sources": [
    {
      "id": "abc123",
      "text": "produto chegou com 10 dias de atraso",
      "score": 1,
      "date": "2017-11-15 00:00:00",
      "similarity": 0.91,
      "product_category": "electronics",
      "delivery_delta_days": 10.0
    }
  ]
}
```

### Docker

```bash
docker-compose up --build
```

A API fica disponível em `http://localhost:8000`. Monte `data/` como volume para usar um índice
pré-construído (configurado no `docker-compose.yml`).

---

## Exemplos de perguntas e respostas

### 1. Investigação de reclamações

**Pergunta:** *Quais são os principais problemas relatados pelos clientes?*

**Resposta:** Os problemas mais recorrentes são: (1) atrasos na entrega — clientes relatam esperas
muito além do prazo estimado; (2) produtos com defeito ou diferentes do anunciado; (3) dificuldade
de contato com o vendedor após a compra. Exemplo: *"o produto chegou completamente diferente do que
estava na foto"* (Nota: 1/5).

---

### 2. Investigação de um tema específico

**Pergunta:** *O que os clientes relatam sobre problemas relacionados à entrega?*

**Resposta:** Atrasos são a principal reclamação. Alguns clientes relatam que o produto chegou
mais de 20 dias após o prazo estimado. Há relatos de pedidos entregues na portaria sem aviso e
produtos extraviados. Clientes com entrega antes do prazo, por outro lado, deixam elogios
consistentes — *"recebi bem antes do prazo estipulado"* (Nota: 5/5).

---

### 3. Busca por experiências positivas

**Pergunta:** *O que os clientes mais elogiam nas compras?*

**Resposta:** Os elogios se concentram em três temas: (1) entrega antes do prazo — *"entregou
antes do previsto, surpreendente"*; (2) qualidade do produto — *"produto idêntico ao anunciado,
ótima qualidade"*; (3) preço justo — *"melhor custo-benefício que encontrei".* Esses padrões
aparecem consistentemente nas avaliações com nota 5.

---

### 4. Pergunta fora do escopo (fallback)

**Pergunta:** *Quais são os melhores restaurantes de São Paulo?*

**Resposta:** Não foram encontradas avaliações suficientemente relevantes na base de conhecimento
para responder a esta pergunta com evidências confiáveis. Tente reformular ou explore temas
presentes nas avaliações: entrega, qualidade dos produtos, atendimento ao cliente, experiência
de compra.

---

### 5. Exploração contextual com metadados

**Pergunta:** *Quais problemas aparecem nas avaliações de produtos de beleza com nota baixa?*

**Resposta (quando enriquecimento ativo):** Nas avaliações da categoria `health_beauty` com nota
1 ou 2, os relatos se concentram em: produtos adulterados ou falsificados, embalagem danificada
na entrega e divergência entre descrição e produto recebido.

---

## Decisões técnicas

### Deduplicação do corpus
O dataset bruto contém 14,5% de avaliações duplicadas (ex: *"muito bom"* aparecia 472×). Sem
deduplicação, qualquer pergunta frequente retornaria 5 cópias idênticas do mesmo texto. A flag
`deduplicate=True` em `load_reviews()` reduz o corpus de 40.950 para 35.006 documentos únicos
mantendo a cobertura semântica sem redundância.

### Concatenação título + mensagem
Avaliações com título informativo (ex: *"Produto com defeito. Chegou quebrado e diferente do
anunciado"*) têm muito mais conteúdo recuperável do que o título ou a mensagem isolados. O
pipeline concatena ambos em um único texto antes de gerar o embedding, seguindo a mesma
abordagem do protótipo V1.

### Normalização NFKC + deduplicação de pontuação
O dataset contém acentuação inconsistente (e.g., `ã` vs `ã` em representações Unicode distintas)
e pontuação repetida (`!!!`). A normalização NFKC garante representação canônica dos caracteres
e `re.sub(r"([!?,.]){2,}", r"\1", text)` remove ruído de pontuação.

### Modelo de embedding multilingual
`paraphrase-multilingual-MiniLM-L12-v2` com `normalize_embeddings=True` cobre 50+ idiomas,
permitindo que queries em inglês ou espanhol recuperem avaliações em português sem tradução
prévia (confirmado nos experimentos: top_sim=0.822 para inglês, 0.921 para espanhol).

### Threshold de similaridade = 0.75
Validado via EXP 2 no notebook de experimentos: threshold < 0.65 permite que queries fora de
escopo (ex: *"time de futebol"*) passem pelo filtro e gerem respostas sem evidências. Threshold
> 0.85 começa a cortar queries in-scope relevantes. O valor 0.75 oferece o melhor equilíbrio.

### ChromaDB com HNSW cosine
Persistência nativa (sem servidor separado), suporte a metadados filtráveis, e integração com
LangChain. Para o tamanho do corpus (~35 mil documentos) a busca aproximada HNSW é suficientemente
precisa e muito mais rápida que busca exata.

### Suporte a múltiplos LLM providers
OpenAI, Groq, Together AI e Ollama são suportados via variável de ambiente, sem alterar o código.
O embedding roda sempre localmente (sem API), tornando a construção do índice gratuita.

---

## Limitações

- Queries muito curtas ou genéricas (*"bom"*, *"produto"*) geram exact match com similaridade=1.0,
  mas produzem respostas sem valor analítico.
- O threshold de 0.75 não resolve completamente queries fora de domínio com sobreposição
  semântica parcial (ex: *"time de futebol do Brasil"* pode retornar documentos em threshold=0.75).
- O enriquecimento de metadados requer download dos 4 CSVs adicionais e re-indexação completa.
