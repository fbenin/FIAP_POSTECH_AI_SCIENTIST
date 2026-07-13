-- Athena Queries — Consultas SQL prontas para a camada Gold.
-- Execute via AWS Console, boto3 ou qualquer cliente Athena.

-- 1. Top 10 municípios com maior índice de alfabetização (ano mais recente)
SELECT
    id_municipio,
    sigla_uf,
    ano,
    taxa_alfabetizacao,
    gap_meta_uf_2030,
    categoria_risco
FROM gold_indicador_municipio
WHERE ano = (SELECT MAX(ano) FROM gold_indicador_municipio)
ORDER BY taxa_alfabetizacao DESC
LIMIT 10;

-- 2. Evolução temporal por UF
SELECT
    ano,
    sigla_uf,
    ROUND(media_taxa_alfabetizacao, 2) AS media_taxa,
    ROUND(mediana_taxa_alfabetizacao, 2) AS mediana_taxa,
    total_municipios
FROM gold_evolucao_temporal_uf
ORDER BY sigla_uf, ano;

-- 3. Municípios abaixo da meta estadual
SELECT
    id_municipio,
    sigla_uf,
    ano,
    taxa_alfabetizacao,
    meta_uf_2030,
    gap_meta_uf_2030,
    atingiu_meta_uf
FROM gold_indicador_municipio
WHERE atingiu_meta_uf = false
  AND ano = (SELECT MAX(ano) FROM gold_indicador_municipio)
ORDER BY gap_meta_uf_2030 ASC;

-- 4. Ranking de UFs no ano mais recente
SELECT
    posicao,
    sigla_uf,
    ano,
    ROUND(media_taxa, 2) AS media_taxa,
    total_municipios,
    municipios_em_risco
FROM gold_ranking_uf
WHERE ano = (SELECT MAX(ano) FROM gold_ranking_uf)
ORDER BY posicao ASC;

-- 5. Municípios com maior gap negativo em relação à meta
SELECT
    id_municipio,
    sigla_uf,
    ano_referencia,
    taxa_alfabetizacao,
    gap_meta_uf_2030,
    meta_uf_2030
FROM gold_municipios_risco
ORDER BY gap_meta_uf_2030 ASC
LIMIT 20;
