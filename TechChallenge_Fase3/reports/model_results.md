# Resultados De Modelagem - Fase 3

Gerado em: 2026-08-30 21:02:16

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

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| hist_gradient_boosting | 0.9529 | 0.8740 | 0.8798 | 0.8769 | 0.9876 |
| random_forest | 0.9314 | 0.7535 | 0.9519 | 0.8411 | 0.9836 |
| logistic_regression | 0.9212 | 0.7251 | 0.9454 | 0.8207 | 0.9820 |
| dummy_most_frequent | 0.8093 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |

Melhor modelo por F1 nesta validacao: `hist_gradient_boosting`.

## Validacao Temporal

Split: treino em 2023 e teste em 2024.

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| logistic_regression | 0.9153 | 0.7658 | 0.8343 | 0.7985 | 0.9698 |
| random_forest | 0.9083 | 0.7382 | 0.8435 | 0.7873 | 0.9646 |
| hist_gradient_boosting | 0.9179 | 0.8639 | 0.7025 | 0.7749 | 0.9679 |
| dummy_most_frequent | 0.7988 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |

Melhor modelo por F1 nesta validacao: `logistic_regression`.

## Leitura Inicial

O baseline `DummyClassifier` confirma que acuracia sozinha nao e suficiente: como a classe majoritaria representa cerca de 81% da base, um modelo que sempre prediz a classe 0 pode parecer razoavel em accuracy, mas tem recall e F1 iguais a zero para a classe de meta atingida.

Na proxima etapa, a comparacao deve priorizar F1, recall da classe positiva e estabilidade entre validacao aleatoria e temporal. Tambem sera necessario interpretar as variaveis mais relevantes para conectar o resultado com decisoes de politica publica.

Observacao importante: `media_portugues` e um indicador educacional do mesmo ciclo observado. Portanto, as metricas devem ser lidas como desempenho de uma solucao diagnostica com dados contemporaneos. Para uma predicao antecipada antes da avaliacao anual, sera necessario testar uma versao sem essa variavel e enriquecer o modelo com dados socioeconomicos e territoriais externos.

## Matrizes De Confusao

Formato: `[[TN, FP], [FN, TP]]`.

- `dummy_most_frequent`: `[[3884, 0], [915, 0]]`
- `logistic_regression`: `[[3556, 328], [50, 865]]`
- `random_forest`: `[[3599, 285], [44, 871]]`
- `hist_gradient_boosting`: `[[3768, 116], [110, 805]]`

## Matrizes De Confusao - Validacao Temporal

Formato: `[[TN, FP], [FN, TP]]`.

- `dummy_most_frequent`: `[[9944, 0], [2504, 0]]`
- `logistic_regression`: `[[9305, 639], [415, 2089]]`
- `random_forest`: `[[9195, 749], [392, 2112]]`
- `hist_gradient_boosting`: `[[9667, 277], [745, 1759]]`
