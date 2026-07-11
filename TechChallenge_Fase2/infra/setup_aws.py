"""
Setup AWS — Cria bucket S3 com estrutura de prefixos e banco Glue/Athena.
Execute uma vez antes de rodar os pipelines.
"""

import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BUCKET = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao-01")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
GLUE_DB = os.getenv("GLUE_DATABASE", "alfabetizacao_db")
ATHENA_OUTPUT = os.getenv("ATHENA_OUTPUT_LOCATION", f"s3://{BUCKET}/athena-results/")

s3 = boto3.client("s3", region_name=REGION)
glue = boto3.client("glue", region_name=REGION)


def create_bucket():
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET)
        else:
            s3.create_bucket(
                Bucket=BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        logger.info("Bucket criado: s3://%s", BUCKET)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            logger.info("Bucket já existe: s3://%s", BUCKET)
        else:
            raise


def create_prefixes():
    prefixes = [
        "bronze/indicador_municipio/",
        "bronze/municipio/",
        "bronze/meta_brasil/",
        "bronze/meta_uf/",
        "bronze/meta_municipio/",
        "bronze/uf/",
        "bronze/streaming/",
        "silver/alfabetizacao/",
        "gold/alfabetizacao_municipio/",
        "gold/evolucao_temporal/",
        "gold/ranking_uf/",
        "athena-results/",
    ]
    for prefix in prefixes:
        s3.put_object(Bucket=BUCKET, Key=prefix)
    logger.info("Prefixos S3 criados.")


def set_lifecycle_policy():
    """Bronze → S3-IA após 90 dias (FinOps)."""
    policy = {
        "Rules": [
            {
                "ID": "bronze-to-ia",
                "Filter": {"Prefix": "bronze/"},
                "Status": "Enabled",
                "Transitions": [{"Days": 90, "StorageClass": "STANDARD_IA"}],
            }
        ]
    }
    s3.put_bucket_lifecycle_configuration(
        Bucket=BUCKET,
        LifecycleConfiguration=policy,
    )
    logger.info("Lifecycle policy aplicada: bronze/ → STANDARD_IA após 90 dias.")


def create_glue_database():
    try:
        glue.create_database(
            DatabaseInput={"Name": GLUE_DB, "Description": "Banco de dados de alfabetização — Tech Challenge Fase 2"}
        )
        logger.info("Glue database criado: %s", GLUE_DB)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            logger.info("Glue database já existe: %s", GLUE_DB)
        else:
            raise


def create_athena_workgroup():
    athena = boto3.client("athena", region_name=REGION)
    try:
        athena.create_work_group(
            Name="alfabetizacao",
            Configuration={
                "ResultConfiguration": {"OutputLocation": ATHENA_OUTPUT},
                "EnforceWorkGroupConfiguration": True,
                "PublishCloudWatchMetricsEnabled": True,
                "BytesScannedCutoffPerQuery": 1_073_741_824,  # 1 GB — FinOps guard
            },
            Description="Workgroup para queries de alfabetização",
        )
        logger.info("Athena workgroup criado: alfabetizacao")
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidRequestException":
            logger.info("Athena workgroup já existe.")
        else:
            raise


def run():
    logger.info("=== Setup AWS iniciado ===")
    create_bucket()
    create_prefixes()
    set_lifecycle_policy()
    create_glue_database()
    create_athena_workgroup()
    logger.info("=== Setup AWS concluído ===")
    logger.info("Próximos passos:")
    logger.info("  1. Configure credenciais: cp .env.example .env && edite .env")
    logger.info("  2. Execute: python pipelines/batch/bronze/ingest_bronze.py")


if __name__ == "__main__":
    run()
