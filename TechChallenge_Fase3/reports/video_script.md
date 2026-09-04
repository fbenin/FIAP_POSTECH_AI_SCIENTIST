# Roteiro Do Video Executivo - Ate 5 Minutos

## 0:00 - 0:30 | Abertura

Neste projeto, analisamos dados publicos de alfabetizacao infantil no Brasil para apoiar decisoes de gestores educacionais. O objetivo foi transformar a camada Gold criada na Fase 2 em uma solucao analitica e preditiva para identificar risco de nao cumprimento das metas de alfabetizacao.

## 0:30 - 1:10 | Problema

A alfabetizacao infantil e um dos indicadores mais importantes do desenvolvimento educacional. O desafio para gestores publicos nao e apenas saber quais municipios estao bem ou mal hoje, mas antecipar onde existe maior risco e quais fatores podem orientar a priorizacao de recursos.

## 1:10 - 1:50 | Base De Dados

Utilizamos a tabela `indicador_municipio` da camada Gold, com 23.995 registros e 18 colunas. A base esta agregada por municipio, ano, serie e rede. Por isso, formulamos o problema como uma classificacao de risco ou cumprimento de meta em nivel municipal, e nao como previsao individual por aluno.

## 1:50 - 2:30 | EDA

Na analise exploratoria, observamos que a taxa media de alfabetizacao subiu de 60,71 em 2023 para 62,13 em 2024. O percentual de registros com meta atingida tambem subiu, de 17,93% para 20,12%. Ainda assim, a maior parte dos registros segue abaixo da meta, o que reforca a importancia de identificar territorios prioritarios.

## 2:30 - 3:20 | Modelagem

Criamos uma pipeline com Scikit-learn, incluindo imputacao, padronizacao de variaveis numericas, encoding de variaveis categoricas e controle de data leakage. Removemos colunas derivadas diretamente da taxa ou da meta, como `taxa_alfabetizacao`, `gap_meta_uf_2030` e `categoria_risco`, para evitar metricas artificialmente altas.

Comparamos baseline, regressao logistica, Random Forest e HistGradientBoosting. No split aleatorio, o melhor F1 foi do HistGradientBoosting. Na validacao temporal, treinando em 2023 e testando em 2024, a regressao logistica teve melhor F1.

## 3:20 - 4:10 | Interpretabilidade

A variavel mais importante foi `media_portugues`, indicando que o desempenho medio em lingua portuguesa e fortemente associado ao cumprimento da meta. Mas existe uma ressalva importante: essa variavel pertence ao mesmo ciclo observado, entao ela deve ser vista como diagnostica. Para uma previsao antes da avaliacao anual, a proxima versao deve testar o modelo sem essa variavel e incluir dados socioeconomicos externos. A variavel `sigla_uf` tambem apareceu com relevancia, mostrando que o contexto territorial influencia bastante os resultados.

## 4:10 - 4:45 | Aplicacao Pratica

Na pratica, essa solucao pode apoiar gestores na identificacao de municipios com maior risco educacional, priorizacao de recursos, planejamento de intervencoes pedagogicas e acompanhamento anual das metas de alfabetizacao.

## 4:45 - 5:00 | Fechamento

Como proximos passos, recomendamos integrar variaveis socioeconomicas externas, ampliar a serie historica e criar dashboards para acompanhamento continuo. O principal valor do projeto e transformar dados publicos em inteligencia aplicada para politicas educacionais.
