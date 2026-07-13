"""
Gold Layer — Datasets Analíticos
Lê a camada Silver e gera tabelas prontas para consumo via Athena/BI.
Modo local (USE_AWS=false): lê de data/silver/ e salva em data/gold/.
"""

import os
import io
import logging
from pathlib import Path

import pandas as pd
import boto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao-01")
SILVER    = os.getenv("S3_SILVER_PREFIX", "silver")
GOLD      = os.getenv("S3_GOLD_PREFIX", "gold")
USE_AWS   = os.getenv("USE_AWS", "false").lower() == "true"
LOCAL_S   = Path(__file__).parent.parent.parent.parent / "data" / "silver"
LOCAL_G   = Path(__file__).parent.parent.parent.parent / "data" / "gold"

s3 = boto3.client("s3") if USE_AWS else None


# ── Leitura Silver ─────────────────────────────────────────────────────────────

def read_silver() -> pd.DataFrame:
    if USE_AWS:
        key = f"{SILVER}/alfabetizacao_municipio/alfabetizacao_municipio.parquet"
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            df = pd.read_parquet(io.BytesIO(obj["Body"].read()))
            logger.info("Silver carregado (S3): %d linhas", len(df))
            return df
        except Exception as e:
            logger.error("Erro ao ler Silver S3 (%s): %s", key, e)
            return pd.DataFrame()
    else:
        frames = []
        base = LOCAL_S / "alfabetizacao_municipio"
        if base.exists():
            for p in base.rglob("*.parquet"):
                part = pd.read_parquet(p)
                # Reconstrói colunas de partição a partir do path (sigla_uf=XX/ano=YYYY)
                for part_dir in p.parts:
                    if "=" in part_dir:
                        k, v = part_dir.split("=", 1)
                        if k not in part.columns:
                            part[k] = v
                frames.append(part)
        if not frames:
            logger.error("Silver local não encontrado em %s — execute transform_silver.py", base)
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        logger.info("Silver carregado (local): %d linhas", len(df))
        return df


# ── Upload/Save Gold ───────────────────────────────────────────────────────────

def upload_parquet(df: pd.DataFrame, name: str) -> None:
    if USE_AWS:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow")
        buffer.seek(0)
        key = f"{GOLD}/{name}/{name}.parquet"
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer.getvalue())
        logger.info("Gold → s3://%s/%s (%d linhas)", S3_BUCKET, key, len(df))
    else:
        out = LOCAL_G / name
        out.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out / f"{name}.parquet", index=False)
        logger.info("Gold local → data/gold/%s/%s.parquet (%d linhas)", name, name, len(df))


# ── Datasets Gold ──────────────────────────────────────────────────────────────

def build_indicador_municipio(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in [
        "id_municipio", "sigla_uf", "ano", "serie", "rede",
        "taxa_alfabetizacao", "media_portugues",
        "meta_mun_2030", "meta_uf_2030", "meta_brasil_2030",
        "gap_meta_municipio_2030", "gap_meta_uf_2030", "atingiu_meta_uf",
    ] if c in df.columns]
    gold = df[cols].copy()
    if "gap_meta_uf_2030" in gold.columns:
        gold["categoria_risco"] = pd.cut(
            pd.to_numeric(gold["gap_meta_uf_2030"], errors="coerce"),
            bins=[-float("inf"), -20, -10, 0, float("inf")],
            labels=["critico", "alto", "moderado", "meta_atingida"]
        ).astype(str)
    return gold


def build_evolucao_temporal(df: pd.DataFrame) -> pd.DataFrame:
    if not {"ano", "sigla_uf", "taxa_alfabetizacao"}.issubset(df.columns):
        return pd.DataFrame()
    df = df.copy()
    df["taxa_alfabetizacao"] = pd.to_numeric(df["taxa_alfabetizacao"], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    return (
        df.groupby(["ano", "sigla_uf"], dropna=False)
        .agg(
            media_taxa_alfabetizacao   = ("taxa_alfabetizacao", "mean"),
            mediana_taxa_alfabetizacao = ("taxa_alfabetizacao", "median"),
            total_municipios           = ("id_municipio",       "nunique"),
        )
        .reset_index()
        .round(2)
        .sort_values(["sigla_uf", "ano"])
    )


def build_ranking_uf(df: pd.DataFrame) -> pd.DataFrame:
    if not {"ano", "sigla_uf", "taxa_alfabetizacao"}.issubset(df.columns):
        return pd.DataFrame()
    df = df.copy()
    df["taxa_alfabetizacao"] = pd.to_numeric(df["taxa_alfabetizacao"], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    ano_max = df["ano"].max()
    ranking = (
        df[df["ano"] == ano_max]
        .groupby("sigla_uf", dropna=False)
        .agg(
            media_taxa       = ("taxa_alfabetizacao", "mean"),
            total_municipios = ("id_municipio",       "nunique"),
        )
        .reset_index()
        .round({"media_taxa": 2})
        .sort_values("media_taxa", ascending=False)
        .reset_index(drop=True)
    )
    ranking.index += 1
    ranking.index.name = "posicao"
    return ranking.reset_index()


def build_municipios_risco(df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    if "gap_meta_uf_2030" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    df["gap_meta_uf_2030"]    = pd.to_numeric(df["gap_meta_uf_2030"], errors="coerce")
    df["taxa_alfabetizacao"]  = pd.to_numeric(df["taxa_alfabetizacao"], errors="coerce")
    df["ano"]                 = pd.to_numeric(df["ano"], errors="coerce")
    ano_max = df["ano"].max()
    return (
        df[(df["ano"] == ano_max) & df["gap_meta_uf_2030"].notna()]
        .groupby(["id_municipio", "sigla_uf"], dropna=False)
        .agg(
            taxa_alfabetizacao = ("taxa_alfabetizacao", "mean"),
            meta_uf_2030       = ("meta_uf_2030",       "first"),
            gap_meta_uf_2030   = ("gap_meta_uf_2030",   "mean"),
        )
        .reset_index()
        .round(2)
        .sort_values("gap_meta_uf_2030")
        .head(top_n)
        .assign(ano_referencia=ano_max)
    )


def build_comparativo_nacional(df: pd.DataFrame) -> pd.DataFrame:
    if "taxa_alfabetizacao" not in df.columns or "ano" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    df["taxa_alfabetizacao"] = pd.to_numeric(df["taxa_alfabetizacao"], errors="coerce")
    df["ano"]                = pd.to_numeric(df["ano"], errors="coerce")
    df["meta_brasil_2030"]   = pd.to_numeric(df.get("meta_brasil_2030"), errors="coerce")
    return (
        df.groupby("ano")
        .agg(
            taxa_media_nacional  = ("taxa_alfabetizacao", "mean"),
            meta_brasil_2030     = ("meta_brasil_2030",   "first"),
            total_municipios     = ("id_municipio",       "nunique"),
        )
        .reset_index()
        .round(2)
        .sort_values("ano")
    )


# ── Leitura Silver microdados ──────────────────────────────────────────────────

def read_silver_microdados() -> pd.DataFrame:
    if USE_AWS:
        key = f"{SILVER}/microdados_alunos/microdados_alunos.parquet"
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            df = pd.read_parquet(io.BytesIO(obj["Body"].read()))
            logger.info("Silver microdados carregado (S3): %d alunos", len(df))
            return df
        except Exception as e:
            logger.warning("Silver microdados não encontrado (%s) — pulando.", e)
            return pd.DataFrame()
    else:
        frames = []
        base = LOCAL_S / "microdados_alunos"
        if base.exists():
            for p in base.rglob("*.parquet"):
                frames.append(pd.read_parquet(p))
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        logger.info("Silver microdados carregado (local): %d alunos", len(df))
        return df


def build_proficiencia_municipio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega proficiência individual por município.
    Permite comparar os microdados SAEB com o indicador oficial do INEP.
    """
    if df.empty or "id_municipio" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["proficiencia_lp_saeb"] = pd.to_numeric(df["proficiencia_lp_saeb"], errors="coerce")
    df["proficiencia_mt_saeb"] = pd.to_numeric(df["proficiencia_mt_saeb"], errors="coerce")
    df["alfabetizado"]         = df["alfabetizado"].astype(bool) if "alfabetizado" in df.columns else (df["proficiencia_lp_saeb"] >= 743)

    return (
        df.groupby("id_municipio")
        .agg(
            total_alunos            = ("id_aluno",            "count"),
            media_proficiencia_lp   = ("proficiencia_lp_saeb","mean"),
            media_proficiencia_mt   = ("proficiencia_mt_saeb","mean"),
            perc_alfabetizados      = ("alfabetizado",        "mean"),
        )
        .reset_index()
        .assign(perc_alfabetizados=lambda x: (x["perc_alfabetizados"] * 100).round(2))
        .round({"media_proficiencia_lp": 2, "media_proficiencia_mt": 2})
        .sort_values("perc_alfabetizados")
    )


# ── Pipeline ───────────────────────────────────────────────────────────────────

def run():
    logger.info("=== Iniciando construção Gold ===")
    df = read_silver()
    if df.empty:
        return

    microdados = read_silver_microdados()

    datasets = {
        "indicador_municipio"      : build_indicador_municipio(df),
        "evolucao_temporal_uf"     : build_evolucao_temporal(df),
        "ranking_uf"               : build_ranking_uf(df),
        "municipios_risco"         : build_municipios_risco(df),
        "comparativo_nacional"     : build_comparativo_nacional(df),
        "proficiencia_municipio"   : build_proficiencia_municipio(microdados),
    }

    for name, gold_df in datasets.items():
        if gold_df.empty:
            logger.warning("Dataset Gold '%s' vazio — pulando.", name)
            continue
        upload_parquet(gold_df, name)

    logger.info("=== Gold concluído: %d datasets ===", len(datasets))
    return datasets


if __name__ == "__main__":
    run()
