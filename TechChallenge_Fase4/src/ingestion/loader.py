"""Load Olist dataset files for the RAG knowledge base.

Expected structure inside data_dir:
    olist_order_reviews_dataset.csv
    olist_orders_dataset.csv        (optional, for metadata enrichment)
    olist_order_items_dataset.csv   (optional, for product categories)
    olist_products_dataset.csv      (optional, for product names)
    product_category_name_translation.csv  (optional, for English labels)

Download from: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_reviews(data_dir: str | Path) -> pd.DataFrame:
    """Load the raw order reviews dataset.

    Returns a DataFrame with all review columns, preserving original dtypes.
    Parses review_creation_date and review_answer_timestamp as datetime.
    """
    path = Path(data_dir) / "olist_order_reviews_dataset.csv"
    df = pd.read_csv(
        path,
        parse_dates=["review_creation_date", "review_answer_timestamp"],
    )
    return df


def load_orders(data_dir: str | Path) -> pd.DataFrame:
    """Load the orders dataset for metadata enrichment (delivery, timing)."""
    path = Path(data_dir) / "olist_orders_dataset.csv"
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    return pd.read_csv(path, parse_dates=date_cols)


def load_products(data_dir: str | Path) -> pd.DataFrame:
    """Load products and category translations."""
    products_path = Path(data_dir) / "olist_products_dataset.csv"
    translation_path = Path(data_dir) / "product_category_name_translation.csv"

    products = pd.read_csv(products_path)

    if translation_path.exists():
        translation = pd.read_csv(translation_path)
        products = products.merge(translation, on="product_category_name", how="left")

    return products


def load_order_items(data_dir: str | Path) -> pd.DataFrame:
    """Load order items for linking orders to product categories."""
    path = Path(data_dir) / "olist_order_items_dataset.csv"
    return pd.read_csv(path, parse_dates=["shipping_limit_date"])


def load_enriched_reviews(data_dir: str | Path) -> pd.DataFrame:
    """Load reviews joined with order and product metadata.

    Adds:
        - order_status, purchase month/year from orders
        - actual vs estimated delivery delta (days late or early)
        - product_category_name_english (first product in order)

    Falls back gracefully if optional CSVs are missing.
    """
    data_dir = Path(data_dir)
    reviews = load_reviews(data_dir)

    try:
        orders = load_orders(data_dir)
        delivery_delta = (
            orders["order_delivered_customer_date"]
            - orders["order_estimated_delivery_date"]
        ).dt.days
        orders = orders.assign(
            delivery_delta_days=delivery_delta,
            purchase_year=orders["order_purchase_timestamp"].dt.year,
            purchase_month=orders["order_purchase_timestamp"].dt.month,
        )
        keep_cols = [
            "order_id",
            "order_status",
            "purchase_year",
            "purchase_month",
            "delivery_delta_days",
        ]
        reviews = reviews.merge(orders[keep_cols], on="order_id", how="left")
    except FileNotFoundError:
        pass

    try:
        items = load_order_items(data_dir)
        products = load_products(data_dir)

        first_item = items.drop_duplicates("order_id")[["order_id", "product_id"]]
        item_category = first_item.merge(
            products[["product_id", "product_category_name_english"]],
            on="product_id",
            how="left",
        )
        reviews = reviews.merge(
            item_category[["order_id", "product_category_name_english"]],
            on="order_id",
            how="left",
        )
    except (FileNotFoundError, KeyError):
        pass

    return reviews
