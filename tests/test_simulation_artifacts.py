from __future__ import annotations

import copy

from analytics_chatbot.evaluation_ops.simulation_artifacts import normalize_simulation_results


def _case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "analyst--regional-revenue",
        "split": "dev",
        "coverage": ["aggregation"],
        "oracle": {
            "reference_sql": "select region, sum(net_revenue) from orders group by region",
            "expected": {"columns": ["region", "value"], "rows": [["EMEA", "42.00"]]},
        },
        "state_expectation": None,
    }
    case.update(overrides)
    return case


def _result(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "messages": [
            {"role": "user", "content": "Compare regional net revenue."},
            {
                "role": "assistant",
                "content": "EMEA net revenue was 42.00.",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {
                            "name": "query_sql",
                            "arguments": '{"query":"select 42"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "name": "query_sql",
                "tool_call_id": "call-1",
                "content": '{"ok":true,"data":{"rows":[["EMEA","42.00"]]}}',
            },
        ],
        "terminated_by": "judge",
        "goal_achieved": True,
        "criteria_verified": True,
        "thread_id": "local-thread-1",
        "token_usage": {"reasoning_tokens": 12, "total_tokens": 100},
        "metadata": {
            "datapoint_id": "analyst--regional-revenue",
            "persona": "analyst",
            "scenario": "regional-revenue",
        },
    }
    result.update(overrides)
    return result


def test_normalizes_raw_result_for_evaluatorq_replay() -> None:
    batch = normalize_simulation_results([_result()], [_case()])

    assert batch.rejected == []
    assert batch.duplicates == []
    assert len(batch.rows) == 1
    row = batch.rows[0]
    assert row.source is None
    assert [message.role for message in row.conversation] == ["user", "tool", "assistant"]
    assert row.conversation[-1].content == row.assistant_response
    assert row.tool_events[0].arguments == {"query": "select 42"}
    assert row.tool_events[0].result == {
        "ok": True,
        "data": {"rows": [["EMEA", "42.00"]]},
    }
    assert row.oracle is not None
    assert row.oracle.expected_answer == {
        "columns": ["region", "value"],
        "rows": [["EMEA", "42.00"]],
    }
    assert row.to_datapoint().expected_output == row.oracle.expected_answer


def test_drops_only_exact_duplicates_and_keeps_distinct_attempts() -> None:
    first = _result()
    duplicate = copy.deepcopy(first)
    duplicate["thread_id"] = "different-runtime-thread"
    duplicate["messages"][1]["tool_calls"][0]["id"] = "different-call-id"  # type: ignore[index]
    duplicate["messages"][2]["tool_call_id"] = "different-call-id"  # type: ignore[index]
    second = copy.deepcopy(first)
    second["thread_id"] = "local-thread-2"
    second["messages"][1]["content"] = "EMEA was 42.00, based on the query result."  # type: ignore[index]

    batch = normalize_simulation_results([first, duplicate, second], [_case()])

    assert len(batch.rows) == 2
    assert len(batch.duplicates) == 1
    assert batch.duplicates[0].case_id == "analyst--regional-revenue"


def test_rejects_failed_runs_and_missing_expected_tools() -> None:
    failed = _result(goal_achieved=False)
    missing_tool = _result(
        messages=[
            {"role": "user", "content": "Compare regional net revenue."},
            {"role": "assistant", "content": "EMEA was 42.00."},
        ],
        thread_id="local-thread-2",
    )

    batch = normalize_simulation_results([failed, missing_tool], [_case()])

    assert batch.rows == []
    assert [item.reasons for item in batch.rejected] == [
        ["goal_not_achieved"],
        ["missing_expected_tool:query_sql"],
    ]


def test_rejects_unpaired_tool_calls_and_non_object_arguments() -> None:
    unpaired = _result(messages=_result()["messages"][:-1])
    invalid_arguments = copy.deepcopy(_result())
    invalid_arguments["messages"][1]["tool_calls"][0]["function"]["arguments"] = "[]"  # type: ignore[index]
    invalid_arguments["thread_id"] = "local-thread-2"

    batch = normalize_simulation_results([unpaired, invalid_arguments], [_case()])

    assert batch.rows == []
    assert batch.rejected[0].reasons == ["unpaired_tool_call:call-1"]
    assert batch.rejected[1].reasons == ["invalid_tool_arguments:call-1"]


def test_enforces_save_expectation() -> None:
    save_case = _case(state_expectation={"authorized": True})
    no_save_case = _case(state_expectation={"authorized": False})

    missing_save = normalize_simulation_results([_result()], [save_case])
    unexpected_save_result = _result()
    messages = unexpected_save_result["messages"]
    assert isinstance(messages, list)
    assistant = messages[1]
    assert isinstance(assistant, dict)
    calls = assistant["tool_calls"]
    assert isinstance(calls, list)
    calls.append(
        {
            "id": "call-2",
            "function": {"name": "save_insight", "arguments": '{"title":"Revenue"}'},
        }
    )
    messages.append(
        {
            "role": "tool",
            "name": "save_insight",
            "tool_call_id": "call-2",
            "content": '{"ok":true}',
        }
    )
    unexpected_save = normalize_simulation_results([unexpected_save_result], [no_save_case])

    assert missing_save.rejected[0].reasons == ["missing_expected_tool:save_insight"]
    assert unexpected_save.rejected[0].reasons == ["unexpected_tool:save_insight"]
