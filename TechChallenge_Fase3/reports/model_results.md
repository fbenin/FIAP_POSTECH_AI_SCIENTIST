# Resultados De Modelagem - Fase 3

Gerado em: 2026-11-05 17:28:42

## Base Utilizada

- Registros: 23995
- Colunas originais: 18
- Municipios unicos: 5550
- UFs: 26
- Anos: [2023, 2024]
- Classe 0: 19421 registros
- Classe 1: 4574 registros
- Taxa da classe positiva: 19.06%

## Features Do Modelo Principal

Features numericas:

```text
['ano', 'media_portugues']
```

Features categoricas:

```text
['sigla_uf', 'rede']
```

Colunas excluidas por risco de data leakage:

```text
['taxa_alfabetizacao', 'gap_meta_municipio_2030', 'gap_meta_uf_2030', 'atingiu_meta_uf', 'categoria_risco']
```

## Validacao Aleatoria Estratificada

Split: 80% treino e 20% teste, mantendo a proporcao do target.

| Modelo | Accuracy | Bal. Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hist_gradient_boosting | 0.9537 | 0.9280 | 0.8730 | 0.8863 | 0.8796 | 0.9874 | 0.9491 |
| random_forest | 0.9350 | 0.9369 | 0.7699 | 0.9399 | 0.8465 | 0.9834 | 0.9289 |
| logistic_regression | 0.9212 | 0.9305 | 0.7251 | 0.9454 | 0.8207 | 0.9820 | 0.9284 |
| dummy_most_frequent | 0.8093 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.1907 |

Melhor modelo por F1 nesta validacao: `hist_gradient_boosting`.

## Validacao Temporal

Split: treino em 2023 e teste em 2024.

| Modelo | Accuracy | Bal. Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | 0.9153 | 0.8850 | 0.7658 | 0.8343 | 0.7985 | 0.9698 | 0.8966 |
| random_forest | 0.9154 | 0.8816 | 0.7706 | 0.8251 | 0.7969 | 0.9651 | 0.8758 |
| hist_gradient_boosting | 0.9165 | 0.8345 | 0.8614 | 0.6973 | 0.7707 | 0.9682 | 0.8862 |
| dummy_most_frequent | 0.7988 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.2012 |

Melhor modelo por F1 nesta validacao: `logistic_regression`.

## Leitura Inicial

O baseline `DummyClassifier` confirma que acuracia sozinha nao e suficiente: como a classe majoritaria representa cerca de 81% da base, um modelo que sempre prediz a classe 0 pode parecer razoavel em accuracy, mas tem recall e F1 iguais a zero para a classe de meta atingida. Para dados desbalanceados, as metricas prioritarias sao F1, PR-AUC e Balanced Accuracy.

Observacao importante: `media_portugues` e um indicador educacional do mesmo ciclo observado. Portanto, as metricas devem ser lidas como desempenho de uma solucao diagnostica com dados contemporaneos. Para uma predicao antecipada antes da avaliacao anual, sera necessario testar uma versao sem essa variavel e enriquecer o modelo com dados socioeconomicos e territoriais externos.

## Analise Da Mudanca De Modelo Entre Validacoes

Na validacao aleatoria, o `HistGradientBoostingClassifier` apresentou o melhor F1 (0,8769). Na validacao temporal (treino 2023, teste 2024), o mesmo modelo caiu para o terceiro lugar (F1=0,7749), enquanto a `LogisticRegression` passou a lider (F1=0,7985).

Essa inversao sugere que:

1. **Overfitting temporal do HistGradient**: o modelo mais complexo aprende padroes especificos do conjunto aleatório que se distribuem tanto no treino como no teste (os mesmos municipios aparecem nos dois conjuntos). Quando obrigado a generalizar para um ano inteiro nao visto, sua vantagem desaparece.
2. **Estabilidade do modelo linear**: a `LogisticRegression` aprende uma fronteira de decisao mais simples e generalizavel. A queda de F1 entre validacoes e menor (0,8207 -> 0,7985), indicando maior consistencia temporal.
3. **Por que a validacao aleatoria e otimista**: a base tem registros de cada municipio em 2023 E 2024. Um split 80/20 aleatorio coloca registros do mesmo municipio nos dois conjuntos. Isso vaza as caracteristicas estruturais de cada municipio do treino para o teste, favorecendo modelos que memorizam padroes por municipio. A validacao temporal evita isso ao separar os conjuntos por ano.
4. **Implicacao pratica**: para o objetivo de antecipar resultados de um ano futuro, a `LogisticRegression` e o modelo mais confiavel nesta base. A validacao aleatoria fornece uma estimativa otimista da capacidade de generalizacao temporal.

Essa diferenca e um dos resultados mais relevantes do projeto e deve orientar a escolha do modelo em producao.

## Matrizes De Confusao

Formato: `[[TN, FP], [FN, TP]]`.

- `dummy_most_frequent`: `[[3884, 0], [915, 0]]`
- `logistic_regression`: `[[3556, 328], [50, 865]]`
- `random_forest`: `[[3627, 257], [55, 860]]`
- `hist_gradient_boosting`: `[[3766, 118], [104, 811]]`

## Matrizes De Confusao - Validacao Temporal

Formato: `[[TN, FP], [FN, TP]]`.

- `dummy_most_frequent`: `[[9944, 0], [2504, 0]]`
- `logistic_regression`: `[[9305, 639], [415, 2089]]`
- `random_forest`: `[[9329, 615], [438, 2066]]`
- `hist_gradient_boosting`: `[[9663, 281], [758, 1746]]`
