"""
Quality Checks — Validações nas camadas Silver e Gold.
Executa assertions e retorna um relatório de qualidade.
Modo local (USE_AWS=false): lê de data/silver/ e data/gold/.
"""

import os
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import pandas as pd
import boto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "tech-challenge-alfabetizacao")
USE_AWS   = os.getenv("USE_AWS", "false").lower() == "true"
LOCAL_ROOT = Path(__file__).parent.parent / "data"

s3 = boto3.client("s3") if USE_AWS else None


@dataclass
class CheckResult:
    check: str
    passed: bool
    detail: str = ""


@dataclass
class QualityReport:
    layer: str
    table: str
    results: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def summary(self) -> str:
        total = len(self.results)
        ok = sum(1 for r in self.results if r.passed)
        status = "PASSED" if self.passed else "FAILED"
        return f"[{status}] {self.layer}/{self.table}: {ok}/{total} checks OK"


def read_parquet_from_s3(prefix: str) -> pd.DataFrame:
    resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    keys = [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".parquet")]
    if not keys:
        return pd.DataFrame()
    frames = []
    for key in keys[:10]:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        frames.append(pd.read_parquet(io.BytesIO(obj["Body"].read())))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def read_parquet_local(layer: str, table: str) -> pd.DataFrame:
    base = LOCAL_ROOT / layer / table
    if not base.exists():
        return pd.DataFrame()
    frames = []
    for p in base.rglob("*.parquet"):
        part = pd.read_parquet(p)
        # Reconstrói colunas de partição do path (e.g. sigla_uf=SP/ano=2023)
        for part_dir in p.parts:
            if "=" in part_dir:
                k, v = part_dir.split("=", 1)
                if k not in part.columns:
                    part[k] = v
        frames.append(part)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def read_table(layer: str, table: str) -> pd.DataFrame:
    if USE_AWS:
        return read_parquet_from_s3(f"{layer}/{table}/")
    return read_parquet_local(layer, table)


# ── Checks individuais ─────────────────────────────────────────────────────────

def check_not_empty(df: pd.DataFrame) -> CheckResult:
    passed = len(df) > 0
    return CheckResult("not_empty", passed, f"{len(df)} linhas")


def check_no_duplicates(df: pd.DataFrame, subset: List[str]) -> CheckResult:
    cols = [c for c in subset if c in df.columns]
    if not cols:
        return CheckResult(f"no_duplicates({subset})", False, "colunas não encontradas")
    dupes = df.duplicated(subset=cols).sum()
    return CheckResult(f"no_duplicates({cols})", dupes == 0, f"{dupes} duplicatas encontradas")


def check_no_nulls(df: pd.DataFrame, cols: List[str]) -> CheckResult:
    present = [c for c in cols if c in df.columns]
    if not present:
        return CheckResult(f"no_nulls({cols})", False, "colunas não encontradas")
    nulls = df[present].isnull().sum().sum()
    return CheckResult(f"no_nulls({present})", nulls == 0, f"{nulls} nulos encontrados")


def check_range(df: pd.DataFrame, col: str, lo: float, hi: float) -> CheckResult:
    if col not in df.columns:
        return CheckResult(f"range({col})", False, "coluna não encontrada")
    out = df[col].dropna()
    violations = ((out < lo) | (out > hi)).sum()
    return CheckResult(f"range({col} in [{lo},{hi}])", violations == 0,
                       f"{violations} valores fora do intervalo")


def check_referential_integrity(df: pd.DataFrame, fk_col: str, ref_values: set) -> CheckResult:
    if fk_col not in df.columns:
        return CheckResult(f"ref_integrity({fk_col})", False, "coluna não encontrada")
    orphans = (~df[fk_col].isin(ref_values)).sum()
    return CheckResult(f"ref_integrity({fk_col})", orphans == 0,
                       f"{orphans} valores sem referência")


# ── Suites de checks por tabela ────────────────────────────────────────────────

def check_silver_alfabetizacao() -> QualityReport:
    report = QualityReport("silver", "alfabetizacao_municipio")
    df = read_table("silver", "alfabetizacao_municipio")

    report.results.append(check_not_empty(df))
    if df.empty:
        return report

    # Chave real: município + ano + serie + rede (um município pode ter múltiplas redes/séries)
    report.results.append(check_no_duplicates(df, ["id_municipio", "ano", "serie", "rede"]))
    report.results.append(check_no_nulls(df, ["id_municipio", "ano"]))
    report.results.append(check_range(df, "taxa_alfabetizacao", 0, 100))

    if "sigla_uf" in df.columns:
        ufs = df["sigla_uf"].dropna().nunique()
        report.results.append(CheckResult("sigla_uf_not_empty", ufs >= 1,
                                          f"{ufs} UFs distintas"))
    return report


def check_gold_indicador_municipio() -> QualityReport:
    report = QualityReport("gold", "indicador_municipio")
    df = read_table("gold", "indicador_municipio")

    report.results.append(check_not_empty(df))
    if df.empty:
        return report

    # Chave real inclui serie e rede — um município tem múltiplas combinações
    report.results.append(check_no_duplicates(df, ["id_municipio", "ano", "serie", "rede"]))
    report.results.append(check_no_nulls(df, ["id_municipio", "ano"]))
    report.results.append(check_range(df, "taxa_alfabetizacao", 0, 100))

    if "gap_meta_uf_2030" in df.columns:
        report.results.append(CheckResult("gap_col_exists", True, "coluna gap_meta_uf_2030 presente"))
    if "atingiu_meta_uf" in df.columns:
        report.results.append(CheckResult("atingiu_meta_col_exists", True, "coluna atingiu_meta_uf presente"))
    return report


def check_gold_evolucao_temporal() -> QualityReport:
    report = QualityReport("gold", "evolucao_temporal_uf")
    df = read_table("gold", "evolucao_temporal_uf")

    report.results.append(check_not_empty(df))
    if df.empty:
        return report

    report.results.append(check_no_duplicates(df, ["ano", "sigla_uf"]))
    report.results.append(check_range(df, "media_taxa_alfabetizacao", 0, 100))
    return report


def check_gold_ranking_uf() -> QualityReport:
    report = QualityReport("gold", "ranking_uf")
    df = read_table("gold", "ranking_uf")

    report.results.append(check_not_empty(df))
    if df.empty:
        return report

    report.results.append(check_no_duplicates(df, ["sigla_uf"]))
    report.results.append(check_range(df, "media_taxa", 0, 100))
    return report


def check_gold_municipios_risco() -> QualityReport:
    report = QualityReport("gold", "municipios_risco")
    df = read_table("gold", "municipios_risco")

    report.results.append(check_not_empty(df))
    if df.empty:
        return report

    report.results.append(check_no_duplicates(df, ["id_municipio"]))
    report.results.append(check_no_nulls(df, ["id_municipio", "sigla_uf"]))
    return report


# ── Runner ─────────────────────────────────────────────────────────────────────

def run() -> bool:
    logger.info("=== Iniciando Quality Checks ===")
    suites = [
        check_silver_alfabetizacao,
        check_gold_indicador_municipio,
        check_gold_evolucao_temporal,
        check_gold_ranking_uf,
        check_gold_municipios_risco,
    ]

    all_passed = True
    for suite_fn in suites:
        report = suite_fn()
        logger.info(report.summary())
        for r in report.results:
            icon = "✓" if r.passed else "✗"
            logger.info("  %s %s — %s", icon, r.check, r.detail)
        if not report.passed:
            all_passed = False

    if all_passed:
        logger.info("=== Todos os checks PASSARAM ===")
    else:
        logger.error("=== FALHAS detectadas — verifique os logs acima ===")

    return all_passed


if __name__ == "__main__":
    import sys
    ok = run()
    sys.exit(0 if ok else 1)
