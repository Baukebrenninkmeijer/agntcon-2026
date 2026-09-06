import json
from pathlib import Path

import duckdb
from evaluatorq.simulation import SimulationDatapoint

from analytics_chatbot.evaluation_ops.cases import build_cases, build_edge_cases, write_cases

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


def test_builds_fifty_harder_multi_turn_edge_cases(tmp_path: Path) -> None:
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

    records = build_edge_cases(database)

    assert len(records) == 50
    assert len({record["id"] for record in records}) == 50
    assert len({record["first_message"] for record in records}) == 50
    assert sum(record["split"] == "dev" for record in records) == 30
    assert sum(record["split"] == "test" for record in records) == 20
    assert all(record["corpus_version"] == "simulation-edge-v2" for record in records)
    assert all(record["scenario"]["is_edge_case"] is True for record in records)
    assert len({record["scenario"]["conversation_strategy"] for record in records}) >= 4
    assert sum(record["expected_min_user_turns"] == 2 for record in records) == 35
    assert sum(record["expected_min_user_turns"] == 3 for record in records) == 15
    assert all(
        any(
            criterion["type"] == "must_happen" and "follow-up" in criterion["description"].lower()
            for criterion in record["scenario"]["criteria"]
        )
        for record in records
    )
    assert all("reference_sql" not in record["scenario"]["ground_truth"] for record in records)
    assert all("expected" not in record["scenario"]["ground_truth"] for record in records)
    assert all(record["oracle"]["expected"] for record in records if record["oracle"])

    output = tmp_path / "edge-cases.jsonl"
    write_cases(records, output)
    loaded = [json.loads(line) for line in output.read_text().splitlines()]
    assert [SimulationDatapoint.model_validate(row).id for row in loaded] == [
        record["id"] for record in records
    ]


def test_edge_v2_oracles_cover_the_staged_final_request(tmp_path: Path) -> None:
    database = tmp_path / "analytics.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            "CREATE TABLE orders AS SELECT * FROM (VALUES "
            "('2025-01-01'::DATE, 'EMEA', 'Software', 'Enterprise', 'completed', "
            "100::DECIMAL(16,2), 90::DECIMAL(16,2), 5::DECIMAL(16,2)),"
            "('2025-02-01'::DATE, 'APAC', 'Software', 'Enterprise', 'completed', "
            "80::DECIMAL(16,2), 70::DECIMAL(16,2), 0::DECIMAL(16,2)),"
            "('2024-01-01'::DATE, 'APAC', 'Data', 'SMB', 'cancelled', "
            "50::DECIMAL(16,2), 0::DECIMAL(16,2), 0::DECIMAL(16,2)),"
            "('2024-02-01'::DATE, 'EMEA', 'Data', 'SMB', 'completed', "
            "20::DECIMAL(16,2), 18::DECIMAL(16,2), 0::DECIMAL(16,2))) "
            "t(order_date, region, product_category, customer_segment, order_status, "
            "gross_revenue, net_revenue, refund_amount)"
        )

    records = build_edge_cases(database)
    expected_by_family = {
        "net-by-region": {
            "columns": ["scope", "year", "region", "net_revenue", "leader_gap"],
            "rows": [
                ["full", None, "EMEA", "108.00", "38.00"],
                ["full", None, "APAC", "70.00", None],
                ["year_leader", 2024, "EMEA", "18.00", None],
                ["year_leader", 2025, "EMEA", "90.00", None],
            ],
        },
        "gross-net-software": {"columns": ["value"], "rows": [["160.00"]]},
        "followup-segment": {
            "columns": ["scope", "year", "customer_segment", "net_revenue", "leader_gap"],
            "rows": [
                ["full", None, "Enterprise", "160.00", "142.00"],
                ["full", None, "SMB", "18.00", None],
                ["year_leader", 2025, "Enterprise", "160.00", None],
            ],
        },
        "ambiguous-revenue": {
            "columns": ["region", "value"],
            "rows": [["EMEA", "90.00"]],
        },
        "mutation-boundary": {"columns": ["value"], "rows": [["178.00"]]},
    }

    for family, expected in expected_by_family.items():
        family_records = [record for record in records if record["id"].endswith(family)]
        assert len(family_records) == 5
        actual = {
            json.dumps(record["oracle"]["expected"], sort_keys=True) for record in family_records
        }
        assert actual == {json.dumps(expected, sort_keys=True)}


def test_pilot_review_preserves_every_attempt_transcript() -> None:
    review = json.loads((ROOT / "orq/resources/datasets/simulation-pilot-review.json").read_text())

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


def test_v3_is_one_persona_fifty_distinct_situations() -> None:
    from analytics_chatbot.evaluation_ops.cases_v3 import SCENARIOS, build_v3_cases

    database = ROOT / "data" / "analytics.duckdb"
    if not database.exists():
        import pytest

        pytest.skip("pinned DuckDB not present")

    records = build_v3_cases(database)

    assert len(records) == 50
    assert len({record["id"] for record in records}) == 50
    assert len({record["first_message"] for record in records}) == 50
    assert {record["persona"]["name"] for record in records} == {"business-analyst"}
    assert all(record["corpus_version"] == "simulation-v3" for record in records)
    assert sum(record["split"] == "dev" for record in records) == 30
    assert sum(record["oracle"] is None for record in records) == 3
    assert all(record["oracle"]["expected"]["rows"] for record in records if record["oracle"])
    assert sum(record["expected_min_user_turns"] > 1 for record in records) == sum(
        scenario.min_user_turns > 1 for scenario in SCENARIOS
    )
    assert [SimulationDatapoint.model_validate(record).id for record in records] == [
        record["id"] for record in records
    ]


def test_v4_enriches_all_fifty_distinct_v3_situations() -> None:
    from analytics_chatbot.evaluation_ops.cases_v4 import build_v4_cases

    records = build_v4_cases(ROOT / "data" / "analytics.duckdb")

    assert len(records) == 50
    assert len({record["id"] for record in records}) == 50
    assert {record["corpus_version"] for record in records} == {"simulation-v4"}
    assert sum(record["split"] == "dev" for record in records) == 30
    assert sum(record["split"] == "test" for record in records) == 20
    assert all(record["id"].startswith("sphere-stakeholder--v4-") for record in records)
    assert all(
        set(record["decision_context"])
        == {"stakeholder", "decision", "delivery_setting", "communication_need"}
        for record in records
    )
    assert all(
        all(value.strip() for value in record["decision_context"].values())
        for record in records
    )
    assert all("Sphere.com" in record["first_message"] for record in records)
    assert not any(
        old in json.dumps(records)
        for old in ("Software", "Hardware", "Services", "Data", "SMB", "Mid-Market", "Enterprise")
    )
