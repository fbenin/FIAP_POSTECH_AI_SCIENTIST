"""
Gera dados de amostra a partir dos arquivos reais do INEP.
Esses arquivos são usados no pipeline local quando o S3 não está disponível.

Execute:
  python data/samples/generate_samples.py
"""

import os
import sys
from pathlib import Path

import pandas as pd

SAMPLES_DIR = Path(__file__).parent
INEP_DIR = Path(os.getenv(
    "INEP_DATA_DIR",
    str(Path.home() / "Desktop/FIAP - Ciências de Dados com IA/Tech Challenges/Fase 2/Dados INEP")
))

INEP_FILES = {
    "meta_brasil"        : "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv",
    "meta_uf"            : "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv",
    "meta_municipio"     : "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_municipio.csv",
    "indicador_uf"       : "br_inep_avaliacao_alfabetizacao_uf.csv",
    "indicador_municipio": "br_inep_avaliacao_alfabetizacao_municipio.csv",
}


def run():
    print(f"Lendo dados INEP de: {INEP_DIR}")
    missing = []

    for name, filename in INEP_FILES.items():
        src = INEP_DIR / filename
        out = SAMPLES_DIR / f"{name}.parquet"

        if not src.exists():
            print(f"  [AVISO] Arquivo não encontrado: {src}")
            missing.append(name)
            continue

        df = pd.read_csv(src, encoding="utf-8", dtype=str)
        df.to_parquet(out, index=False, engine="pyarrow")
        print(f"  Salvo: {out.name} ({len(df):,} linhas, {len(df.columns)} colunas)")

    if missing:
        print(f"\n[AVISO] {len(missing)} arquivo(s) INEP não encontrado(s): {missing}")
        print("  Verifique a variável INEP_DATA_DIR no .env")
        sys.exit(1)
    else:
        print("\nAmostras geradas com sucesso a partir dos dados reais INEP.")


if __name__ == "__main__":
    run()
