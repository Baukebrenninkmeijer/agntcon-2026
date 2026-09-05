from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from analytics_chatbot.evaluation_ops import TraceBackedEvaluationRow
from analytics_chatbot.evaluation_ops.hosted_evaluators import orq_evaluator


def _row(*, expected_answer: Any = "EUR 42") -> TraceBackedEvaluationRow:
    return TraceBackedEvaluationRow.model_validate(
        {
            "case_id": "case-001",
            "evaluation_split": "dev",
            "conversation": [
                {"role": "user", "content": "Use net revenue."},
                {"role": "assistant", "content": "I will calculate it."},
                {"role": "tool", "content": '{"private_result": 42}'},
                {"role": "user", "content": "What was the result?"},
                {"role": "assistant", "content": "It was EUR 42."},
            ],
            "assistant_response": "It was EUR 42.",
            "oracle": None
            if expected_answer is None
            else {"expected_answer": expected_answer},
        }
    )


class FakeEvals:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def invoke_async(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


@pytest.mark.asyncio
async def test_orq_evaluator_routes_answer_correctness_and_maps_result() -> None:
    evals = FakeEvals(
        SimpleNamespace(
            result=SimpleNamespace(
                value="pass",
                explanation="The value matches the oracle.",
                passed=True,
                trace_id="runtime-trace",
                span_id="runtime-span",
                evaluator_id="runtime-evaluator",
            )
        )
    )
    evaluator = orq_evaluator(
        client=SimpleNamespace(evals=evals),
        evaluator_selector="evaluator-id@immutable-version",
    )
    row = _row(expected_answer={"value": "EUR 42"})

    result = await evaluator["scorer"](
        {"data": row.to_datapoint(), "output": "It was EUR 42.", "row": 0}
    )

    assert evaluator["name"] == "answer_correctness@immutable-version"
    assert result.value == "pass"
    assert result.explanation == "The value matches the oracle."
    assert result.pass_ is True
    assert result.raw_output == {
        "trace_id": "runtime-trace",
        "span_id": "runtime-span",
        "evaluator_id": "runtime-evaluator",
    }
    assert evals.calls == [
        {
            "id": "evaluator-id@immutable-version",
            "query": "What was the result?",
            "output": "It was EUR 42.",
            "reference": '{"value": "EUR 42"}',
            "messages": [
                {"role": "user", "content": "Use net revenue."},
                {"role": "assistant", "content": "I will calculate it."},
                {"role": "user", "content": "What was the result?"},
                {"role": "assistant", "content": "It was EUR 42."},
            ],
        }
    ]


def test_orq_evaluator_versions_have_distinct_scorer_names() -> None:
    client = SimpleNamespace(evals=FakeEvals())

    baseline = orq_evaluator(client=client, evaluator_selector="runtime-id@1.0.0")
    candidate = orq_evaluator(client=client, evaluator_selector="runtime-id@1.0.1")

    assert baseline["name"] == "answer_correctness@1.0.0"
    assert candidate["name"] == "answer_correctness@1.0.1"
    assert baseline["name"] != candidate["name"]


@pytest.mark.asyncio
async def test_orq_evaluator_allows_result_without_runtime_linkage() -> None:
    evals = FakeEvals(
        SimpleNamespace(
            result=SimpleNamespace(value="fail", explanation="Mismatch.", passed=False)
        )
    )
    evaluator = orq_evaluator(
        client=SimpleNamespace(evals=evals),
        evaluator_selector="runtime-id@1.0.0",
    )

    result = await evaluator["scorer"](
        {"data": _row().to_datapoint(), "output": "It was EUR 41."}
    )

    assert result.raw_output is None


@pytest.mark.asyncio
async def test_orq_evaluator_fails_when_sdk_returns_no_result() -> None:
    evals = FakeEvals(SimpleNamespace(result=None))
    evaluator = orq_evaluator(
        client=SimpleNamespace(evals=evals),
        evaluator_selector="evaluator-id@immutable-version",
    )

    with pytest.raises(RuntimeError, match="returned no result"):
        await evaluator["scorer"](
            {"data": _row().to_datapoint(), "output": "It was EUR 42."}
        )


@pytest.mark.asyncio
async def test_orq_evaluator_propagates_sdk_errors() -> None:
    sdk_error = ConnectionError("SDK unavailable")
    evaluator = orq_evaluator(
        client=SimpleNamespace(evals=FakeEvals(error=sdk_error)),
        evaluator_selector="evaluator-id@immutable-version",
    )

    with pytest.raises(ConnectionError) as raised:
        await evaluator["scorer"](
            {"data": _row().to_datapoint(), "output": "It was EUR 42."}
        )

    assert raised.value is sdk_error


@pytest.mark.asyncio
async def test_orq_evaluator_routes_non_applicability_without_sdk_call() -> None:
    evals = FakeEvals(error=AssertionError("SDK must not be called"))
    evaluator = orq_evaluator(
        client=SimpleNamespace(evals=evals),
        evaluator_selector="evaluator-id@immutable-version",
    )

    result = await evaluator["scorer"](
        {"data": _row(expected_answer=None).to_datapoint(), "output": "No answer."}
    )

    assert result.value == "not_applicable"
    assert result.pass_ is None
    assert result.explanation == "No expected answer/oracle is available."
    assert evals.calls == []


def test_orq_evaluator_requires_versioned_selector() -> None:
    with pytest.raises(ValueError, match="id@version"):
        orq_evaluator(
            client=SimpleNamespace(evals=FakeEvals()),
            evaluator_selector="mutable-evaluator-id",
        )
