# Relatorio Tecnico - Tech Challenge Fase 3

## Definicao Do Problema: Diagnostico Ou Predicao?

O projeto e apresentado como uma solucao de classificacao/diagnostico municipal, nao como predicao individual de alunos. Essa distincao e intencional:

- **Granularidade**: os dados disponiveis estao em nivel municipal/agregado, nao individual.
- **`media_portugues`**: e um indicador educacional do mesmo ciclo observado (mesmo ano da avaliacao). Portanto, ela fortalece a leitura diagnostica, mas nao estaria disponivel em um cenario de predicao antes da avaliacao anual.
- **Objetivo operacional**: o modelo pode identificar municipios com padrao de risco a partir de dados do ciclo atual, apoiando monitoramento e priorizacao de intervencoes.

Para um modelo genuinamente ex-ante (antes da avaliacao), seria necessario: (a) remover `media_portugues`, (b) enriquecer a base com indicadores socioeconomicos, territoriais e historicos de anos anteriores.

## Base De Dados

Tabela principal:

```text
data/gold/indicador_municipio/indicador_municipio.parquet
```

Dimensoes:

```text
23.995 registros
18 colunas
5.550 municipios
26 UFs
anos 2023 e 2024
```

## Variavel-Alvo

O target binario foi derivado de `categoria_risco`:

```text
1 = meta_atingida
0 = critico, alto ou moderado
```

Distribuicao:

```text
0 - em risco ou abaixo da meta: 19.421 registros (80,94%)
1 - meta atingida:              4.574 registros (19,06%)
```

## Controle De Data Leakage

As seguintes colunas foram removidas da matriz de features do modelo principal:

```text
taxa_alfabetizacao
gap_meta_municipio_2030
gap_meta_uf_2030
atingiu_meta_uf
categoria_risco
```

Essas variaveis sao derivadas diretamente da taxa de alfabetizacao, das metas ou da classificacao de risco. Usa-las no treino poderia inflar artificialmente as metricas.

## Features Do Modelo Principal

Features numericas:

```text
ano
media_portugues
```

Features categoricas:

```text
sigla_uf
rede
```

Colunas constantes, como `serie` e metas com valor unico na base atual, foram descartadas automaticamente.

> **Nota sobre `meta_mun_2030`**: esta coluna e uma candidata valida pois a meta 2030 e definida antecipadamente e seria conhecida antes da avaliacao anual. Entretanto, na base disponivel ela apresenta apenas 1 valor unico em toda a base (`nunique == 1`), sendo descartada automaticamente pelo filtro `drop_constant=True` em `get_feature_columns`. Em uma base com mais variacao nessa coluna, sua inclusao seria justificavel como informacao conhecida ex-ante.

## Pipeline

A pipeline foi implementada com Scikit-learn:

```text
dados Gold
-> criacao do target
-> selecao de features sem leakage
-> split de validacao
-> imputacao de nulos
-> padronizacao numerica
-> one-hot encoding categorico
-> modelo supervisionado
-> metricas
```

Modelos avaliados:

```text
DummyClassifier
LogisticRegression
RandomForestClassifier
HistGradientBoostingClassifier
```

## Resultados

> As tabelas completas com todas as metricas (inclusive `balanced_accuracy` e `pr_auc`) estao em `reports/model_results.md` (gerado automaticamente) e nos CSVs `model_metrics_random.csv` / `model_metrics_temporal.csv`.

### Validacao Aleatoria Estratificada

| Modelo | Bal. Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hist_gradient_boosting | 0.9280 | 0.8730 | 0.8863 | 0.8796 | 0.9874 | 0.9491 |
| random_forest | 0.9369 | 0.7699 | 0.9399 | 0.8465 | 0.9834 | 0.9289 |
| logistic_regression | 0.9305 | 0.7251 | 0.9454 | 0.8207 | 0.9820 | 0.9284 |
| dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.1907 |

### Validacao Temporal

Treino em 2023 e teste em 2024.

| Modelo | Bal. Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | 0.9176 | 0.7658 | 0.8343 | 0.7985 | 0.9698 | — |
| random_forest | 0.9102 | 0.7382 | 0.8435 | 0.7873 | 0.9646 | — |
| hist_gradient_boosting | 0.9045 | 0.8639 | 0.7025 | 0.7749 | 0.9679 | — |
| dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | — |

### Analise Da Mudanca De Modelo Entre Validacoes

O melhor modelo muda entre as duas estrategias de validacao: `HistGradientBoosting` lidera na validacao aleatoria (F1=0,8796) mas cai para terceiro na temporal (F1=0,7749), enquanto a `LogisticRegression` sobe de terceira para primeira (F1=0,7985).

A causa principal e estrutural: a base tem registros de cada municipio em 2023 E 2024. Um split 80/20 aleatorio coloca registros do mesmo municipio em treino e teste simultaneamente, vazando suas caracteristicas estruturais para o conjunto de avaliacao. Modelos mais complexos como HistGradient aprendem esses padroes por municipio e parecem generalizar bem — mas o que estao fazendo e memorizar. A validacao temporal evita esse vazamento ao separar conjuntos inteiramente por ano.

Para generalizacao para anos futuros, a `LogisticRegression` e a escolha mais robusta nesta base.

### Metricas Para Dados Desbalanceados

A classe positiva (`meta_atingida`) representa apenas 19,06% da base. ROC-AUC elevado pode ser enganoso em cenarios desbalanceados porque o eixo X usa FPR (falsos positivos sobre o total de negativos), que e dominado pela classe majoritaria. As metricas mais informativas sao F1, PR-AUC (Precision-Recall AUC) e Balanced Accuracy. O PR-AUC do `dummy` e apenas 0,19, confirmando que o modelo nulo nao tem utilidade diagnostica.

## Interpretabilidade

A interpretabilidade foi analisada por:

- importancia por permutacao;
- coeficientes da regressao logistica;
- feature importance da Random Forest.

Principais fatores:

- `media_portugues`: variavel de maior peso no modelo, associada ao desempenho educacional no mesmo ciclo.
- `sigla_uf`: indica diferencas territoriais relevantes entre estados.
- `rede`: contribuicao menor no modelo atual; requer dicionario oficial para interpretacao de negocio.
- `ano`: baixa importancia na validacao temporal, pois ha apenas dois anos na base.

**Cuidado na interpretacao**: importancia elevada de uma variavel no modelo nao implica causalidade. Por exemplo, o fato de `sigla_uf_RS` ter coeficiente positivo indica associacao entre ser do Rio Grande do Sul e atingir a meta nesta base — nao que a localizacao geografica cause esse resultado. Os fatores reais podem incluir diferencias historicas de investimento, politicas educacionais estaduais ou perfil socioeconomico da populacao. A interpretabilidade do modelo revela correlacoes nos dados observados, que devem ser validadas com especialistas antes de orientar politicas.

Ponto de cautela adicional: `media_portugues` e um indicador educacional do mesmo ciclo observado. Assim, ela fortalece a leitura diagnostica, mas pode nao estar disponivel em um cenario de previsao antecipada antes da avaliacao anual.

## Aplicacao Em Politicas Publicas

O modelo pode apoiar gestores na priorizacao de municipios com maior risco de nao cumprimento das metas de alfabetizacao. A solucao pode ser usada para:

- identificar territorios vulneraveis;
- apoiar alocacao de recursos;
- orientar planos de intervencao pedagogica;
- monitorar evolucao anual das metas;
- complementar dashboards educacionais.

## Limitacoes

- A base nao esta em nivel individual de aluno.
- Ha apenas dois anos disponiveis, limitando a validacao temporal a um unico periodo (2023->2024). Estrategias como `GroupKFold` agrupando por municipio ou por ano seriam mais robustas com mais ciclos historicos.
- A validacao aleatoria 80/20 coloca registros do mesmo municipio em treino e teste simultaneamente, porque cada municipio tem dados em 2023 e 2024. Isso introduce um vazamento estrutural das caracteristicas municipais que favorece modelos mais complexos e inflaciona as metricas em relacao ao cenario real de predicao para um ano novo.
- A interpretacao de `rede` depende de dicionario de dados.
- Os resultados indicam associacao estatistica, nao causalidade. Variaveis importantes no modelo podem refletir fatores confundidores nao observados (ex: investimento historico, nivel socioeconomico regional).
- Variaveis socioeconomicas externas ainda nao foram integradas.
- `media_portugues` e contemporanea ao ciclo avaliado, limitando o uso do modelo para predicao ex-ante.

## Proximas Evolucoes

- Integrar dados externos do IBGE, PNAD, FUNDEB ou Atlas do Desenvolvimento Humano.
- Usar mais anos historicos para validacao temporal robusta com multiplos periodos de teste.
- Aplicar `GroupKFold` agrupando por municipio para evitar que o mesmo municipio apareca em treino e teste simultaneamente.
- Criar dashboards para gestores.
- Avaliar calibracao das probabilidades (Platt scaling ou isotonic regression).
- Aplicar SHAP para interpretabilidade mais granular.
- Construir experimento sem `media_portugues` para avaliar capacidade de predicao genuinamente ex-ante.
