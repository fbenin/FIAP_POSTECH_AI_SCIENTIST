# Tech Challenge - Fase 4: Voice of Customer Intelligence com RAG

## Contexto

Empresas de e-commerce recebem diariamente milhares de avaliações contendo percepções, elogios, reclamações e relatos sobre diferentes etapas da jornada de compra. Analisar manualmente esse volume de dados é uma tarefa complexa e pouco escalável.

Este projeto desenvolve uma solução de **Voice of Customer Intelligence** baseada em **Retrieval-Augmented Generation (RAG)**, capaz de permitir a exploração inteligente das avaliações de clientes presentes na base **Brazilian E-Commerce Public Dataset by Olist** (Kaggle).

## Objetivo

Construir um sistema que permite a gestores e analistas realizarem perguntas em linguagem natural como:

- "Quais são os principais problemas relatados pelos clientes?"
- "O que os clientes mais elogiam em sua experiência de compra?"
- "Quais reclamações relacionadas à entrega aparecem com maior frequência?"
- "Quais padrões podem ser identificados nas avaliações de clientes insatisfeitos?"

A solução recupera avaliações relevantes da base de conhecimento e as utiliza como evidência para fundamentar cada resposta, evitando alucinações e garantindo rastreabilidade dos insights.

## Base de Dados

- **Fonte**: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data)
- **Volume**: ~100 mil pedidos (2016–2018)
- **Foco**: Conteúdos textuais das avaliações dos clientes (`review_comment_title`, `review_comment_message`)
- **Enriquecimento**: nota da avaliação, período da compra, categoria do produto, delta de entrega (dias de atraso/adiantamento)

---

## Arquitetura RAG

```
Pergunta do usuário
       ↓
Pré-processamento da pergunta
       ↓
Geração de embedding da query  [sentence-transformers]
       ↓
Busca semântica no índice FAISS  [IndexFlatIP + L2-norm]
       ↓
Filtro por limiar de similaridade  [cosine ≥ 0.30]
       ↓
Construção do contexto para o LLM
       ↓
Geração da resposta  [OpenAI gpt-4o-mini]
       ↓
Resposta fundamentada + evidências rastreáveis
```

---

## Decisões Técnicas

| Componente | Escolha | Justificativa |
|---|---|---|
| **Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo multilingual (50+ idiomas), suporte nativo a português, 384 dimensões, roda em CPU (~420 MB). Otimizado para similaridade semântica de parágrafos curtos — adequado ao tamanho médio das avaliações Olist. |
| **Vector Store** | FAISS `IndexFlatIP` | Busca exata (sem aproximação), sem servidor externo, índice é um arquivo em disco. Escala para os ~40 k documentos do dataset sem necessidade de GPU ou infraestrutura adicional. |
| **Similaridade** | Cosseno via produto interno | Vetores L2-normalizados + IndexFlatIP = similaridade cosseno. Insensível ao comprimento do texto, o que é importante dado que avaliações Olist variam de 2 a 300+ palavras. |
| **LLM** | OpenAI `gpt-4o-mini` | Custo baixo (~0,0015 USD/1k tokens), suporte robusto a português, instrução following confiável para o estilo "responda apenas com base no contexto". |
| **Orquestração** | Implementação direta (sem LangChain) | O pipeline é simples o suficiente para ser implementado em ~80 linhas. Evitar abstrações desnecessárias torna o código mais legível para toda a equipe. |
| **Limiar de evidência** | `min_score = 0.30`, `min_count = 2` | Abaixo de 0.30 o modelo recupera avaliações sem relação semântica com a query. Exigir ≥ 2 documentos evita respostas fundamentadas em um único relato atípico. |

---

## Preparação da Base de Conhecimento

### Seleção dos dados

Utilizamos o arquivo `olist_order_reviews_dataset.csv` como fonte primária. Os campos `review_comment_title` e `review_comment_message` contêm os textos das avaliações — o restante do dataset (nota, datas, categorias) é tratado como metadado.

Avaliações sem qualquer texto (apenas nota numérica) são excluídas, pois não contribuem para a recuperação semântica.

### Limpeza e preparação

1. **Normalização Unicode (NFKC):** uniformiza caracteres especiais e compatibilidade de codificação, comum em textos mobile/web.
2. **Colapso de espaços em branco:** remove espaços múltiplos, tabs e quebras de linha internas.
3. **Deduplicação de pontuação:** `!!!` → `!`, `...` → `.`.
4. **Concatenação título + mensagem:** quando ambos existem, o documento final é `"<título>. <mensagem>"`. Quando apenas um existe, usa-se o disponível.

### Tratamento de valores ausentes

- Avaliações sem texto são **removidas** (não preenchidas com placeholder).
- Metadados ausentes (ex.: categoria de produto quando o CSV de produtos não está disponível) são armazenados como `null` nos metadados do documento — não impedem a indexação.

### Estrutura dos documentos

Cada documento é um dicionário com dois campos:

```json
{
  "text": "produto chegou bem embalado e dentro do prazo",
  "metadata": {
    "review_id": "abc123",
    "order_id": "xyz789",
    "review_score": 5,
    "review_creation_date": "2018-03-15T00:00:00",
    "purchase_year": 2018,
    "purchase_month": 3,
    "delivery_delta_days": -2,
    "product_category_name_english": "housewares"
  }
}
```

---

## Estratégia do Pipeline RAG

### Recuperação

A query do usuário é codificada pelo mesmo modelo de embeddings usado na indexação. O FAISS retorna os `k` vetores mais próximos por similaridade cosseno. Documentos abaixo do limiar `min_score` são descartados antes de serem enviados ao LLM.

### Construção do contexto

Cada avaliação recuperada é formatada como:

```
[Avaliação 1 | Nota: 1/5 | Similaridade: 0.72]
produto chegou completamente diferente do que estava na foto...

---

[Avaliação 2 | Nota: 2/5 | Similaridade: 0.65]
...
```

Essa estrutura permite ao LLM identificar a origem de cada trecho e ao usuário rastrear quais avaliações sustentam cada insight.

### Geração da resposta

O LLM recebe um **system prompt** que instrui:
1. Responder **exclusivamente** com base nas avaliações fornecidas.
2. Citar trechos concretos ao apontar padrões.
3. **Admitir explicitamente** quando as evidências são insuficientes — sem inventar informações.

### Tratamento de perguntas sem evidências suficientes

Se menos de 2 avaliações forem recuperadas acima do limiar de similaridade, o sistema **não chama o LLM** e retorna uma mensagem padrão informando que a base não contém evidências suficientes. Isso evita que o LLM produza respostas convincentes porém não fundamentadas (*hallucination*).

---

## Estrutura do Projeto

```
TechChallenge_Fase4/
├── data/
│   ├── raw/               # CSVs originais do Kaggle (gitignored)
│   └── processed/         # Documentos, índice FAISS e pkl (gitignored)
├── notebooks/
│   ├── 01_exploracao.ipynb         # EDA das avaliações → gera documents.json
│   ├── 02_base_conhecimento.ipynb  # Embeddings + índice FAISS
│   └── 03_pipeline_rag.ipynb       # Pipeline RAG completo com exemplos
├── scripts/
│   └── download_data.py   # Download automático do dataset via Kaggle API
├── src/
│   ├── ingestion/     # Carga e limpeza dos dados Olist
│   ├── knowledge_base/# Geração de embeddings e construção do índice
│   ├── retrieval/     # Busca semântica sobre o índice FAISS
│   └── rag/           # Pipeline RAG: contexto + geração
├── images/            # Gráficos gerados pelos notebooks
├── .env.example       # Template para configurar OPENAI_API_KEY
├── requirements.txt
└── README.md
```

---

## Como Executar

### 1. Pré-requisitos

- Python 3.11+
- Conta OpenAI com `gpt-4o-mini` disponível

### 2. Instalação

```bash
git clone <url-do-repositorio>
cd TechChallenge_Fase4
pip install -r requirements.txt
```

### 3. Configurar API Key

Crie um arquivo `.env` na raiz do projeto (`TechChallenge_Fase4/`):

```
OPENAI_API_KEY=sk-...
```

### 4. Baixar o dataset via Kaggle API

Crie um token de API em [kaggle.com/settings/account](https://www.kaggle.com/settings/account) → **Create New Token** — isso baixa `kaggle.json`. Coloque-o na pasta correta:

```bash
# Linux / Mac
mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

# Windows
# mova para C:\Users\<usuario>\.kaggle\kaggle.json
```

Depois execute o script de download:

```bash
python scripts/download_data.py
```

Isso baixa e descompacta todos os CSVs do Olist em `data/raw/` automaticamente.

### 5. Executar os notebooks em ordem

```bash
jupyter notebook
```

| Notebook | O que faz | Saída |
|---|---|---|
| `01_exploracao.ipynb` | EDA das avaliações, exporta documentos limpos | `data/processed/documents.json` |
| `02_base_conhecimento.ipynb` | Gera embeddings e constrói o índice FAISS | `data/processed/reviews.index` + `documents.pkl` |
| `03_pipeline_rag.ipynb` | Demonstração do pipeline RAG com exemplos | Respostas + evidências no notebook |

---

## Exemplos de Perguntas e Respostas

> Os exemplos abaixo são ilustrativos. As respostas reais são geradas pelo LLM a partir das avaliações recuperadas.

**"Quais são os principais problemas relatados pelos clientes?"**
> Com base nas avaliações recuperadas, os problemas mais frequentes são: (1) atraso na entrega — clientes relatam receber produtos dias ou semanas após o prazo estimado; (2) produto divergente — o item recebido não corresponde às fotos ou à descrição do anúncio; (3) produto com defeito — menções a eletrônicos que não funcionam e produtos danificados na embalagem. *[Avaliações 1, 3 e 7 sustentam essa análise.]*

**"O que os clientes mais elogiam em sua experiência?"**
> Os elogios mais recorrentes concentram-se em: entrega antes do prazo, embalagem cuidadosa que protegeu o produto e qualidade do produto conforme anunciado. Clientes de produtos de beleza e artigos domésticos destacam com frequência a relação custo-benefício. *[Avaliações 2, 4, 5 e 8 sustentam essa análise.]*

**"Qual foi o impacto da taxa de câmbio no preço dos produtos?" (fora do escopo)**
> Não foram encontradas avaliações suficientemente relevantes na base de conhecimento para responder a esta pergunta com evidências confiáveis. Tente reformular ou faça uma pergunta relacionada aos temas presentes nas avaliações de clientes do e-commerce (entrega, produto, atendimento, etc.).

---

## Tecnologias

| Biblioteca | Versão | Uso |
|---|---|---|
| `sentence-transformers` | ≥ 2.7 | Geração de embeddings |
| `faiss-cpu` | ≥ 1.8 | Índice vetorial |
| `openai` | ≥ 1.0 | Geração de respostas |
| `pandas` / `numpy` | — | Manipulação dos dados |
| `python-dotenv` | — | Gerenciamento de credenciais |
| `matplotlib` / `seaborn` | — | Visualizações EDA |

---

## Equipe

Projeto desenvolvido como parte da pós-graduação em Inteligência Artificial para Cientistas (POSTECH / FIAP).
