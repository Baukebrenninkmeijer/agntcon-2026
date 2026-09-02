"""Lazy Polars generation and DuckDB materialization for demo business data."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

import duckdb
import polars as pl
from pydantic import BaseModel

DATASET_START = date(2024, 1, 1)
DATASET_END = date(2025, 12, 31)
DEFAULT_ORDER_COUNT = 25_000
DEFAULT_SEED = 2026

REGIONS: dict[str, tuple[str, ...]] = {
    "EMEA": ("Netherlands", "Germany", "France", "United Kingdom"),
    "North America": ("United States", "Canada"),
    "APAC": ("Japan", "Australia", "Singapore", "India"),
    "LATAM": ("Brazil", "Mexico", "Argentina", "Chile"),
}

PRODUCTS: dict[str, tuple[tuple[str, int], ...]] = {
    "Software": (("Analytics Pro", 49_900), ("Automation Suite", 79_900)),
    "Hardware": (("Edge Appliance", 149_900), ("Sensor Kit", 39_900)),
    "Services": (("Implementation", 249_900), ("Training", 89_900)),
    "Data": (("Market Feed", 29_900), ("Risk Dataset", 59_900)),
}

SEGMENTS = ("SMB", "Mid-Market", "Enterprise")


class DatasetManifest(BaseModel):
    schema_version: str
    seed: int
    row_count: int
    min_order_date: date
    max_order_date: date
    month_count: int
    content_hash: str


def _status(rng: random.Random) -> str:
    draw = rng.random()
    if draw < 0.82:
        return "completed"
    if draw < 0.90:
        return "refunded"
    if draw < 0.95:
        return "cancelled"
    return "pending"


def generate_orders(
    count: int = DEFAULT_ORDER_COUNT,
    seed: int = DEFAULT_SEED,
) -> pl.LazyFrame:
    """Build deterministic base columns and derive financials in a lazy Polars plan."""

    if count < 2:
        raise ValueError("count must be at least 2 so the dataset covers both date bounds")

    rng = random.Random(seed)
    regions = tuple(REGIONS)
    categories = tuple(PRODUCTS)
    day_count = (DATASET_END - DATASET_START).days
    columns: dict[str, list[object]] = {
        "order_id": [],
        "customer_id": [],
        "order_date": [],
        "order_month": [],
        "region": [],
        "country": [],
        "product": [],
        "product_category": [],
        "customer_segment": [],
        "quantity": [],
        "unit_price_cents": [],
        "discount_basis_points": [],
        "order_status": [],
        "refund_basis_points": [],
        "cost_basis_points": [],
    }

    for index in range(count):
        if index == 0:
            order_date = DATASET_START
        elif index == 1:
            order_date = DATASET_END
        else:
            order_date = DATASET_START + timedelta(days=rng.randint(0, day_count))

        region = rng.choice(regions)
        country = rng.choice(REGIONS[region])
        category = rng.choice(categories)
        product, base_price_cents = rng.choice(PRODUCTS[category])
        segment = rng.choice(SEGMENTS)
        quantity = rng.randint(1, 12 if segment == "Enterprise" else 6)
        unit_price_cents = base_price_cents * rng.randint(8_500, 11_500) // 10_000
        status = _status(rng)
        values = {
            "order_id": f"ORD-{index + 1:07d}",
            "customer_id": f"CUS-{rng.randint(1, 4_000):05d}",
            "order_date": order_date,
            "order_month": order_date.replace(day=1),
            "region": region,
            "country": country,
            "product": product,
            "product_category": category,
            "customer_segment": segment,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "discount_basis_points": rng.choice((0, 0, 0, 500, 1_000, 1_500, 2_000)),
            "order_status": status,
            "refund_basis_points": rng.randint(2_500, 10_000) if status == "refunded" else 0,
            "cost_basis_points": {
                "Software": 2_000,
                "Hardware": 6_500,
                "Services": 4_500,
                "Data": 2_500,
            }[category],
        }
        for name, value in values.items():
            columns[name].append(value)

    gross = pl.col("quantity") * pl.col("unit_price_cents")
    discounted = gross * (10_000 - pl.col("discount_basis_points")) // 10_000
    refund = discounted * pl.col("refund_basis_points") // 10_000
    net = (
        pl.when(pl.col("order_status").is_in(["cancelled", "pending"]))
        .then(pl.lit(0))
        .otherwise(discounted - refund)
    )
    return (
        pl.DataFrame(columns, strict=False)
        .lazy()
        .with_columns(
            gross.alias("gross_revenue_cents"),
            net.alias("net_revenue_cents"),
            (gross * pl.col("cost_basis_points") // 10_000).alias("cost_cents"),
            refund.alias("refund_amount_cents"),
        )
        .drop("refund_basis_points", "cost_basis_points")
    )


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_database(
    path: Path,
    count: int = DEFAULT_ORDER_COUNT,
    seed: int = DEFAULT_SEED,
) -> DatasetManifest:
    """Stream generated data to Parquet, then atomically materialize DuckDB."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_parquet = path.with_suffix(path.suffix + ".source.parquet.tmp")
    temporary_manifest = path.with_suffix(path.suffix + ".manifest.json.tmp")
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    for temporary in (temporary_path, temporary_parquet, temporary_manifest):
        temporary.unlink(missing_ok=True)

    generate_orders(count=count, seed=seed).sink_parquet(temporary_parquet, engine="streaming")
    content_hash = _file_hash(temporary_parquet)

    connection = duckdb.connect(str(temporary_path))
    try:
        connection.execute(
            """
            CREATE TABLE orders AS
            SELECT
                order_id,
                customer_id,
                order_date,
                order_month,
                region,
                country,
                product,
                product_category,
                customer_segment,
                quantity,
                CAST(unit_price_cents / 100.0 AS DECIMAL(14, 2)) AS unit_price,
                CAST(discount_basis_points / 10000.0 AS DECIMAL(6, 4)) AS discount_rate,
                CAST(gross_revenue_cents / 100.0 AS DECIMAL(16, 2)) AS gross_revenue,
                CAST(net_revenue_cents / 100.0 AS DECIMAL(16, 2)) AS net_revenue,
                CAST(cost_cents / 100.0 AS DECIMAL(16, 2)) AS cost,
                order_status,
                CAST(refund_amount_cents / 100.0 AS DECIMAL(16, 2)) AS refund_amount
            FROM read_parquet(?)
            """,
            [str(temporary_parquet)],
        )
        connection.execute("ALTER TABLE orders ADD PRIMARY KEY (order_id)")
        connection.execute("CREATE INDEX orders_date_idx ON orders(order_date)")
        connection.execute("CREATE INDEX orders_region_idx ON orders(region)")
        connection.execute("CREATE INDEX orders_category_idx ON orders(product_category)")
        bounds = connection.execute(
            "SELECT min(order_date), max(order_date), count(DISTINCT order_month) FROM orders"
        ).fetchone()
    finally:
        connection.close()
        temporary_parquet.unlink(missing_ok=True)

    if bounds is None:
        raise RuntimeError("failed to calculate dataset bounds")

    manifest = DatasetManifest(
        schema_version="revenue-v1",
        seed=seed,
        row_count=count,
        min_order_date=bounds[0],
        max_order_date=bounds[1],
        month_count=bounds[2],
        content_hash=content_hash,
    )
    temporary_manifest.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)
    temporary_manifest.replace(manifest_path)
    return manifest
