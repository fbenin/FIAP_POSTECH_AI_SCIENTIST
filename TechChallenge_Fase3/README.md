# Tech Challenge — Fase 3
## Predição e Inteligência Analítica para Alfabetização no Brasil

**Pos Tech FIAP — AI Scientist**

---

## Objetivo

Desenvolver um modelo supervisionado capaz de prever se um aluno será considerado **alfabetizado ou não alfabetizado**, utilizando variáveis educacionais, territoriais e socioeconômicas.

Os dados são provenientes da camada Gold construída na Fase 2, com possível enriquecimento via IBGE, Censo Escolar, FUNDEB, PNAD e Atlas do Desenvolvimento Humano.

---

## Definição Analítica

A camada Gold disponível para esta fase está em granularidade agregada, com registros por município, ano, série e rede de ensino. Por isso, nesta implementação o problema será tratado como uma classificação de risco educacional em nível municipal/agregado, e não como uma predição individual por aluno.

Tabela principal:

```text
data/gold/indicador_municipio/indicador_municipio.parquet
```

Dimensão validada:

```text
23.995 registros x 18 colunas
```

### Variável-alvo

O target binário inicial será derivado da coluna `categoria_risco`:

```text
1 = meta_atingida
0 = critico, alto ou moderado
```

Distribuição validada:

```text
0 - em risco ou abaixo da meta: 19.421 registros (80,94%)
1 - meta atingida:              4.574 registros (19,06%)
```

### Controle De Data Leakage

As colunas abaixo são derivadas diretamente da taxa de alfabetização, das metas ou da própria classificação de risco. Por isso, não devem ser usadas como features no modelo preditivo principal:

```text
taxa_alfabetizacao
gap_meta_municipio_2030
gap_meta_uf_2030
atingiu_meta_uf
categoria_risco
```

Essas variáveis podem ser usadas na análise exploratória e em análises explicativas, mas serão removidas da matriz de features do modelo principal para evitar vazamento da resposta.

### Features Candidatas Iniciais

Features candidatas para o primeiro modelo sem leakage:

```text
ano
sigla_uf
serie
rede
media_portugues
meta_mun_2030
meta_uf_2030
meta_brasil_2030
proporcao_aluno_nivel_0
proporcao_aluno_nivel_1
proporcao_aluno_nivel_2
proporcao_aluno_nivel_3
```

As colunas `proporcao_aluno_nivel_*` possuem valores nulos em 2023 e serão avaliadas durante a EDA antes de entrar no modelo final.

Colunas sem variação na base atual, como `serie` e metas constantes, podem ser descartadas automaticamente na preparação da matriz de features.

---

## Estrutura do Projeto

```
TechChallenge_Fase3/
├── data/               # Dados Gold disponíveis para execução local
├── notebooks/          # Análises exploratórias e experimentos
├── src/
│   ├── preprocessing/  # Limpeza, encoding, scaling
│   ├── modeling/       # Treinamento dos modelos
│   ├── evaluation/     # Métricas e validação
│   └── visualization/  # Gráficos e visualizações
├── reports/            # Relatórios gerados
├── images/             # Imagens para documentação
├── requirements.txt
└── README.md
```

---

## Organização Do Código

A pasta `src/` concentra as funções reutilizáveis do projeto para reduzir dependência dos notebooks e facilitar a reprodução dos experimentos.

```text
src/
├── preprocessing/
│   └── features.py     # carga da Gold, target binário e matriz de features
├── modeling/
│   └── train.py        # ColumnTransformer, pipelines e modelos candidatos
├── evaluation/
│   └── metrics.py      # métricas de classificação e comparação de modelos
└── visualization/
    └── plots.py        # funções auxiliares para gráficos e salvamento de figuras
```

Exemplo de uso:

```python
from src.preprocessing import build_feature_matrix, load_indicator_municipio
from src.modeling import build_model_pipeline, get_candidate_models, split_train_test
from src.evaluation import evaluate_classifier

df = load_indicator_municipio()
X, y, info = build_feature_matrix(df)

X_train, X_test, y_train, y_test = split_train_test(X, y)
model = get_candidate_models()["logistic_regression"]
pipeline = build_model_pipeline(model, info["numeric_features"], info["categorical_features"])
pipeline.fit(X_train, y_train)

metrics = evaluate_classifier(pipeline, X_test, y_test)
```

Para executar o treino dos modelos candidatos e gerar os relatórios:

```bash
python -m src.modeling.run_training
```

Os resultados são salvos em:

```text
reports/model_results.md
reports/model_metrics_random.csv
reports/model_metrics_temporal.csv
reports/model_metrics.json
```

Para executar a etapa de interpretabilidade:

```bash
python -m src.evaluation.run_interpretability
```

Os resultados são salvos em:

```text
reports/interpretability.md
reports/logistic_coefficients.csv
reports/random_forest_feature_importance.csv
reports/permutation_importance_temporal.csv
images/model_permutation_importance_temporal.png
```

---

## Status

> EDA, modelagem inicial, avaliação e interpretabilidade concluídas. Relatórios executivos disponíveis em `reports/`.

---

## Resultados Principais

### EDA

- A base principal possui 23.995 registros e 18 colunas.
- A classe positiva (`meta_atingida`) representa 19,06% dos registros.
- A taxa média de alfabetização subiu de 60,71 em 2023 para 62,13 em 2024.
- O percentual de registros com meta atingida subiu de 17,93% em 2023 para 20,12% em 2024.
- As colunas `proporcao_aluno_nivel_*` possuem nulos concentrados em 2023.
- CE se destaca positivamente na base, com taxa média de 89,83 e 83,88% dos registros com meta atingida.

### Modelagem

Foram comparados quatro modelos:

- `DummyClassifier`
- `LogisticRegression`
- `RandomForestClassifier`
- `HistGradientBoostingClassifier`

Na validação aleatória estratificada, o melhor F1 foi do `HistGradientBoostingClassifier`:

```text
accuracy=0,9529 | precision=0,8740 | recall=0,8798 | f1=0,8769 | roc_auc=0,9876
```

Na validação temporal, treinando em 2023 e testando em 2024, o melhor F1 foi da `LogisticRegression`:

```text
accuracy=0,9153 | precision=0,7658 | recall=0,8343 | f1=0,7985 | roc_auc=0,9698
```

### Interpretabilidade

A variável mais importante foi `media_portugues`, seguida por `sigla_uf`. Isso sugere que o desempenho em língua portuguesa e o contexto territorial são os principais fatores associados ao cumprimento da meta na base analisada.

Como `media_portugues` é um indicador educacional do próprio ciclo observado, ela deve ser interpretada como variável contemporânea de diagnóstico. Para um modelo estritamente antecipatório, antes da avaliação anual, a próxima versão deve testar uma matriz sem essa variável e com enriquecimento socioeconômico/territorial externo.

---

## Relatórios

```text
reports/model_results.md
reports/interpretability.md
reports/technical_report.md
reports/executive_summary.md
reports/video_script.md
```

---

## Limitações

- A base está em nível agregado, não individual por aluno.
- Há apenas dois anos disponíveis, o que limita a validação temporal.
- A variável `rede` está codificada numericamente sem dicionário oficial no repositório.
- A modelagem identifica associações, não relações causais.
- Colunas derivadas diretamente da taxa de alfabetização e das metas foram excluídas do modelo principal por risco de data leakage.
- `media_portugues` pode não estar disponível em um cenário de previsão antes da avaliação; neste trabalho, ela é usada como indicador contemporâneo associado ao resultado.
