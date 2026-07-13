"""
Lambda handler — Pipeline Híbrido de Alfabetização
Orquestra: Bronze (raw→bronze) → Silver → Gold → Quality checks
Invocado diariamente pelo EventBridge.
"""

import json
import logging
import os
import sys
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda executa com /var/task como raiz — adiciona para imports relativos funcionarem
sys.path.insert(0, "/var/task")


def handler(event, context):
    bucket = os.environ.get("S3_BUCKET_NAME", "tech-challenge-alfabetizacao-01")
    os.environ.setdefault("S3_BUCKET_NAME",    bucket)
    os.environ.setdefault("S3_RAW_PREFIX",     "raw")
    os.environ.setdefault("S3_BRONZE_PREFIX",  "bronze")
    os.environ.setdefault("S3_SILVER_PREFIX",  "silver")
    os.environ.setdefault("S3_GOLD_PREFIX",    "gold")
    os.environ["USE_AWS"] = "true"

    results = {}

    # ── 1. Bronze ────────────────────────────────────────────────────────────
    try:
        logger.info("=== STEP 1/4: Bronze ===")
        from pipelines.batch.bronze.ingest_bronze import run as run_bronze
        results["bronze"] = run_bronze()
        logger.info("Bronze OK: %s", results["bronze"])
    except Exception:
        logger.error("Bronze FALHOU:\n%s", traceback.format_exc())
        return _response(500, "bronze", results)

    # ── 2. Silver ────────────────────────────────────────────────────────────
    try:
        logger.info("=== STEP 2/4: Silver ===")
        from pipelines.batch.silver.transform_silver import run as run_silver
        run_silver()
        results["silver"] = "ok"
        logger.info("Silver OK")
    except Exception:
        logger.error("Silver FALHOU:\n%s", traceback.format_exc())
        return _response(500, "silver", results)

    # ── 3. Gold ──────────────────────────────────────────────────────────────
    try:
        logger.info("=== STEP 3/4: Gold ===")
        from pipelines.batch.gold.build_gold import run as run_gold
        run_gold()
        results["gold"] = "ok"
        logger.info("Gold OK")
    except Exception:
        logger.error("Gold FALHOU:\n%s", traceback.format_exc())
        return _response(500, "gold", results)

    # ── 4. Quality checks ────────────────────────────────────────────────────
    try:
        logger.info("=== STEP 4/4: Quality ===")
        from quality.checks.quality_checks import run as run_quality
        passed = run_quality()
        results["quality"] = "passed" if passed else "warnings"
        logger.info("Quality: %s", results["quality"])
    except Exception:
        logger.error("Quality FALHOU:\n%s", traceback.format_exc())
        results["quality"] = "error"

    return _response(200, "completed", results)


def _response(status: int, step: str, results: dict) -> dict:
    body = {"step": step, "results": results}
    logger.info("Pipeline finalizado — status=%d body=%s", status, json.dumps(body))
    return {"statusCode": status, "body": json.dumps(body)}
