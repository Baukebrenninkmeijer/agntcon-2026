import os
from pathlib import Path

import pytest

from analytics_chatbot.agent import AnalyticsChatbot
from analytics_chatbot.config import Settings, TraceContext
from analytics_chatbot.data import seed_database

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("ANALYTICS_CHATBOT_LIVE_TEST") != "1",
        reason="set ANALYTICS_CHATBOT_LIVE_TEST=1 to call the orq AI Gateway",
    ),
]


def test_live_agent_queries_sql_and_returns_trace_identity(tmp_path: Path) -> None:
    database = tmp_path / "analytics.duckdb"
    seed_database(database)
    settings = Settings(database_path=database, runs_path=tmp_path / "runs")

    response = AnalyticsChatbot(settings=settings).ask(
        "What was net revenue by region in 2025? Use the database before answering.",
        context=TraceContext(
            run_kind="smoke",
            interface="pytest",
            evaluation_split="smoke",
            case_id="live-gateway-regional-revenue",
            identity_id="pydata2026-smoke-test",
        ),
    )

    assert response.answer
    assert any(call.name == "query_sql" and call.result.ok for call in response.tool_calls)
    assert response.thread_id
    assert response.response_id
