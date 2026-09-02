import json
from pathlib import Path

from typer.testing import CliRunner

from analytics_chatbot.cli import app
from analytics_chatbot.models import AgentResponse

runner = CliRunner()


def test_seed_data_command(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["seed-data", "--database", str(tmp_path / "analytics.duckdb")]
    )
    assert result.exit_code == 0
    assert "25,000" in result.stdout


def test_ask_json_output_uses_injected_chatbot(monkeypatch, tmp_path: Path) -> None:
    class FakeChatbot:
        def ask(self, message, conversation=None, context=None):
            return AgentResponse(
                answer="Revenue is 123.45.",
                run_id="run-1",
                thread_id="thread-1",
                response_id="resp-1",
                artifact_path=str(tmp_path / "events.jsonl"),
            )

    monkeypatch.setattr("analytics_chatbot.cli._build_chatbot", lambda: FakeChatbot())
    result = runner.invoke(app, ["ask", "total revenue", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["thread_id"] == "thread-1"


def test_show_run_reads_finalized_events(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    (run_dir / "events.jsonl").write_text(
        '{"type":"run_started","message":"hello"}\n'
        '{"type":"run_finished","status":"succeeded"}\n'
    )
    monkeypatch.setenv("ANALYTICS_CHATBOT_RUNS_PATH", str(tmp_path))

    result = runner.invoke(app, ["show-run", "run-1", "--json"])

    assert result.exit_code == 0
    assert len(json.loads(result.stdout)) == 2
