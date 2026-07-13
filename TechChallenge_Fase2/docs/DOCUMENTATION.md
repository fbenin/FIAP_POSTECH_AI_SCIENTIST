# TECH CHALLENGE FASE 2 — Documentação Técnica

## O que é este projeto

Repositório criado para o **Tech Challenge Fase 2 do curso IAST/FIAP (PÓS TECH)**.
O objetivo é construir uma pipeline híbrida de dados (Batch + Streaming) para analisar
o **Indicador Criança Alfabetizada** do INEP, usando a **Arquitetura Medalhão** na AWS.

---

## Estrutura de Pastas

```
tech-challenge-fase2/
│
├── notebooks/                          ← PIPELINE PRINCIPAL (Jupyter — executar nesta ordem)
│   ├── 01_setup_e_ingestao_bronze.ipynb
│   ├── 02_silver_transformation.ipynb
│   ├── 03_gold_analytics.ipynb
│   ├── 04_streaming_simulation.ipynb
│   ├── 05_quality_checks.ipynb
│   └── 06_validacao_queries.ipynb
│
├── pipelines/                          ← Scripts Python equivalentes (produção / Lambda)
│   ├── batch/
│   │   ├── bronze/ingest_bronze.py     ← lê s3://bucket/raw/ → grava s3://bucket/bronze/
│   │   ├── silver/transform_silver.py
│   │   └── gold/build_gold.py          ← gera 6 datasets analíticos
│   ├── streaming/
│   │   ├── producer.py
│   │   └── consumer.py
│   └── orchestration/dags/
│       └── pipeline_alfabetizacao.py   ← DAG Airflow (referência — substituído por Lambda)
│
├── quality/
│   └── checks/
│       └── quality_checks.py           ← Suite de validações por camada
│
├── infra/
│   ├── setup_aws.py                    ← Cria bucket S3 + Glue DB + Athena workgroup
│   ├── setup_lambda_pipeline.py        ← Provisiona Lambda + EventBridge (carga automática)
│   └── lambda/
│       └── handler.py                  ← Handler Lambda: Bronze→Silver→Gold→Quality
│
├── monitoring/
│   ├── alerts/                         ← Configurações de alertas CloudWatch
│   └── dashboards/                     ← Configurações de dashboards
│
├── data/
│   ├── bronze/                         ← Bronze local (gerado pelos notebooks)
│   ├── silver/                         ← Silver local (gerado pelos notebooks)
│   ├── gold/                           ← Gold local (gerado pelos notebooks)
│   └── samples/
│       ├── generate_samples.py         ← Converte CSVs INEP reais → Parquet
│       ├── download_saeb_sample.py     ← Baixa amostra dos microdados SAEB
│       └── create_synthetic_samples.py ← Gera dados sintéticos para testes
│
├── docs/
│   ├── DOCUMENTATION.md                ← Este arquivo
│   ├── athena_queries.sql              ← 5 queries SQL prontas para Athena
│   └── quality_reports/               ← Relatórios JSON gerados pelo notebook 05
│
├── docker-compose.yml                  ← Airflow local (referência)
├── requirements.txt
└── .env.example
```

---

## Dados INEP — Fonte Real (S3 Raw)

Os 6 arquivos CSV do INEP estão armazenados na camada **Raw** do S3, de forma imutável:

```
s3://tech-challenge-alfabetizacao-01/raw/
```

| Arquivo | Linhas | Granularidade |
|---|---|---|
| `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv` | 3 | Nacional |
| `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv` | 54 | Estadual |
| `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_municipio.csv` | 10.704 | Municipal |
| `br_inep_avaliacao_alfabetizacao_uf.csv` | 145 | Estadual |
| `br_inep_avaliacao_alfabetizacao_municipio.csv` | 23.995 | Municipal |
| `microdados_alunos_saeb_2021_amostra.csv` | 10.000 | Individual (alunos 2º ano EF) |

> A pasta `dadosINEP/` local foi removida do repositório. O pipeline lê diretamente do S3 `raw/` — não há dependência de arquivos locais.

**Colunas principais:**
- `ano` — ano de referência (2023, 2024…)
- `sigla_uf` — sigla do estado (ex: "SP")
- `id_municipio` — código IBGE de 7 dígitos
- `taxa_alfabetizacao` — % crianças alfabetizadas no 2º ano EF
- `meta_alfabetizacao_2024` … `meta_alfabetizacao_2030` — trajetória de metas
- `rede` — tipo de rede escolar (ex: "Pública", "Municipal")
- `serie` — série avaliada (sempre 2 = 2º ano EF)
- `media_portugues` — proficiência média na escala SAEB (743 = ponto de corte)

---

## Arquivo por arquivo

---

### `notebooks/01_setup_e_ingestao_bronze.ipynb`

**O que faz:** Configura a infraestrutura AWS e realiza a ingestão da camada Bronze.

**Seções:**
1. Instalação de dependências e imports
2. Configuração de variáveis (bucket S3, região, prefixos raw/ e bronze/)
3. Funções de setup AWS: `create_bucket()`, `set_lifecycle_policy()`, `create_glue_database()`, `create_athena_workgroup()`
4. Leitura dos 6 CSVs diretamente de `s3://bucket/raw/` via `s3_client.get_object()`, com adição de metadados: `_fonte`, `_arquivo_origem`, `_data_ingestao`
5. EDA básica: schema, nulos, valores únicos por dataset
6. Conversão para Parquet e upload para `s3://bucket/bronze/`
7. Verificação final com contagem de linhas por tabela

**Fonte dos dados:**
O notebook lê os CSVs diretamente da camada Raw do S3 (`s3://bucket/raw/`). Não há leitura de arquivos locais.

**Por que metadados no Bronze:**
Seguindo o padrão das aulas de Arquitetura de Big Data (notebook `02_carga_camada_bronze.py` da professora),
cada registro Bronze recebe `_data_ingestao` e `_fonte` para rastreabilidade e reprocessamento.

**Particionamento Bronze:**
```
s3://bucket/bronze/<tabela>/run_ts=20250710T120000/<tabela>.parquet
```
Permite reprocessar uma janela específica sem re-ingerir todo o histórico.

**FinOps aplicado:**
- S3 Lifecycle: `bronze/` migra para `STANDARD_IA` após 90 dias (45% mais barato)
- Athena workgroup com limite de 1 GB por query

---

### `notebooks/02_silver_transformation.ipynb`

**O que faz:** Limpeza, padronização e integração das 5 bases na camada Silver.

**Transformações por tabela:**

| Tabela | Transformações |
|---|---|
| `meta_brasil` | Lowercase, numérico, dedup por `[ano, rede]`, title-case em `rede` |
| `meta_uf` | + `sigla_uf` upper, drop nulos em `sigla_uf` |
| `meta_municipio` | + `id_municipio` zfill(7), drop nulos em `[id_municipio, ano]` |
| `indicador_uf` | Converte `serie` e `rede` para Int64, filtra `taxa` ∈ [0,100] |
| `indicador_municipio` | Converte `serie` e `rede` para Int64, filtra `taxa` ∈ [0,100], extrai `sigla_uf` dos 2 primeiros dígitos do `id_municipio` via mapa IBGE |

**Integração (JOINs na Silver):**
```
indicador_municipio
  LEFT JOIN meta_municipio   ON [id_municipio, ano]
  LEFT JOIN meta_uf          ON [sigla_uf, ano]
  LEFT JOIN meta_brasil      ON [ano]
```
> Nota: a coluna `rede` é excluída das chaves de join porque tem encoding diferente entre tabelas (numérico vs texto).

**Colunas calculadas criadas:**
- `gap_meta_municipio_2030` = `taxa_alfabetizacao` − `meta_mun_2030`
- `gap_meta_uf_2030` = `taxa_alfabetizacao` − `meta_uf_2030`
- `atingiu_meta_uf` = `gap_meta_uf_2030 >= 0` (booleano)

**Particionamento Silver:**
```
s3://bucket/silver/alfabetizacao_municipio/sigla_uf=SP/ano=2023/data.parquet
```
Reduz custo Athena em até 90% para queries filtradas por UF ou ano.

---

### `notebooks/03_gold_analytics.ipynb`

**O que faz:** Constrói os 6 datasets analíticos da camada Gold.

| Dataset | Construção | Uso |
|---|---|---|
| `indicador_municipio` | Seleciona colunas-chave + adiciona `categoria_risco` (4 faixas de gap) | Dashboard principal, análise por município |
| `evolucao_temporal_uf` | GroupBy `[ano, sigla_uf]`: média, mediana, total_municipios | Séries históricas, tendências regionais |
| `ranking_uf` | GroupBy `sigla_uf` no ano mais recente, ordena por `media_taxa` | Comparativo entre estados |
| `municipios_risco` | Top 100 municípios com pior `gap_meta_uf_2030` | Priorização de políticas públicas |
| `comparativo_nacional` | Derrete colunas `meta_2024..2030` em linhas (melt) | Evolução nacional vs trajetória |
| `proficiencia_municipio` | Agrega proficiência SAEB dos microdados por município | Correlação proficiência × alfabetização |

**EDA Gold:**
- Gráfico horizontal: Top 10 e Bottom 10 UFs por taxa de alfabetização
- Gráfico de linha: taxa realizada vs trajetória de meta nacional

**Feature matrix para ML:**
```python
feature_cols = [
    "taxa_alfabetizacao",      # TARGET
    "media_portugues",         # proficiência linguística
    "meta_mun_2030",           # nível de ambição da meta
    "gap_meta_uf_2030",        # gap atual
    "proporcao_aluno_nivel_0", # % alunos sem proficiência
]
```

---

### `notebooks/04_streaming_simulation.ipynb`

**O que faz:** Simula ingestão de eventos em tempo quase real.

**Por que streaming:**
Dados educacionais do INEP são anuais (Batch), mas secretarias municipais podem
enviar atualizações intermediárias. O streaming captura esses eventos entre janelas batch.

**Arquitetura:**
```
Producer (Python)  →  fila JSONL  →  Consumer  →  Bronze/streaming/ (Parquet)
                  [em produção: substituir por Kinesis Data Streams]
```

**Eventos simulados:**
- Tipo: `indicador_atualizado`, `meta_revisada`, `medicao_desempenho`, `avaliacao_municipal`
- Payload: `sigla_uf`, `id_municipio`, `ano`, `serie`, `rede`, `taxa_alfabetizacao`, `media_portugues`
- Municípios: 10 municípios reais de capitais brasileiras (códigos IBGE corretos)

**Micro-batch:** 10 eventos → flush como Parquet em `bronze/streaming/dt=YYYY-MM-DD/`

**Referência de produção:** O notebook inclui snippets comentados mostrando como substituir
a fila JSONL por `boto3.client("kinesis").put_record()` / `get_records()`.

**Validações aplicadas:**
- Nulos em `sigla_uf`, `id_municipio`, `taxa_alfabetizacao`
- Event IDs duplicados
- `taxa_alfabetizacao` fora do intervalo [0, 100]

---

### `notebooks/05_quality_checks.ipynb`

**O que faz:** Suite completa de qualidade de dados + monitoramento + FinOps.

**Framework de qualidade:**
```python
@dataclass
class CheckResult:
    check: str
    passed: bool
    detail: str
    severity: str  # "error" | "warning" | "info"

@dataclass
class QualityReport:
    layer: str
    table: str
    n_rows: int
    results: List[CheckResult]
```

**Checks implementados:**
| Função | Verifica |
|---|---|
| `check_not_empty(df)` | Tabela com pelo menos 1 linha |
| `check_no_duplicates(df, subset)` | Sem linhas duplicadas nas colunas-chave |
| `check_no_nulls(df, cols)` | Campos obrigatórios sem nulos |
| `check_range(df, col, lo, hi)` | Valores dentro do intervalo esperado |
| `check_ref_integrity(df, fk_col, ref_values)` | Chave estrangeira com referência válida |
| `check_completeness_ufs(df, col, 27)` | Cobertura dos 27 estados brasileiros |

**Suites por camada:**
- `suite_bronze()` → valida os 6 arquivos Bronze
- `suite_silver()` → valida `alfabetizacao_municipio`, `alfabetizacao_uf` e `microdados_alunos`
- `suite_gold()` → valida os 6 datasets Gold

**Saída:**
- Tabela resumo: status por tabela, contagem de linhas, erros e avisos
- Arquivo JSON em `docs/quality_reports/quality_report_<timestamp>.json`
- Exit implícito: se há falhas de `severity="error"`, o resultado é `passed=False`

**Monitoramento operacional:**
- Tamanho de cada camada em MB
- Número de arquivos Parquet por camada
- Lista de alertas de qualidade pendentes

**Análise FinOps:**
- Estimativa detalhada por serviço AWS
- Tabela de economias aplicadas (Parquet, particionamento, Airflow local, etc.)
- Gráfico de breakdown de custo

---

### `pipelines/batch/bronze/ingest_bronze.py`

**O que é:** Versão script Python do notebook 01, executada pela Lambda em produção.

**Funcionamento:**
- Lê cada CSV diretamente de `s3://bucket/raw/<arquivo>.csv` via `boto3`
- Adiciona metadados de ingestão (`_fonte`, `_arquivo_origem`, `_data_ingestao`)
- Converte para Parquet e grava em `s3://bucket/bronze/<tabela>/run_ts=.../`

**Sem fallback local:** o pipeline requer acesso ao S3. Não há leitura de arquivos locais nem dependência de Base dos Dados.

---

### `pipelines/batch/silver/transform_silver.py`

**O que é:** Versão script Python do notebook 02, refatorada para produção.

**Mudanças em relação à versão original:**
- Colunas corrigidas para o schema real do INEP (a versão anterior usava `perc_alfabetizados`,
  `meta`; o schema real usa `taxa_alfabetizacao`, `meta_alfabetizacao_2030`)
- Extração de `sigla_uf` dos 2 primeiros dígitos do `id_municipio` via mapa IBGE
  (os arquivos INEP de município não têm coluna `sigla_uf`)
- `rede` removida das chaves de JOIN (encoding diferente entre tabelas: numérico vs texto)
- Suporte a modo local e modo AWS controlado por `USE_AWS`

---

### `pipelines/batch/gold/build_gold.py`

**O que é:** Versão script Python do notebook 03.

**Datasets gerados (6):**
- `gold/indicador_municipio/` — taxa + metas + gaps + categoria de risco por município
- `gold/evolucao_temporal_uf/` — série histórica por UF (média, mediana, total_municipios)
- `gold/ranking_uf/` — ranking por estado no ano mais recente
- `gold/municipios_risco/` — top 100 municípios com maior gap negativo vs meta 2030
- `gold/comparativo_nacional/` — evolução nacional vs trajetória de metas 2024–2030
- `gold/proficiencia_municipio/` — proficiência SAEB por município (dos microdados alunos)

---

### `pipelines/streaming/producer.py`

**O que é:** Gerador de eventos simulados.

**Configurável via env:**
- `STREAMING_INTERVAL` — segundos entre eventos (padrão: 2)

**Para substituir por Kinesis em produção:**
```python
kinesis.put_record(
    StreamName="alfabetizacao-indicadores",
    Data=json.dumps(event).encode(),
    PartitionKey=event["payload"]["sigla_uf"]
)
```

---

### `pipelines/streaming/consumer.py`

**O que é:** Consumidor de eventos com persistência no Bronze.

**Configurável via env:**
- `STREAMING_FLUSH_EVERY` — eventos por micro-batch (padrão: 10)
- `STREAMING_POLL_INTERVAL` — segundos entre polls (padrão: 3)

---

### `quality/quality_checks.py`

**O que é:** Versão script Python do notebook 05, sem EDA nem gráficos.

**Integração com Airflow:** retorna `True/False` e lança `ValueError` em caso de falha,
o que faz a task Airflow marcar como `FAILED` e disparar retry.

---

### `orchestration/dags/pipeline_alfabetizacao.py`

**O que é:** DAG Airflow de referência — mantida no repositório para documentação da lógica de orquestração.

**Em produção, a orquestração é feita pela AWS Lambda + EventBridge** (ver `infra/lambda/handler.py`). O Airflow local via Docker não é mais o mecanismo de agendamento ativo.

**Grafo de dependências:**
```
start → ingest_bronze → transform_silver → quality_check_silver
      → build_gold → quality_check_gold → end
```

**Agendamento original:** `0 6 * * *` — diário às 6h UTC (mesma frequência mantida no EventBridge)

**Proteção:** quality checks são bloqueantes — Gold só é construído se Silver passar.

---

### `infra/lambda/handler.py`

**O que é:** Handler da AWS Lambda que orquestra o pipeline completo em produção.

**Fluxo de execução:**
```
1. Bronze  — lê s3://bucket/raw/ → grava s3://bucket/bronze/
2. Silver  — lê Bronze → transforma → grava s3://bucket/silver/
3. Gold    — lê Silver → agrega → grava s3://bucket/gold/
4. Quality — valida camadas Silver e Gold; loga resultado no CloudWatch
```

**Retorno:** JSON com `statusCode` e resultados de cada etapa. Em caso de falha, a etapa seguinte não é executada.

---

### `infra/setup_lambda_pipeline.py`

**O que é:** Script boto3 idempotente que provisiona toda a infraestrutura de agendamento na AWS.

**O que cria/atualiza:**
1. IAM Role `lambda-pipeline-alfabetizacao-role` (LambdaBasicExecution + S3FullAccess)
2. Lambda function `pipeline-alfabetizacao` (Python 3.12, 512 MB, timeout 15 min)
3. EventBridge rule `pipeline-alfabetizacao-daily` (`cron(0 6 * * ? *)` — diário às 6h UTC)
4. Permissão para o EventBridge invocar a Lambda

**Execute uma vez para provisionar; reexecute após alterar o código para atualizar a Lambda.**

```bash
python infra/setup_lambda_pipeline.py
```

---

### `data/samples/generate_samples.py`

**O que é:** Converte os CSVs reais do INEP em arquivos Parquet para desenvolvimento local.

**Mudança em relação à versão original:**
A versão anterior gerava dados **sintéticos** (aleatórios). A versão atual lê os
**CSVs reais do INEP** e os converte para Parquet. Isso garante que os testes locais
usem os mesmos dados que o pipeline em produção usaria.

**Como usar:**
```bash
INEP_DATA_DIR="/caminho/para/Dados INEP" python3 data/samples/generate_samples.py
```

**Resultado:**
```
data/samples/meta_brasil.parquet           (3 linhas)
data/samples/meta_uf.parquet              (54 linhas)
data/samples/meta_municipio.parquet       (10.704 linhas)
data/samples/indicador_uf.parquet         (145 linhas)
data/samples/indicador_municipio.parquet  (23.995 linhas)
data/samples/microdados_alunos.parquet    (10.000 linhas)
```

Outros scripts no mesmo diretório:
- `download_saeb_sample.py` — baixa amostra dos microdados SAEB diretamente da fonte
- `create_synthetic_samples.py` — gera dados sintéticos aleatórios para testes unitários

---

### `infra/setup_aws.py`

**O que é:** Script de criação da infraestrutura AWS (idempotente — pode ser reexecutado).

**O que cria:**
1. Bucket S3 com bloqueio de acesso público
2. Lifecycle policy: `bronze/` → `STANDARD_IA` após 90 dias
3. Glue Database `alfabetizacao_db`
4. Athena Workgroup com limite de 1 GB por query e CloudWatch habilitado

**Execute uma vez antes de qualquer pipeline em produção.**

---

### `docs/athena_queries.sql`

**O que é:** 5 queries SQL prontas para executar no Athena contra a camada Gold.

| Query | O que retorna |
|---|---|
| 1 | Top 10 municípios por taxa de alfabetização |
| 2 | Evolução temporal por UF |
| 3 | Municípios abaixo da meta estadual |
| 4 | Ranking completo de UFs |
| 5 | Municípios com maior gap negativo vs meta |

---

## Git Workflow

```
main         ← código estável, entregável final
develop      ← integração entre features
feature/*    ← desenvolvimento de cada funcionalidade
```

**Branches existentes:**
- `feature/bronze-ingestion` — notebooks + ingestão Bronze
- `feature/silver-transformation` — transformação Silver
- `feature/gold-analytics` — camada Gold
- `feature/streaming` — producer/consumer

**Fluxo correto:**
```bash
git checkout feature/<nome>
# faz alterações
git add <arquivos específicos>
git commit -m "feat: descrição clara do que foi feito"
git push origin feature/<nome>
# abre Pull Request: feature/* → develop
# após merge de todas: develop → main
```

---

## Como Executar

### Opção 1 — Notebooks (recomendado)

```bash
pip install -r requirements.txt
cp .env.example .env  # configure credenciais AWS
cd notebooks/
jupyter notebook
# execute na ordem: 01 → 02 → 03 → 04 → 05 → 06
```

> Os notebooks leem os dados diretamente de `s3://bucket/raw/` e requerem credenciais AWS.

### Opção 2 — Scripts Python

```bash
# Pré-requisitos
aws configure
cp .env.example .env  # preencha com suas credenciais; atualize GLUE_IAM_ROLE

# Setup (uma vez)
python3 infra/setup_aws.py

# Pipeline
python3 pipelines/batch/bronze/ingest_bronze.py   # lê raw/ → grava bronze/
python3 pipelines/batch/silver/transform_silver.py
python3 pipelines/batch/gold/build_gold.py
python3 quality/checks/quality_checks.py
```

### Opção 3 — Carga Automática (Lambda + EventBridge)

O pipeline roda automaticamente todos os dias às **6h UTC**.

```bash
# Provisionar infraestrutura (uma vez):
python infra/setup_lambda_pipeline.py

# Invocar manualmente para testar:
aws lambda invoke \
  --function-name pipeline-alfabetizacao \
  --payload '{}' /tmp/out.json && cat /tmp/out.json

# Acompanhar logs em tempo real:
aws logs tail /aws/lambda/pipeline-alfabetizacao --follow
```

---

## Decisões Arquiteturais

### Por que Parquet e não CSV?

- 60-80% menor em disco → menos custo S3
- Athena lê apenas as colunas do SELECT → menos bytes escaneados → menor custo
- Suporte nativo a tipos (Int64, float64, bool) → sem ambiguidade de schema

### Por que particionamento `sigla_uf/ano`?

Athena usa particionamento Hive-style para pular arquivos irrelevantes.
Uma query `WHERE sigla_uf = 'SP' AND ano = 2023` escaneia apenas 1 partição
em vez de todas as 54 (27 UFs × 2 anos).

### Por que JOINs na Silver e não na Gold?

- Silver é a "verdade única" — cada análise Gold parte do mesmo dado limpo
- Mais fácil auditar: se um join estiver errado, corrige na Silver e regenera todas as Gold
- Reduz duplicação: sem precisar replicar a lógica de join em cada dataset Gold

### Por que Athena e não Redshift?

- Volume dos dados (~35k linhas) não justifica um cluster fixo
- Athena paga por bytes escaneados: ~$0.25/mês para este projeto
- Redshift mínimo: ~$182/mês (dc2.large reservado) — custo injustificado

### Por que Lambda + EventBridge em vez de Airflow/MWAA?

- MWAA: ~$400/mês mínimo; Lambda é praticamente gratuito (free tier cobre 1M invocações/mês)
- Pipeline completo roda em segundos para este volume (~35k linhas) — bem abaixo do timeout de 15 min
- Sem infraestrutura para manter; logs automáticos no CloudWatch
- Trade-off: sem retry granular por task (Airflow oferece retry por step); aceitável para projeto acadêmico

---

## O que falta para produção

### Credenciais AWS

```bash
aws configure
# ou configure variáveis no .env:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
```

### Repositório GitHub

```bash
# após criar o repo em github.com:
git remote add origin https://github.com/SEU_USERNAME/tech-challenge-fase2.git
git push -u origin main
git push origin develop
git push origin feature/bronze-ingestion
git push origin feature/silver-transformation
git push origin feature/gold-analytics
git push origin feature/streaming
```

### IAM Role para Glue (console AWS)

1. IAM → Roles → Create role → AWS service → Glue
2. Policies: `AWSGlueServiceRole` + `AmazonS3FullAccess`
3. Nome: `GlueServiceRole`
4. Atualizar `GLUE_IAM_ROLE` no `.env`

### Melhorias opcionais

- [ ] Glue Crawlers para atualização automática do schema no Catalog
- [ ] CloudWatch Alarms para falhas de ingestão
- [ ] Integração de fontes externas: Censo Escolar, Atlas IDH, FUNDEB
- [ ] Modelo preditivo de alfabetização (scikit-learn ou SageMaker)
- [ ] Dashboard AWS QuickSight conectado ao Athena Gold
