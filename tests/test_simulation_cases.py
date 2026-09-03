import json
from pathlib import Path

import duckdb
from evaluatorq.simulation import SimulationDatapoint

from analytics_chatbot.evaluation_ops.cases import build_cases, write_cases


def test_builds_fifty_stable_oracle_backed_cases(tmp_path: Path) -> None:
    database = tmp_path / "analytics.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            "CREATE TABLE orders AS SELECT * FROM (VALUES "
            "('2025-01-01'::DATE, 'EMEA', 'Software', 'Enterprise', 'completed', "
            "100::DECIMAL(16,2), 90::DECIMAL(16,2), 5::DECIMAL(16,2)),"
            "('2024-01-01'::DATE, 'APAC', 'Data', 'SMB', 'cancelled', "
            "50::DECIMAL(16,2), 0::DECIMAL(16,2), 0::DECIMAL(16,2))) "
            "t(order_date, region, product_category, customer_segment, order_status, "
            "gross_revenue, net_revenue, refund_amount)"
        )

    records = build_cases(database)

    assert len(records) == 50
    assert len({record["id"] for record in records}) == 50
    assert sum(record["split"] == "dev" for record in records) == 30
    assert sum(record["split"] == "test" for record in records) == 20
    coverage = {label for record in records for label in record["coverage"]}
    assert {
        "multi-turn-retention",
        "explicit-save",
        "no-save-intent",
        "ambiguity-clarification",
    } <= coverage
    assert all(record["oracle"]["expected"] for record in records if record["oracle"])

    output = tmp_path / "cases.jsonl"
    write_cases(records, output)
    loaded = [json.loads(line) for line in output.read_text().splitlines()]
    assert [SimulationDatapoint.model_validate(row).id for row in loaded] == [
        record["id"] for record in records
    ]
