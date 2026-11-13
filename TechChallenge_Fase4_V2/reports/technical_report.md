# Relatório Técnico — Voice of Customer Intelligence com RAG

**Tech Challenge Fase 4 — Pos Tech FIAP AI Scientist**

---

## 1. Objetivo

Desenvolver um sistema de **Retrieval-Augmented Generation (RAG)** capaz de responder perguntas
em linguagem natural sobre as avaliações de clientes do dataset Olist, fundamentando cada resposta
nos comentários reais recuperados da base de conhecimento e recusando responder quando evidências
suficientes não estiverem disponíveis.

---

## 2. Arquitetura Geral

O sistema segue uma arquitetura RAG clássica com cinco estágios:

```
[1] Construção offline da base de conhecimento
    CSV(s) → limpeza → enriquecimento → embeddings → ChromaDB

[2] Consulta em tempo real
    Pergunta → embedding → busca cosine (ChromaDB) → filtragem por threshold
         │
    sem evidências → fallback explícito
         │
    com evidências → construção do contexto → LLM → resposta + fontes
```

### Componentes principais

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace) | Suporte multilingual, roda localmente |
| Vector store | ChromaDB (HNSW cosine) | Persistência nativa, metadados filtráveis |
| LLM | OpenAI GPT-4o-mini / Groq Llama-3 / Together / Ollama | Configurável via `.env` |
| Framework | LangChain + FastAPI | Integração LLM/vectorstore + API REST |

---

## 3. Preparação da Base de Conhecimento

### 3.1 Seleção dos dados

O dataset Olist contém múltiplos arquivos CSV. Para este sistema foram utilizados:

- **Obrigatório:** `olist_order_reviews_dataset.csv` — textos e notas das avaliações
- **Opcionais (enriquecimento):** `olist_orders_dataset.csv`, `olist_order_items_dataset.csv`,
  `olist_products_dataset.csv`, `product_category_name_translation.csv`

Do total de ~115 mil registros, aproximadamente 40% possuem texto no campo
`review_comment_message`. Os demais registros (somente nota numérica) são descartados por não
terem conteúdo textual indexável.

### 3.2 Limpeza e preparação dos textos

**Concatenação título + mensagem:** Quando uma avaliação possui `review_comment_title` e
`review_comment_message`, ambos são concatenados em um único documento:
`"<título>. <mensagem>"`. Isso captura informações do título (frequentemente mais direto) junto
ao corpo da avaliação.

**Normalização NFKC:** Unicode Normalization Form KC garante representação canônica de caracteres
acentuados, evitando que a mesma palavra com diferentes encodings receba embeddings distintos.

**Deduplicação de pontuação:** O padrão `([!?,.]){2,}` colapsa pontuação repetida (`!!!` → `!`),
reduzindo ruído sem alterar o conteúdo semântico.

**Colapso de espaços:** Múltiplos espaços e quebras de linha são normalizados para um único espaço.

### 3.3 Tratamento de valores ausentes

| Campo | Tratamento |
|-------|-----------|
| `review_comment_message` nulo | Descartado (sem texto = sem conteúdo indexável) |
| `review_comment_title` nulo | Usa apenas o `review_comment_message` |
| Ambos nulos | Descartado |
| Metadados opcionais ausentes | Fallback gracioso: indexa sem o campo |

### 3.4 Enriquecimento com metadados

Quando os CSVs de pedidos e produtos estão disponíveis, cada documento recebe:

- **`delivery_delta_days`:** `order_delivered_customer_date − order_estimated_delivery_date` (em dias).
  Negativo = entrega antes do prazo; positivo = atraso.
- **`product_category`:** Categoria em inglês, obtida via join orders → items → products → translation.
- **`purchase_year` / `purchase_month`:** Mês e ano da compra, para análise temporal.

Esses metadados são armazenados no ChromaDB como campos de metadata e incluídos no bloco de
contexto enviado ao LLM, permitindo análises como *"reclamações de entrega em eletrônicos"*.

### 3.5 Deduplicação

O corpus bruto contém 14,5% de avaliações duplicadas exatas após normalização (ex: *"muito bom"*
aparecia 472×, *"bom"* 342×). Sem deduplicação, os 5 documentos mais próximos de qualquer query
frequente seriam cópias idênticas, degradando a cobertura e a qualidade da resposta.

A flag `deduplicate=True` remove duplicatas após a normalização, reduzindo o corpus de 40.950 para
35.006 documentos únicos (redução de 14,5%).

### 3.6 Criação dos embeddings

**Modelo:** `paraphrase-multilingual-MiniLM-L12-v2` com `normalize_embeddings=True` (L2-norm).

Escolhido por:
- Cobertura de 50+ idiomas, incluindo português
- Leve (117M parâmetros) — indexação de 35 mil documentos em ~10 minutos em CPU
- Validado experimentalmente: recupera reviews relevantes para queries em inglês (top_sim=0.822)
  e espanhol (top_sim=0.921) sem tradução prévia

### 3.7 Armazenamento e indexação

**ChromaDB** com `hnsw:space=cosine` e vetores L2-normalizados. Vantagens:
- Persistência nativa em disco (sem servidor externo)
- Campos de metadata armazenados junto ao documento
- Integração nativa com LangChain
- Busca aproximada HNSW eficiente para o tamanho do corpus (~35 mil documentos)

---

## 4. Pipeline RAG

### 4.1 Transformação da pergunta

A pergunta do usuário é convertida para embedding usando o mesmo modelo
(`paraphrase-multilingual-MiniLM-L12-v2`) utilizado na indexação. Isso garante que a pergunta
e os documentos compartilhem o mesmo espaço vetorial.

### 4.2 Recuperação semântica

O ChromaDB calcula a distância cosine entre o embedding da pergunta e os documentos indexados
via HNSW, retornando os `RETRIEVAL_TOP_K` (padrão: 5) candidatos mais próximos.

A distância cosine é convertida para similaridade no intervalo [0, 1]:
`similarity = max(0.0, 1.0 - distance / 2.0)`

### 4.3 Seleção por threshold

Documentos com `similarity < SIMILARITY_THRESHOLD` (padrão: 0.75) são descartados. Quando
nenhum documento passa pelo filtro, o sistema retorna uma mensagem de fallback explícita sem
invocar o LLM, evitando alucinações em perguntas fora do domínio.

**Justificativa do threshold 0.75** (validado via EXP 2):

| Threshold | Docs in-scope | Docs out-of-scope |
|-----------|--------------|-------------------|
| 0.50 | 5 | 5 |
| 0.65 | 5 | 5 |
| **0.75** | **5** | **3** ← escolhido |
| 0.80 | 5 | 1 |
| 0.85 | 3 | 0 |
| 0.90 | 1 | 0 |

Threshold 0.75 mantém cobertura completa para queries in-scope e reduz significativamente as out-of-scope. Thresholds ≥ 0.85 eliminam o ruído mas passam a descartar consultas legítimas. O threshold não elimina completamente queries semanticamente ambíguas (e.g., "time de futebol do Brasil" retorna 3 documentos a 0.75 por sobreposição com o contexto brasileiro — documentado como limitação).

### 4.4 Construção do contexto

Cada documento recuperado é formatado em um bloco estruturado:

```
[Avaliação 1 | Nota: 1/5 | Similaridade: 0.91]
Categoria: health_beauty
Entrega: 12 dias após o prazo
Texto: produto chegou completamente diferente do anunciado...

---

[Avaliação 2 | Nota: 2/5 | Similaridade: 0.87]
...
```

A nota da avaliação (1–5) fornece contexto de sentimento. O delta de entrega e a categoria
permitem ao LLM identificar padrões contextuais sem precisar inferir a partir do texto.

### 4.5 Geração da resposta

O prompt instrui o LLM a:
1. Basear cada afirmação em pelo menos uma avaliação fornecida
2. Citar trechos concretos ao identificar padrões
3. Declarar explicitamente quando as evidências forem insuficientes
4. Utilizar metadados (categoria, prazo) para enriquecer a análise
5. Responder em português

A resposta inclui o flag `has_evidence: bool` para que a aplicação consumidora distinga respostas
fundamentadas de fallbacks.

---

## 5. Resultados dos Experimentos

Experimentos detalhados disponíveis em `notebooks/02_experimentos_rag.ipynb`.

### EXP 1 — Baseline (threshold=0.75, k=5)

5 perguntas representativas do domínio + 1 fora de escopo:
- Perguntas in-scope: 5 documentos recuperados, respostas coerentes com o corpus
- Pergunta fora de escopo (*"melhores restaurantes de São Paulo"*): fallback ativado corretamente

### EXP 2 — Impacto do threshold

Threshold 0.75 é o ponto de equilíbrio: separa in-scope de out-of-scope sem cortar cobertura.

### EXP 3 — Impacto do top_k

k=5 captura os documentos mais relevantes sem inflar o contexto. Em k=15, a similaridade mínima
cai apenas para ~0.828, indicando alta densidade semântica no corpus.

### EXP 4 — Edge cases

| Caso | Resultado |
|------|-----------|
| Inglês | Funciona (top_sim=0.822) |
| Espanhol | Funciona (top_sim=0.921) |
| Negação (*"NÃO chegou no prazo"*) | Captura semântica correta (top_sim=0.986) |
| Query genérica (*"bom"*) | Exact match; resposta de baixo valor analítico |

---

## 6. Limitações

- **Queries genéricas:** Termos curtos como *"bom"* retornam exact match com similaridade=1.0
  mas produzem respostas sem profundidade analítica.
- **Sobreposição semântica parcial:** Queries como *"time de futebol do Brasil"* podem retornar
  documentos com threshold=0.75 por sobreposição contextual com o domínio brasileiro. Um
  classificador de intenção poderia mitigar isso.
- **Re-indexação necessária após enriquecimento:** Adicionar os CSVs opcionais exige reconstruir
  o índice ChromaDB (`python -m src.embeddings.builder`).
- **Sem memória de conversa:** Cada pergunta é tratada de forma independente; perguntas de
  follow-up não aproveitam o contexto da pergunta anterior.

---

## 7. Conclusão

O sistema implementa com sucesso uma arquitetura RAG sobre avaliações de clientes de e-commerce,
permitindo exploração semântica de ~35 mil comentários em linguagem natural. Os mecanismos de
fallback por threshold e prompt constrained garantem que as respostas sejam sempre fundamentadas
em evidências reais, evitando alucinações. O enriquecimento opcional com metadados de entrega e
categoria eleva a qualidade analítica das respostas para perguntas contextuais.
