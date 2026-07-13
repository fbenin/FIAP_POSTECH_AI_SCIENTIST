"""
Bronze Layer — Batch Ingestion
Extrai dados da Base dos Dados e salva como Parquet no S3 (camada Bronze).
Modo local (USE_AWS=false): salva em data/bronze/ sem precisar de AWS.
"""

import os
import io
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import boto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET  = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao")
S3_PREFIX  = os.getenv("S3_BRONZE_PREFIX", "bronze")
USE_AWS    = os.getenv("USE_AWS", "false").lower() == "true"
LOCAL_B    = Path(__file__).parent.parent.parent.parent / "data" / "bronze"
RUN_TS     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

s3 = boto3.client("s3") if USE_AWS else None


def upload_parquet(df: pd.DataFrame, s3_key: str) -> None:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=buffer.getvalue())
    logger.info("Uploaded %d rows → s3://%s/%s", len(df), S3_BUCKET, s3_key)


def save_local(df: pd.DataFrame, name: str) -> None:
    LOCAL_B.mkdir(parents=True, exist_ok=True)
    path = LOCAL_B / f"{name}.parquet"
    df.to_parquet(path, index=False)
    logger.info("Local bronze/%s.parquet: %d linhas", name, len(df))


def ingest_indicador_municipio() -> pd.DataFrame:
    """
    Baixa o indicador Criança Alfabetizada por município via Base dos Dados.
    Requer billing project GCP configurado.
    """
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando indicador_municipio via basedosdados...")
        df = bd.read_table(
            dataset_id="br_inep_indicador_crianca_alfabetizada",
            table_id="municipio",
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando dados de amostra.", e)
        return _load_sample("indicador_municipio.parquet")


def ingest_municipio() -> pd.DataFrame:
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando tabela municipio...")
        df = bd.read_table(
            dataset_id="br_bd_diretorios_brasil",
            table_id="municipio",
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando dados de amostra.", e)
        return _load_sample("municipio.parquet")


def ingest_meta_brasil() -> pd.DataFrame:
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando meta_alfabetizacao_brasil...")
        df = bd.read_table(
            dataset_id="br_inep_indicador_crianca_alfabetizada",
            table_id="meta_brasil",
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando dados de amostra.", e)
        return _load_sample("meta_brasil.parquet")


def ingest_meta_uf() -> pd.DataFrame:
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando meta_alfabetizacao_uf...")
        df = bd.read_table(
            dataset_id="br_inep_indicador_crianca_alfabetizada",
            table_id="meta_uf",
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando dados de amostra.", e)
        return _load_sample("meta_uf.parquet")


def ingest_meta_municipio() -> pd.DataFrame:
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando meta_alfabetizacao_municipio...")
        df = bd.read_table(
            dataset_id="br_inep_indicador_crianca_alfabetizada",
            table_id="meta_municipio",
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando dados de amostra.", e)
        return _load_sample("meta_municipio.parquet")


def ingest_uf() -> pd.DataFrame:
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando tabela indicador_uf...")
        df = bd.read_table(
            dataset_id="br_inep_indicador_crianca_alfabetizada",
            table_id="uf",
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando dados de amostra.", e)
        return _load_sample("indicador_uf.parquet")


def ingest_microdados_alunos() -> pd.DataFrame:
    """
    Microdados SAEB 2021 — alunos do 2º ano EF (foco da alfabetização).
    Usa amostra pré-gerada por data/samples/download_saeb_sample.py.
    Contém proficiência individual em LP e MT, além de dados de escola e município.
    """
    try:
        import basedosdados as bd
        project = os.getenv("BASEDOSDADOS_PROJECT_ID")
        logger.info("Baixando microdados_alunos via basedosdados...")
        df = bd.read_sql(
            query="""
                SELECT * FROM `basedosdados.br_inep_saeb.aluno`
                WHERE ano = 2021 AND serie = 2
                ORDER BY RAND()
                LIMIT 10000
            """,
            billing_project_id=project,
        )
        return df
    except Exception as e:
        logger.warning("basedosdados indisponível (%s) — usando amostra SAEB local.", e)
        return _load_sample("microdados_alunos.parquet")


def _load_sample(filename: str) -> pd.DataFrame:
    path = os.path.join(os.path.dirname(__file__), "../../../data/samples", filename)
    if os.path.exists(path):
        return pd.read_parquet(path)
    logger.error("Arquivo de amostra não encontrado: %s", path)
    return pd.DataFrame()


SOURCES = {
    "indicador_municipio" : ingest_indicador_municipio,
    "indicador_uf"        : ingest_uf,
    "meta_brasil"         : ingest_meta_brasil,
    "meta_uf"             : ingest_meta_uf,
    "meta_municipio"      : ingest_meta_municipio,
    "microdados_alunos"   : ingest_microdados_alunos,
}


def run():
    logger.info("=== Iniciando ingestão Bronze (USE_AWS=%s) ===", USE_AWS)
    results = {}
    for name, fn in SOURCES.items():
        try:
            df = fn()
            if df.empty:
                logger.warning("DataFrame vazio para %s — pulando.", name)
                continue
            if USE_AWS:
                key = f"{S3_PREFIX}/{name}/run_ts={RUN_TS}/{name}.parquet"
                upload_parquet(df, key)
            else:
                save_local(df, name)
            results[name] = len(df)
        except Exception as e:
            logger.error("Erro ao ingerir %s: %s", name, e)

    logger.info("=== Bronze concluído: %s ===", results)
    return results


if __name__ == "__main__":
    run()
