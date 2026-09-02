from pathlib import Path

import pytest

from analytics_chatbot.data import seed_database
from analytics_chatbot.sql_tool import SqlTool


@pytest.fixture(scope="module")
def database_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("sql-tool") / "analytics.duckdb"
    seed_database(path, count=1_000)
    return path


@pytest.fixture
def sql_tool(database_path: Path) -> SqlTool:
    return SqlTool(database_path=database_path, max_rows=200, timeout_seconds=2)


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM orders",
        "UPDATE orders SET region = 'EMEA'",
        "SELECT 1; SELECT 2",
        "COPY orders TO '/tmp/orders.csv'",
        "SELECT * FROM read_csv_auto('/tmp/private.csv')",
        "SELECT * FROM read_parquet('/tmp/private.parquet')",
    ],
)
def test_rejects_unsafe_sql(sql_tool: SqlTool, query: str) -> None:
    result = sql_tool.execute(query)

    assert result.ok is False
    assert result.error_code == "unsafe_sql"


def test_caps_query_rows(sql_tool: SqlTool) -> None:
    result = sql_tool.execute("SELECT * FROM orders ORDER BY order_id")

    assert result.ok is True
    assert len(result.data["rows"]) == 200
    assert result.data["truncated"] is True
    assert result.data["columns"][0] == "order_id"


def test_returns_structured_database_error(sql_tool: SqlTool) -> None:
    result = sql_tool.execute("SELECT missing_column FROM orders")

    assert result.ok is False
    assert result.error_code == "query_error"
    assert "missing_column" in (result.error or "")


def test_allows_common_table_expression(sql_tool: SqlTool) -> None:
    result = sql_tool.execute(
        "WITH revenue AS (SELECT region, sum(net_revenue) AS total FROM orders GROUP BY region) "
        "SELECT * FROM revenue ORDER BY total DESC"
    )

    assert result.ok is True
    assert len(result.data["rows"]) == 4
    assert result.data["truncated"] is False
