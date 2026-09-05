"""Validate evaluatorq simulation artifacts and normalize them for replay."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from analytics_chatbot.evaluation_ops import (
    ConversationMessage,
    OracleEvidence,
    ToolEvent,
    TraceBackedEvaluationRow,
)


@dataclass(frozen=True)
class SimulationArtifactIssue:
    """A rejected or duplicate raw simulation result."""

    case_id: str
    reasons: list[str]
    transcript_fingerprint: str | None = None


@dataclass(frozen=True)
class SimulationArtifactBatch:
    """Accepted rows plus explicit reasons for every omitted result."""

    rows: list[TraceBackedEvaluationRow]
    rejected: list[SimulationArtifactIssue]
    duplicates: list[SimulationArtifactIssue]


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _as_sequence(value: Any) -> Sequence[Any] | None:
    return value if isinstance(value, Sequence) and not isinstance(value, str | bytes) else None


def _case_id(result: Mapping[str, Any]) -> str:
    metadata = _as_mapping(result.get("metadata")) or {}
    value = metadata.get("datapoint_id")
    return str(value) if value else "unknown"


def _fingerprint(messages: Any) -> str | None:
    sequence = _as_sequence(messages)
    if sequence is None:
        return None
    semantic_messages: list[Any] = []
    for value in sequence:
        if not isinstance(value, Mapping):
            semantic_messages.append(value)
            continue
        message = dict(value)
        message.pop("tool_call_id", None)
        raw_calls = _as_sequence(message.get("tool_calls"))
        if raw_calls is not None:
            calls = []
            for raw_call in raw_calls:
                if not isinstance(raw_call, Mapping):
                    calls.append(raw_call)
                    continue
                call = dict(raw_call)
                call.pop("id", None)
                call.pop("item_id", None)
                calls.append(call)
            message["tool_calls"] = calls
        semantic_messages.append(message)

    payload = json.dumps(semantic_messages, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _json_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return dict(parsed) if isinstance(parsed, Mapping) else None


def _json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _normal_termination(result: Mapping[str, Any]) -> bool:
    value = str(result.get("terminated_by") or "").lower()
    return value not in {"error", "timeout", "max_turns", "exception"}


def _preflight(result: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if result.get("goal_achieved") is not True:
        reasons.append("goal_not_achieved")
    if not _normal_termination(result):
        reasons.append("abnormal_termination")
    if result.get("criteria_verified") is False:
        reasons.append("criteria_not_verified")
    if _as_sequence(result.get("messages")) is None:
        reasons.append("missing_messages")
    return reasons


def _normalize_conversation(
    messages: Sequence[Any],
) -> tuple[list[ConversationMessage], list[ToolEvent], list[str]]:
    conversation: list[ConversationMessage] = []
    calls: dict[str, tuple[str, dict[str, Any]]] = {}
    declared_call_ids: set[str] = set()
    results: dict[str, tuple[str, Any]] = {}
    call_order: list[str] = []
    reasons: list[str] = []
    pending_answer: str | None = None

    def flush_answer() -> None:
        nonlocal pending_answer
        if pending_answer:
            conversation.append(ConversationMessage(role="assistant", content=pending_answer))
        pending_answer = None

    for raw_message in messages:
        message = _as_mapping(raw_message)
        if message is None:
            reasons.append("invalid_message")
            continue
        role = str(message.get("role") or "")
        content = message.get("content")
        text = content if isinstance(content, str) and content.strip() else None

        if role in {"user", "system"}:
            flush_answer()
            if text:
                conversation.append(ConversationMessage(role=role, content=text))
            else:
                reasons.append(f"empty_{role}_message")
            continue

        if role == "assistant":
            flush_answer()
            raw_calls = _as_sequence(message.get("tool_calls")) or []
            for raw_call in raw_calls:
                call = _as_mapping(raw_call)
                function = _as_mapping(call.get("function")) if call else None
                call_id = str(call.get("id") or "") if call else ""
                name = str(function.get("name") or "") if function else ""
                arguments = _json_object(function.get("arguments")) if function else None
                if not call_id or not name:
                    reasons.append("invalid_tool_call")
                    continue
                declared_call_ids.add(call_id)
                if arguments is None:
                    reasons.append(f"invalid_tool_arguments:{call_id}")
                    continue
                if call_id in calls:
                    reasons.append(f"duplicate_tool_call:{call_id}")
                    continue
                calls[call_id] = (name, arguments)
                call_order.append(call_id)
            if text:
                if raw_calls:
                    pending_answer = text
                else:
                    conversation.append(ConversationMessage(role="assistant", content=text))
            continue

        if role == "tool":
            call_id = str(message.get("tool_call_id") or "")
            name = str(message.get("name") or "")
            if not call_id:
                reasons.append("invalid_tool_result")
                continue
            if call_id in results:
                reasons.append(f"duplicate_tool_result:{call_id}")
                continue
            parsed = _json_value(content)
            results[call_id] = (name, parsed)
            if text:
                conversation.append(ConversationMessage(role="tool", content=text))
            else:
                conversation.append(
                    ConversationMessage(role="tool", content=json.dumps(parsed, default=str))
                )
            continue

        reasons.append(f"unsupported_message_role:{role or 'missing'}")

    flush_answer()

    events: list[ToolEvent] = []
    for call_id in call_order:
        if call_id not in calls:
            continue
        if call_id not in results:
            reasons.append(f"unpaired_tool_call:{call_id}")
            continue
        name, arguments = calls[call_id]
        result_name, result = results[call_id]
        if result_name and result_name != name:
            reasons.append(f"tool_name_mismatch:{call_id}")
            continue
        error = None
        if isinstance(result, Mapping) and result.get("ok") is False:
            error_value = result.get("error") or result.get("error_code")
            error = str(error_value) if error_value else "tool call failed"
        events.append(ToolEvent(name=name, arguments=arguments, result=result, error=error))

    for call_id in results.keys() - declared_call_ids:
        reasons.append(f"orphan_tool_result:{call_id}")

    return conversation, events, reasons


def _tool_expectations(case: Mapping[str, Any], events: Sequence[ToolEvent]) -> list[str]:
    names = [event.name for event in events]
    reasons: list[str] = []
    if case.get("oracle") is not None and "query_sql" not in names:
        reasons.append("missing_expected_tool:query_sql")
    state = _as_mapping(case.get("state_expectation"))
    if state and state.get("authorized") is True and "save_insight" not in names:
        reasons.append("missing_expected_tool:save_insight")
    if state and state.get("authorized") is False and "save_insight" in names:
        reasons.append("unexpected_tool:save_insight")
    return reasons


def _oracle(case: Mapping[str, Any]) -> OracleEvidence | None:
    raw = _as_mapping(case.get("oracle"))
    if raw is None:
        return None
    coverage = _as_sequence(case.get("coverage")) or []
    return OracleEvidence(
        expected_answer=raw.get("expected"),
        reference_sql=raw.get("reference_sql"),
        query_requirements=[str(item) for item in coverage],
    )


def _metadata(result: Mapping[str, Any]) -> dict[str, str | int | float | bool | None]:
    raw = _as_mapping(result.get("metadata")) or {}
    usage = _as_mapping(result.get("token_usage")) or {}
    fields: dict[str, Any] = {
        "persona": raw.get("persona"),
        "scenario": raw.get("scenario"),
        "terminated_by": result.get("terminated_by"),
        "goal_completion_score": result.get("goal_completion_score"),
        "criteria_verified": result.get("criteria_verified"),
        "turn_count": result.get("turn_count"),
        "thread_id": result.get("thread_id"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    scalar = str | int | float | bool
    return {
        key: value for key, value in fields.items() if value is None or isinstance(value, scalar)
    }


def normalize_simulation_results(
    results: Iterable[Mapping[str, Any]],
    cases: Iterable[Mapping[str, Any]],
) -> SimulationArtifactBatch:
    """Convert accepted raw evaluatorq results without mutating the source values."""

    case_index: dict[str, Mapping[str, Any]] = {}
    for case in cases:
        case_id = str(case.get("id") or "")
        if not case_id:
            raise ValueError("case definition is missing id")
        if case_id in case_index:
            raise ValueError(f"duplicate case definition: {case_id}")
        case_index[case_id] = case

    rows: list[TraceBackedEvaluationRow] = []
    rejected: list[SimulationArtifactIssue] = []
    duplicates: list[SimulationArtifactIssue] = []
    seen: set[tuple[str, str]] = set()

    for result in results:
        case_id = _case_id(result)
        fingerprint = _fingerprint(result.get("messages"))
        reasons = _preflight(result)
        case = case_index.get(case_id)
        if case is None:
            reasons.append("unknown_case_id")
        if reasons:
            rejected.append(SimulationArtifactIssue(case_id, reasons, fingerprint))
            continue
        assert case is not None
        assert fingerprint is not None

        conversation, events, reasons = _normalize_conversation(result["messages"])
        if not reasons:
            reasons.extend(_tool_expectations(case, events))
        assistant_response = next(
            (message.content for message in reversed(conversation) if message.role == "assistant"),
            None,
        )
        if assistant_response is None:
            reasons.append("missing_final_assistant_response")
        elif not conversation or conversation[-1].role != "assistant":
            reasons.append("final_assistant_not_last")
        if case.get("oracle") is not None and _oracle(case) is None:
            reasons.append("missing_oracle")
        if reasons:
            rejected.append(SimulationArtifactIssue(case_id, reasons, fingerprint))
            continue

        identity = (case_id, fingerprint)
        if identity in seen:
            duplicates.append(SimulationArtifactIssue(case_id, ["exact_duplicate"], fingerprint))
            continue
        seen.add(identity)
        rows.append(
            TraceBackedEvaluationRow(
                case_id=case_id,
                evaluation_split=str(case.get("split")),
                source=None,
                conversation=conversation,
                assistant_response=assistant_response,
                oracle=_oracle(case),
                tool_events=events,
                metadata=_metadata(result),
            )
        )

    return SimulationArtifactBatch(rows=rows, rejected=rejected, duplicates=duplicates)
