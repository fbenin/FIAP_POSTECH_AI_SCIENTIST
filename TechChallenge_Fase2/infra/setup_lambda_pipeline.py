"""
Provisiona na AWS:
  1. IAM Role para a Lambda
  2. Empacota o código e sobe a Lambda function
  3. EventBridge rule (cron diário às 6h UTC)
  4. Permissão para o EventBridge invocar a Lambda

Pré-requisitos:
  - Credenciais AWS configuradas (env vars ou ~/.aws/credentials)
  - Dependências instaladas: boto3, python-dotenv, pandas, pyarrow
  - Rodar da raiz do projeto: python infra/setup_lambda_pipeline.py
"""

import io
import json
import logging
import os
import sys
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Configurações ─────────────────────────────────────────────────────────────
REGION        = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
BUCKET        = os.getenv("S3_BUCKET_NAME",     "tech-challenge-alfabetizacao-01")
LAMBDA_NAME   = "pipeline-alfabetizacao"
ROLE_NAME     = "lambda-pipeline-alfabetizacao-role"
RULE_NAME     = "pipeline-alfabetizacao-daily"
SCHEDULE      = "cron(0 6 * * ? *)"   # diário às 6h UTC
TIMEOUT       = 900                    # 15 min (máximo Lambda)
MEMORY        = 512                    # MB

ROOT = Path(__file__).parent.parent    # raiz do projeto

iam    = boto3.client("iam",    region_name=REGION)
lam    = boto3.client("lambda", region_name=REGION)
events = boto3.client("events", region_name=REGION)
sts    = boto3.client("sts",    region_name=REGION)


# ── 1. IAM Role ───────────────────────────────────────────────────────────────
def ensure_iam_role() -> str:
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    try:
        role = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Role para Lambda do pipeline de alfabetização"
        )
        arn = role["Role"]["Arn"]
        logger.info("IAM Role criada: %s", arn)
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
            logger.info("IAM Role já existe: %s", arn)
        else:
            raise

    # Políticas necessárias
    policies = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    ]
    for policy_arn in policies:
        try:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy_arn)
            logger.info("Policy anexada: %s", policy_arn)
        except ClientError as e:
            if "already" not in str(e).lower():
                raise

    logger.info("Aguardando propagação da IAM Role...")
    time.sleep(10)
    return arn


# ── 2. Zip do código ──────────────────────────────────────────────────────────
def build_zip() -> bytes:
    """Empacota handler + pipelines + quality em memória."""
    buffer = io.BytesIO()
    dirs_to_pack = [
        ROOT / "infra" / "lambda",
        ROOT / "pipelines",
        ROOT / "quality",
    ]
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for base_dir in dirs_to_pack:
            for path in sorted(base_dir.rglob("*.py")):
                if "__pycache__" in str(path):
                    continue
                arcname = path.relative_to(ROOT)
                zf.write(path, arcname)
                logger.info("  + %s", arcname)

    size_kb = buffer.tell() / 1024
    logger.info("ZIP gerado: %.1f KB", size_kb)
    buffer.seek(0)
    return buffer.read()


# ── 3. Lambda function ────────────────────────────────────────────────────────
def ensure_lambda(role_arn: str, zip_bytes: bytes) -> str:
    env_vars = {
        "S3_BUCKET_NAME":   BUCKET,
        "S3_RAW_PREFIX":    "raw",
        "S3_BRONZE_PREFIX": "bronze",
        "S3_SILVER_PREFIX": "silver",
        "S3_GOLD_PREFIX":   "gold",
        "USE_AWS":          "true",
    }
    try:
        resp = lam.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="infra/lambda/handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=TIMEOUT,
            MemorySize=MEMORY,
            Environment={"Variables": env_vars},
            Description="Pipeline diário: Bronze → Silver → Gold → Quality",
        )
        arn = resp["FunctionArn"]
        logger.info("Lambda criada: %s", arn)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            resp = lam.update_function_code(
                FunctionName=LAMBDA_NAME,
                ZipFile=zip_bytes,
            )
            lam.update_function_configuration(
                FunctionName=LAMBDA_NAME,
                Timeout=TIMEOUT,
                MemorySize=MEMORY,
                Environment={"Variables": env_vars},
            )
            arn = resp["FunctionArn"]
            logger.info("Lambda atualizada: %s", arn)
        else:
            raise

    # Aguarda a função ficar ativa
    waiter = lam.get_waiter("function_active_v2")
    waiter.wait(FunctionName=LAMBDA_NAME)
    return arn


# ── 4. EventBridge rule ───────────────────────────────────────────────────────
def ensure_eventbridge(lambda_arn: str):
    rule_resp = events.put_rule(
        Name=RULE_NAME,
        ScheduleExpression=SCHEDULE,
        State="ENABLED",
        Description="Dispara pipeline de alfabetização diariamente às 6h UTC",
    )
    rule_arn = rule_resp["RuleArn"]
    logger.info("EventBridge rule: %s → %s", RULE_NAME, SCHEDULE)

    events.put_targets(
        Rule=RULE_NAME,
        Targets=[{"Id": "lambda-pipeline", "Arn": lambda_arn}],
    )
    logger.info("Target adicionado: %s", lambda_arn)

    # Permissão para o EventBridge invocar a Lambda
    account_id = sts.get_caller_identity()["Account"]
    try:
        lam.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId="eventbridge-daily-trigger",
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_arn,
        )
        logger.info("Permissão EventBridge→Lambda adicionada")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            logger.info("Permissão já existe")
        else:
            raise


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    logger.info("=== Provisionando infraestrutura Lambda + EventBridge ===")
    logger.info("Bucket : %s | Região: %s", BUCKET, REGION)

    role_arn   = ensure_iam_role()
    zip_bytes  = build_zip()
    lambda_arn = ensure_lambda(role_arn, zip_bytes)
    ensure_eventbridge(lambda_arn)

    logger.info("=== Provisionamento concluído ===")
    logger.info("Lambda  : %s", lambda_arn)
    logger.info("Schedule: %s (diário às 6h UTC)", SCHEDULE)
    logger.info("")
    logger.info("Para invocar manualmente:")
    logger.info("  aws lambda invoke --function-name %s --payload '{}' /tmp/out.json && cat /tmp/out.json", LAMBDA_NAME)


if __name__ == "__main__":
    main()
