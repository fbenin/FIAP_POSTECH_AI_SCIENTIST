# Relatorio Tecnico - Tech Challenge Fase 3

## Contexto

O projeto busca aplicar tecnicas de analise exploratoria e Machine Learning ao contexto da alfabetizacao infantil no Brasil. A base utilizada vem da camada Gold construida na Fase 2, com informacoes agregadas por municipio, ano, serie e rede.

Embora o enunciado mencione predicao individual de aluno alfabetizado ou nao alfabetizado, os dados disponiveis nesta fase estao agregados. Por isso, o problema foi formulado como classificacao de risco/cumprimento de meta em nivel municipal/agregado.

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

### Validacao Aleatoria Estratificada

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| hist_gradient_boosting | 0,9529 | 0,8740 | 0,8798 | 0,8769 | 0,9876 |
| random_forest | 0,9314 | 0,7535 | 0,9519 | 0,8411 | 0,9836 |
| logistic_regression | 0,9212 | 0,7251 | 0,9454 | 0,8207 | 0,9820 |
| dummy_most_frequent | 0,8093 | 0,0000 | 0,0000 | 0,0000 | 0,5000 |

### Validacao Temporal

Treino em 2023 e teste em 2024.

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| logistic_regression | 0,9153 | 0,7658 | 0,8343 | 0,7985 | 0,9698 |
| random_forest | 0,9083 | 0,7382 | 0,8435 | 0,7873 | 0,9646 |
| hist_gradient_boosting | 0,9179 | 0,8639 | 0,7025 | 0,7749 | 0,9679 |
| dummy_most_frequent | 0,7988 | 0,0000 | 0,0000 | 0,0000 | 0,5000 |

## Interpretabilidade

A interpretabilidade foi analisada por:

- importancia por permutacao;
- coeficientes da regressao logistica;
- feature importance da Random Forest.

Principais fatores:

- `media_portugues`: variavel mais importante, associada diretamente ao desempenho educacional.
- `sigla_uf`: indica diferencas territoriais relevantes.
- `rede`: apresenta contribuicao menor no modelo atual e depende de dicionario oficial para interpretacao de negocio.
- `ano`: pouca importancia na validacao temporal, pois ha apenas dois anos na base.

Ponto de cautela: `media_portugues` e um indicador educacional do mesmo ciclo observado. Assim, ela fortalece a leitura diagnostica, mas pode nao estar disponivel em um cenario de previsao antecipada antes da avaliacao anual. Para uso preditivo ex-ante, recomenda-se testar uma versao sem essa variavel e enriquecer a base com indicadores socioeconomicos e territoriais externos.

## Aplicacao Em Politicas Publicas

O modelo pode apoiar gestores na priorizacao de municipios com maior risco de nao cumprimento das metas de alfabetizacao. A solucao pode ser usada para:

- identificar territorios vulneraveis;
- apoiar alocacao de recursos;
- orientar planos de intervencao pedagogica;
- monitorar evolucao anual das metas;
- complementar dashboards educacionais.

## Limitacoes

- A base nao esta em nivel individual de aluno.
- Ha apenas dois anos disponiveis.
- A interpretacao de `rede` depende de dicionario de dados.
- Os resultados indicam associacao, nao causalidade.
- Variaveis socioeconomicas externas ainda nao foram integradas.
- `media_portugues` pode representar informacao contemporanea ao resultado, nao necessariamente disponivel antes da avaliacao.

## Proximas Evolucoes

- Integrar dados externos do IBGE, PNAD, FUNDEB ou Atlas do Desenvolvimento Humano.
- Usar mais anos historicos para validacao temporal robusta.
- Criar dashboards para gestores.
- Avaliar calibracao das probabilidades.
- Aplicar SHAP em uma etapa posterior, caso a dependencia seja aprovada no projeto.
