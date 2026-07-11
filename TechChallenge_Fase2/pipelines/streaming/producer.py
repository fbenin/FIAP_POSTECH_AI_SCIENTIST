"""
Streaming Producer — Simula eventos de atualização de indicadores.
Publica eventos JSON em um arquivo de fila local (ou substitua por Kinesis/SQS).
"""

import os
import json
import time
import random
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

QUEUE_FILE = "/tmp/streaming_queue.jsonl"
INTERVAL_SECONDS = int(os.getenv("STREAMING_INTERVAL", "2"))

UFS = ["SP", "RJ", "MG", "BA", "PR", "RS", "PE", "CE", "PA", "MA"]
EVENT_TYPES = ["indicador_atualizado", "meta_revisada", "medicao_desempenho"]


def generate_event() -> dict:
    return {
        "event_id": f"evt_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        "event_type": random.choice(EVENT_TYPES),
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "sigla_uf": random.choice(UFS),
            "id_municipio": str(random.randint(1000000, 9999999)),
            "ano": random.choice([2021, 2022, 2023]),
            "perc_alfabetizados": round(random.uniform(40, 99), 2),
            "fonte": "streaming_simulado",
        },
    }


def run(max_events: int = 100):
    logger.info("Producer iniciado — publicando eventos em %s", QUEUE_FILE)
    count = 0
    with open(QUEUE_FILE, "a") as f:
        while count < max_events:
            event = generate_event()
            f.write(json.dumps(event) + "\n")
            f.flush()
            logger.info("Publicado: %s | uf=%s perc=%.1f%%",
                        event["event_id"],
                        event["payload"]["sigla_uf"],
                        event["payload"]["perc_alfabetizados"])
            count += 1
            time.sleep(INTERVAL_SECONDS)
    logger.info("Producer encerrado após %d eventos.", count)


if __name__ == "__main__":
    run()
