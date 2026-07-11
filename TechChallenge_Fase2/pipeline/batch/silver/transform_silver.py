"""
Silver Layer — Transformação e Integração
Lê dados brutos do S3 Bronze (ou local), limpa, normaliza e integra as bases.
Baseado nas colunas reais dos datasets INEP de avaliação de alfabetização.
"""

import os
import io
import logging
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import boto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET  = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao")
BRONZE     = os.getenv("S3_BRONZE_PREFIX", "bronze")
SILVER     = os.getenv("S3_SILVER_PREFIX", "silver")
USE_AWS    = os.getenv("USE_AWS", "false").lower() == "true"
LOCAL_B    = Path(__file__).parent.parent.parent.parent / "data" / "bronze"
LOCAL_S    = Path(__file__).parent.parent.parent.parent / "data" / "silver"
RUN_TS     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

s3 = boto3.client("s3") if USE_AWS else None

# Colunas de meta (trajetória 2024-2030)
META_TRAJECTORY_COLS = [
    "meta_alfabetizacao_2024", "meta_alfabetizacao_2025",
    "meta_alfabetizacao_2026", "meta_alfabetizacao_2027",
    "meta_alfabetizacao_2028", "meta_alfabetizacao_2029",
    "meta_alfabetizacao_2030",
]

# Mapa código IBGE UF → sigla
UF_MAP = {
    "11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP","17":"TO",
    "21":"MA","22":"PI","23":"CE","24":"RN","25":"PB","26":"PE","27":"AL",
    "28":"SE","29":"BA","31":"MG","32":"ES","33":"RJ","35":"SP","41":"PR",
    "42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF",
}


# ── S3 / local helpers ────────────────────────────────────────────────────────

def _read_s3_latest(prefix: str) -> pd.DataFrame:
    resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    objs = sorted(
        [o for o in resp.get("Contents", []) if o["Key"].endswith(".parquet")],
        key=lambda o: o["LastModified"], reverse=True,
    )
    if not objs:
        logger.warning("Nenhum arquivo em s3://%s/%s", S3_BUCKET, prefix)
        return pd.DataFrame()
    obj = s3.get_object(Bucket=S3_BUCKET, Key=objs[0]["Key"])
    return pd.read_parquet(io.BytesIO(obj["Body"].read()))


def _read_local(name: str) -> pd.DataFrame:
    path = LOCAL_B / f"{name}.parquet"
    if not path.exists():
        logger.error("Bronze local não encontrado: %s — execute ingest_bronze.py", path)
        return pd.DataFrame()
    return pd.read_parquet(path)


def read_bronze(name: str) -> pd.DataFrame:
    df = _read_s3_latest(f"{BRONZE}/{name}") if USE_AWS else _read_local(name)
    meta_cols = [c for c in df.columns if c.startswith("_")]
    return df.drop(columns=meta_cols)


def _upload_parquet(df: pd.DataFrame, key: str) -> None:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer.getvalue())
    logger.info("Salvo %d linhas → s3://%s/%s", len(df), S3_BUCKET, key)


def _save_local(df: pd.DataFrame, name: str, partition_cols=None) -> None:
    LOCAL_S.mkdir(parents=True, exist_ok=True)
    base = LOCAL_S / name
    base.mkdir(parents=True, exist_ok=True)
    if partition_cols and all(c in df.columns for c in partition_cols):
        for keys, grp in df.groupby(partition_cols):
            if not isinstance(keys, tuple):
                keys = (keys,)
            sub = base
            for col, val in zip(partition_cols, keys):
                sub = sub / f"{col}={val}"
            sub.mkdir(parents=True, exist_ok=True)
            grp.drop(columns=partition_cols, errors="ignore").to_parquet(
                sub / "data.parquet", index=False)
    else:
        df.to_parquet(base / "data.parquet", index=False)
    logger.info("Local silver/%s: %d linhas", name, len(df))


# ── Limpeza ────────────────────────────────────────────────────────────────────

def _lower_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    return df


def _to_numeric(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean_meta_brasil(df: pd.DataFrame) -> pd.DataFrame:
    df = _lower_cols(df)
    df = _to_numeric(df, ["ano", "taxa_alfabetizacao", "percentual_participacao"] + META_TRAJECTORY_COLS)
    df["ano"] = df["ano"].astype("Int64")
    df["rede"] = df["rede"].str.strip().str.title()
    df = df.drop_duplicates(subset=["ano", "rede"])
    logger.info("clean meta_brasil: %d linhas", len(df))
    return df


def clean_meta_uf(df: pd.DataFrame) -> pd.DataFrame:
    df = _lower_cols(df)
    df = _to_numeric(df, ["ano", "taxa_alfabetizacao", "percentual_participacao"] + META_TRAJECTORY_COLS)
    df["ano"] = df["ano"].astype("Int64")
    df["sigla_uf"] = df["sigla_uf"].str.strip().str.upper()
    df = df.drop_duplicates(subset=["ano", "sigla_uf", "rede"])
    df = df.dropna(subset=["sigla_uf"])
    logger.info("clean meta_uf: %d linhas", len(df))
    return df


def clean_meta_municipio(df: pd.DataFrame) -> pd.DataFrame:
    df = _lower_cols(df)
    df = _to_numeric(df, ["ano", "taxa_alfabetizacao", "percentual_participacao"] + META_TRAJECTORY_COLS)
    df["ano"] = df["ano"].astype("Int64")
    df["id_municipio"] = df["id_municipio"].astype(str).str.zfill(7)
    df = df.drop_duplicates(subset=["ano", "id_municipio", "rede"])
    df = df.dropna(subset=["id_municipio", "ano"])
    logger.info("clean meta_municipio: %d linhas", len(df))
    return df


def clean_indicador_uf(df: pd.DataFrame) -> pd.DataFrame:
    df = _lower_cols(df)
    num_cols = ["ano", "taxa_alfabetizacao", "media_portugues",
                "proporcao_aluno_nivel_0", "proporcao_aluno_nivel_1",
                "proporcao_aluno_nivel_2", "proporcao_aluno_nivel_3",
                "proporcao_aluno_nivel_4", "proporcao_aluno_nivel_5",
                "proporcao_aluno_nivel_6", "proporcao_aluno_nivel_7",
                "proporcao_aluno_nivel_8"]
    df = _to_numeric(df, num_cols)
    df["ano"] = df["ano"].astype("Int64")
    df["sigla_uf"] = df["sigla_uf"].str.strip().str.upper()
    df["serie"] = pd.to_numeric(df["serie"], errors="coerce").astype("Int64")
    df["rede"] = pd.to_numeric(df["rede"], errors="coerce").astype("Int64")
    mask = df["taxa_alfabetizacao"].isna() | df["taxa_alfabetizacao"].between(0, 100)
    df = df[mask].drop_duplicates(subset=["ano", "sigla_uf", "serie", "rede"])
    df = df.dropna(subset=["sigla_uf", "ano"])
    logger.info("clean indicador_uf: %d linhas", len(df))
    return df


def clean_indicador_municipio(df: pd.DataFrame) -> pd.DataFrame:
    df = _lower_cols(df)
    num_cols = ["ano", "taxa_alfabetizacao", "media_portugues",
                "proporcao_aluno_nivel_0", "proporcao_aluno_nivel_1",
                "proporcao_aluno_nivel_2", "proporcao_aluno_nivel_3",
                "proporcao_aluno_nivel_4", "proporcao_aluno_nivel_5",
                "proporcao_aluno_nivel_6", "proporcao_aluno_nivel_7",
                "proporcao_aluno_nivel_8"]
    df = _to_numeric(df, num_cols)
    df["ano"] = df["ano"].astype("Int64")
    df["id_municipio"] = df["id_municipio"].astype(str).str.zfill(7)
    df["serie"] = pd.to_numeric(df["serie"], errors="coerce").astype("Int64")
    df["rede"] = pd.to_numeric(df["rede"], errors="coerce").astype("Int64")
    mask = df["taxa_alfabetizacao"].isna() | df["taxa_alfabetizacao"].between(0, 100)
    df = df[mask].drop_duplicates(subset=["ano", "id_municipio", "serie", "rede"])
    df = df.dropna(subset=["id_municipio", "ano"])
    # Extrai sigla_uf do código do município
    df["sigla_uf"] = df["id_municipio"].str[:2].map(UF_MAP)
    logger.info("clean indicador_municipio: %d linhas", len(df))
    return df


# ── Integração ────────────────────────────────────────────────────────────────

def integrate_municipio(ind_mun, meta_mun, meta_uf_df, meta_brasil_df):
    df = ind_mun.copy()

    # Metas municipais — join por id_municipio + ano apenas
    # (coluna rede tem encoding diferente entre tabelas: numérico vs texto)
    meta_mun_cols = ["id_municipio", "ano"]
    if "meta_alfabetizacao_2030" in meta_mun.columns:
        meta_mun_cols.append("meta_alfabetizacao_2030")
    meta_mun_slim = (meta_mun[meta_mun_cols]
                     .drop_duplicates(subset=["id_municipio", "ano"])
                     .rename(columns={"meta_alfabetizacao_2030": "meta_mun_2030"}))
    df = df.merge(meta_mun_slim, on=["id_municipio", "ano"], how="left")

    # Metas estaduais — join por sigla_uf + ano
    if "meta_alfabetizacao_2030" in meta_uf_df.columns:
        meta_uf_slim = (meta_uf_df[["sigla_uf", "ano", "meta_alfabetizacao_2030"]]
                        .drop_duplicates(subset=["sigla_uf", "ano"])
                        .rename(columns={"meta_alfabetizacao_2030": "meta_uf_2030"}))
        df = df.merge(meta_uf_slim, on=["sigla_uf", "ano"], how="left")

    # Meta nacional — join por ano
    if "meta_alfabetizacao_2030" in meta_brasil_df.columns:
        meta_br_slim = (meta_brasil_df[["ano", "meta_alfabetizacao_2030"]]
                        .drop_duplicates(subset=["ano"])
                        .rename(columns={"meta_alfabetizacao_2030": "meta_brasil_2030"}))
        df = df.merge(meta_br_slim, on=["ano"], how="left")

    # Gaps
    if "taxa_alfabetizacao" in df.columns:
        if "meta_mun_2030" in df.columns:
            df["gap_meta_municipio_2030"] = (df["taxa_alfabetizacao"] - df["meta_mun_2030"]).round(2)
        if "meta_uf_2030" in df.columns:
            df["gap_meta_uf_2030"] = (df["taxa_alfabetizacao"] - df["meta_uf_2030"]).round(2)
            df["atingiu_meta_uf"] = df["gap_meta_uf_2030"] >= 0

    df["_data_processamento"] = RUN_TS
    return df


# ── Pipeline principal ────────────────────────────────────────────────────────

def run():
    logger.info("=== Iniciando transformação Silver ===")

    meta_brasil     = clean_meta_brasil(read_bronze("meta_brasil"))
    meta_uf         = clean_meta_uf(read_bronze("meta_uf"))
    meta_municipio  = clean_meta_municipio(read_bronze("meta_municipio"))
    indicador_uf    = clean_indicador_uf(read_bronze("indicador_uf"))
    indicador_mun   = clean_indicador_municipio(read_bronze("indicador_municipio"))

    if indicador_mun.empty:
        logger.error("indicador_municipio vazio — abortando Silver.")
        return

    silver_mun = integrate_municipio(indicador_mun, meta_municipio, meta_uf, meta_brasil)

    if USE_AWS:
        _upload_parquet(silver_mun,     f"{SILVER}/alfabetizacao_municipio/alfabetizacao_municipio.parquet")
        _upload_parquet(indicador_uf,   f"{SILVER}/indicador_uf/indicador_uf.parquet")
        _upload_parquet(meta_brasil,    f"{SILVER}/meta_brasil/meta_brasil.parquet")
        _upload_parquet(meta_uf,        f"{SILVER}/meta_uf/meta_uf.parquet")
        _upload_parquet(meta_municipio, f"{SILVER}/meta_municipio/meta_municipio.parquet")
    else:
        _save_local(silver_mun,    "alfabetizacao_municipio", ["sigla_uf", "ano"])
        _save_local(indicador_uf,  "alfabetizacao_uf",        ["sigla_uf", "ano"])
        _save_local(meta_brasil,   "meta_brasil")

    logger.info("=== Silver concluído: %d linhas integradas ===", len(silver_mun))
    return silver_mun


if __name__ == "__main__":
    run()
