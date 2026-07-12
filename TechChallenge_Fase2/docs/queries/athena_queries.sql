-- Athena Queries — Consultas SQL prontas para a camada Gold.
-- Execute via AWS Console, boto3 ou qualquer cliente Athena.

-- 1. Top 10 municípios com maior índice de alfabetização (ano mais recente)
SELECT
    id_municipio,
    sigla_uf,
    ano,
    taxa_alfabetizacao,
    gap_meta_uf_2030
FROM gold_indicador_municipio
WHERE ano = (SELECT MAX(ano) FROM gold_indicador_municipio)
ORDER BY taxa_alfabetizacao DESC
LIMIT 10;

-- 2. Evolução temporal por UF
SELECT
    ano,
    sigla_uf,
    ROUND(AVG(taxa_alfabetizacao), 2) AS media_taxa,
    COUNT(DISTINCT id_municipio) AS total_municipios
FROM gold_indicador_municipio
GROUP BY ano, sigla_uf
ORDER BY sigla_uf, ano;

-- 3. Municípios abaixo da meta estadual
SELECT
    id_municipio,
    sigla_uf,
    ano,
    taxa_alfabetizacao,
    gap_meta_uf_2030,
    atingiu_meta_uf
FROM gold_indicador_municipio
WHERE atingiu_meta_uf = false
  AND ano = (SELECT MAX(ano) FROM gold_indicador_municipio)
ORDER BY gap_meta_uf_2030 ASC;

-- 4. Ranking de UFs no ano mais recente
SELECT
    sigla_uf,
    ano,
    ROUND(AVG(taxa_alfabetizacao), 2) AS media_taxa,
    COUNT(DISTINCT id_municipio) AS total_municipios
FROM gold_indicador_municipio
WHERE ano = (SELECT MAX(ano) FROM gold_indicador_municipio)
GROUP BY sigla_uf, ano
ORDER BY media_taxa DESC;

-- 5. Municípios com maior gap negativo em relação à meta
SELECT
    id_municipio,
    sigla_uf,
    ano,
    taxa_alfabetizacao,
    gap_meta_uf_2030,
    categoria_risco
FROM gold_indicador_municipio
WHERE gap_meta_uf_2030 IS NOT NULL
ORDER BY gap_meta_uf_2030 ASC
LIMIT 20;
