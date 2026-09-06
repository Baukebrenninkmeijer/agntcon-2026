from __future__ import annotations

import json
from importlib import import_module
from typing import Any

import pytest
from evaluatorq import DataPoint, EvaluationResult, llm_jury
from evaluatorq.common.jury import Prediction

from analytics_chatbot.evaluation_ops import (
    AtomicJudge,
    TraceBackedEvaluationRow,
    build_atomic_evaluator,
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
        "decision_context": {
            "stakeholder": "CFO preparing the board narrative",
            "decision": "decide which region needs review",
            "delivery_setting": "one-paragraph board-prep note",
            "communication_need": "lead with the decision-relevant comparison",
        },
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


@pytest.mark.asyncio
async def test_llm_jury_returns_detailed_all_assignment_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verdicts = {
        "openai/model-a": "pass",
        "anthropic/model-b": "pass",
        "google/model-c": "fail",
    }

    async def fake_run_single_judge(*, model: str, **_kwargs: Any) -> Prediction:
        return Prediction(value=verdicts[model], explanation=f"{model} explanation")

    monkeypatch.setattr(
        import_module("evaluatorq.llm_jury"),
        "_run_single_judge",
        fake_run_single_judge,
    )
    evaluator = llm_jury(
        name="decision_support_quality",
        criteria="Does this response support the stated decision?",
        judges=["openai/model-a", "anthropic/model-b", "google/model-c"],
        repetitions=3,
        assignment="all",
        min_successful_judges=2,
        labels=["pass", "fail", "not_applicable"],
        passing_labels=["pass"],
        aggregator="majority",
        client=object(),
    )

    result = await evaluator["scorer"](
        {"data": DataPoint(inputs={"question": "Q"}), "output": "A"}
    )

    assert result.raw_output is not None
    jury = result.raw_output["jury"]
    assert jury["judges_configured"] == 3
    assert jury["judges_succeeded"] == 3
    assert jury["raw_agreement"] == pytest.approx(2 / 3)
    assert [vote["model"] for vote in jury["votes"]] == [
        "openai/model-a",
        "anthropic/model-b",
        "google/model-c",
    ]
    assert all(len(vote["repetitions"]) == 3 for vote in jury["votes"])
    assert all("explanation" in vote for vote in jury["votes"])
    assert all(
        repetition == {
            "value": vote["value"],
            "explanation": f"{vote['model']} explanation",
        }
        for vote in jury["votes"]
        for repetition in vote["repetitions"]
    )


def test_trace_row_round_trips_to_evaluatorq_datapoint() -> None:
    row = _row()

    point = row.to_datapoint()
    restored = TraceBackedEvaluationRow.from_datapoint(point)

    assert restored == row
    assert point.inputs["messages"] == [message.model_dump() for message in row.conversation]
    assert point.expected_output == "EUR 42"
    assert restored.decision_context is not None
    assert restored.decision_context.model_dump(mode="json") == {
        "stakeholder": "CFO preparing the board narrative",
        "decision": "decide which region needs review",
        "delivery_setting": "one-paragraph board-prep note",
        "communication_need": "lead with the decision-relevant comparison",
    }


def test_self_contained_simulation_row_needs_no_trace_source() -> None:
    row = _row(source=None)

    restored = TraceBackedEvaluationRow.from_datapoint(row.to_datapoint())

    assert restored.source is None


@pytest.mark.asyncio
async def test_historic_rows_without_decision_context_skip_the_judge() -> None:
    calls = 0

    def jury_factory(**_kwargs: Any) -> dict[str, Any]:
        async def scorer(_params: dict[str, Any]) -> EvaluationResult:
            nonlocal calls
            calls += 1
            return EvaluationResult(value="pass", explanation="judged", pass_=True)

        return {"name": AtomicJudge.DECISION_SUPPORT_QUALITY.value, "scorer": scorer}

    evaluator = build_atomic_evaluator(
        AtomicJudge.DECISION_SUPPORT_QUALITY,
        jury_factory=jury_factory,
    )
    result = await evaluator["scorer"](
        {
            "data": _row(decision_context=None).to_datapoint(),
            "output": "It was EUR 42.",
            "row": 0,
        }
    )

    assert calls == 0
    assert result.value == "not_applicable"
    assert result.pass_ is None
    assert result.explanation


@pytest.mark.asyncio
async def test_decision_support_judge_receives_exact_reference_free_evidence() -> None:
    captured: dict[str, Any] = {}

    def jury_factory(*, name: str, **kwargs: Any) -> dict[str, Any]:
        captured[name] = {"configuration": kwargs}

        async def scorer(params: dict[str, Any]) -> EvaluationResult:
            captured[name]["params"] = params
            return EvaluationResult(value="pass", explanation="ok", pass_=True)

        return {"name": name, "scorer": scorer}

    evaluator = build_atomic_evaluator(
        AtomicJudge.DECISION_SUPPORT_QUALITY,
        jury_factory=jury_factory,
    )
    replayed_output = "  It was EUR 42.\nRecorded bytes stay intact.  "

    await evaluator["scorer"](
        {"data": _row().to_datapoint(), "output": replayed_output, "row": 7}
    )

    params = captured[AtomicJudge.DECISION_SUPPORT_QUALITY.value]["params"]
    evidence = params["data"].inputs["evidence"]
    row = _row()
    assert evidence == {
        "decision_context": row.decision_context.model_dump(mode="json"),
        "conversation": [message.model_dump(mode="json") for message in row.conversation],
        "tool_events": [event.model_dump(mode="json") for event in row.tool_events],
        "final_response": row.assistant_response,
    }
    assert params["data"].expected_output is None
    assert params["row"] == 7
    assert params["output"].encode() == replayed_output.encode()
    serialized = json.dumps(params["data"].model_dump(exclude_none=True))
    for forbidden in (
        "expected_output",
        "expected_answer",
        "reference_sql",
        "query_requirements",
    ):
        assert forbidden not in serialized


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

    assert [judge.value for judge in AtomicJudge] == ["decision_support_quality"]
    assert len(captured) == 1
    for configuration in captured:
        prompt = configuration["prompt"]
        assert "{{input.all_messages}}" in prompt
        assert "{{output.response}}" in prompt
        assert "{{input.expected_output}}" not in prompt
        assert (
            "Does the response turn the analysis into a clear, appropriately scoped input to "
            "the stakeholder's stated decision, using sound judgment about emphasis, "
            "explanation, caveats, and next steps?"
        ) in prompt
        assert (
            "You have no reference answer or ideal response. Do not recompute the analysis or "
            "grade SQL."
        ) in prompt
        assert (
            "Return not_applicable only when the required decision context is absent or the "
            "criterion itself\ndoes not apply to the request."
        ) in prompt
        assert configuration["judges"] == [
            "openai/model-a",
            "anthropic/model-b",
            "google/model-c",
        ]
        assert configuration["repetitions"] == 3
        assert configuration["labels"] == ["pass", "fail", "not_applicable"]
        assert configuration["passing_labels"] == ["pass"]
        assert configuration["assignment"] == "all"
        assert configuration["aggregator"] == "majority"
        assert configuration["min_successful_judges"] == 2


def test_atomic_evaluator_accepts_repetition_override() -> None:
    captured: dict[str, Any] = {}

    def jury_factory(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"name": kwargs["name"], "scorer": _unused_scorer}

    build_atomic_evaluator(
        AtomicJudge.DECISION_SUPPORT_QUALITY,
        repetitions=5,
        jury_factory=jury_factory,
    )

    assert captured["repetitions"] == 5


@pytest.mark.asyncio
async def test_run_trace_evaluation_replays_recorded_output_without_inference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}
    scored: dict[str, Any] = {}
    experiment_urls: list[str] = []
    recorded = "  It was EUR 42.\nNo regeneration — exact bytes.  "

    async def exploding_job(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("a target/replay job must not run")

    monkeypatch.setattr(
        "analytics_chatbot.evaluation_ops.replay_trace_response",
        exploding_job,
    )

    async def scorer(params: dict[str, Any]) -> EvaluationResult:
        scored.update(params)
        return EvaluationResult(value=True)

    async def native_runner(name: str, **kwargs: Any) -> list[Any]:
        observed.update(name=name, **kwargs)
        assert "jobs" not in kwargs
        output = kwargs["data"][0].inputs["messages"][-1]["content"]
        await kwargs["evaluators"][0]["scorer"](
            {"data": kwargs["data"][0], "output": output, "row": 0}
        )
        return []

    result = await run_trace_evaluation(
        [
            _row(
                conversation=[
                    {"role": "user", "content": "What was EMEA net revenue in Q1?"},
                    {"role": "assistant", "content": recorded},
                ],
                assistant_response=recorded,
            )
        ],
        evaluators=[{"name": "stub", "scorer": scorer}],
        experiment_name="trace-eval-test",
        experiment_path="pydata2026",
        native_runner=native_runner,
        print_results=False,
        experiment_url_out=experiment_urls,
        inference=False,
    )

    assert result == []
    assert observed["name"] == "trace-eval-test"
    assert observed["path"] == "pydata2026"
    assert observed["inference"] is False
    assert observed["_experiment_url_out"] is experiment_urls
    assert scored["output"] == recorded
    assert scored["output"].encode() == recorded.encode()
    assert observed["evaluators"][0]["name"] == "stub"


@pytest.mark.asyncio
async def test_run_trace_evaluation_rejects_target_inference() -> None:
    with pytest.raises(ValueError, match="inference must remain False"):
        await run_trace_evaluation([_row()], inference=True)


@pytest.mark.asyncio
async def test_run_trace_evaluation_defaults_to_decision_support_quality() -> None:
    observed: dict[str, Any] = {}

    async def native_runner(name: str, **kwargs: Any) -> list[Any]:
        observed.update(name=name, **kwargs)
        return []

    await run_trace_evaluation(
        [_row()],
        native_runner=native_runner,
        print_results=False,
    )

    assert [evaluator["name"] for evaluator in observed["evaluators"]] == [
        AtomicJudge.DECISION_SUPPORT_QUALITY.value
    ]


@pytest.mark.asyncio
async def test_run_trace_evaluation_rejects_explicitly_empty_evaluators() -> None:
    async def native_runner(_name: str, **_kwargs: Any) -> list[Any]:
        raise AssertionError("invalid input must fail before evaluatorq runs")

    with pytest.raises(ValueError, match="at least one evaluator"):
        await run_trace_evaluation(
            [_row()],
            evaluators=[],
            native_runner=native_runner,
            print_results=False,
        )


async def _unused_scorer(_params: dict[str, Any]) -> EvaluationResult:
    return EvaluationResult(value=True)
