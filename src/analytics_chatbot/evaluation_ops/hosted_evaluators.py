"""Evaluatorq scorer adapters for versioned hosted Orq evaluators."""

from __future__ import annotations

import json
from typing import Any

from evaluatorq import EvaluationResult
from evaluatorq.common.llm_limit import llm_slot
from evaluatorq.types import Evaluator, ScorerParameter


def _reference_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str)


def orq_evaluator(
    *,
    http_client: Any,
    api_key: str,
    evaluator_selector: str,
    scorer_name: str | None = None,
    base_url: str = "https://my.orq.ai",
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
        async with llm_slot():
            response = await http_client.post(
                f"{base_url.rstrip('/')}/v3/evaluators/{evaluator_selector}/invoke",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "context": {
                        "input": {
                            "user_query": user_query,
                            "expected_output": _reference_text(row.oracle.expected_answer),
                        },
                        "output": {"response": output},
                        "messages": conversation,
                    }
                },
            )
        response.raise_for_status()
        remote_result = response.json()
        if not isinstance(remote_result, dict):
            raise RuntimeError(
                f"Orq evaluator {evaluator_selector!r} returned a non-object result"
            )
        value = remote_result.get("value")
        if value is None or (isinstance(value, str) and not value.strip()):
            raise RuntimeError(
                f"Orq evaluator {evaluator_selector!r} returned a result without a value"
            )
        raw_output = {
            key: remote_result[key]
            for key in ("trace_id", "span_id", "evaluator_id")
            if remote_result.get(key) is not None
        }
        return EvaluationResult(
            value=value,
            explanation=remote_result.get("explanation"),
            pass_=remote_result.get("passed"),
            raw_output=raw_output or None,
        )

    return {
        "name": scorer_name or f"answer_correctness@{version}",
        "scorer": scorer,
    }


__all__ = ["orq_evaluator"]
