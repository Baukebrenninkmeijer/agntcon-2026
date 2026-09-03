from __future__ import annotations

from typing import Any

import pytest
from evaluatorq import EvaluationResult

from analytics_chatbot.evaluation_ops import (
    AtomicJudge,
    TraceBackedEvaluationRow,
    build_atomic_evaluators,
    run_trace_evaluation,
)


def _row(**overrides: Any) -> TraceBackedEvaluationRow:
    data: dict[str, Any] = {
        "schema_version": "trace-eval-v1",
        "case_id": "case-001",
        "evaluation_split": "dev",
        "source": {"trace_id": "trace-1", "span_ids": ["span-1"]},
        "conversation": [
            {"role": "user", "content": "What was EMEA net revenue in Q1?"},
            {"role": "assistant", "content": "It was EUR 42."},
        ],
        "assistant_response": "It was EUR 42.",
        "oracle": {
            "expected_answer": "EUR 42",
            "reference_sql": "select 42 as net_revenue",
            "query_requirements": ["exclude cancelled orders", "subtract refunds"],
        },
        "tool_events": [
            {
                "name": "query_sql",
                "arguments": {"query": "select 42 as net_revenue"},
                "result": {"columns": ["net_revenue"], "rows": [[42]]},
            }
        ],
        "retrievals": [],
        "state_before": {"saved_insights": []},
        "state_after": {"saved_insights": []},
    }
    data.update(overrides)
    return TraceBackedEvaluationRow.model_validate(data)


def test_trace_row_round_trips_to_evaluatorq_datapoint() -> None:
    row = _row()

    point = row.to_datapoint()
    restored = TraceBackedEvaluationRow.from_datapoint(point)

    assert restored == row
    assert point.inputs["messages"] == [message.model_dump() for message in row.conversation]
    assert point.expected_output == "EUR 42"


@pytest.mark.parametrize(
    ("judge", "overrides"),
    [
        (AtomicJudge.ANSWER_CORRECTNESS, {"oracle": None}),
        (AtomicJudge.QUERY_SEMANTICS, {"tool_events": []}),
        (
            AtomicJudge.EVIDENCE_FAITHFULNESS,
            {"tool_events": [], "retrievals": []},
        ),
        (
            AtomicJudge.MULTI_TURN_CONSISTENCY,
            {
                "conversation": [
                    {"role": "user", "content": "What was revenue?"},
                    {"role": "assistant", "content": "EUR 42."},
                ],
                "assistant_response": "EUR 42.",
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_inapplicable_rows_skip_the_judge(
    judge: AtomicJudge, overrides: dict[str, Any]
) -> None:
    calls = 0

    def jury_factory(**_kwargs: Any) -> dict[str, Any]:
        async def scorer(_params: dict[str, Any]) -> EvaluationResult:
            nonlocal calls
            calls += 1
            return EvaluationResult(value="pass", explanation="judged", pass_=True)

        return {"name": judge.value, "scorer": scorer}

    evaluator = next(
        item
        for item in build_atomic_evaluators(jury_factory=jury_factory)
        if item["name"] == judge.value
    )
    result = await evaluator["scorer"](
        {"data": _row(**overrides).to_datapoint(), "output": "It was EUR 42.", "row": 0}
    )

    assert calls == 0
    assert result.value == "not_applicable"
    assert result.pass_ is None
    assert result.explanation


@pytest.mark.asyncio
async def test_each_judge_receives_only_its_evidence_projection() -> None:
    captured: dict[str, Any] = {}

    def jury_factory(*, name: str, **kwargs: Any) -> dict[str, Any]:
        captured[name] = {"configuration": kwargs}

        async def scorer(params: dict[str, Any]) -> EvaluationResult:
            captured[name]["params"] = params
            return EvaluationResult(value="pass", explanation="ok", pass_=True)

        return {"name": name, "scorer": scorer}

    evaluators = build_atomic_evaluators(jury_factory=jury_factory)
    point = _row().to_datapoint()
    for evaluator in evaluators:
        await evaluator["scorer"]({"data": point, "output": "It was EUR 42.", "row": 7})

    correctness = captured[AtomicJudge.ANSWER_CORRECTNESS.value]["params"]
    faithfulness = captured[AtomicJudge.EVIDENCE_FAITHFULNESS.value]["params"]
    semantics = captured[AtomicJudge.QUERY_SEMANTICS.value]["params"]

    assert correctness["data"].expected_output == "EUR 42"
    assert "query_requirements" not in correctness["data"].inputs["evidence"]
    assert faithfulness["data"].expected_output is None
    assert "expected_answer" not in faithfulness["data"].inputs["evidence"]
    assert "reference_sql" not in faithfulness["data"].inputs["evidence"]
    assert semantics["data"].inputs["evidence"]["query_requirements"] == [
        "exclude cancelled orders",
        "subtract refunds",
    ]
    assert correctness["row"] == faithfulness["row"] == 7


def test_jury_configuration_preserves_template_variables_and_verdict_space() -> None:
    captured: list[dict[str, Any]] = []

    def jury_factory(**kwargs: Any) -> dict[str, Any]:
        captured.append(kwargs)

        async def scorer(_params: dict[str, Any]) -> EvaluationResult:
            return EvaluationResult(value="pass")

        return {"name": kwargs["name"], "scorer": scorer}

    build_atomic_evaluators(
        judges=["openai/model-a", "anthropic/model-b", "google/model-c"],
        jury_factory=jury_factory,
    )

    assert len(captured) == 4
    for configuration in captured:
        prompt = configuration["prompt"]
        assert "{{input.all_messages}}" in prompt
        assert "{{output.response}}" in prompt
        assert "{{input.expected_output}}" in prompt
        assert configuration["labels"] == ["pass", "fail", "not_applicable"]
        assert configuration["passing_labels"] == ["pass"]
        assert configuration["assignment"] == "all"
        assert configuration["aggregator"] == "majority"
        assert configuration["min_successful_judges"] == 2


@pytest.mark.asyncio
async def test_run_trace_evaluation_uses_native_evaluatorq_flow() -> None:
    observed: dict[str, Any] = {}

    async def native_runner(name: str, **kwargs: Any) -> list[Any]:
        observed.update(name=name, **kwargs)
        job_result = await kwargs["jobs"][0](kwargs["data"][0], 0)
        observed["job_result"] = job_result
        return []

    result = await run_trace_evaluation(
        [_row()],
        evaluators=[{"name": "stub", "scorer": _unused_scorer}],
        experiment_name="trace-eval-test",
        native_runner=native_runner,
        print_results=False,
    )

    assert result == []
    assert observed["name"] == "trace-eval-test"
    assert observed["job_result"] == {
        "name": "trace-backed-response",
        "output": "It was EUR 42.",
    }
    assert observed["inference"] is True
    assert observed["evaluators"][0]["name"] == "stub"


async def _unused_scorer(_params: dict[str, Any]) -> EvaluationResult:
    return EvaluationResult(value=True)
