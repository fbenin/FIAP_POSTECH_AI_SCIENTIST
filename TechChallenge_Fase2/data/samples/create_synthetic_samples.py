"""
Gera dados sintéticos compatíveis com o esquema INEP para testes locais.
Não requer BigQuery, S3 ou arquivos CSV reais.
"""

import random
from pathlib import Path
import pandas as pd

SAMPLES_DIR = Path(__file__).parent
random.seed(42)

UF_MAP = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

ANOS = [2021, 2022, 2023]
REDES = [1, 2, 3]
SERIES = [2]

def _mun_id(uf_code: str, i: int) -> str:
    return f"{uf_code}{str(i).zfill(5)}"


def make_meta_brasil():
    rows = []
    for ano in ANOS:
        for rede in ["Pública", "Municipal", "Estadual"]:
            rows.append({
                "ano": ano,
                "rede": rede,
                "taxa_alfabetizacao": round(random.uniform(50, 75), 1),
                "percentual_participacao": round(random.uniform(85, 98), 1),
                "meta_alfabetizacao_2024": 60.0,
                "meta_alfabetizacao_2025": 65.0,
                "meta_alfabetizacao_2026": 70.0,
                "meta_alfabetizacao_2027": 74.0,
                "meta_alfabetizacao_2028": 77.0,
                "meta_alfabetizacao_2029": 79.0,
                "meta_alfabetizacao_2030": 80.0,
            })
    df = pd.DataFrame(rows)
    df.to_parquet(SAMPLES_DIR / "meta_brasil.parquet", index=False)
    print(f"  meta_brasil.parquet: {len(df)} linhas")


def make_meta_uf():
    rows = []
    for uf_code, sigla in UF_MAP.items():
        for ano in ANOS:
            for rede in ["Pública", "Municipal"]:
                base = random.uniform(40, 72)
                rows.append({
                    "ano": ano,
                    "sigla_uf": sigla,
                    "rede": rede,
                    "taxa_alfabetizacao": round(base, 1),
                    "percentual_participacao": round(random.uniform(80, 98), 1),
                    "meta_alfabetizacao_2024": round(base + 5, 1),
                    "meta_alfabetizacao_2025": round(base + 8, 1),
                    "meta_alfabetizacao_2026": round(base + 11, 1),
                    "meta_alfabetizacao_2027": round(base + 13, 1),
                    "meta_alfabetizacao_2028": round(base + 15, 1),
                    "meta_alfabetizacao_2029": round(base + 17, 1),
                    "meta_alfabetizacao_2030": round(base + 20, 1),
                })
    df = pd.DataFrame(rows)
    df.to_parquet(SAMPLES_DIR / "meta_uf.parquet", index=False)
    print(f"  meta_uf.parquet: {len(df)} linhas")


def make_meta_municipio():
    rows = []
    for uf_code, sigla in UF_MAP.items():
        for i in range(1, 11):
            mun_id = _mun_id(uf_code, i)
            for ano in ANOS:
                base = random.uniform(35, 70)
                rows.append({
                    "ano": ano,
                    "id_municipio": mun_id,
                    "rede": "Pública",
                    "taxa_alfabetizacao": round(base, 1),
                    "percentual_participacao": round(random.uniform(75, 98), 1),
                    "meta_alfabetizacao_2024": round(base + 4, 1),
                    "meta_alfabetizacao_2025": round(base + 7, 1),
                    "meta_alfabetizacao_2026": round(base + 10, 1),
                    "meta_alfabetizacao_2027": round(base + 13, 1),
                    "meta_alfabetizacao_2028": round(base + 15, 1),
                    "meta_alfabetizacao_2029": round(base + 17, 1),
                    "meta_alfabetizacao_2030": round(base + 20, 1),
                })
    df = pd.DataFrame(rows)
    df.to_parquet(SAMPLES_DIR / "meta_municipio.parquet", index=False)
    print(f"  meta_municipio.parquet: {len(df)} linhas")


def make_indicador_uf():
    rows = []
    for uf_code, sigla in UF_MAP.items():
        for ano in ANOS:
            for serie in SERIES:
                for rede in REDES:
                    taxa = round(random.uniform(40, 80), 1)
                    rows.append({
                        "ano": ano,
                        "sigla_uf": sigla,
                        "serie": serie,
                        "rede": rede,
                        "taxa_alfabetizacao": taxa,
                        "media_portugues": round(random.uniform(600, 850), 1),
                        **{f"proporcao_aluno_nivel_{n}": round(random.uniform(0, 20), 1) for n in range(9)},
                    })
    df = pd.DataFrame(rows)
    df.to_parquet(SAMPLES_DIR / "indicador_uf.parquet", index=False)
    print(f"  indicador_uf.parquet: {len(df)} linhas")


def make_indicador_municipio():
    rows = []
    for uf_code, sigla in UF_MAP.items():
        for i in range(1, 11):
            mun_id = _mun_id(uf_code, i)
            for ano in ANOS:
                for serie in SERIES:
                    for rede in REDES:
                        taxa = round(random.uniform(30, 85), 1)
                        rows.append({
                            "ano": ano,
                            "id_municipio": mun_id,
                            "serie": serie,
                            "rede": rede,
                            "taxa_alfabetizacao": taxa,
                            "media_portugues": round(random.uniform(580, 860), 1),
                            **{f"proporcao_aluno_nivel_{n}": round(random.uniform(0, 20), 1) for n in range(9)},
                        })
    df = pd.DataFrame(rows)
    df.to_parquet(SAMPLES_DIR / "indicador_municipio.parquet", index=False)
    print(f"  indicador_municipio.parquet: {len(df)} linhas")


if __name__ == "__main__":
    print("Gerando amostras sintéticas INEP...")
    make_meta_brasil()
    make_meta_uf()
    make_meta_municipio()
    make_indicador_uf()
    make_indicador_municipio()
    print("Amostras geradas com sucesso.")
