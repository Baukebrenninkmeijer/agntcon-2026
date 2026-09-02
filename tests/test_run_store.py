import json
from pathlib import Path

from analytics_chatbot.run_store import RunStore


def test_finalize_atomically_promotes_partial_run(tmp_path: Path) -> None:
    store = RunStore(tmp_path, run_id="run-1")
    store.append({"type": "user_message", "content": "hello"})

    final_path = store.finalize({"status": "completed"})

    assert final_path.name == "events.jsonl"
    assert not (final_path.parent / "events.partial.jsonl").exists()
    events = [json.loads(line) for line in final_path.read_text().splitlines()]
    assert [event["type"] for event in events] == ["user_message", "run_finished"]
    assert events[-1]["status"] == "completed"


def test_abort_preserves_diagnostic_partial_run(tmp_path: Path) -> None:
    store = RunStore(tmp_path, run_id="run-2")
    store.append({"type": "user_message", "content": "hello"})

    partial_path = store.abort("gateway failed")

    assert partial_path.name == "events.partial.jsonl"
    assert partial_path.exists()
    events = [json.loads(line) for line in partial_path.read_text().splitlines()]
    assert events[-1]["type"] == "run_failed"
    assert events[-1]["error"] == "gateway failed"
