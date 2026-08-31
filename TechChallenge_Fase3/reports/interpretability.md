# Interpretabilidade Dos Modelos - Fase 3

Gerado em: 2026-08-30 21:04:26

## Objetivo

Esta etapa busca entender quais variaveis mais influenciam a classificacao de risco/cumprimento de meta em nivel municipal/agregado.

## Importancia Por Permutacao

A importancia por permutacao foi calculada sobre a validacao temporal, usando o modelo de regressao logistica e a metrica F1. Essa leitura mede quanto o desempenho cai quando uma variavel e embaralhada.

| Feature | Importancia media | Desvio |
|---|---:|---:|
| media_portugues | 0.6085 | 0.0047 |
| sigla_uf | 0.0318 | 0.0042 |
| rede | 0.0005 | 0.0007 |
| ano | 0.0000 | 0.0000 |

## Coeficientes Da Regressao Logistica

Os coeficientes indicam a direcao da associacao depois do preprocessamento. Valores positivos aumentam a probabilidade estimada de meta atingida; valores negativos reduzem essa probabilidade.

| Feature | Coeficiente | Peso absoluto |
|---|---:|---:|
| media_portugues | 7.0317 | 7.0317 |
| sigla_uf_RS | 2.9399 | 2.9399 |
| sigla_uf_CE | -2.7795 | 2.7795 |
| sigla_uf_PR | 2.5973 | 2.5973 |
| sigla_uf_SC | 2.4091 | 2.4091 |
| sigla_uf_MS | -2.4073 | 2.4073 |
| sigla_uf_GO | 1.7347 | 1.7347 |
| sigla_uf_RO | -1.6151 | 1.6151 |

## Importancia Da Random Forest

A Random Forest ajuda a enxergar variaveis relevantes por reducao de impureza nas arvores.

| Feature | Importancia |
|---|---:|
| media_portugues | 0.8441 |
| sigla_uf_CE | 0.0329 |
| sigla_uf_BA | 0.0261 |
| ano | 0.0136 |
| sigla_uf_RN | 0.0109 |

## Leitura Executiva

- `media_portugues` aparece como a variavel mais forte do modelo, o que e coerente com o problema: melhor desempenho em lingua portuguesa esta associado a maior chance de cumprimento da meta.
- `sigla_uf` tambem aparece com peso relevante, indicando que fatores territoriais e contextuais diferenciam bastante os municipios.
- `rede` contribui para a classificacao, mas deve ser interpretada com cuidado porque a base usa codigos numericos sem dicionario oficial no repositorio.
- `ano` ajuda a capturar a diferenca entre 2023 e 2024, mas nao substitui uma serie historica mais longa.

Como `media_portugues` pertence ao ciclo educacional analisado, ela deve ser usada com cautela em narrativas preditivas. O resultado mostra forte associacao diagnostica; para antecipacao operacional antes da avaliacao, a recomendacao e criar um experimento sem essa variavel.

## Cuidados De Interpretacao

- A interpretabilidade confirma associacoes no nivel agregado da base, nao causalidade individual.
- As colunas diretamente derivadas da taxa de alfabetizacao e das metas foram excluidas do modelo principal para evitar data leakage.
- `media_portugues` pode nao estar disponivel antes da avaliacao anual, entao nao deve ser vendida como variavel plenamente ex-ante.
- Como ha apenas dois anos disponiveis, a validacao temporal e util, mas ainda limitada para afirmar estabilidade futura.
