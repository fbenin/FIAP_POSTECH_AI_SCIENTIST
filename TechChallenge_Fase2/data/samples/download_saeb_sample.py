"""
Download de amostra aleatória dos microdados SAEB 2021 (2º ano EF).

Baixa diretamente do INEP sem precisar de GCP ou BigQuery:
  https://download.inep.gov.br/microdados/microdados_saeb_2021_ensino_fundamental_e_medio.zip

Extrai apenas DADOS/TS_ALUNO_2EF.csv (alunos do 2º ano — foco da alfabetização),
amostra N linhas aleatórias e salva em:
  - dadosINEP/microdados_alunos_saeb_2021_amostra.csv  (para o repo)
  - data/samples/microdados_alunos.parquet              (para o pipeline)

Execute:
  python data/samples/download_saeb_sample.py
  python data/samples/download_saeb_sample.py --n 5000
"""

import argparse
import io
import logging
import zipfile
from pathlib import Path

import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

URL_SAEB = "https://download.inep.gov.br/microdados/microdados_saeb_2021_ensino_fundamental_e_medio.zip"
CSV_DENTRO_ZIP = "DADOS/TS_ALUNO_2EF.csv"

ROOT = Path(__file__).parent.parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"
DADOS_INEP_DIR = ROOT / "dadosINEP"


def download_and_sample(n: int = 10000) -> pd.DataFrame:
    logger.info("Baixando microdados SAEB 2021 do INEP (~664 MB)...")
    logger.info("URL: %s", URL_SAEB)

    resp = requests.get(URL_SAEB, stream=True, verify=False, timeout=300)
    resp.raise_for_status()

    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    chunks = []
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        chunks.append(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded / total * 100
            if downloaded % (50 * 1024 * 1024) < 1024 * 1024:
                logger.info("  %.0f%% (%d MB de %d MB)", pct, downloaded // 1024 // 1024, total // 1024 // 1024)

    logger.info("Download concluído. Extraindo %s...", CSV_DENTRO_ZIP)
    zip_bytes = io.BytesIO(b"".join(chunks))

    with zipfile.ZipFile(zip_bytes) as z:
        with z.open(CSV_DENTRO_ZIP) as f:
            df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)

    logger.info("CSV extraído: %d linhas, %d colunas", len(df), len(df.columns))

    sample = df.sample(n=min(n, len(df)), random_state=42)
    logger.info("Amostra aleatória: %d linhas (seed=42)", len(sample))
    return sample


def save(df: pd.DataFrame) -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    DADOS_INEP_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = SAMPLES_DIR / "microdados_alunos.parquet"
    df.to_parquet(parquet_path, index=False)
    logger.info("Salvo: %s", parquet_path)

    csv_path = DADOS_INEP_DIR / "microdados_alunos_saeb_2021_amostra.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info("Salvo: %s (%d KB)", csv_path, csv_path.stat().st_size // 1024)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baixa amostra dos microdados SAEB 2021")
    parser.add_argument("--n", type=int, default=10000, help="Número de linhas (padrão: 10000)")
    args = parser.parse_args()

    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    df = download_and_sample(args.n)
    save(df)
    logger.info("Concluído. Colunas disponíveis: %s", list(df.columns[:10]))
