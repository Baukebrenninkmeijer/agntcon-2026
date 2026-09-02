from pathlib import Path

from analytics_chatbot.insights import InsightStore, SaveInsightArgs


def test_saves_structured_insight_and_changes_state(tmp_path: Path) -> None:
    store = InsightStore(tmp_path)
    before = store.snapshot()

    result = store.save(
        SaveInsightArgs(
            title="EMEA growth",
            summary="Revenue rose quarter over quarter.",
            supporting_sql="SELECT 1",
            tags=["emea", "growth"],
        )
    )
    after = store.snapshot()

    assert result.ok is True
    assert before["count"] == 0
    assert after["count"] == 1
    assert before["sha256"] != after["sha256"]
    assert result.data["insight"]["title"] == "EMEA growth"


def test_rejects_blank_insight_fields(tmp_path: Path) -> None:
    store = InsightStore(tmp_path)

    result = store.save(
        SaveInsightArgs(title=" ", summary="Summary", supporting_sql="SELECT 1")
    )

    assert result.ok is False
    assert result.error_code == "invalid_insight"
    assert store.snapshot()["count"] == 0
