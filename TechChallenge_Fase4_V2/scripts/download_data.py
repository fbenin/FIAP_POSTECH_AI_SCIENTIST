"""
Baixa o Brazilian E-Commerce Public Dataset by Olist via Kaggle API.

Pré-requisitos:
  1. pip install kaggle
  2. Crie um token em https://www.kaggle.com/settings/account
     (botão "Create New Token" → baixa kaggle.json)
  3. Coloque o arquivo em ~/.kaggle/kaggle.json
     Linux/Mac:  mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
     Windows:    mova para C:\\Users\\<usuario>\\.kaggle\\kaggle.json

Uso:
  python scripts/download_data.py
"""

import subprocess
import sys
from pathlib import Path

DATASET = "olistbr/brazilian-ecommerce"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"

REQUIRED_FILES = [
    "olist_order_reviews_dataset.csv",
]
OPTIONAL_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
]


def check_kaggle():
    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("Erro: pacote 'kaggle' não instalado.")
        print("Execute: pip install kaggle")
        sys.exit(1)


def download():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    missing = [f for f in REQUIRED_FILES if not (OUTPUT_DIR / f).exists()]

    if not missing:
        print(f"Dataset já presente em {OUTPUT_DIR}")
        return

    print(f"Baixando dataset '{DATASET}' para {OUTPUT_DIR} ...")
    result = subprocess.run(
        [
            sys.executable, "-m", "kaggle",
            "datasets", "download",
            "-d", DATASET,
            "-p", str(OUTPUT_DIR),
            "--unzip",
        ],
        check=False,
    )

    if result.returncode != 0:
        print("\nFalha no download. Verifique:")
        print("  • ~/.kaggle/kaggle.json existe e tem permissão 600")
        print("    chmod 600 ~/.kaggle/kaggle.json")
        print("  • Token válido em https://www.kaggle.com/settings/account")
        sys.exit(result.returncode)

    csvs = list(OUTPUT_DIR.glob("*.csv"))
    print(f"\nDownload concluído. {len(csvs)} arquivo(s) em {OUTPUT_DIR}:")
    for f in sorted(csvs):
        size_mb = f.stat().st_size / 1_048_576
        print(f"  {f.name:55s} {size_mb:6.1f} MB")

    missing_req = [f for f in REQUIRED_FILES if not (OUTPUT_DIR / f).exists()]
    if missing_req:
        print(f"\nAviso: arquivo(s) obrigatório(s) não encontrado(s): {missing_req}")
        sys.exit(1)


if __name__ == "__main__":
    check_kaggle()
    download()
