# Post-hoc Trace Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retrieve a completed orq trace, invoke an existing orq evaluator against its recorded generation, and persist a local record linking the source trace/span to the separate evaluation trace/span.

**Architecture:** A pure mapper converts hydrated SDK trace spans into the structured evaluator context. An async service owns trace/span resolution and `orq.evals.invoke_async`, while an append-only JSONL ledger records both sets of IDs and the exact normalized context. The Typer CLI exposes the workflow without coupling mapping tests to the network.

**Tech Stack:** Python 3.11+, Pydantic 2, Typer, orq-ai-sdk 4.14.7+, pytest, pytest-asyncio, Ruff

## Global Constraints

- Keep the implementation project-local; do not modify the shared evaluator-alignment skill.
- Retrieve source traces read-only and never write machine verdicts as human annotations.
- Invoke existing evaluators through `orq.evals.invoke_async`; never create, update, or delete evaluators.
- Persist both source IDs and returned evaluation IDs for every successful invocation.
- Preserve repeated invocations as separate ledger entries for stability analysis.
- Fail before invocation when source content cannot be mapped without guessing.
- Never persist or print credentials.
- Keep non-live tests network-free through an injected Orq client.
- Document the capability in `README.md`, `CLAUDE.md`, and `AGENTS.md`.

## File Structure

- Create `src/analytics_chatbot/evaluation.py`: models, pure mapper, ledger, and async service.
- Create `tests/test_evaluation.py`: mapper, ledger, and service behavior.
- Create `tests/test_live_evaluation.py`: opt-in live smoke test.
- Modify `src/analytics_chatbot/cli.py` and `tests/test_cli.py`: `evaluate-trace` command.
- Modify `src/analytics_chatbot/__init__.py`: public exports.
- Modify `pyproject.toml` and `uv.lock`: SDK and async-test dependencies.
- Modify `README.md`; create `CLAUDE.md` and `AGENTS.md`: operating guidance.

---

### Task 1: Normalize trace content into evaluator context

**Files:**
- Create: `src/analytics_chatbot/evaluation.py`
- Create: `tests/test_evaluation.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: a hydrated span represented by an SDK model or `Mapping[str, Any]`.
- Produces: `TraceEvaluationInput` and `map_trace_to_evaluation_context(span: Any) -> TraceEvaluationInput`.

- [ ] **Step 1: Add dependencies**

```bash
uv add 'orq-ai-sdk>=4.14.7'
uv add --dev 'pytest-asyncio>=1.2'
```

Expected: `pyproject.toml` and `uv.lock` resolve successfully.

- [ ] **Step 2: Write failing mapper tests**

Create `tests/test_evaluation.py`:

```python
import pytest

from analytics_chatbot.evaluation import TraceMappingError, map_trace_to_evaluation_context


def test_maps_chat_span_to_canonical_context() -> None:
    span = {
        "trace_id": "source-trace",
        "span_id": "source-span",
        "attributes": {"gen_ai": {
            "input": [{"role": "user", "content": "hi"}],
            "output": {"role": "assistant", "content": "Hello!"},
        }},
    }
    mapped = map_trace_to_evaluation_context(span)
    assert mapped.source_trace_id == "source-trace"
    assert mapped.source_span_id == "source-span"
    assert mapped.context == {
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "Hello!"},
        ],
        "input": {"user_query": "hi"},
        "output": {"response": "Hello!"},
    }


def test_does_not_duplicate_an_existing_final_assistant_message() -> None:
    span = {
        "trace_id": "source-trace",
        "span_id": "source-span",
        "attributes": {"gen_ai": {
            "input": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "Hello!"},
            ],
            "output": {"role": "assistant", "content": "Hello!"},
        }},
    }
    mapped = map_trace_to_evaluation_context(span)
    assert [message["role"] for message in mapped.context["messages"]] == [
        "user", "assistant"
    ]


class FakeSdkSpan:
    def model_dump(self, **_kwargs):
        return {"span": {
            "summary": {"trace_id": "trace-2", "span_id": "span-2"},
            "attributes": {"gen_ai": {
                "input": {
                    "messages": [{"role": "user", "content": "EMEA revenue?"}],
                    "system_instructions": "Use finance data.",
                    "retrievals": ["EMEA revenue is 42."],
                    "expected_output": "42",
                },
                "output": {
                    "response": "EMEA revenue is 42.",
                    "tools_called": [{
                        "name": "query_sql",
                        "arguments": '{"query":"SELECT 42"}',
                        "output": '{"value":42}',
                    }],
                },
            }},
        }}


def test_maps_structured_span_and_optional_fields() -> None:
    mapped = map_trace_to_evaluation_context(FakeSdkSpan())
    assert mapped.context["input"] == {
        "user_query": "EMEA revenue?",
        "system_instructions": "Use finance data.",
        "retrievals": ["EMEA revenue is 42."],
        "expected_output": "42",
    }
    assert mapped.context["output"]["tools_called"][0]["name"] == "query_sql"
    assert mapped.context["messages"][-1]["content"] == "EMEA revenue is 42."


@pytest.mark.parametrize(
    ("gen_ai", "message"),
    [
        ({"input": [], "output": {"content": "answer"}}, "user query"),
        ({"input": [{"role": "user", "content": "question"}]}, "assistant response"),
    ],
)
def test_rejects_missing_required_content(gen_ai, message) -> None:
    span = {
        "trace_id": "bad-trace",
        "span_id": "bad-span",
        "attributes": {"gen_ai": gen_ai},
    }
    with pytest.raises(TraceMappingError, match=message):
        map_trace_to_evaluation_context(span)
```

- [ ] **Step 3: Run tests to verify red**

```bash
uv run pytest tests/test_evaluation.py -v
```

Expected: FAIL because `analytics_chatbot.evaluation` does not exist.

- [ ] **Step 4: Implement the pure mapper**

Create `src/analytics_chatbot/evaluation.py`:

```python
"""Post-hoc evaluation of content recorded in orq traces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict


class TraceMappingError(ValueError):
    """Raised when a trace span cannot be mapped without guessing."""


class TraceEvaluationInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_trace_id: str
    source_span_id: str
    context: dict[str, Any]


def _dump(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json", exclude_none=True)
    raise TraceMappingError(f"unsupported trace span type: {type(value).__name__}")


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        for key in ("content", "text", "response"):
            rendered = _text(value.get(key))
            if rendered:
                return rendered
        return ""
    if isinstance(value, list):
        return "\n".join(filter(None, (_text(item) for item in value))).strip()
    return ""


def _parts(span: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = _dump(span)
    detail = _dump(payload["span"]) if payload.get("span") else payload
    summary = _dump(detail["summary"]) if detail.get("summary") else detail
    attributes = _dump(detail.get("attributes") or payload.get("attributes") or {})
    return summary, attributes


def _messages(raw_input: Any) -> list[dict[str, Any]]:
    candidate = raw_input
    if isinstance(raw_input, Mapping):
        candidate = raw_input.get("messages") or raw_input.get("all_messages") or []
    if not isinstance(candidate, list):
        return []
    return [dict(message) for message in candidate if isinstance(message, Mapping)]


def _latest_user_text(messages: list[dict[str, Any]]) -> str:
    return next(
        (_text(message.get("content")) for message in reversed(messages) if message.get("role") == "user"),
        "",
    )


def _non_empty(target: dict[str, Any], key: str, value: Any) -> None:
    if value not in (None, "", []):
        target[key] = value


def map_trace_to_evaluation_context(span: Any) -> TraceEvaluationInput:
    summary, attributes = _parts(span)
    trace_id = summary.get("trace_id") or _dump(summary.get("context") or {}).get("trace_id")
    span_id = summary.get("span_id") or summary.get("id") or summary.get("_id")
    gen_ai = _dump(attributes.get("gen_ai") or {})
    raw_input = gen_ai.get("input") or {}
    structured_input = _dump(raw_input) if isinstance(raw_input, Mapping) else {}
    raw_output = gen_ai.get("output") or {}
    structured_output = _dump(raw_output) if isinstance(raw_output, Mapping) else {}
    messages = _messages(raw_input)
    query = (
        _latest_user_text(messages)
        or _text(structured_input.get("user_query"))
        or _text(structured_input.get("query"))
        or _text(structured_input.get("input"))
    )
    response = (
        _text(structured_output.get("response"))
        or _text(structured_output.get("content"))
        or _text(raw_output)
    )
    if not trace_id or not span_id:
        raise TraceMappingError("trace span is missing trace_id or span_id")
    if not query:
        raise TraceMappingError("trace span has no textual user query")
    if not response:
        raise TraceMappingError("trace span has no textual assistant response")
    if not messages or messages[-1].get("role") != "assistant" or _text(
        messages[-1].get("content")
    ) != response:
        messages.append({"role": "assistant", "content": response})

    evaluator_input: dict[str, Any] = {"user_query": query}
    _non_empty(evaluator_input, "system_instructions", structured_input.get("system_instructions"))
    _non_empty(evaluator_input, "retrievals", structured_input.get("retrievals"))
    _non_empty(
        evaluator_input,
        "expected_output",
        structured_input.get("expected_output") or structured_input.get("reference"),
    )
    evaluator_output: dict[str, Any] = {"response": response}
    _non_empty(evaluator_output, "tools_called", structured_output.get("tools_called"))
    return TraceEvaluationInput(
        source_trace_id=str(trace_id),
        source_span_id=str(span_id),
        context={"messages": messages, "input": evaluator_input, "output": evaluator_output},
    )
```

- [ ] **Step 5: Run tests and lint to verify green**

```bash
uv run pytest tests/test_evaluation.py -v
uv run ruff check src/analytics_chatbot/evaluation.py tests/test_evaluation.py
```

Expected: both commands PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/analytics_chatbot/evaluation.py tests/test_evaluation.py
git commit -m "feat: map orq traces to evaluator context"
```

---

### Task 2: Persist an append-only linked evaluation ledger

**Files:**
- Modify: `src/analytics_chatbot/evaluation.py`
- Modify: `tests/test_evaluation.py`

**Interfaces:**
- Consumes: normalized invocation context and evaluator result fields.
- Produces: `LinkedEvaluation` and `EvaluationLedger.append(record: LinkedEvaluation) -> Path`.

- [ ] **Step 1: Write the failing ledger test**

Append to `tests/test_evaluation.py`:

```python
import json
from pathlib import Path

from analytics_chatbot.evaluation import EvaluationLedger, LinkedEvaluation


def _linked_record(invocation_id: str) -> LinkedEvaluation:
    return LinkedEvaluation(
        invocation_id=invocation_id,
        recorded_at="2026-09-02T12:00:00Z",
        source_trace_id="source-trace",
        source_span_id="source-span",
        evaluator_id="evaluator-1",
        invocation_context={
            "messages": [],
            "input": {"user_query": "hi"},
            "output": {"response": "hello"},
        },
        evaluation_trace_id=f"evaluation-trace-{invocation_id}",
        evaluation_span_id=f"evaluation-span-{invocation_id}",
        result_type="boolean",
        value=True,
        passed=True,
        explanation="Relevant greeting.",
        status="completed",
    )


def test_ledger_appends_repeated_linked_evaluations(tmp_path: Path) -> None:
    ledger = EvaluationLedger(tmp_path / "evaluations.jsonl")
    path = ledger.append(_linked_record("one"))
    ledger.append(_linked_record("two"))
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["invocation_id"] for row in rows] == ["one", "two"]
    assert rows[0]["source_trace_id"] == "source-trace"
    assert rows[0]["evaluation_trace_id"] == "evaluation-trace-one"
```

- [ ] **Step 2: Run the test to verify red**

```bash
uv run pytest tests/test_evaluation.py::test_ledger_appends_repeated_linked_evaluations -v
```

Expected: FAIL because the ledger types do not exist.

- [ ] **Step 3: Implement the linked record and ledger**

Import `Path` and add below `TraceEvaluationInput` in `evaluation.py`:

```python
class LinkedEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)
    invocation_id: str
    recorded_at: str
    source_trace_id: str
    source_span_id: str
    evaluator_id: str
    invocation_context: dict[str, Any]
    evaluation_trace_id: str
    evaluation_span_id: str
    result_type: str | None = None
    value: Any = None
    passed: bool | None = None
    explanation: str | None = None
    status: str | None = None
    categories: list[str] | None = None
    confidence: float | None = None


class EvaluationLedger:
    """Append-only local persistence for post-hoc evaluator invocations."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, record: LinkedEvaluation) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as destination:
            destination.write(record.model_dump_json(exclude_none=True) + "\n")
            destination.flush()
        return self.path
```

- [ ] **Step 4: Run tests and lint to verify green**

```bash
uv run pytest tests/test_evaluation.py -v
uv run ruff check src/analytics_chatbot/evaluation.py tests/test_evaluation.py
```

Expected: both commands PASS and both repeated records remain present.

- [ ] **Step 5: Commit**

```bash
git add src/analytics_chatbot/evaluation.py tests/test_evaluation.py
git commit -m "feat: persist linked evaluator runs"
```

---

### Task 3: Retrieve the source span and invoke an existing evaluator

**Files:**
- Modify: `src/analytics_chatbot/evaluation.py`
- Modify: `tests/test_evaluation.py`
- Modify: `src/analytics_chatbot/__init__.py`

**Interfaces:**
- Consumes: injected `client.traces.*_async`, `client.evals.invoke_async`, and `EvaluationLedger`.
- Produces: `PosthocTraceEvaluator.evaluate(trace_id: str, evaluator_id: str, span_id: str | None = None) -> LinkedEvaluation`.

- [ ] **Step 1: Write the failing happy-path service test**

Append to `tests/test_evaluation.py`:

```python
from types import SimpleNamespace

from analytics_chatbot.evaluation import PosthocEvaluationError, PosthocTraceEvaluator


class FakeTraces:
    def __init__(self) -> None:
        self.get_span_calls = []

    async def get_async(self, *, trace_id):
        return {"trace": {"trace_id": trace_id, "leading_span_id": "source-span"}}

    async def get_span_async(self, *, trace_id, span_id):
        self.get_span_calls.append((trace_id, span_id))
        return {"span": {
            "summary": {"trace_id": trace_id, "span_id": span_id},
            "attributes": {"gen_ai": {
                "input": [{"role": "user", "content": "hi"}],
                "output": {"role": "assistant", "content": "hello"},
            }},
        }}


class FakeEvals:
    def __init__(self) -> None:
        self.calls = []

    async def invoke_async(self, **kwargs):
        self.calls.append(kwargs)
        return {"result": {
            "type": "boolean",
            "value": True,
            "passed": True,
            "explanation": "Relevant greeting.",
            "trace_id": "evaluation-trace",
            "span_id": "evaluation-span",
            "evaluator_id": kwargs["id"],
            "status": "completed",
        }}


@pytest.mark.asyncio
async def test_service_links_source_and_evaluation_ids(tmp_path: Path) -> None:
    client = SimpleNamespace(traces=FakeTraces(), evals=FakeEvals())
    service = PosthocTraceEvaluator(
        client=client,
        ledger=EvaluationLedger(tmp_path / "evaluations.jsonl"),
        invocation_id_factory=lambda: "invocation-1",
        clock=lambda: "2026-09-02T12:00:00Z",
    )
    record = await service.evaluate("source-trace", "evaluator-1")
    assert client.traces.get_span_calls == [("source-trace", "source-span")]
    assert client.evals.calls[0] == {"id": "evaluator-1", "context": record.invocation_context}
    assert record.source_trace_id == "source-trace"
    assert record.evaluation_trace_id == "evaluation-trace"
    assert record.evaluation_span_id == "evaluation-span"
```

- [ ] **Step 2: Run the test to verify red**

```bash
uv run pytest tests/test_evaluation.py::test_service_links_source_and_evaluation_ids -v
```

Expected: FAIL because the service does not exist.

- [ ] **Step 3: Implement span resolution and evaluator invocation**

Import `Callable`, `UTC`, `datetime`, and `uuid4`, then add:

```python
def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _uuid() -> str:
    return str(uuid4())


class PosthocEvaluationError(RuntimeError):
    """Raised when retrieval or evaluation cannot produce a linked record."""


class PosthocTraceEvaluator:
    def __init__(
        self,
        *,
        client: Any,
        ledger: EvaluationLedger,
        invocation_id_factory: Callable[[], str] = _uuid,
        clock: Callable[[], str] = _utc_now,
    ) -> None:
        self.client = client
        self.ledger = ledger
        self.invocation_id_factory = invocation_id_factory
        self.clock = clock

    async def _resolve_span_id(self, trace_id: str, span_id: str | None) -> str:
        if span_id:
            return span_id
        trace_response = _dump(await self.client.traces.get_async(trace_id=trace_id))
        trace = _dump(trace_response.get("trace") or {})
        resolved = trace.get("leading_span_id") or trace.get("root_span_id") or trace.get("span_id")
        if resolved:
            return str(resolved)
        listed = _dump(await self.client.traces.list_spans_async(trace_id=trace_id))
        candidates = [
            _dump(item)
            for item in listed.get("data") or []
            if _dump(item).get("type")
            in {"span.responses", "span.chat_completion", "generation"}
        ]
        if len(candidates) != 1:
            raise PosthocEvaluationError(
                f"trace {trace_id!r} has {len(candidates)} generation spans; pass --span-id"
            )
        candidate_id = candidates[0].get("span_id")
        if not candidate_id:
            raise PosthocEvaluationError(f"trace {trace_id!r} candidate has no span_id")
        return str(candidate_id)

    async def evaluate(
        self,
        trace_id: str,
        evaluator_id: str,
        span_id: str | None = None,
    ) -> LinkedEvaluation:
        resolved_span_id = await self._resolve_span_id(trace_id, span_id)
        hydrated = await self.client.traces.get_span_async(
            trace_id=trace_id,
            span_id=resolved_span_id,
        )
        mapped = map_trace_to_evaluation_context(hydrated)
        if mapped.source_trace_id != trace_id or mapped.source_span_id != resolved_span_id:
            raise PosthocEvaluationError("hydrated span identity does not match the request")
        invoked = await self.client.evals.invoke_async(id=evaluator_id, context=mapped.context)
        result = _dump(_dump(invoked).get("result") or {})
        evaluation_trace_id = result.get("trace_id")
        evaluation_span_id = result.get("span_id")
        returned_evaluator_id = result.get("evaluator_id") or evaluator_id
        if not evaluation_trace_id or not evaluation_span_id:
            raise PosthocEvaluationError("evaluator response lacks trace_id or span_id")
        if returned_evaluator_id != evaluator_id:
            raise PosthocEvaluationError("evaluator response identity does not match the request")
        record = LinkedEvaluation(
            invocation_id=self.invocation_id_factory(),
            recorded_at=self.clock(),
            source_trace_id=mapped.source_trace_id,
            source_span_id=mapped.source_span_id,
            evaluator_id=evaluator_id,
            invocation_context=mapped.context,
            evaluation_trace_id=str(evaluation_trace_id),
            evaluation_span_id=str(evaluation_span_id),
            result_type=result.get("type"),
            value=result.get("value"),
            passed=result.get("passed"),
            explanation=result.get("explanation"),
            status=result.get("status"),
            categories=result.get("categories"),
            confidence=result.get("confidence"),
        )
        self.ledger.append(record)
        return record
```

- [ ] **Step 4: Add ambiguity and invalid-result tests**

Append:

```python
@pytest.mark.asyncio
async def test_service_requires_explicit_ambiguous_span(tmp_path: Path) -> None:
    class AmbiguousTraces(FakeTraces):
        async def get_async(self, *, trace_id):
            return {"trace": {"trace_id": trace_id}}

        async def list_spans_async(self, *, trace_id):
            return {"data": [
                {"span_id": "one", "type": "span.responses"},
                {"span_id": "two", "type": "span.chat_completion"},
            ]}

    service = PosthocTraceEvaluator(
        client=SimpleNamespace(traces=AmbiguousTraces(), evals=FakeEvals()),
        ledger=EvaluationLedger(tmp_path / "evaluations.jsonl"),
    )
    with pytest.raises(PosthocEvaluationError, match="pass --span-id"):
        await service.evaluate("source-trace", "evaluator-1")


@pytest.mark.asyncio
async def test_service_rejects_result_without_evaluation_ids(tmp_path: Path) -> None:
    class MissingIdsEvals:
        async def invoke_async(self, **kwargs):
            return {"result": {"value": True, "evaluator_id": kwargs["id"]}}

    path = tmp_path / "evaluations.jsonl"
    service = PosthocTraceEvaluator(
        client=SimpleNamespace(traces=FakeTraces(), evals=MissingIdsEvals()),
        ledger=EvaluationLedger(path),
    )
    with pytest.raises(PosthocEvaluationError, match="lacks trace_id or span_id"):
        await service.evaluate("source-trace", "evaluator-1")
    assert not path.exists()
```

- [ ] **Step 5: Export the public types**

Import `EvaluationLedger`, `LinkedEvaluation`, `PosthocTraceEvaluator`,
`TraceEvaluationInput`, and `map_trace_to_evaluation_context` in
`src/analytics_chatbot/__init__.py`, then add those exact names to `__all__`.

- [ ] **Step 6: Run tests and lint to verify green**

```bash
uv run pytest tests/test_evaluation.py -v
uv run ruff check src/analytics_chatbot/evaluation.py src/analytics_chatbot/__init__.py tests/test_evaluation.py
```

Expected: all tests PASS; Ruff has no diagnostics.

- [ ] **Step 7: Commit**

```bash
git add src/analytics_chatbot/evaluation.py src/analytics_chatbot/__init__.py tests/test_evaluation.py
git commit -m "feat: evaluate completed orq traces"
```

---

### Task 4: Expose post-hoc evaluation through the CLI

**Files:**
- Modify: `src/analytics_chatbot/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `PosthocTraceEvaluator.evaluate` and `Settings.runs_path`.
- Produces: `analytics-chatbot evaluate-trace TRACE_ID --evaluator EVALUATOR_ID [--span-id SPAN_ID]`.

- [ ] **Step 1: Write the failing CLI test**

Append to `tests/test_cli.py`:

```python
from analytics_chatbot.evaluation import LinkedEvaluation


def test_evaluate_trace_command_prints_linked_record(monkeypatch) -> None:
    class FakeEvaluator:
        async def evaluate(self, trace_id, evaluator_id, span_id=None):
            assert (trace_id, evaluator_id, span_id) == (
                "source-trace", "evaluator-1", "source-span"
            )
            return LinkedEvaluation(
                invocation_id="invocation-1",
                recorded_at="2026-09-02T12:00:00Z",
                source_trace_id=trace_id,
                source_span_id=span_id,
                evaluator_id=evaluator_id,
                invocation_context={
                    "messages": [],
                    "input": {"user_query": "hi"},
                    "output": {"response": "hello"},
                },
                evaluation_trace_id="evaluation-trace",
                evaluation_span_id="evaluation-span",
                value=True,
            )

    monkeypatch.setattr("analytics_chatbot.cli._build_trace_evaluator", lambda: FakeEvaluator())
    result = runner.invoke(app, [
        "evaluate-trace", "source-trace", "--evaluator", "evaluator-1",
        "--span-id", "source-span",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_trace_id"] == "source-trace"
    assert payload["evaluation_trace_id"] == "evaluation-trace"
```

- [ ] **Step 2: Run the CLI test to verify red**

```bash
uv run pytest tests/test_cli.py::test_evaluate_trace_command_prints_linked_record -v
```

Expected: FAIL because the builder and command do not exist.

- [ ] **Step 3: Add the builder and command**

Import `asyncio`, `Orq`, `EvaluationLedger`, and `PosthocTraceEvaluator` in
`src/analytics_chatbot/cli.py`. Add:

```python
def _build_trace_evaluator() -> PosthocTraceEvaluator:
    settings = Settings()
    if not settings.orq_api_key:
        raise typer.BadParameter("ORQ_API_KEY is required for post-hoc evaluation")
    return PosthocTraceEvaluator(
        client=Orq(api_key=settings.orq_api_key),
        ledger=EvaluationLedger(settings.runs_path / "evaluations.jsonl"),
    )


@app.command("evaluate-trace")
def evaluate_trace(
    trace_id: Annotated[str, typer.Argument(help="Completed source trace ID.")],
    evaluator_id: Annotated[
        str,
        typer.Option("--evaluator", help="Existing orq evaluator ID or versioned ID."),
    ],
    span_id: Annotated[
        str | None,
        typer.Option(help="Explicit source generation span ID."),
    ] = None,
) -> None:
    """Evaluate recorded trace content and persist source/evaluation linkage."""
    record = asyncio.run(
        _build_trace_evaluator().evaluate(trace_id, evaluator_id, span_id)
    )
    typer.echo(record.model_dump_json(indent=2, exclude_none=True))
```

- [ ] **Step 4: Run tests and help to verify green**

```bash
uv run pytest tests/test_cli.py::test_evaluate_trace_command_prints_linked_record -v
uv run analytics-chatbot evaluate-trace --help
```

Expected: test PASSES; help lists the argument and both options.

- [ ] **Step 5: Commit**

```bash
git add src/analytics_chatbot/cli.py tests/test_cli.py
git commit -m "feat: add posthoc trace evaluation command"
```

---

### Task 5: Add opt-in live verification and operating guidance

**Files:**
- Create: `tests/test_live_evaluation.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `CLAUDE.md`
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: the service and CLI from Tasks 3–4.
- Produces: an opt-in live probe and durable instructions for humans and coding agents.

- [ ] **Step 1: Write the opt-in live test**

Create `tests/test_live_evaluation.py`:

```python
import asyncio
import os
from pathlib import Path

import pytest
from orq_ai_sdk import Orq

from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation import EvaluationLedger, PosthocTraceEvaluator


@pytest.mark.live
def test_live_posthoc_evaluation_links_both_traces(tmp_path: Path) -> None:
    if os.getenv("ANALYTICS_CHATBOT_LIVE_EVALUATION") != "1":
        pytest.skip("set ANALYTICS_CHATBOT_LIVE_EVALUATION=1 to invoke an evaluator")
    trace_id = os.environ["ANALYTICS_CHATBOT_LIVE_TRACE_ID"]
    evaluator_id = os.environ["ANALYTICS_CHATBOT_LIVE_EVALUATOR_ID"]
    settings = Settings()
    assert settings.orq_api_key
    service = PosthocTraceEvaluator(
        client=Orq(api_key=settings.orq_api_key),
        ledger=EvaluationLedger(tmp_path / "evaluations.jsonl"),
    )
    record = asyncio.run(service.evaluate(trace_id, evaluator_id))
    assert record.source_trace_id == trace_id
    assert record.evaluator_id == evaluator_id
    assert record.evaluation_trace_id != trace_id
    assert record.evaluation_span_id
```

Change the pytest marker description in `pyproject.toml` to:

```toml
markers = ["live: opt-in tests that call the orq Gateway or evaluator APIs"]
```

- [ ] **Step 2: Verify the live test skips by default**

```bash
uv run pytest tests/test_live_evaluation.py -v
```

Expected: one SKIPPED test and no network request.

- [ ] **Step 3: Document the operator workflow**

Add a `Post-hoc trace evaluation` section to `README.md` containing:

````markdown
## Post-hoc trace evaluation

Evaluate a completed orq trace without rerunning the chatbot:

```bash
uv run analytics-chatbot evaluate-trace SOURCE_TRACE_ID \
  --evaluator EXISTING_EVALUATOR_ID
```

Pass `--span-id SOURCE_SPAN_ID` when a trace has multiple generation spans.
Successful invocations append to `runs/evaluations.jsonl`, preserving the exact
normalized context, source trace/span IDs, evaluator ID, and separate evaluation
trace/span IDs. Repeated entries are intentional stability samples. These are
machine results; human annotations remain separate ground truth.
````

Add this opt-in command under the existing live test documentation:

```bash
ANALYTICS_CHATBOT_LIVE_EVALUATION=1 \
ANALYTICS_CHATBOT_LIVE_TRACE_ID=SOURCE_TRACE_ID \
ANALYTICS_CHATBOT_LIVE_EVALUATOR_ID=EXISTING_EVALUATOR_ID \
uv run pytest tests/test_live_evaluation.py -m live -q
```

- [ ] **Step 4: Create both agent-guidance files**

Create `CLAUDE.md` and `AGENTS.md` with identical content:

```markdown
# Repository Agent Guidance

## Post-hoc orq evaluation

This project evaluates completed orq traces through
`uv run analytics-chatbot evaluate-trace TRACE_ID --evaluator EVALUATOR_ID`.
The implementation is in `src/analytics_chatbot/evaluation.py`; linked results
are appended to `runs/evaluations.jsonl`.

Preserve these semantics:

- Source traces are read-only; evaluator runs have separate trace/span IDs.
- Persist both source and evaluation IDs.
- Invoke stored evaluators with `orq.evals.invoke_async`.
- Preserve repeated evaluations as stability samples.
- Machine results are not human annotations or correctness labels.
- Keep unit tests network-free; live tests require
  `ANALYTICS_CHATBOT_LIVE_EVALUATION=1`.
```

- [ ] **Step 5: Run full non-live verification**

```bash
uv run pytest -m "not live" -q
uv run ruff check .
git diff --check origin/main...
```

Expected: tests PASS, Ruff reports no diagnostics, and Git reports no whitespace errors.

- [ ] **Step 6: Run the authorized live probe**

```bash
ANALYTICS_CHATBOT_LIVE_EVALUATION=1 \
ANALYTICS_CHATBOT_LIVE_TRACE_ID=3eeb24ec7104c4ea2adc05b0f2994b38 \
ANALYTICS_CHATBOT_LIVE_EVALUATOR_ID=01KE75M4Z6AWN5EBRHBSYDF97K \
uv run pytest tests/test_live_evaluation.py -m live -q
```

Expected: PASS with a test-local linked record. If Orq returns an authorization,
retention, or schema error, report the exact response and do not silently replace
the trace or evaluator.

- [ ] **Step 7: Confirm scope and commit**

```bash
git status --short
git diff --stat origin/main...
git add README.md CLAUDE.md AGENTS.md pyproject.toml tests/test_live_evaluation.py
git commit -m "docs: describe linked trace evaluations"
```

Include `uv.lock` in this commit only if Step 1 changed it. Leave the user's
unrelated untracked files untouched.

---

## Completion Check

- Chat-style and structured spans map to canonical evaluator context.
- Missing query/response content and ambiguous span selection fail loudly.
- Stored evaluators are invoked through `orq.evals.invoke_async`.
- `runs/evaluations.jsonl` links both trace/span pairs plus evaluator ID.
- Repeated invocations append instead of overwrite.
- The CLI prints the linked result as JSON.
- Non-live tests and Ruff pass.
- The live probe passes or produces a precisely reported external API blocker.
- `README.md`, `CLAUDE.md`, and `AGENTS.md` describe the provenance boundary.
