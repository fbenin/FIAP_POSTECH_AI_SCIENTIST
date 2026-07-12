"""
Athena Queries — Consultas SQL prontas para a camada Gold.
Execute via AWS Console, boto3 ou qualquer cliente Athena.
"""

-- 1. Top 10 municípios com maior índice de alfabetização (ano mais recente)
SELECT
    id_municipio,
    nome_municipio,
    sigla_uf,
    ano,
    perc_alfabetizados,
    gap_meta_uf
FROM alfabetizacao_municipio
WHERE ano = (SELECT MAX(ano) FROM alfabetizacao_municipio)
ORDER BY perc_alfabetizados DESC
LIMIT 10;

-- 2. Evolução temporal por UF
SELECT
    ano,
    sigla_uf,
    nome_uf,
    ROUND(media_perc_alfabetizados, 2) AS media_perc,
    total_municipios
FROM evolucao_temporal
ORDER BY sigla_uf, ano;

-- 3. Municípios abaixo da meta estadual
SELECT
    id_municipio,
    nome_municipio,
    sigla_uf,
    ano,
    perc_alfabetizados,
    meta_uf,
    ROUND(gap_meta_uf, 2) AS gap
FROM alfabetizacao_municipio
WHERE atingiu_meta_uf = false
  AND ano = (SELECT MAX(ano) FROM alfabetizacao_municipio)
ORDER BY gap ASC;

-- 4. Ranking de UFs no ano mais recente
SELECT
    posicao,
    sigla_uf,
    nome_uf,
    ROUND(media_perc_alfabetizados, 2) AS media_perc
FROM ranking_uf
ORDER BY posicao;

-- 5. Municípios com maior gap negativo em relação à meta
SELECT
    nome_municipio,
    sigla_uf,
    ano,
    perc_alfabetizados,
    meta_municipio,
    ROUND(gap_meta_municipio, 2) AS gap_municipio
FROM alfabetizacao_municipio
WHERE gap_meta_municipio IS NOT NULL
ORDER BY gap_meta_municipio ASC
LIMIT 20;
