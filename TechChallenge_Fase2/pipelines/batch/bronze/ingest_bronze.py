"""
Bronze Layer — Batch Ingestion
Lê CSVs brutos de s3://<bucket>/raw/ e salva como Parquet em s3://<bucket>/bronze/.
"""

import io
import logging
import os
from datetime import datetime, timezone

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET     = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao-01")
S3_RAW_PREFIX = os.getenv("S3_RAW_PREFIX", "raw")
S3_PREFIX     = os.getenv("S3_BRONZE_PREFIX", "bronze")
RUN_TS        = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

s3 = boto3.client("s3")

RAW_FILES = {
    "meta_brasil"        : "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv",
    "meta_uf"            : "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv",
    "meta_municipio"     : "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_municipio.csv",
    "indicador_uf"       : "br_inep_avaliacao_alfabetizacao_uf.csv",
    "indicador_municipio": "br_inep_avaliacao_alfabetizacao_municipio.csv",
    "microdados_alunos"  : "microdados_alunos_saeb_2021_amostra.csv",
}


def read_raw(name: str) -> pd.DataFrame:
    s3_key = f"{S3_RAW_PREFIX}/{RAW_FILES[name]}"
    logger.info("Lendo s3://%s/%s", S3_BUCKET, s3_key)
    response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
    df = pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str)
    df["_fonte"]          = name
    df["_arquivo_origem"] = RAW_FILES[name]
    df["_data_ingestao"]  = RUN_TS
    logger.info("%-25s: %d linhas carregadas", name, len(df))
    return df


def upload_bronze(df: pd.DataFrame, name: str) -> None:
    s3_key = f"{S3_PREFIX}/{name}/run_ts={RUN_TS}/{name}.parquet"
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=buffer.getvalue())
    logger.info("Bronze salvo: s3://%s/%s (%d linhas)", S3_BUCKET, s3_key, len(df))


def run():
    logger.info("=== Iniciando ingestão Bronze — lendo de s3://%s/%s/ ===", S3_BUCKET, S3_RAW_PREFIX)
    results = {}
    for name in RAW_FILES:
        try:
            df = read_raw(name)
            upload_bronze(df, name)
            results[name] = len(df)
        except Exception as e:
            logger.error("Erro ao processar %s: %s", name, e)

    logger.info("=== Bronze concluído: %s ===", results)
    return results


if __name__ == "__main__":
    run()
