import asyncio
import json
from collections import deque
from pathlib import Path

import duckdb
import pytest
from evaluatorq.contracts import Message

from analytics_chatbot.agent import AgentLoopError, AnalyticsChatbot
from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation_ops.target import AnalyticsChatbotTarget
from analytics_chatbot.models import GatewayFunctionCall, GatewayResponse
from analytics_chatbot.prompts import SYSTEM_PROMPT


class FakeGateway:
    def __init__(self) -> None:
        self.responses: deque[GatewayResponse | Exception] = deque()
        self.calls: list[dict] = []

    def function_call(self, name: str, arguments: dict | str, call_id: str = "call-1") -> None:
        payload = arguments if isinstance(arguments, str) else json.dumps(arguments)
        self.responses.append(
            GatewayResponse(
                response_id=f"resp-{len(self.responses) + 1}",
                function_calls=[GatewayFunctionCall(call_id=call_id, name=name, arguments=payload)],
            )
        )

    def text(self, value: str) -> None:
        self.responses.append(
            GatewayResponse(response_id=f"resp-{len(self.responses) + 1}", text=value)
        )

    def create_response(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.popleft()
        if isinstance(response, Exception):
            raise response
        return response


def test_system_prompt_is_a_rudimentary_sphere_baseline() -> None:
    prompt = " ".join(SYSTEM_PROMPT.lower().split())

    assert "sphere.com" in prompt
    assert "wholesale home-appliance orders" in prompt
    assert "use query_sql before making factual claims" in prompt
    assert "never claim that an insight was saved unless the tool succeeds" in prompt
    assert "do not recommend an action unless the user explicitly asks for one" in prompt
    for coaching_phrase in (
        "foreground",
        "decision impact",
        "adapt detail",
        "recommend next steps",
        "board narrative",
    ):
        assert coaching_phrase not in prompt


@pytest.fixture
def chatbot(tmp_path: Path):
    database = tmp_path / "analytics.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute("CREATE TABLE orders (net_revenue DECIMAL(12, 2), region VARCHAR)")
        connection.execute("INSERT INTO orders VALUES (123.45, 'EMEA')")
    gateway = FakeGateway()
    settings = Settings(database_path=database, runs_path=tmp_path / "runs")
    return AnalyticsChatbot(settings=settings, gateway=gateway), gateway


def test_executes_sql_then_returns_answer(chatbot) -> None:
    bot, gateway = chatbot
    gateway.function_call("query_sql", {"query": "SELECT sum(net_revenue) AS revenue FROM orders"})
    gateway.text("Net revenue is 123.45.")

    response = bot.ask("What is total net revenue?")

    assert response.answer == "Net revenue is 123.45."
    assert [call.name for call in response.tool_calls] == ["query_sql"]
    assert response.tool_calls[0].result.ok is True
    assert gateway.calls[1]["conversation"].previous_response_id == "resp-1"
    assert gateway.calls[1]["input_items"][0]["type"] == "function_call_output"
    assert Path(response.artifact_path).exists()


def test_save_tool_requires_explicit_request(chatbot) -> None:
    bot, gateway = chatbot
    gateway.text("EMEA revenue is 123.45.")
    bot.ask("What is EMEA revenue?")
    assert "save_insight" not in {tool["name"] for tool in gateway.calls[0]["tools"]}


def test_save_tool_records_state_change(chatbot) -> None:
    bot, gateway = chatbot
    gateway.function_call(
        "save_insight",
        {
            "title": "EMEA revenue",
            "summary": "EMEA revenue is 123.45.",
            "supporting_sql": "SELECT sum(net_revenue) FROM orders",
        },
    )
    gateway.text("Saved.")

    response = bot.ask("Calculate EMEA revenue and save that insight.")

    assert "save_insight" in {tool["name"] for tool in gateway.calls[0]["tools"]}
    assert response.state_changes[0].before["count"] == 0
    assert response.state_changes[0].after["count"] == 1


@pytest.mark.parametrize(
    ("name", "arguments", "error_code"),
    [
        ("query_sql", "{bad", "malformed_arguments"),
        ("not_a_tool", {}, "unknown_tool"),
    ],
)
def test_tool_failures_remain_in_trajectory(chatbot, name, arguments, error_code) -> None:
    bot, gateway = chatbot
    gateway.function_call(name, arguments)
    gateway.text("I could not complete that.")

    response = bot.ask("Analyze revenue")

    assert response.tool_calls[0].result.error_code == error_code
    events = Path(response.artifact_path).read_text()
    assert error_code in events


def test_repeated_tool_call_is_stopped(chatbot) -> None:
    bot, gateway = chatbot
    query = {"query": "SELECT sum(net_revenue) FROM orders"}
    gateway.function_call("query_sql", query, "call-1")
    gateway.function_call("query_sql", query, "call-2")
    gateway.text("Stopped repeating and answered.")

    response = bot.ask("Analyze revenue")

    assert response.tool_calls[-1].result.error_code == "repeated_tool_call"


def test_gateway_error_keeps_partial_run(chatbot) -> None:
    bot, gateway = chatbot
    gateway.responses.append(RuntimeError("gateway down"))

    with pytest.raises(RuntimeError, match="gateway down"):
        bot.ask("Analyze revenue")

    partials = list(bot.settings.runs_path.glob("*/events.partial.jsonl"))
    assert len(partials) == 1
    assert "run_failed" in partials[0].read_text()


def test_step_limit_is_enforced(chatbot) -> None:
    bot, gateway = chatbot
    bot.settings.max_tool_steps = 1
    gateway.function_call("query_sql", {"query": "SELECT 1"}, "call-1")

    with pytest.raises(AgentLoopError, match="step limit"):
        bot.ask("Analyze revenue")


def test_evaluatorq_target_preserves_case_and_conversation(chatbot) -> None:
    bot, gateway = chatbot
    gateway.text("First answer")
    gateway.text("Follow-up answer")
    target = AnalyticsChatbotTarget(
        bot.settings,
        {"Start the case": "case-01"},
        chatbot=bot,
    )

    async def run_turns():
        first = await target.respond([Message(role="user", content="Start the case")])
        second = await target.respond([Message(role="user", content="Follow up")])
        return first, second

    first, second = asyncio.run(run_turns())

    assert first.output[-1].text == "First answer"
    assert second.output[-1].text == "Follow-up answer"
    assert target.case_id == "case-01"
    assert gateway.calls[0]["conversation"].thread_id == gateway.calls[1]["conversation"].thread_id
