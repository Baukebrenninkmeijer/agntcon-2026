"""Normalize recorded Orq traces for evaluatorq's no-inference replay path."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from evaluatorq import DataPoint


class TraceImportError(ValueError):
    """Raised when a recorded trace cannot be imported without guessing."""


def _dump(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _dump(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_dump(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _dump(model_dump(mode="json", by_alias=True, exclude_none=True))
    return value


def _json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in '"[{':
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def _nested(mapping: Mapping[str, Any], path: str) -> Any:
    if path in mapping:
        return mapping[path]
    value: Any = mapping
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _span_payload(value: Any) -> dict[str, Any]:
    payload = _dump(value)
    if not isinstance(payload, Mapping):
        raise TraceImportError(f"unsupported trace payload: {type(value).__name__}")
    payload = dict(payload)
    if isinstance(payload.get("span"), Mapping):
        payload = dict(payload["span"])
    summary = payload.get("summary")
    if isinstance(summary, Mapping):
        payload = {**summary, **payload}
        payload.pop("summary", None)
    if payload.get("span_id") is None and payload.get("id") is not None:
        payload["span_id"] = payload["id"]
    return payload


def _trace_spans(value: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = _dump(value)
    if not isinstance(payload, Mapping):
        raise TraceImportError(f"unsupported trace payload: {type(value).__name__}")
    payload = dict(payload)
    wrapper = payload.get("trace")
    if isinstance(wrapper, Mapping):
        payload = {**wrapper, **payload}

    if "spans" not in payload:
        return payload, [_span_payload(payload)]
    raw_spans = payload["spans"]
    if not isinstance(raw_spans, Sequence) or isinstance(raw_spans, str | bytes):
        raise TraceImportError("trace span collection must be a list")
    spans = [_span_payload(span) for span in raw_spans]
    if not spans:
        raise TraceImportError("trace span collection is empty")
    return payload, spans


def _is_evaluator(span: Mapping[str, Any]) -> bool:
    descriptor = " ".join(str(span.get(key, "")).lower() for key in ("type", "name", "operation"))
    if "evaluator" in descriptor or "evaluation" in descriptor:
        return True
    attributes = span.get("attributes")
    return isinstance(attributes, Mapping) and (
        any(str(key).startswith(("gen_ai.evaluation.", "orq.evaluator.")) for key in attributes)
        or _nested(attributes, "gen_ai.evaluation") is not None
        or _nested(attributes, "orq.evaluator") is not None
    )


def _span_id(span: Mapping[str, Any]) -> str | None:
    value = span.get("span_id") or span.get("id")
    return str(value) if value else None


def _parent_id(span: Mapping[str, Any]) -> str | None:
    value = span.get("parent_span_id") or span.get("parent_id")
    if not value and isinstance(span.get("context"), Mapping):
        value = span["context"].get("parent_span_id")
    return str(value) if value else None


def _lineage(span: dict[str, Any], by_id: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result = [span]
    seen = {_span_id(span)}
    parent_id = _parent_id(span)
    while parent_id and parent_id not in seen and parent_id in by_id:
        parent = by_id[parent_id]
        result.append(parent)
        seen.add(parent_id)
        messages: list[dict[str, Any]] = []
        for member in reversed(result):
            _merge_messages(messages, _span_messages(member))
        if (
            any(message.get("role") == "user" for message in messages)
            and _final_output(messages).strip()
        ):
            break
        parent_id = _parent_id(parent)
    result.reverse()
    return result


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("text", "content", "value", "response", "output_text"):
            if key in value:
                rendered = _text(value[key])
                if rendered:
                    return rendered
        return ""
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return "\n".join(part for item in value if (part := _text(item)))
    return ""


def _tool_call(call: Mapping[str, Any]) -> dict[str, Any]:
    function = call.get("function") if isinstance(call.get("function"), Mapping) else call
    call_id = call.get("id") or call.get("call_id") or function.get("id")
    normalized = {
        "id": str(call_id) if call_id is not None else "",
        "type": "function",
        "function": {
            "name": str(function.get("name") or call.get("name") or ""),
            "arguments": function.get("arguments", call.get("arguments")),
        },
    }
    return normalized


def _message(value: Mapping[str, Any], default_role: str | None = None) -> dict[str, Any] | None:
    kind = str(value.get("type", "")).lower()
    if kind in {"function_call", "tool_call"}:
        return {"role": "assistant", "content": None, "tool_calls": [_tool_call(value)]}
    if kind in {"function_call_output", "tool_call_response", "tool_result"}:
        raw_result = value.get("output", value.get("response", value.get("content")))
        content = (
            raw_result if isinstance(raw_result, str) else json.dumps(raw_result, sort_keys=True)
        )
        return {
            "role": "tool",
            "tool_call_id": str(value.get("call_id") or value.get("id") or ""),
            "content": content,
            "_raw_result": raw_result,
        }

    role = value.get("role") or default_role
    if not role:
        return None
    if role == "tool":
        raw_result = value.get("content", value.get("output", value.get("response")))
        content = (
            raw_result if isinstance(raw_result, str) else json.dumps(raw_result, sort_keys=True)
        )
        return {
            "role": "tool",
            "tool_call_id": str(
                value.get("tool_call_id") or value.get("call_id") or value.get("id") or ""
            ),
            "content": content,
            "_raw_result": raw_result,
        }
    message: dict[str, Any] = {"role": str(role)}
    content = value.get("content", value.get("body"))
    parts = value.get("parts")
    if parts is not None:
        content = parts
    rendered = _text(content)
    message["content"] = rendered if rendered else None

    raw_calls = value.get("tool_calls")
    if isinstance(raw_calls, Sequence) and not isinstance(raw_calls, str | bytes):
        calls = [_tool_call(call) for call in raw_calls if isinstance(call, Mapping)]
    else:
        calls = []
    if isinstance(parts, Sequence) and not isinstance(parts, str | bytes):
        calls.extend(
            _tool_call(part)
            for part in parts
            if isinstance(part, Mapping)
            and str(part.get("type", "")).lower() in {"function_call", "tool_call"}
        )
    if calls:
        message["tool_calls"] = calls
    if message["content"] is None and not calls:
        return None
    return message


def _messages(value: Any, default_role: str | None = None) -> list[dict[str, Any]]:
    value = _json_value(value)
    if value is None:
        return []
    if isinstance(value, str):
        return [{"role": default_role, "content": value}] if default_role and value else []
    if isinstance(value, Mapping):
        for key in ("messages", "all_messages", "output"):
            if key in value:
                nested = _messages(value[key], default_role)
                if nested:
                    return nested
        choices = value.get("choices")
        if isinstance(choices, Sequence) and not isinstance(choices, str | bytes):
            result = []
            for choice in choices:
                if isinstance(choice, Mapping):
                    result.extend(_messages(choice.get("message", choice), default_role))
            if result:
                return result
        message = _message(value, default_role)
        return [message] if message else []
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        result = []
        for item in value:
            if isinstance(item, Mapping):
                message = _message(item, default_role)
                if message:
                    result.append(message)
            elif isinstance(item, str) and default_role:
                result.append({"role": default_role, "content": item})
        return result
    return []


def _event_messages(span: Mapping[str, Any]) -> list[dict[str, Any]]:
    events = span.get("events")
    if not isinstance(events, Sequence) or isinstance(events, str | bytes):
        return []
    result = []
    for event in events:
        if not isinstance(event, Mapping):
            continue
        name = str(event.get("name", "")).lower()
        role = next(
            (
                candidate
                for candidate in ("system", "user", "assistant", "tool")
                if candidate in name
            ),
            None,
        )
        if role is None or "message" not in name:
            continue
        body = event.get("body", event.get("attributes", {}))
        if not isinstance(body, Mapping):
            body = {"content": body}
        message = _message(body, role)
        if message:
            result.append(message)
    return result


def _entity_messages(span: Mapping[str, Any], direction: str) -> list[dict[str, Any]]:
    entities = span.get("entities")
    if not isinstance(entities, Sequence) or isinstance(entities, str | bytes):
        return []
    for entity in entities:
        if not isinstance(entity, Mapping):
            continue
        descriptor = str(
            entity.get("name") or entity.get("type") or entity.get("key") or ""
        ).lower()
        if direction in descriptor and "message" in descriptor:
            value = entity.get("value", entity.get("messages", entity.get("data")))
            messages = _messages(value, "user" if direction == "input" else "assistant")
            if messages:
                return messages
    return []


def _span_messages(span: Mapping[str, Any]) -> list[dict[str, Any]]:
    attributes = span.get("attributes") if isinstance(span.get("attributes"), Mapping) else {}
    input_value = _nested(attributes, "gen_ai.input.messages")
    output_value = _nested(attributes, "gen_ai.output.messages")

    nested_input = _nested(attributes, "gen_ai.input")
    nested_output = _nested(attributes, "gen_ai.output")
    if input_value is None and nested_input is not None:
        input_value = (
            nested_input.get("messages", nested_input)
            if isinstance(nested_input, Mapping)
            else nested_input
        )
    if output_value is None and nested_output is not None:
        output_value = (
            nested_output.get("messages", nested_output)
            if isinstance(nested_output, Mapping)
            else nested_output
        )

    direct_input = span.get("input")
    direct_output = span.get("output")
    inputs = (
        _messages(input_value, "user")
        if input_value is not None
        else _messages(direct_input, "user")
    )
    if not inputs:
        inputs = _entity_messages(span, "input") or _event_messages(span)
    outputs = (
        _messages(output_value, "assistant")
        if output_value is not None
        else _messages(direct_output, "assistant")
    )
    if not outputs:
        outputs = _entity_messages(span, "output")
    combined = list(inputs)
    _merge_messages(combined, outputs)
    return combined


def _merge_messages(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> None:
    overlap = min(len(existing), len(incoming))
    while overlap and existing[-overlap:] != incoming[:overlap]:
        overlap -= 1
    existing.extend(incoming[overlap:])


def _final_output(messages: Sequence[Mapping[str, Any]]) -> str:
    for message in reversed(messages):
        if (
            message.get("role") == "assistant"
            and (content := _text(message.get("content"))).strip()
        ):
            return content
    return ""


def _tool_evidence(messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for message in messages:
        calls = message.get("tool_calls")
        if isinstance(calls, Sequence) and not isinstance(calls, str | bytes):
            for call in calls:
                if not isinstance(call, Mapping):
                    continue
                function = (
                    call.get("function") if isinstance(call.get("function"), Mapping) else call
                )
                item = {
                    "call_id": str(call.get("id") or call.get("call_id") or ""),
                    "name": str(function.get("name") or ""),
                    "arguments": function.get("arguments"),
                    "result": None,
                }
                evidence.append(item)
                if item["call_id"]:
                    by_id[item["call_id"]] = item
        if message.get("role") == "tool":
            call_id = str(message.get("tool_call_id") or "")
            result = message.get("_raw_result", message.get("content"))
            if call_id in by_id:
                by_id[call_id]["result"] = result
    return evidence


def _metadata(trace: Mapping[str, Any], span: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for container in (trace, span, span.get("attributes")):
        if not isinstance(container, Mapping):
            continue
        embedded = container.get("metadata")
        if isinstance(embedded, Mapping):
            result.update(embedded)
        for key, value in container.items():
            key = str(key)
            if key.startswith(("metadata.", "orq.metadata.")):
                result[key.split(".")[-1]] = value
    attributes = span.get("attributes")
    if isinstance(attributes, Mapping):
        for key in ("gen_ai.request.model", "gen_ai.response.model"):
            if key in attributes:
                result[key] = attributes[key]
    for key in ("type", "name", "operation", "provider", "model", "start_time", "end_time"):
        if span.get(key) is not None:
            result.setdefault(key, span[key])
    return result


def _identity_value(trace: Mapping[str, Any], span: Mapping[str, Any], *keys: str) -> Any:
    attributes = span.get("attributes") if isinstance(span.get("attributes"), Mapping) else {}
    metadata = _metadata(trace, span)
    for container in (span, attributes, metadata, trace):
        if not isinstance(container, Mapping):
            continue
        for key in keys:
            value = _nested(container, key)
            if value not in (None, ""):
                return value
    return None


def _lineage_identity(
    trace: Mapping[str, Any], lineage: Sequence[Mapping[str, Any]], *keys: str
) -> Any:
    for span in reversed(lineage):
        if (value := _identity_value(trace, span, *keys)) is not None:
            return value
    return None


def _expected_output(lineage: Sequence[Mapping[str, Any]]) -> Any:
    for span in reversed(lineage):
        attributes = span.get("attributes") if isinstance(span.get("attributes"), Mapping) else {}
        for container in (span.get("input"), attributes, span):
            if isinstance(container, Mapping):
                value = container.get("expected_output", container.get("expectedOutput"))
                if value is not None:
                    return value
    return None


def import_run_audit(artifact_path: str | Path) -> DataPoint:
    """Convert an exact local run JSONL artifact into an evaluatorq ``DataPoint``.

    This is the evidence-preserving fallback for hosted traces whose public span
    payload omits messages or tool details. It reads only the recorded artifact and
    never retrieves or reruns a model response.
    """

    path = Path(artifact_path)
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise TraceImportError(
                f"invalid run audit JSON on line {line_number}: {error.msg}"
            ) from error
        if not isinstance(event, Mapping):
            raise TraceImportError(f"run audit line {line_number} is not an object")
        events.append(dict(event))

    started = next((event for event in events if event.get("type") == "run_started"), None)
    finished = next(
        (event for event in reversed(events) if event.get("type") == "run_finished"), None
    )
    if started is None:
        raise TraceImportError("run audit has no run_started event")
    if finished is None or finished.get("status") != "succeeded":
        raise TraceImportError("run audit is not successfully finalized")

    messages: list[dict[str, Any]] = []
    opening = started.get("message")
    if isinstance(opening, str) and opening.strip():
        messages.append({"role": "user", "content": opening})

    latest_response_id: str | None = None
    for event in events:
        event_type = event.get("type")
        if event_type == "gateway_response":
            if event.get("response_id"):
                latest_response_id = str(event["response_id"])
            raw_calls = event.get("function_calls")
            calls = (
                [_tool_call(call) for call in raw_calls if isinstance(call, Mapping)]
                if isinstance(raw_calls, Sequence) and not isinstance(raw_calls, str | bytes)
                else []
            )
            content = event.get("text")
            rendered = content if isinstance(content, str) and content else None
            if calls or rendered:
                message: dict[str, Any] = {"role": "assistant", "content": rendered}
                if calls:
                    message["tool_calls"] = calls
                messages.append(message)
        elif event_type == "tool_call":
            raw_result = event.get("result")
            content = (
                raw_result
                if isinstance(raw_result, str)
                else json.dumps(raw_result, sort_keys=True, default=str)
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(event.get("call_id") or ""),
                    "content": content,
                    "_raw_result": raw_result,
                }
            )

    final_output = _final_output(messages)
    if not any(message.get("role") == "user" for message in messages):
        raise TraceImportError("run audit has no usable user message")
    if not final_output.strip():
        raise TraceImportError("run audit has no usable final assistant message")

    evidence = _tool_evidence(messages)
    clean_messages = [
        {key: value for key, value in message.items() if not key.startswith("_raw_")}
        for message in messages
    ]
    trace_context = (
        dict(started["trace_context"])
        if isinstance(started.get("trace_context"), Mapping)
        else {}
    )
    response_id = finished.get("response_id") or latest_response_id
    source = {
        "run_id": started.get("run_id"),
        "thread_id": started.get("thread_id"),
        "response_id": response_id,
        "actor_id": trace_context.get("identity_id"),
        "case_id": trace_context.get("case_id"),
        "artifact_path": str(path),
    }
    metadata = dict(trace_context)
    metadata.update(
        {
            key: value
            for key, value in finished.items()
            if key not in {"type", "run_id", "thread_id", "response_id"}
        }
    )
    return DataPoint(
        inputs={
            "messages": clean_messages,
            "recorded_output": final_output,
            "tool_evidence": evidence,
            "source": {key: value for key, value in source.items() if value is not None},
            "metadata": metadata,
        }
    )


def import_orq_trace(trace_or_span: Any) -> DataPoint:
    """Convert an Orq trace/span into a native evaluatorq replay ``DataPoint``.

    The returned point is passed directly in evaluatorq's ``data`` sequence with
    ``inference=False``. No target job is called; evaluatorq replays the final assistant
    message already present in ``inputs['messages']``.
    """

    trace, spans = _trace_spans(trace_or_span)
    candidates = [span for span in spans if not _is_evaluator(span)]
    if not candidates:
        raise TraceImportError("trace has no non-evaluator spans")
    by_id = {span_id: span for span in spans if (span_id := _span_id(span))}
    order = {id(span): index for index, span in enumerate(spans)}
    candidates.sort(
        key=lambda span: (
            str(span.get("type", "")).lower() != "trace",
            str(span.get("ended_at") or span.get("end_time") or span.get("started_at") or ""),
            order[id(span)],
        ),
        reverse=True,
    )

    saw_user = False
    saw_output = False
    for selected in candidates:
        lineage = [selected]
        messages = _span_messages(selected)
        if (
            not any(message.get("role") == "user" for message in messages)
            or not _final_output(messages).strip()
        ):
            lineage = _lineage(selected, by_id)
            messages = []
            for span in lineage:
                _merge_messages(messages, _span_messages(span))
        has_user = any(message.get("role") == "user" for message in messages)
        saw_user = saw_user or has_user
        final_output = _final_output(messages)
        saw_output = saw_output or bool(final_output.strip())
        if not has_user or not final_output.strip():
            continue

        evidence = _tool_evidence(messages)
        clean_messages = [
            {key: value for key, value in message.items() if not key.startswith("_raw_")}
            for message in messages
        ]
        trace_id = selected.get("trace_id") or trace.get("trace_id")
        source: dict[str, Any] = {
            "trace_id": str(trace_id) if trace_id is not None else None,
            "span_id": _span_id(selected),
            "session_id": _lineage_identity(
                trace, lineage, "session_id", "session.id", "thread_id"
            ),
            "actor_id": _lineage_identity(
                trace, lineage, "actor_id", "identity_id", "identity", "user.id"
            ),
            "case_id": _lineage_identity(trace, lineage, "case_id"),
        }
        source = {key: value for key, value in source.items() if value is not None}
        lineage_ids = [span_id for span in lineage if (span_id := _span_id(span))]
        if len(lineage_ids) > 1:
            source["lineage_span_ids"] = lineage_ids

        metadata: dict[str, Any] = {}
        for span in lineage:
            metadata.update(_metadata(trace, span))

        return DataPoint(
            inputs={
                "messages": clean_messages,
                "recorded_output": final_output,
                "tool_evidence": evidence,
                "source": source,
                "metadata": metadata,
            },
            expected_output=_expected_output(lineage),
        )

    if not saw_user:
        raise TraceImportError(
            "trace has no usable user message; use the exact local run audit when the public "
            "trace payload omits messages"
        )
    if not saw_output:
        raise TraceImportError(
            "trace has no usable final assistant message; use the exact local run audit when "
            "the public trace payload omits messages"
        )
    raise TraceImportError(
        "trace has no span lineage with a user message and final assistant output"
    )
