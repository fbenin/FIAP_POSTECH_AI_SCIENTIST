# Tech Challenge Fase 2 — Pipeline Híbrido de Alfabetização no Brasil

**FIAP POSTECH — Ciências de Dados com IA**  
**Fase 2: Data Prepare — Arquitetura de Big Data**

---

## Contexto do Problema

A alfabetização na infância é um dos pilares fundamentais para o desenvolvimento educacional, social e econômico de um país. O **Compromisso Nacional Criança Alfabetizada** mobiliza União, estados, Distrito Federal e municípios com o objetivo de garantir que todas as crianças brasileiras estejam alfabetizadas até o final do **2º ano do ensino fundamental até 2030**.

O **Indicador Criança Alfabetizada**, definido pelo INEP em 2023 a partir da Pesquisa Alfabetiza Brasil, mede o percentual de estudantes que atingem **743 pontos na escala de proficiência do SAEB** — ponto de corte a partir do qual a criança é considerada alfabetizada.

Este projeto constrói uma **pipeline híbrida (Batch + Streaming)** para integrar, tratar e disponibilizar esses dados em uma camada analítica confiável na AWS, habilitando análises de desigualdade educacional e políticas públicas baseadas em evidências.

---

## O Desafio Educacional

Em 2023, a taxa nacional de alfabetização das crianças ao final do 2º ano era de **55,9%** (rede pública). A meta para 2030 é atingir **80%**. Isso significa que o Brasil precisa elevar em ~24 pontos percentuais o indicador em 7 anos — com disparidades enormes entre estados e municípios.

Para entender esses fatores, é necessário integrar múltiplas fontes:

| Fonte | Descrição | Granularidade |
|---|---|---|
| `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv` | Meta nacional e taxa realizada | Nacional |
| `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv` | Metas por estado | Estadual |
| `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_municipio.csv` | Metas por município | Municipal (~10.704 linhas) |
| `br_inep_avaliacao_alfabetizacao_uf.csv` | Indicadores de desempenho por UF | Estadual (~145 linhas) |
| `br_inep_avaliacao_alfabetizacao_municipio.csv` | Indicadores de desempenho por município | Municipal (~23.995 linhas) |

---

## Arquitetura da Solução

### Diagrama da Pipeline

```
╔══════════════════════════════════════════════════════════════════════╗
║                        FONTES DE DADOS                               ║
║                                                                      ║
║  ┌─────────────────────────┐   ┌──────────────────────────────────┐  ║
║  │  INEP / Base dos Dados  │   │  Streaming Simulado (Python)     │  ║
║  │  5 datasets INEP (CSV)  │   │  Eventos de atualização          │  ║
║  │  - meta_brasil          │   │  - indicador_atualizado          │  ║
║  │  - meta_uf              │   │  - meta_revisada                 │  ║
║  │  - meta_municipio       │   │  - medicao_desempenho            │  ║
║  │  - indicador_uf         │   └────────────┬─────────────────────┘  ║
║  │  - indicador_municipio  │                │ (Kinesis em produção)  ║
║  └────────────┬────────────┘                │                        ║
╚═══════════════╪═════════════════════════════╪════════════════════════╝
                │  Batch (diário)             │  Near-real-time
                ▼                             ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    BRONZE LAYER  (S3 Parquet)                        ║
║                                                                      ║
║  s3://bucket/bronze/meta_brasil/run_ts=.../                          ║
║  s3://bucket/bronze/meta_uf/run_ts=.../                              ║
║  s3://bucket/bronze/meta_municipio/run_ts=.../                       ║
║  s3://bucket/bronze/indicador_uf/run_ts=.../                         ║
║  s3://bucket/bronze/indicador_municipio/run_ts=.../                  ║
║  s3://bucket/bronze/streaming/dt=YYYY-MM-DD/batch_*.parquet          ║
║                                                                      ║
║  Características: dados brutos, metadados de ingestão,              ║
║  histórico completo, lifecycle → S3-IA após 90 dias (FinOps)         ║
╚══════════════════════════════╤═══════════════════════════════════════╝
                               │  AWS Glue ETL Job
                               ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    SILVER LAYER  (S3 Parquet Particionado)           ║
║                                                                      ║
║  Transformações:                                                     ║
║  ✓ Limpeza e padronização de tipos                                   ║
║  ✓ Tratamento de nulos e duplicatas                                  ║
║  ✓ Normalização de chaves (id_municipio zfill(7), sigla_uf upper)   ║
║  ✓ Integração: indicadores + metas municipais + metas estaduais     ║
║  ✓ Cálculo de gaps em relação à meta 2030                            ║
║                                                                      ║
║  s3://bucket/silver/alfabetizacao_municipio/sigla_uf=SP/ano=2023/   ║
║  s3://bucket/silver/alfabetizacao_uf/sigla_uf=SP/ano=2023/          ║
╚══════════════════════════════╤═══════════════════════════════════════╝
                               │  AWS Glue ETL Job
                               ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    GOLD LAYER  (S3 Parquet Analítico)                ║
║                                                                      ║
║  Datasets prontos para consumo:                                      ║
║  • indicador_municipio  — taxa + metas + gaps por município          ║
║  • evolucao_temporal_uf — série histórica por estado                 ║
║  • ranking_uf           — ranking de UFs no ano mais recente         ║
║  • municipios_risco     — municípios mais distantes da meta          ║
║  • comparativo_nacional — evolução nacional vs trajetória 2030       ║
╚══════════════════════════════╤═══════════════════════════════════════╝
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
        AWS Athena                     Dashboards / ML
     (SQL ad-hoc)              (Power BI / Looker / scikit-learn)
```

### Fluxo de Dados

```
1. [Batch]     INEP CSV → S3 Bronze (Parquet + metadados ingestão)
2. [Streaming] Eventos → fila JSONL → S3 Bronze/streaming/
3. [ETL]       S3 Bronze → Glue Job → S3 Silver (particionado por sigla_uf/ano)
4. [ETL]       S3 Silver → Glue Job → S3 Gold (datasets analíticos)
5. [Query]     S3 Gold → Athena (SQL) → BI / ML
6. [Monitor]   Cada etapa → CloudWatch Logs + Quality Checks Python
```

---

## Stack Tecnológica

| Componente | Tecnologia | Justificativa |
|---|---|---|
| **Storage (todas as camadas)** | AWS S3 | Barato ($0.023/GB), durável 11 9s, integrado nativamente com Glue e Athena |
| **ETL / Transformação** | AWS Glue (PySpark) + Python (pandas) | Serverless: escala automática, sem gestão de cluster; scripts Python para modo local |
| **Consulta analítica** | AWS Athena | SQL direto no S3, paga por query ($5/TB), sem servidor fixo |
| **Orquestração** | Apache Airflow (Docker local) | Open source, DAG diário, evita custo do MWAA (~$400/mês) |
| **Ingestão Batch** | Python + `basedosdados` SDK | SDK oficial da plataforma fonte; fallback para CSV INEP local |
| **Streaming simulado** | Python producer/consumer | Simula Kinesis sem custo em dev; código pronto para migrar para Kinesis |
| **Qualidade de dados** | Python (pandas + assertions) | Framework leve, sem dependências extras, integrado ao DAG |
| **Formato de arquivo** | **Parquet (PyArrow)** | 60-80% menor que CSV; columnar reduz custo Athena em ~10x |
| **Notebooks** | Jupyter (.ipynb) | Documentação executável, EDA integrada, facilita reprodução |

---

## Estrutura do Repositório

```
tech-challenge-fase2/
│
├── notebooks/                          ← PIPELINE PRINCIPAL (Jupyter)
│   ├── 01_setup_e_ingestao_bronze.ipynb   # Setup AWS + ingestão Bronze
│   ├── 02_silver_transformation.ipynb     # Limpeza + integração Silver
│   ├── 03_gold_analytics.ipynb            # Datasets analíticos Gold
│   ├── 04_streaming_simulation.ipynb      # Producer/Consumer streaming
│   └── 05_quality_checks.ipynb            # Validação + FinOps
│
├── pipelines/
│   ├── batch/
│   │   ├── bronze/ingest_bronze.py        # Ingestão batch (Base dos Dados)
│   │   ├── silver/transform_silver.py     # Transformações Silver
│   │   └── gold/build_gold.py             # Construção Gold
│   └── streaming/
│       ├── producer.py                    # Gerador de eventos
│       └── consumer.py                    # Consumidor + persistência Bronze
│
├── quality/
│   └── quality_checks.py                  # Suite de checks por camada
│
├── orchestration/
│   └── dags/pipeline_alfabetizacao.py     # DAG Airflow (Bronze→Silver→Gold)
│
├── infra/
│   └── setup_aws.py                       # Cria S3 + Glue DB + Athena workgroup
│
├── data/
│   ├── bronze/                            # Bronze local (gerado pelos notebooks)
│   ├── silver/                            # Silver local (gerado pelos notebooks)
│   ├── gold/                              # Gold local (gerado pelos notebooks)
│   └── samples/
│       └── generate_samples.py            # Gera amostras dos CSVs INEP reais
│
├── docs/
│   ├── athena_queries.sql                 # Queries SQL prontas para Athena
│   ├── DOCUMENTATION.md                   # Documentação técnica detalhada
│   └── quality_reports/                   # Relatórios JSON de qualidade
│
├── docker-compose.yml                     # Airflow local
├── requirements.txt
└── .env.example                           # Template de variáveis de ambiente
```

---

## Como Executar

### Pré-requisitos

```bash
Python 3.9+
pip install -r requirements.txt

# Para execução com AWS real:
aws configure  # configure suas credenciais
```

### Opção 1: Notebooks (recomendado)

Execute na ordem — cada notebook depende do anterior:

```bash
cd notebooks/
jupyter notebook

# Ordem de execução:
# 01_setup_e_ingestao_bronze.ipynb
# 02_silver_transformation.ipynb
# 03_gold_analytics.ipynb
# 04_streaming_simulation.ipynb
# 05_quality_checks.ipynb
```

Os notebooks funcionam **sem credenciais AWS** (modo local) — os dados são processados e salvos em `data/bronze/`, `data/silver/`, `data/gold/`.

### Opção 2: Scripts Python (produção/Glue)

```bash
# 1. Configure variáveis de ambiente
cp .env.example .env
# edite .env: S3_BUCKET_NAME, AWS_DEFAULT_REGION, USE_AWS=true

# 2. Setup AWS (criar bucket, Glue DB, Athena workgroup)
python infra/setup_aws.py

# 3. Gerar amostras dos dados INEP (necessário apenas uma vez)
python data/samples/generate_samples.py

# 4. Pipeline Bronze
python pipelines/batch/bronze/ingest_bronze.py

# 5. Streaming (terminais separados)
python pipelines/streaming/producer.py &
python pipelines/streaming/consumer.py &

# 6. Silver
python pipelines/batch/silver/transform_silver.py

# 7. Gold
python pipelines/batch/gold/build_gold.py

# 8. Quality Checks
python quality/quality_checks.py
```

### Opção 3: Airflow (orquestração)

```bash
docker-compose up -d
# Acesse http://localhost:8080 (user: admin / pass: admin)
# Ative a DAG: pipeline_alfabetizacao
```

### Variáveis de Ambiente (.env)

```env
# AWS
S3_BUCKET_NAME=tech-challenge-alfabetizacao
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=sua_key
AWS_SECRET_ACCESS_KEY=sua_secret
USE_AWS=false                       # true para usar S3 real

# Base dos Dados (opcional — para ingestão via API)
BASEDOSDADOS_PROJECT_ID=seu_projeto_gcp

# Caminho dos dados INEP locais
INEP_DATA_DIR=/caminho/para/Dados INEP

# Glue / Athena
GLUE_DATABASE=alfabetizacao_db
ATHENA_OUTPUT_LOCATION=s3://tech-challenge-alfabetizacao/athena-results/
```

---

## Decisões Arquiteturais

### Batch vs Streaming

| Aspecto | Batch | Streaming |
|---|---|---|
| **Quando usar** | Dados históricos consolidados (censos, avaliações anuais) | Eventos em tempo quase real (atualizações de secretarias) |
| **Latência** | Horas (job diário) | Segundos a minutos |
| **Custo** | Mais barato por volume | Mais caro por evento |
| **Escolha** | Dados INEP históricos completos | Alertas e atualizações entre janelas batch |

**Decisão:** pipeline híbrida — Batch para o bulk histórico, Streaming para eventos de atualização. O Streaming é simulado localmente com fila JSONL e código pronto para Kinesis em produção.

### Data Lake (S3 + Athena) vs Data Warehouse (Redshift)

- **Escolha: Data Lake**
- **Razão:** Volume moderado (~30k linhas); Athena elimina o custo fixo de cluster (~$182/mês Redshift mínimo). Trade-off: queries ~10x mais lentas que Redshift, mas aceitável para análises educacionais não-interativas.

### AWS Glue vs EMR

- **Escolha: Glue Serverless**
- **Razão:** Volume de dados em MB, não TB. EMR seria superdimensionado. Glue cobra apenas pelo tempo de execução do job — custo próximo a zero para este volume.

### Parquet vs CSV vs JSON

- **Escolha: Parquet (PyArrow)**
- **Razão:** Columnar permite que Athena leia apenas as colunas necessárias; compressão reduz storage em 60-80%; particionamento Hive-style reduz scan do Athena em até 90%.

---

## Monitoramento da Pipeline

| Mecanismo | Como Funciona |
|---|---|
| **Logs Python (logging)** | Cada etapa logueia volume processado, erros e timing |
| **Quality Checks** | Suite de assertions (not_empty, no_duplicates, range, ref_integrity) por camada |
| **Relatório JSON** | `docs/quality_reports/quality_report_*.json` gerado a cada execução |
| **Airflow Task Status** | Cada task Bronze/Silver/Gold/Quality tem status de sucesso/falha |
| **CloudWatch Logs** | Glue Jobs publicam logs automaticamente (ativado no workgroup Athena) |
| **Athena workgroup** | Limite de 1 GB de scan por query — alerta se query exceder |

---

## FinOps — Otimização de Custos

| Prática | Impacto Estimado |
|---|---|
| **Parquet vs CSV** | ~70% menos armazenamento S3; ~10x menos custo Athena (paga por bytes) |
| **Particionamento `sigla_uf/ano`** | Athena escaneia só partições relevantes → ~90% redução de custo por query |
| **S3 Lifecycle Bronze → S3-IA (90 dias)** | ~45% redução no custo de dados frios de auditoria |
| **Airflow Docker vs MWAA** | Economiza ~$400/mês |
| **Athena vs Redshift** | Sem cluster fixo → ~$182/mês economizado |
| **Glue Serverless vs EMR** | Paga apenas pelo tempo de execução |
| **Athena workgroup 1 GB limit** | Previne queries acidentais caras |

**Estimativa de custo mensal (ambiente de estudo):**

| Serviço | Custo/mês | Observação |
|---|---|---|
| S3 Standard (< 5 GB) | $0.30 | $0.023/GB |
| S3 Standard-IA (Bronze) | $0.10 | após 90 dias |
| AWS Glue (4 DPU-hora) | $1.76 | $0.44/DPU-hora |
| AWS Athena (5 GB) | $0.25 | $5/TB, Parquet 10x barato |
| CloudWatch Logs | $0.50 | |
| **TOTAL** | **~$3/mês** | |

---

## Regras de Qualidade de Dados

A suite de checks valida cada camada:

```python
# Exemplo de checks Silver
check_not_empty(df)
check_no_duplicates(df, ["id_municipio", "ano", "serie", "rede"])
check_no_nulls(df, ["id_municipio", "ano"])
check_range(df, "taxa_alfabetizacao", 0, 100)
check_completeness_ufs(df, "sigla_uf", expected_count=27)
check_ref_integrity(df, "sigla_uf", ufs_validas)
```

---

## Aplicação em Inteligência Artificial

A camada Gold habilita diretamente:

### 1. Predição de Alfabetização por Município
```
Features: taxa_anterior, media_portugues, proporcao_nivel_0, meta_municipio, sigla_uf
Target:   taxa_alfabetizacao (próximo ano)
Modelos:  Gradient Boosting, Random Forest, XGBoost
```

### 2. Classificação de Municípios em Risco
```
Target:   atingira_meta_2030 (binário)
Features: gap_meta_uf_2030, evolucao_2023-2024, proporcao_nivel_0
```

### 3. Clustering de Vulnerabilidade Educacional
```
Algoritmo: K-Means ou DBSCAN
Features:  taxa_alfabetizacao, media_portugues, gap_meta
Saída:     grupos de municípios por perfil educacional
```

### 4. Análise de Séries Temporais
```
Dataset:  gold_evolucao_temporal_uf
Modelos:  Prophet, SARIMA, LSTM
Uso:      projetar trajetória de cada UF até 2030
```

**A feature matrix está pronta no notebook 03** (`gold_indicador_municipio`) com 23k+ registros e variáveis numéricas alinhadas para scikit-learn.

---

## Git Workflow

```
main          ← produção estável
develop       ← integração
feature/*     ← desenvolvimento de funcionalidades
```

Branches criadas:
- `feature/bronze-ingestion`
- `feature/silver-transformation`
- `feature/gold-analytics`
- `feature/streaming`

PRs de `feature/*` → `develop` → `main` com revisão e comentários justificando alterações.

---

## Fonte dos Dados

- **INEP — Avaliação de Alfabetização:** [Base dos Dados — Indicador Criança Alfabetizada](https://basedosdados.org/dataset/br_inep_indicador_crianca_alfabetizada)
- **Ponto de corte:** 743 pontos na escala SAEB (definido pela Pesquisa Alfabetiza Brasil, 2023)
- **Meta nacional:** 80% das crianças alfabetizadas ao final do 2º ano do EF até 2030
