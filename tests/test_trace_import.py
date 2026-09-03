import json
from pathlib import Path

import pytest
from evaluatorq import DataPoint
from evaluatorq.evaluatorq import extract_recorded_response

from analytics_chatbot.evaluation_ops.trace_import import (
    TraceImportError,
    import_orq_trace,
    import_run_audit,
)

FIXTURES = Path(__file__).parent / "fixtures" / "traces"


def load_trace(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_imports_chat_completions_as_evaluatorq_datapoint() -> None:
    point = import_orq_trace(load_trace("chat_completions.json"))

    assert isinstance(point, DataPoint)
    assert [message["role"] for message in point.inputs["messages"]] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
    ]
    assert point.inputs["messages"][-1]["content"] == "EMEA revenue was 42."
    assert point.inputs["recorded_output"] == "EMEA revenue was 42."
    assert point.inputs["tool_evidence"] == [
        {
            "call_id": "call-chat-1",
            "name": "query_sql",
            "arguments": '{"query":"SELECT 42 AS revenue"}',
            "result": '{"revenue":42}',
        }
    ]
    assert point.inputs["source"] == {
        "trace_id": "trace-chat",
        "span_id": "span-chat",
        "session_id": "session-chat",
        "actor_id": "analyst@example.com",
        "case_id": "case-chat",
    }
    assert point.inputs["metadata"]["split"] == "dev"
    assert point.expected_output == "42"
    assert extract_recorded_response(point.inputs["messages"]) == "EMEA revenue was 42."


def test_imports_responses_api_items_without_losing_structured_tool_result() -> None:
    point = import_orq_trace(load_trace("responses_api.json"))

    assert point.inputs["recorded_output"] == "Saved the EMEA result."
    assert point.inputs["tool_evidence"] == [
        {
            "call_id": "call-responses-1",
            "name": "save_insight",
            "arguments": '{"text":"EMEA revenue was 42"}',
            "result": {"ok": True, "id": "insight-1"},
        }
    ]
    assert point.inputs["source"]["actor_id"] == "simulator-actor"
    assert point.inputs["source"]["case_id"] == "case-responses"
    assert point.inputs["messages"][-1] == {
        "role": "assistant",
        "content": "Saved the EMEA result.",
    }


def test_imports_otel_genai_messages_from_attributes_and_events() -> None:
    point = import_orq_trace(load_trace("otel_genai.json"))

    assert [message["role"] for message in point.inputs["messages"]] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
    ]
    assert point.inputs["tool_evidence"][0]["arguments"] == {"query": "SELECT 52 AS gross_revenue"}
    assert point.inputs["tool_evidence"][0]["result"] == {"gross_revenue": 52}
    assert point.inputs["source"]["session_id"] == "session-otel"
    assert point.inputs["metadata"]["gen_ai.request.model"] == "example-model"


def test_imports_hydrated_orq_span_with_json_encoded_gen_ai_input_and_output() -> None:
    span = {
        "span": {
            "summary": {
                "trace_id": "trace-hydrated",
                "span_id": "span-hydrated",
                "type": "trace",
            },
            "attributes": {
                "gen_ai": {
                    "input": json.dumps("Question from the agent trace"),
                    "output": json.dumps(
                        [
                            {
                                "type": "message",
                                "role": "assistant",
                                "content": [{"type": "output_text", "text": "Recorded answer"}],
                            }
                        ]
                    ),
                }
            },
        }
    }

    point = import_orq_trace(span)

    assert point.inputs["messages"] == [
        {"role": "user", "content": "Question from the agent trace"},
        {"role": "assistant", "content": "Recorded answer"},
    ]


def test_uses_latest_non_evaluator_span_and_walks_to_parent_for_messages() -> None:
    trace = {
        "trace_id": "trace-tree",
        "spans": [
            {
                "trace_id": "trace-tree",
                "span_id": "parent",
                "type": "agent",
                "ended_at": "2026-09-03T10:00:00Z",
                "input": {"messages": [{"role": "user", "content": "Question"}]},
            },
            {
                "trace_id": "trace-tree",
                "span_id": "terminal",
                "parent_span_id": "parent",
                "type": "span.response",
                "ended_at": "2026-09-03T10:00:02Z",
                "output": {
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "Answer"}],
                        }
                    ]
                },
            },
            {
                "trace_id": "trace-tree",
                "span_id": "evaluator",
                "parent_span_id": "terminal",
                "type": "evaluator",
                "ended_at": "2026-09-03T10:00:03Z",
                "input": {"messages": [{"role": "user", "content": "Grade it"}]},
                "output": {"content": "pass"},
            },
        ],
    }

    point = import_orq_trace(trace)

    assert point.inputs["recorded_output"] == "Answer"
    assert point.inputs["source"]["span_id"] == "terminal"
    assert point.inputs["source"]["lineage_span_ids"] == ["parent", "terminal"]


def test_trace_root_does_not_eclipse_richer_agent_span() -> None:
    trace = {
        "trace_id": "trace-agent",
        "spans": [
            {
                "trace_id": "trace-agent",
                "span_id": "root",
                "type": "trace",
                "ended_at": "2026-09-03T10:00:03Z",
                "attributes": {
                    "gen_ai": {
                        "input": json.dumps("Flattened request and tool result"),
                        "output": json.dumps([{"role": "assistant", "content": "Final answer"}]),
                    }
                },
            },
            {
                "trace_id": "trace-agent",
                "span_id": "agent",
                "parent_span_id": "root",
                "type": "span.agent",
                "ended_at": "2026-09-03T10:00:02Z",
                "attributes": {
                    "gen_ai": {
                        "input": json.dumps(
                            [
                                {"role": "user", "content": "Question"},
                                {
                                    "type": "function_call",
                                    "call_id": "call-1",
                                    "name": "lookup",
                                    "arguments": {"key": "value"},
                                },
                                {
                                    "type": "function_call_output",
                                    "call_id": "call-1",
                                    "output": {"value": 1},
                                },
                            ]
                        ),
                        "output": json.dumps({"role": "assistant", "content": "Final answer"}),
                    }
                },
            },
            {
                "trace_id": "trace-agent",
                "span_id": "response",
                "parent_span_id": "agent",
                "type": "span.responses",
                "ended_at": "2026-09-03T10:00:02Z",
                "attributes": {
                    "gen_ai": {
                        "output": json.dumps([{"role": "assistant", "content": "Final answer"}])
                    }
                },
            },
        ],
    }

    point = import_orq_trace(trace)

    assert point.inputs["source"]["span_id"] == "response"
    assert point.inputs["source"]["lineage_span_ids"] == ["agent", "response"]
    assert point.inputs["tool_evidence"] == [
        {
            "call_id": "call-1",
            "name": "lookup",
            "arguments": {"key": "value"},
            "result": {"value": 1},
        }
    ]


def test_imports_exact_local_run_audit_when_trace_payload_is_scrubbed(tmp_path: Path) -> None:
    artifact = tmp_path / "events.jsonl"
    events = [
        {
            "type": "run_started",
            "run_id": "run-audit",
            "thread_id": "thread-audit",
            "message": "What is revenue?",
            "trace_context": {
                "identity_id": "audit-actor",
                "case_id": "case-audit",
                "run_kind": "simulation",
            },
        },
        {
            "type": "gateway_response",
            "step": 0,
            "response_id": "resp-1",
            "text": "",
            "function_calls": [
                {
                    "call_id": "call-audit",
                    "name": "query_sql",
                    "arguments": '{"query":"SELECT 42"}',
                }
            ],
        },
        {
            "type": "tool_call",
            "step": 0,
            "call_id": "call-audit",
            "name": "query_sql",
            "arguments": {"query": "SELECT 42"},
            "result": {"ok": True, "data": {"value": 42}},
        },
        {
            "type": "gateway_response",
            "step": 1,
            "response_id": "resp-2",
            "text": "Revenue is 42.",
            "function_calls": [],
        },
        {
            "type": "run_finished",
            "status": "succeeded",
            "response_id": "resp-2",
            "tool_call_count": 1,
        },
    ]
    artifact.write_text("".join(json.dumps(event) + "\n" for event in events))

    point = import_run_audit(artifact)

    assert [message["role"] for message in point.inputs["messages"]] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]
    assert point.inputs["tool_evidence"] == [
        {
            "call_id": "call-audit",
            "name": "query_sql",
            "arguments": '{"query":"SELECT 42"}',
            "result": {"ok": True, "data": {"value": 42}},
        }
    ]
    assert point.inputs["recorded_output"] == "Revenue is 42."
    assert point.inputs["source"] == {
        "run_id": "run-audit",
        "thread_id": "thread-audit",
        "response_id": "resp-2",
        "actor_id": "audit-actor",
        "case_id": "case-audit",
        "artifact_path": str(artifact),
    }
    assert point.inputs["metadata"]["run_kind"] == "simulation"
    assert extract_recorded_response(point.inputs["messages"]) == "Revenue is 42."


def test_summary_only_trace_points_to_exact_audit_fallback() -> None:
    with pytest.raises(TraceImportError, match="local run audit"):
        import_orq_trace(
            {
                "trace_id": "summary-only",
                "span_id": "root",
                "type": "trace",
                "attributes": {"gen_ai": {"operation": {"name": "responses"}}},
            }
        )


def test_run_audit_must_be_successfully_finalized(tmp_path: Path) -> None:
    artifact = tmp_path / "events.partial.jsonl"
    events = [
        {"type": "run_started", "run_id": "run-partial", "message": "Question"},
        {"type": "gateway_response", "response_id": "resp-1", "text": "Draft"},
    ]
    artifact.write_text("".join(json.dumps(event) + "\n" for event in events))

    with pytest.raises(TraceImportError, match="not successfully finalized"):
        import_run_audit(artifact)


@pytest.mark.parametrize(
    ("span", "match"),
    [
        (
            {"trace_id": "t", "span_id": "s", "output": {"content": "answer"}},
            "user message",
        ),
        (
            {
                "trace_id": "t",
                "span_id": "s",
                "input": {"messages": [{"role": "user", "content": "question"}]},
            },
            "final assistant",
        ),
        ({"trace_id": "t", "spans": "not-a-list"}, "span collection"),
    ],
)
def test_rejects_malformed_or_missing_messages(span: dict, match: str) -> None:
    with pytest.raises(TraceImportError, match=match):
        import_orq_trace(span)
