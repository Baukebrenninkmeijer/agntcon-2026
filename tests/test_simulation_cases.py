import json
from pathlib import Path

import duckdb
from evaluatorq.simulation import SimulationDatapoint

from analytics_chatbot.evaluation_ops.cases import build_cases, write_cases

ROOT = Path(__file__).resolve().parents[1]


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


def test_pilot_review_preserves_every_attempt_transcript() -> None:
    review = json.loads(
        (ROOT / "orq/resources/datasets/simulation-pilot-review.json").read_text()
    )

    assert [attempt["attempt"] for attempt in review["attempts"]] == [1, 2, 3]
    for attempt in review["attempts"]:
        transcript = attempt["transcript"]
        assert transcript[0]["role"] == "user"
        assert transcript[-1]["role"] == "assistant"
        assert transcript[-1].get("content")
        assert sum(item.get("type") == "reasoning_summary" for item in transcript) == 2
        tool_calls = [item for item in transcript if "tool_call" in item]
        tool_results = [item for item in transcript if item["role"] == "tool"]
        assert len(tool_calls) == len(tool_results) >= 1
        assert [item["tool_call"]["name"] for item in tool_calls] == [
            item["name"] for item in tool_results
        ]

    serialized = json.dumps(review)
    for forbidden_key in ('"trace_id"', '"span_id"', '"thread_id"', '"call_id"'):
        assert forbidden_key not in serialized
