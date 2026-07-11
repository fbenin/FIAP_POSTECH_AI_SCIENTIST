"""
Streaming Consumer — Lê eventos da fila local e persiste no S3 Bronze/streaming.
Modo local (USE_AWS=false): persiste em data/bronze/streaming/ como Parquet.
"""

import os
import io
import json
import time
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import boto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET    = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao")
QUEUE_FILE   = "/tmp/streaming_queue.jsonl"
FLUSH_EVERY  = int(os.getenv("STREAMING_FLUSH_EVERY", "10"))
POLL_INTERVAL = int(os.getenv("STREAMING_POLL_INTERVAL", "3"))
USE_AWS      = os.getenv("USE_AWS", "false").lower() == "true"
LOCAL_STREAM = Path(__file__).parent.parent.parent / "data" / "bronze" / "streaming"

s3 = boto3.client("s3") if USE_AWS else None


def persist_batch(events: list) -> None:
    if not events:
        return
    df = pd.DataFrame([e["payload"] for e in events])
    df["event_id"]        = [e["event_id"] for e in events]
    df["event_type"]      = [e["event_type"] for e in events]
    df["event_timestamp"] = [e["timestamp"] for e in events]

    ts  = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    day = datetime.utcnow().strftime("%Y-%m-%d")

    if USE_AWS:
        key = f"bronze/streaming/dt={day}/batch_{ts}.parquet"
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow")
        buffer.seek(0)
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer.getvalue())
        logger.info("Batch de %d eventos → s3://%s/%s", len(events), S3_BUCKET, key)
    else:
        out = LOCAL_STREAM / f"dt={day}"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"batch_{ts}.parquet"
        df.to_parquet(path, index=False)
        logger.info("Batch de %d eventos → %s", len(events), path)


def run():
    logger.info("Consumer iniciado — monitorando %s", QUEUE_FILE)
    processed_lines = 0
    buffer = []

    while True:
        try:
            with open(QUEUE_FILE, "r") as f:
                lines = f.readlines()

            new_lines = lines[processed_lines:]
            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    buffer.append(event)
                    processed_lines += 1
                    logger.debug("Consumido: %s", event.get("event_id"))
                except json.JSONDecodeError:
                    logger.warning("Linha inválida ignorada: %s", line[:80])

            if len(buffer) >= FLUSH_EVERY:
                persist_batch(buffer)
                buffer.clear()

        except FileNotFoundError:
            logger.info("Aguardando fila em %s...", QUEUE_FILE)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
