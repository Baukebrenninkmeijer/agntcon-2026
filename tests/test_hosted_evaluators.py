from __future__ import annotations

import asyncio
from typing import Any

import pytest
from evaluatorq.common.llm_limit import llm_concurrency_limit

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


class FakeHttpResponse:
    def __init__(self, payload: Any = None, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error

    def json(self) -> Any:
        return self.payload


class FakeAsyncHttpClient:
    def __init__(self, response: FakeHttpResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    async def post(self, url: str, **kwargs: Any) -> Any:
        self.calls.append({"url": url, **kwargs})
        return self.response


@pytest.mark.asyncio
async def test_orq_evaluator_routes_answer_correctness_and_maps_result() -> None:
    http_client = FakeAsyncHttpClient(
        FakeHttpResponse(
            {
                "value": "pass",
                "explanation": "The value matches the oracle.",
                "passed": True,
                "trace_id": "runtime-trace",
                "span_id": "runtime-span",
                "evaluator_id": "runtime-evaluator",
            }
        )
    )
    evaluator = orq_evaluator(
        http_client=http_client,
        api_key="secret-not-for-output",
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
    assert http_client.calls == [
        {
            "url": "https://my.orq.ai/v3/evaluators/evaluator-id@immutable-version/invoke",
            "headers": {
                "Authorization": "Bearer secret-not-for-output",
                "Content-Type": "application/json",
            },
            "json": {
                "context": {
                    "input": {
                        "user_query": "What was the result?",
                        "expected_output": '{"value": "EUR 42"}',
                    },
                    "output": {"response": "It was EUR 42."},
                    "messages": [
                        {"role": "user", "content": "Use net revenue."},
                        {"role": "assistant", "content": "I will calculate it."},
                        {"role": "user", "content": "What was the result?"},
                        {"role": "assistant", "content": "It was EUR 42."},
                    ],
                }
            },
        }
    ]


def test_orq_evaluator_versions_have_distinct_scorer_names() -> None:
    http_client = FakeAsyncHttpClient(FakeHttpResponse({}))

    baseline = orq_evaluator(
        http_client=http_client,
        api_key="secret",
        evaluator_selector="runtime-id@1.0.0",
    )
    candidate = orq_evaluator(
        http_client=http_client,
        api_key="secret",
        evaluator_selector="runtime-id@1.0.1",
    )

    assert baseline["name"] == "answer_correctness@1.0.0"
    assert candidate["name"] == "answer_correctness@1.0.1"
    assert baseline["name"] != candidate["name"]


@pytest.mark.asyncio
async def test_orq_evaluator_allows_result_without_runtime_linkage() -> None:
    http_client = FakeAsyncHttpClient(
        FakeHttpResponse({"value": "fail", "explanation": "Mismatch.", "passed": False})
    )
    evaluator = orq_evaluator(
        http_client=http_client,
        api_key="secret",
        evaluator_selector="runtime-id@1.0.0",
    )

    result = await evaluator["scorer"](
        {"data": _row().to_datapoint(), "output": "It was EUR 41."}
    )

    assert result.raw_output is None


@pytest.mark.asyncio
async def test_orq_evaluator_fails_when_http_response_has_no_value() -> None:
    http_client = FakeAsyncHttpClient(FakeHttpResponse({"explanation": "No verdict."}))
    evaluator = orq_evaluator(
        http_client=http_client,
        api_key="secret",
        evaluator_selector="evaluator-id@immutable-version",
    )

    with pytest.raises(RuntimeError, match="without a value"):
        await evaluator["scorer"](
            {"data": _row().to_datapoint(), "output": "It was EUR 42."}
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["", "   "])
async def test_orq_evaluator_rejects_blank_string_values(value: str) -> None:
    evaluator = orq_evaluator(
        http_client=FakeAsyncHttpClient(FakeHttpResponse({"value": value})),
        api_key="secret",
        evaluator_selector="evaluator-id@immutable-version",
    )

    with pytest.raises(RuntimeError, match="without a value"):
        await evaluator["scorer"](
            {"data": _row().to_datapoint(), "output": "It was EUR 42."}
        )


@pytest.mark.asyncio
async def test_orq_evaluator_propagates_http_errors() -> None:
    http_error = ConnectionError("HTTP unavailable")
    evaluator = orq_evaluator(
        http_client=FakeAsyncHttpClient(FakeHttpResponse(error=http_error)),
        api_key="secret",
        evaluator_selector="evaluator-id@immutable-version",
    )

    with pytest.raises(ConnectionError) as raised:
        await evaluator["scorer"](
            {"data": _row().to_datapoint(), "output": "It was EUR 42."}
        )

    assert raised.value is http_error


@pytest.mark.asyncio
async def test_orq_evaluator_routes_non_applicability_without_http_call() -> None:
    http_client = FakeAsyncHttpClient(
        FakeHttpResponse(error=AssertionError("HTTP must not be called"))
    )
    evaluator = orq_evaluator(
        http_client=http_client,
        api_key="secret",
        evaluator_selector="evaluator-id@immutable-version",
    )

    result = await evaluator["scorer"](
        {"data": _row(expected_answer=None).to_datapoint(), "output": "No answer."}
    )

    assert result.value == "not_applicable"
    assert result.pass_ is None
    assert result.explanation == "No expected answer/oracle is available."
    assert http_client.calls == []


def test_orq_evaluator_requires_versioned_selector() -> None:
    with pytest.raises(ValueError, match="id@version"):
        orq_evaluator(
            http_client=FakeAsyncHttpClient(FakeHttpResponse({})),
            api_key="secret",
            evaluator_selector="mutable-evaluator-id",
        )


@pytest.mark.asyncio
async def test_orq_evaluator_obeys_evaluatorq_llm_parallelism() -> None:
    active_requests = 0
    maximum_active_requests = 0

    class SlowAsyncHttpClient(FakeAsyncHttpClient):
        async def post(self, url: str, **kwargs: Any) -> Any:
            nonlocal active_requests, maximum_active_requests
            active_requests += 1
            maximum_active_requests = max(maximum_active_requests, active_requests)
            await asyncio.sleep(0.01)
            active_requests -= 1
            return await super().post(url, **kwargs)

    evaluator = orq_evaluator(
        http_client=SlowAsyncHttpClient(FakeHttpResponse({"value": "pass"})),
        api_key="secret",
        evaluator_selector="evaluator-id@immutable-version",
    )
    params = {"data": _row().to_datapoint(), "output": "It was EUR 42."}

    async with llm_concurrency_limit(1):
        await asyncio.gather(evaluator["scorer"](params), evaluator["scorer"](params))

    assert maximum_active_requests == 1
