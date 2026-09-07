from pathlib import Path

import duckdb
import polars as pl

from analytics_chatbot.data import generate_orders, seed_database

EXPECTED_PRODUCTS = {
    "Small Appliances": {"Espresso Machine", "Air Purifier"},
    "Cleaning": {"Robot Vacuum", "Dishwasher"},
    "Laundry": {"Washing Machine", "Tumble Dryer"},
    "Major Appliances": {"Refrigerator", "Heat Pump"},
}
EXPECTED_SEGMENTS = {
    "Independent Retailers",
    "Regional Chains",
    "National Retailers",
}


def test_generate_orders_is_lazy() -> None:
    orders = generate_orders(count=100)

    assert isinstance(orders, pl.LazyFrame)
    assert orders.collect_schema()["order_date"] == pl.Date
    assert orders.select(pl.len()).collect(engine="streaming").item() == 100


def test_seed_database_is_deterministic(tmp_path: Path) -> None:
    first = seed_database(tmp_path / "first.duckdb")
    second = seed_database(tmp_path / "second.duckdb")

    assert first.row_count == second.row_count == 25_000
    assert first.content_hash == second.content_hash
    assert first.min_order_date.isoformat() == "2024-01-01"
    assert first.max_order_date.isoformat() == "2025-12-31"
    assert first.month_count == second.month_count == 24


def test_seeded_orders_cover_business_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "analytics.duckdb"
    seed_database(path)

    with duckdb.connect(str(path), read_only=True) as connection:
        result = connection.execute(
            "SELECT count(DISTINCT region), count(DISTINCT product_category), "
            "count(DISTINCT customer_segment), count(DISTINCT order_status) FROM orders"
        ).fetchone()

    assert result == (4, 4, 3, 4)


def test_seeded_orders_use_sphere_catalog(tmp_path: Path) -> None:
    path = tmp_path / "sphere.duckdb"
    manifest = seed_database(path)

    with duckdb.connect(str(path), read_only=True) as connection:
        products = connection.execute(
            "SELECT product_category, product FROM orders GROUP BY ALL"
        ).fetchall()
        segments = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT customer_segment FROM orders"
            ).fetchall()
        }

    by_category: dict[str, set[str]] = {}
    for category, product in products:
        by_category.setdefault(category, set()).add(product)

    assert by_category == EXPECTED_PRODUCTS
    assert segments == EXPECTED_SEGMENTS
    assert manifest.schema_version == "sphere-orders-v1"


def test_revenue_semantics_are_consistent(tmp_path: Path) -> None:
    path = tmp_path / "analytics.duckdb"
    seed_database(path, count=1_000)

    with duckdb.connect(str(path), read_only=True) as connection:
        violations = connection.execute(
            """
            SELECT count(*)
            FROM orders
            WHERE net_revenue < 0
               OR refund_amount < 0
               OR (order_status IN ('cancelled', 'pending') AND net_revenue <> 0)
               OR net_revenue > gross_revenue
            """
        ).fetchone()

    assert violations == (0,)
