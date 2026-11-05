# Resumo Executivo - Tech Challenge Fase 3

## Visao Geral

Este projeto analisa indicadores de alfabetizacao infantil no Brasil e usa Machine Learning para identificar registros municipais com maior chance de atingir ou nao a meta educacional.

A solucao foi construida a partir da camada Gold da Fase 2, com dados agregados por municipio, ano, serie e rede de ensino.

## Problema

Gestores publicos precisam antecipar riscos educacionais e identificar territorios que exigem maior atencao. A alfabetizacao infantil e um indicador central para o desenvolvimento social, mas apenas observar os resultados atuais nao e suficiente para orientar decisoes futuras.

## Abordagem

O problema foi tratado como uma classificacao binaria:

```text
1 = meta de alfabetizacao atingida
0 = registro em risco ou abaixo da meta
```

Foram avaliados modelos de classificacao com validacao aleatoria e validacao temporal, treinando em 2023 e testando em 2024.

## Principais Achados

- A taxa media de alfabetizacao passou de 60,71 em 2023 para 62,13 em 2024.
- O percentual de registros com meta atingida passou de 17,93% para 20,12%.
- A classe positiva representa apenas 19,06% da base, exigindo cuidado com metricas alem da acuracia.
- CE aparece como destaque positivo, com taxa media de 89,83 e 83,88% dos registros com meta atingida.
- `media_portugues` foi a variavel mais importante para explicar as predicoes.
- `sigla_uf` mostra que o componente territorial tem papel relevante no risco educacional.

Esse achado deve ser lido com cautela: `media_portugues` e um indicador do mesmo ciclo observado, portanto funciona melhor como leitura diagnostica. Para antecipar risco antes da avaliacao anual, a proxima versao deve testar o modelo sem essa variavel e incorporar dados socioeconomicos externos.

## Resultado Dos Modelos

Na validacao aleatoria (80/20 aleatorio estratificado), o melhor modelo foi o `HistGradientBoostingClassifier`, com F1 de 0,8796 e PR-AUC de 0,9491.

Na validacao temporal (treino 2023, teste 2024), a `LogisticRegression` teve o melhor F1, com 0,7985, indicando melhor estabilidade para um ano nao visto.

**Por que o melhor modelo muda entre as validacoes?** A base contem registros de cada municipio tanto em 2023 quanto em 2024. No split aleatorio, o mesmo municipio aparece em treino e teste ao mesmo tempo, vazando suas caracteristicas estruturais para a avaliacao. Isso favorece modelos complexos como o HistGradient — que aprende padroes por municipio — e inflaciona as metricas. A validacao temporal e a referencia correta para estimar desempenho em anos futuros. O fato de o HistGradient cair mais que a LogisticRegression na transicao (de F1=0,8796 para 0,7707, vs. 0,8207 para 0,7985) sugere que o modelo complexo estava memorizando padroes especificos de municipio, enquanto o modelo linear aprendeu uma representacao mais generalizavel.

Para uso em producao — onde o objetivo e antecipar resultados de ciclos futuros — a `LogisticRegression` e a escolha mais robusta.

## Valor Para Gestores Publicos

A solucao pode apoiar:

- priorizacao de municipios em maior risco;
- planejamento de intervencoes pedagogicas;
- direcionamento de recursos;
- monitoramento das metas de alfabetizacao;
- construcao de dashboards de acompanhamento.

## Limitacoes

O modelo trabalha em nivel municipal/agregado, nao individual por aluno. Tambem ha apenas dois anos de dados, o que limita a leitura de tendencia futura, e a principal variavel explicativa pode nao estar disponivel antes da avaliacao anual. Por isso, a solucao deve ser interpretada como apoio analitico para decisao, nao como diagnostico definitivo.
