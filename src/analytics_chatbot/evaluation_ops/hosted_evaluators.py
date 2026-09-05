"""Evaluatorq scorer adapters for versioned hosted Orq evaluators."""

from __future__ import annotations

import json
from typing import Any

from evaluatorq import EvaluationResult
from evaluatorq.types import Evaluator, ScorerParameter


def _reference_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str)


def orq_evaluator(
    *,
    client: Any,
    evaluator_selector: str,
    scorer_name: str | None = None,
) -> Evaluator:
    """Build an answer-correctness scorer backed by one immutable Orq version."""

    evaluator_id, separator, version = evaluator_selector.partition("@")
    if not separator or not evaluator_id or not version or "@" in version:
        raise ValueError("evaluator_selector must be an immutable id@version selector")

    async def scorer(params: ScorerParameter) -> EvaluationResult:
        from analytics_chatbot.evaluation_ops import TraceBackedEvaluationRow

        row = TraceBackedEvaluationRow.from_datapoint(params["data"])
        if row.oracle is None or row.oracle.expected_answer is None:
            return EvaluationResult(
                value="not_applicable",
                explanation="No expected answer/oracle is available.",
                pass_=None,
            )

        output = params["output"]
        if not isinstance(output, str):
            raise TypeError("answer-correctness evaluation requires a string output")
        conversation = [
            message.model_dump(mode="json")
            for message in row.conversation
            if message.role != "tool"
        ]
        user_query = next(
            message.content for message in reversed(row.conversation) if message.role == "user"
        )
        response = await client.evals.invoke_async(
            id=evaluator_selector,
            query=user_query,
            output=output,
            reference=_reference_text(row.oracle.expected_answer),
            messages=conversation,
        )
        remote_result = response.result
        if remote_result is None:
            raise RuntimeError(
                f"Orq evaluator {evaluator_selector!r} returned no result"
            )
        if remote_result.value is None:
            raise RuntimeError(
                f"Orq evaluator {evaluator_selector!r} returned a result without a value"
            )
        raw_output = {
            key: value
            for key in ("trace_id", "span_id", "evaluator_id")
            if (value := getattr(remote_result, key, None)) is not None
        }
        return EvaluationResult(
            value=remote_result.value,
            explanation=remote_result.explanation,
            pass_=remote_result.passed,
            raw_output=raw_output or None,
        )

    return {
        "name": scorer_name or f"answer_correctness@{version}",
        "scorer": scorer,
    }


__all__ = ["orq_evaluator"]
