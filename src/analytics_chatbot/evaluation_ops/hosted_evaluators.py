"""Evaluatorq scorer adapters for versioned hosted Orq evaluators."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from evaluatorq import EvaluationResult
from evaluatorq.common.llm_limit import llm_slot
from evaluatorq.types import Evaluator, ScorerParameter


def _reference_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str)


class _Retryable(RuntimeError):
    """A 5xx the evaluator route returned; retried before surfacing."""


def orq_evaluator(
    *,
    http_client: Any,
    api_key: str,
    evaluator_selector: str,
    scorer_name: str | None = None,
    base_url: str = "https://my.orq.ai",
    attempts: int = 3,
    retry_delay: float = 2.0,
) -> Evaluator:
    """Build an answer-correctness scorer backed by one immutable Orq version."""

    evaluator_id, separator, version = evaluator_selector.partition("@")
    if not separator or not evaluator_id or not version or "@" in version:
        raise ValueError("evaluator_selector must be an immutable id@version selector")

    async def scorer(params: ScorerParameter) -> EvaluationResult:
        from analytics_chatbot.evaluation_ops import TraceBackedEvaluationRow

        row = TraceBackedEvaluationRow.from_datapoint(params["data"])
        output = params["output"]
        if not isinstance(output, str):
            raise TypeError("answer-correctness evaluation requires a string output")
        # Reference-free judge: the full ordered conversation, tool turns included, is the
        # only evidence. The oracle is deliberately withheld so alignment can grade against it.
        conversation = [message.model_dump(mode="json") for message in row.conversation]
        user_query = next(
            message.content for message in reversed(row.conversation) if message.role == "user"
        )
        payload = {
            "context": {
                "input": {
                    "user_query": user_query,
                    "all_messages": json.dumps(conversation, ensure_ascii=False),
                },
                "output": {"response": output},
                "messages": conversation,
            }
        }
        # A single transient provider failure must not poison a 50-row run: the replay
        # validator rejects any empty score, so retry 5xx/transport errors a few times.
        for attempt in range(1, attempts + 1):
            try:
                async with llm_slot():
                    response = await http_client.post(
                        f"{base_url.rstrip('/')}/v3/evaluators/{evaluator_selector}/invoke",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                if getattr(response, "status_code", 200) >= 500 and attempt < attempts:
                    raise _Retryable(response.text)
                response.raise_for_status()
                break
            except (_Retryable, httpx.TransportError, ConnectionError, TimeoutError):
                if attempt >= attempts:
                    raise
                await asyncio.sleep(retry_delay * attempt)
        remote_result = response.json()
        if not isinstance(remote_result, dict):
            raise RuntimeError(f"Orq evaluator {evaluator_selector!r} returned a non-object result")
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
