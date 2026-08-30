# Dados

Os dados **não são versionados** neste repositório. Baixe localmente via AWS CLI antes de rodar os notebooks.

## Pré-requisito

AWS CLI configurado com acesso ao bucket `tech-challenge-alfabetizacao-01`.

## Download

```bash
aws s3 sync s3://tech-challenge-alfabetizacao-01/gold/ data/gold/
```

## Estrutura esperada após o download

```
data/
└── gold/
    ├── comparativo_nacional/comparativo_nacional.parquet
    ├── evolucao_temporal_uf/evolucao_temporal_uf.parquet
    ├── indicador_municipio/indicador_municipio.parquet
    ├── municipios_risco/municipios_risco.parquet
    ├── proficiencia_municipio/proficiencia_municipio.parquet
    └── ranking_uf/ranking_uf.parquet
```

## Tabela principal

`indicador_municipio` — 23.995 linhas, 18 colunas. Base usada para modelagem.
