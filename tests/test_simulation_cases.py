import json
from pathlib import Path

from analytics_chatbot.data import seed_database
from analytics_chatbot.evaluation_ops.cases import V4_CONTEXTS, build_v4_cases, write_cases

ROOT = Path(__file__).resolve().parents[1]


def test_v4_enriches_all_fifty_distinct_situations(tmp_path: Path) -> None:
    database = tmp_path / "sphere.duckdb"
    seed_database(database)
    records = build_v4_cases(database)

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


def test_v4_decision_contexts_follow_the_analytical_direction() -> None:
    expected = {
        "top3-countries-then-segment": (
            "I need to see which customer segment leads inside the top-revenue country.",
            "Please retain the top-country scope and name the leading segment.",
        ),
        "no-save-then-top": (
            "I need to move from category detail to category leadership without persistence.",
            "Please keep the no-save constraint active and name the leading category.",
        ),
        "category-region-drill": (
            "I need to understand how the global leading category's revenue is distributed "
            "across regions.",
            "Please retain the selected category and make the regional split and top-region "
            "share explicit.",
        ),
        "product-drill": (
            "I need to understand the leading product's unit movement and discounting.",
            "Please retain the product and distinguish units from average discount rate.",
        ),
    }

    assert {
        key: (context.decision, context.communication_need)
        for key, context in V4_CONTEXTS.items()
        if key in expected
    } == expected
    assert (
        "This is for a one-sentence board brief."
        in V4_CONTEXTS["top-country-net"].render()
    )


def test_v4_regenerates_the_tracked_corpus_byte_for_byte(tmp_path: Path) -> None:
    database = tmp_path / "sphere.duckdb"
    seed_database(database)
    output = tmp_path / "cases.jsonl"
    write_cases(build_v4_cases(database), output)

    tracked = ROOT / "orq/resources/datasets/simulation-cases-v4.jsonl"
    assert output.read_bytes() == tracked.read_bytes()
