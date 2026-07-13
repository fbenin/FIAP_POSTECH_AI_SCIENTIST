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
| `microdados_alunos_saeb_2021_amostra.csv` | Microdados SAEB 2021 — alunos do 2º ano EF | Individual (~10.000 linhas) |

Todos os arquivos CSV estão armazenados na camada **Raw** do S3 (`s3://tech-challenge-alfabetizacao-01/raw/`) e são lidos diretamente de lá pelo pipeline.

---

## Arquitetura da Solução

### Diagrama da Pipeline

```
╔══════════════════════════════════════════════════════════════════════╗
║                        FONTES DE DADOS                               ║
║                                                                      ║
║  ┌──────────────────────────────────┐   ┌──────────────────────────┐  ║
║  │  S3 Raw  (CSV — imutável)        │   │  Streaming Simulado      │  ║
║  │  s3://bucket/raw/                │   │  Eventos de atualização  │  ║
║  │  - meta_brasil                   │   │  - indicador_atualizado  │  ║
║  │  - meta_uf                       │   │  - meta_revisada         │  ║
║  │  - meta_municipio                │   │  - medicao_desempenho    │  ║
║  │  - indicador_uf                  │   └───────────┬──────────────┘  ║
║  │  - indicador_municipio           │               │ (Kinesis em    ║
║  │  - microdados_alunos_saeb_2021   │               │  produção)     ║
║  └────────────┬─────────────────────┘               │                ║
╚═══════════════╪═════════════════════════════════════╪════════════════╝
                │  EventBridge (cron diário 6h UTC)   │  Near-real-time
                │  → Lambda pipeline-alfabetizacao    │
                ▼                                     ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    BRONZE LAYER  (S3 Parquet)                        ║
║                                                                      ║
║  s3://bucket/bronze/meta_brasil/run_ts=.../                          ║
║  s3://bucket/bronze/meta_uf/run_ts=.../                              ║
║  s3://bucket/bronze/meta_municipio/run_ts=.../                       ║
║  s3://bucket/bronze/indicador_uf/run_ts=.../                         ║
║  s3://bucket/bronze/indicador_municipio/run_ts=.../                  ║
║  s3://bucket/bronze/microdados_alunos/run_ts=.../                    ║
║  s3://bucket/bronze/streaming/dt=YYYY-MM-DD/batch_*.parquet          ║
║                                                                      ║
║  Características: dados brutos, metadados de ingestão,              ║
║  histórico completo, lifecycle → S3-IA após 90 dias (FinOps)         ║
╚══════════════════════════════╤═══════════════════════════════════════╝
                               │  Lambda / Python ETL
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
║  s3://bucket/silver/microdados_alunos/                               ║
╚══════════════════════════════╤═══════════════════════════════════════╝
                               │  Lambda / Python ETL
                               ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    GOLD LAYER  (S3 Parquet Analítico)                ║
║                                                                      ║
║  Datasets prontos para consumo:                                      ║
║  • indicador_municipio      — taxa + metas + gaps por município      ║
║  • evolucao_temporal_uf     — série histórica por estado             ║
║  • ranking_uf               — ranking de UFs no ano mais recente     ║
║  • municipios_risco         — municípios mais distantes da meta      ║
║  • comparativo_nacional     — evolução nacional vs trajetória 2030   ║
║  • proficiencia_municipio   — proficiência SAEB por município        ║
╚══════════════════════════════╤═══════════════════════════════════════╝
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
        AWS Athena                     Dashboards / ML
     (SQL ad-hoc)              (Power BI / Looker / scikit-learn)
```

### Fluxo de Dados

```
1. [Raw]       CSVs INEP armazenados em s3://bucket/raw/ (imutável)
2. [Batch]     Lambda lê Raw CSV → converte Parquet → S3 Bronze (com metadados de ingestão)
3. [Streaming] Eventos → fila JSONL → S3 Bronze/streaming/
4. [ETL]       S3 Bronze → Python ETL → S3 Silver (particionado por sigla_uf/ano)
5. [ETL]       S3 Silver → Python ETL → S3 Gold (datasets analíticos)
6. [Query]     S3 Gold → Athena (SQL) → BI / ML
7. [Monitor]   Cada etapa → CloudWatch Logs + Quality Checks Python
```

---

## Stack Tecnológica

| Componente | Tecnologia | Justificativa |
|---|---|---|
| **Storage (todas as camadas)** | AWS S3 | Barato ($0.023/GB), durável 11 9s, integrado nativamente com Glue e Athena |
| **Raw Layer** | AWS S3 (`/raw/`) | CSVs originais do INEP armazenados de forma imutável; pipeline sempre lê daqui |
| **ETL / Transformação** | Python (pandas + boto3) | Serverless via Lambda; sem gestão de cluster |
| **Consulta analítica** | AWS Athena | SQL direto no S3, paga por query ($5/TB), sem servidor fixo |
| **Orquestração** | AWS Lambda + EventBridge | Serverless, cron diário às 6h UTC, custo próximo a zero |
| **Ingestão Batch** | Python + boto3 (lê S3 raw/) | Lê diretamente os CSVs da camada Raw no S3 |
| **Streaming simulado** | Python producer/consumer | Simula Kinesis sem custo em dev; código pronto para migrar para Kinesis |
| **Qualidade de dados** | Python (pandas + assertions) | Framework leve, sem dependências extras, integrado à Lambda |
| **Formato de arquivo** | **Parquet (PyArrow)** | 60-80% menor que CSV; columnar reduz custo Athena em ~10x |
| **Notebooks** | Jupyter (.ipynb) | Documentação executável, EDA integrada, facilita reprodução |

---

## Estrutura do Repositório

```
tech-challenge-fase2/
│
├── notebooks/                          ← PIPELINE PRINCIPAL (Jupyter)
│   ├── 01_setup_e_ingestao_bronze.ipynb   # Setup AWS + ingestão Bronze (lê S3 raw/)
│   ├── 02_silver_transformation.ipynb     # Limpeza + integração Silver
│   ├── 03_gold_analytics.ipynb            # Datasets analíticos Gold
│   ├── 04_streaming_simulation.ipynb      # Producer/Consumer streaming
│   ├── 05_quality_checks.ipynb            # Validação + FinOps
│   └── 06_validacao_queries.ipynb         # Validação de queries Athena
│
├── pipelines/
│   ├── batch/
│   │   ├── bronze/ingest_bronze.py        # Lê CSVs de S3 raw/ → grava S3 bronze/
│   │   ├── silver/transform_silver.py     # Transformações Silver
│   │   └── gold/build_gold.py             # Construção Gold (6 datasets)
│   ├── streaming/
│   │   ├── producer.py                    # Gerador de eventos
│   │   └── consumer.py                    # Consumidor + persistência Bronze
│   └── orchestration/
│       └── dags/pipeline_alfabetizacao.py # DAG Airflow (referência — substituído por Lambda)
│
├── quality/
│   └── checks/
│       └── quality_checks.py              # Suite de checks por camada
│
├── infra/
│   ├── setup_aws.py                       # Cria S3 + Glue DB + Athena workgroup
│   ├── setup_lambda_pipeline.py           # Provisiona Lambda + EventBridge (carga automática)
│   └── lambda/
│       └── handler.py                     # Handler da Lambda (Bronze→Silver→Gold→Quality)
│
├── data/
│   ├── bronze/                            # Bronze local (gerado pelos notebooks)
│   ├── silver/                            # Silver local (gerado pelos notebooks)
│   ├── gold/                              # Gold local (gerado pelos notebooks)
│   └── samples/
│       ├── generate_samples.py            # Converte CSVs INEP → Parquet local
│       ├── download_saeb_sample.py        # Baixa amostra dos microdados SAEB
│       └── create_synthetic_samples.py    # Gera dados sintéticos para testes
│
├── monitoring/
│   ├── alerts/                            # Configurações de alertas CloudWatch
│   └── dashboards/                        # Configurações de dashboards
│
├── docs/
│   ├── athena_queries.sql                 # Queries SQL prontas para Athena
│   ├── DOCUMENTATION.md                   # Documentação técnica detalhada
│   └── quality_reports/                   # Relatórios JSON de qualidade
│
├── docker-compose.yml                     # Airflow local (referência)
├── requirements.txt
└── .env.example                           # Template de variáveis de ambiente
```

---

## Como Executar

### Pré-requisitos

```bash
Python 3.9+
pip install -r requirements.txt

# Credenciais AWS (necessário para todos os modos):
aws configure  # ou configure no .env
```

### Opção 1: Notebooks (recomendado)

Execute na ordem — cada notebook depende do anterior:

```bash
cd notebooks/
jupyter notebook

# Ordem de execução:
# 01_setup_e_ingestao_bronze.ipynb   ← lê CSVs de s3://bucket/raw/
# 02_silver_transformation.ipynb
# 03_gold_analytics.ipynb
# 04_streaming_simulation.ipynb
# 05_quality_checks.ipynb
# 06_validacao_queries.ipynb
```

> Os notebooks leem os dados diretamente do S3 (`raw/`) e requerem credenciais AWS.

### Opção 2: Scripts Python (produção)

```bash
# 1. Configure variáveis de ambiente
cp .env.example .env
# edite .env: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, USE_AWS=true
# atenção: atualize GLUE_IAM_ROLE com o ARN da sua conta AWS

# 2. Setup AWS (criar bucket, Glue DB, Athena workgroup) — apenas uma vez
python infra/setup_aws.py

# 3. Pipeline manual
python pipelines/batch/bronze/ingest_bronze.py   # lê raw/ → grava bronze/
python pipelines/batch/silver/transform_silver.py
python pipelines/batch/gold/build_gold.py
python quality/checks/quality_checks.py
```

### Opção 3: Carga Automática (Lambda + EventBridge — recomendado para produção)

O pipeline é executado automaticamente todos os dias às **6h UTC** via AWS Lambda + EventBridge.

```bash
# Provisionar infraestrutura (apenas uma vez):
python infra/setup_lambda_pipeline.py

# Invocar manualmente para testar:
aws lambda invoke \
  --function-name pipeline-alfabetizacao \
  --payload '{}' /tmp/out.json && cat /tmp/out.json

# Acompanhar logs:
aws logs tail /aws/lambda/pipeline-alfabetizacao --follow
```

**Recursos provisionados:**

| Recurso | Nome | Detalhe |
|---|---|---|
| IAM Role | `lambda-pipeline-alfabetizacao-role` | LambdaBasicExecution + S3FullAccess |
| Lambda | `pipeline-alfabetizacao` | Python 3.12, 512 MB, timeout 15 min |
| EventBridge | `pipeline-alfabetizacao-daily` | `cron(0 6 * * ? *)` — diário às 6h UTC |

### Variáveis de Ambiente (.env)

```env
# AWS
AWS_ACCESS_KEY_ID=sua_key
AWS_SECRET_ACCESS_KEY=sua_secret
AWS_DEFAULT_REGION=us-east-1

# S3
S3_BUCKET_NAME=tech-challenge-alfabetizacao-01
S3_RAW_PREFIX=raw
S3_BRONZE_PREFIX=bronze
S3_SILVER_PREFIX=silver
S3_GOLD_PREFIX=gold

# Controle de execução
USE_AWS=true                        # true = lê/grava S3; false = modo local

# Glue / Athena
GLUE_DATABASE=alfabetizacao_db
GLUE_IAM_ROLE=arn:aws:iam::<sua-conta>:role/GlueServiceRole   # substitua pelo ARN da sua conta
ATHENA_OUTPUT_LOCATION=s3://tech-challenge-alfabetizacao-01/athena-results/
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
| **CloudWatch Logs** | Lambda publica logs automaticamente em `/aws/lambda/pipeline-alfabetizacao` |
| **EventBridge** | Disparo diário às 6h UTC com histórico de invocações no console AWS |
| **Athena workgroup** | Limite de 1 GB de scan por query — alerta se query exceder |

---

## FinOps — Otimização de Custos

| Prática | Impacto Estimado |
|---|---|
| **Parquet vs CSV** | ~70% menos armazenamento S3; ~10x menos custo Athena (paga por bytes) |
| **Particionamento `sigla_uf/ano`** | Athena escaneia só partições relevantes → ~90% redução de custo por query |
| **S3 Lifecycle Bronze → S3-IA (90 dias)** | ~45% redução no custo de dados frios de auditoria |
| **Lambda + EventBridge vs MWAA** | Economiza ~$400/mês (MWAA mínimo); Lambda é praticamente gratuito |
| **Athena vs Redshift** | Sem cluster fixo → ~$182/mês economizado |
| **Glue Serverless vs EMR** | Paga apenas pelo tempo de execução |
| **Athena workgroup 1 GB limit** | Previne queries acidentais caras |

**Estimativa de custo mensal (ambiente de estudo):**

| Serviço | Custo/mês | Observação |
|---|---|---|
| S3 Standard (< 5 GB) | $0.30 | $0.023/GB — inclui camada raw/ |
| S3 Standard-IA (Bronze) | $0.10 | após 90 dias |
| AWS Lambda | ~$0.00 | free tier: 1M invocações/mês |
| EventBridge | ~$0.00 | free tier: 14M eventos/mês |
| AWS Athena (5 GB) | $0.25 | $5/TB, Parquet 10x barato |
| CloudWatch Logs | $0.50 | |
| **TOTAL** | **~$1/mês** | |

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

## Fonte dos Dados

- **INEP — Avaliação de Alfabetização:** [Base dos Dados — Indicador Criança Alfabetizada](https://basedosdados.org/dataset/073a39d4-89cf-4068-b1e8-34ed0d9c0b72?table=e1de7a6a-5038-4e81-89f0-a15f2cc12c9b)
- **Ponto de corte:** 743 pontos na escala SAEB (definido pela Pesquisa Alfabetiza Brasil, 2023)
- **Meta nacional:** 80% das crianças alfabetizadas ao final do 2º ano do EF até 2030
