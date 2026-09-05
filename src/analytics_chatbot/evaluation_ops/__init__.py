"""Evaluatorq-native evaluation of imported, trace-backed conversations.

The simulation/import layer owns trace retrieval.  This module owns the stable
row contract, rubric-specific evidence projection, applicability routing, and
the single native evaluatorq experiment call.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Sequence
from enum import StrEnum
from typing import Any, Literal

from evaluatorq import DataPoint, EvaluationResult, evaluatorq, job, llm_jury
from evaluatorq.types import DataPointResult, Evaluator, ScorerParameter
from pydantic import BaseModel, ConfigDict, Field, model_validator

from analytics_chatbot.evaluation_ops.hosted_evaluators import orq_evaluator
from analytics_chatbot.evaluation_ops.trace_import import (
    TraceImportError,
    import_orq_trace,
    import_run_audit,
)

SCHEMA_VERSION = "trace-eval-v1"
DEFAULT_JUDGES = (
    "openai/gpt-5.6-luna",
    "groq/qwen/qwen3.8-27b",
    "google-ai/gemini-3.5-flash-lite",
)
VERDICT_LABELS = ["pass", "fail", "not_applicable"]


class AtomicJudge(StrEnum):
    """The independently alignable atomic rubrics."""

    ANSWER_CORRECTNESS = "answer_correctness"
    QUERY_SEMANTICS = "query_semantics"
    EVIDENCE_FAITHFULNESS = "evidence_faithfulness"
    MULTI_TURN_CONSISTENCY = "multi_turn_consistency"


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["system", "user", "assistant", "tool"]
    content: str = Field(min_length=1)


class TraceSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trace_id: str = Field(min_length=1)
    span_ids: list[str] = Field(min_length=1)


class OracleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_answer: str | int | float | bool | dict[str, Any] | None = None
    reference_sql: str | None = None
    query_requirements: list[str] = Field(default_factory=list)


class ToolEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None


class TraceBackedEvaluationRow(BaseModel):
    """Versioned field contract emitted by the trace import adapter.

    The row deliberately retains raw conversation, tools, retrievals, and state
    so each rubric can receive its own evidence slice without depending on a
    lossy OpenResponses conversion or a process-local simulation cache.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["trace-eval-v1"] = SCHEMA_VERSION
    case_id: str = Field(min_length=1)
    evaluation_split: Literal["dev", "test"]
    source: TraceSource | None = None
    conversation: list[ConversationMessage] = Field(min_length=2)
    assistant_response: str = Field(min_length=1)
    oracle: OracleEvidence | None = None
    tool_events: list[ToolEvent] = Field(default_factory=list)
    retrievals: list[Any] = Field(default_factory=list)
    state_before: dict[str, Any] | None = None
    state_after: dict[str, Any] | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def response_must_be_recorded(self) -> TraceBackedEvaluationRow:
        assistant_messages = [
            message.content for message in self.conversation if message.role == "assistant"
        ]
        if not assistant_messages or assistant_messages[-1] != self.assistant_response:
            raise ValueError("assistant_response must equal the final assistant message")
        return self

    def to_datapoint(self) -> DataPoint:
        expected = self.oracle.expected_answer if self.oracle is not None else None
        return DataPoint(
            inputs={
                "trace_evidence": self.model_dump(mode="json"),
                "messages": [message.model_dump(mode="json") for message in self.conversation],
            },
            expected_output=expected,
        )

    @classmethod
    def from_datapoint(cls, point: DataPoint) -> TraceBackedEvaluationRow:
        evidence = point.inputs.get("trace_evidence")
        if not isinstance(evidence, dict):
            raise ValueError("DataPoint.inputs.trace_evidence must be an object")
        return cls.model_validate(evidence)


class _JudgeSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    judge: AtomicJudge
    criterion: str
    applies: Callable[[TraceBackedEvaluationRow], bool]
    project: Callable[[TraceBackedEvaluationRow], dict[str, Any]]
    not_applicable_reason: str


def _conversation(row: TraceBackedEvaluationRow) -> list[dict[str, str]]:
    return [message.model_dump(mode="json") for message in row.conversation]


def _answer_correctness_evidence(row: TraceBackedEvaluationRow) -> dict[str, Any]:
    return {
        "conversation": [
            message.model_dump(mode="json")
            for message in row.conversation
            if message.role != "tool"
        ]
    }


def _query_semantics_evidence(row: TraceBackedEvaluationRow) -> dict[str, Any]:
    assert row.oracle is not None
    return {
        "conversation": _conversation(row),
        "query_calls": [
            event.model_dump(mode="json")
            for event in row.tool_events
            if event.name == "query_sql"
        ],
        "reference_sql": row.oracle.reference_sql,
        "query_requirements": row.oracle.query_requirements,
    }


def _faithfulness_evidence(row: TraceBackedEvaluationRow) -> dict[str, Any]:
    return {
        "conversation": _conversation(row),
        "tool_results": [
            {
                "name": event.name,
                "result": event.result,
                "error": event.error,
            }
            for event in row.tool_events
        ],
        "retrievals": row.retrievals,
    }


def _multi_turn_evidence(row: TraceBackedEvaluationRow) -> dict[str, Any]:
    return {
        "conversation": _conversation(row),
        "state_before": row.state_before,
        "state_after": row.state_after,
        "tool_events": [event.model_dump(mode="json") for event in row.tool_events],
    }


def _has_query_reference(row: TraceBackedEvaluationRow) -> bool:
    return row.oracle is not None and bool(
        row.oracle.reference_sql or row.oracle.query_requirements
    )


def _has_query_call(row: TraceBackedEvaluationRow) -> bool:
    return any(event.name == "query_sql" for event in row.tool_events)


def _has_grounding_evidence(row: TraceBackedEvaluationRow) -> bool:
    return bool(row.retrievals) or any(event.result is not None for event in row.tool_events)


def _is_multi_turn(row: TraceBackedEvaluationRow) -> bool:
    return sum(message.role == "user" for message in row.conversation) >= 2


_SPECS = (
    _JudgeSpec(
        judge=AtomicJudge.ANSWER_CORRECTNESS,
        criterion=(
            "Decide whether the final answer is factually correct relative to the expected "
            "answer. Ignore whether the answer is supported by the recorded evidence; that is "
            "graded separately."
        ),
        applies=lambda row: row.oracle is not None and row.oracle.expected_answer is not None,
        project=_answer_correctness_evidence,
        not_applicable_reason="No expected answer/oracle is available.",
    ),
    _JudgeSpec(
        judge=AtomicJudge.QUERY_SEMANTICS,
        criterion=(
            "Decide whether the executed analytics query implements the user's requested "
            "metric, filters, joins, aggregation, time boundary, and gross/net/refund/cancellation "
            "semantics. Grade the query, not the prose answer."
        ),
        applies=lambda row: _has_query_call(row) and _has_query_reference(row),
        project=_query_semantics_evidence,
        not_applicable_reason="No executed query or semantic query reference is available.",
    ),
    _JudgeSpec(
        judge=AtomicJudge.EVIDENCE_FAITHFULNESS,
        criterion=(
            "Decide whether every factual claim in the final answer is entailed by the recorded "
            "tool results or retrievals. Do not use the expected answer to decide this rubric: a "
            "faithful answer can still be incorrect when its evidence is wrong."
        ),
        applies=_has_grounding_evidence,
        project=_faithfulness_evidence,
        not_applicable_reason="No tool result or retrieval evidence is available.",
    ),
    _JudgeSpec(
        judge=AtomicJudge.MULTI_TURN_CONSISTENCY,
        criterion=(
            "Decide whether the assistant consistently retains and applies constraints, resolved "
            "references, corrections, and authorized state across the multi-turn conversation."
        ),
        applies=_is_multi_turn,
        project=_multi_turn_evidence,
        not_applicable_reason="The conversation contains fewer than two user turns.",
    ),
)


_PROMPT = """# Criterion
{criterion}

# Raw scoped evidence
{{{{input.all_messages}}}}

# Assistant response
{{{{output.response}}}}

# Reference answer (empty when this rubric intentionally does not use one)
{{{{input.expected_output}}}}

Return `pass` or `fail`. `not_applicable` is reserved for the deterministic router.
"""


def _project_datapoint(row: TraceBackedEvaluationRow, spec: _JudgeSpec) -> DataPoint:
    evidence = spec.project(row)
    expected = (
        row.oracle.expected_answer
        if spec.judge is AtomicJudge.ANSWER_CORRECTNESS and row.oracle is not None
        else None
    )
    return DataPoint(
        inputs={
            "evidence": evidence,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(evidence, sort_keys=True, default=str),
                }
            ],
        },
        expected_output=expected,
    )


def build_atomic_evaluator(
    judge: AtomicJudge,
    *,
    judges: Sequence[str] = DEFAULT_JUDGES,
    jury_factory: Callable[..., Evaluator] = llm_jury,
) -> Evaluator:
    """Build one routed evaluatorq jury for an independently selectable rubric."""

    selected_judge = AtomicJudge(judge)
    spec = next(spec for spec in _SPECS if spec.judge is selected_judge)
    jury = jury_factory(
        name=spec.judge.value,
        prompt=_PROMPT.format(criterion=spec.criterion),
        judges=list(judges),
        repetitions=1,
        assignment="all",
        min_successful_judges=2,
        verdict_kind="categorical",
        labels=list(VERDICT_LABELS),
        passing_labels=["pass"],
        aggregator="majority",
        structured_output=True,
    )
    jury_scorer = jury["scorer"]

    async def routed_scorer(params: ScorerParameter) -> EvaluationResult | dict[str, Any]:
        row = TraceBackedEvaluationRow.from_datapoint(params["data"])
        if not spec.applies(row):
            return EvaluationResult(
                value="not_applicable",
                explanation=spec.not_applicable_reason,
                pass_=None,
            )
        projected: ScorerParameter = {
            "data": _project_datapoint(row, spec),
            "output": params["output"],
        }
        if "row" in params:
            projected["row"] = params["row"]
        return await jury_scorer(projected)

    return {"name": spec.judge.value, "scorer": routed_scorer}


def build_atomic_evaluators(
    *,
    judges: Sequence[str] = DEFAULT_JUDGES,
    jury_factory: Callable[..., Evaluator] = llm_jury,
) -> list[Evaluator]:
    """Build four routed evaluatorq juries with a stable categorical verdict space."""

    return [
        build_atomic_evaluator(spec.judge, judges=judges, jury_factory=jury_factory)
        for spec in _SPECS
    ]


@job("trace-backed-response")
async def replay_trace_response(data: DataPoint, _row: int = 0) -> str:
    """Expose the already-observed response as a native evaluatorq job output."""

    return TraceBackedEvaluationRow.from_datapoint(data).assistant_response


NativeRunner = Callable[..., Awaitable[list[DataPointResult]]]


async def run_trace_evaluation(
    rows: Sequence[TraceBackedEvaluationRow],
    *,
    evaluators: list[Evaluator] | None = None,
    experiment_name: str = "analytics-chatbot-trace-evaluation",
    experiment_path: str | None = None,
    native_runner: NativeRunner = evaluatorq,
    datapoint_parallelism: int = 5,
    llm_parallelism: int = 6,
    print_results: bool = True,
    experiment_url_out: list[str] | None = None,
) -> list[DataPointResult]:
    """Score imported rows through evaluatorq's native experiment lifecycle."""

    if not rows:
        raise ValueError("at least one trace-backed row is required")
    if evaluators is not None and not evaluators:
        raise ValueError("at least one evaluator is required when evaluators are provided")
    selected_evaluators = evaluators or [
        build_atomic_evaluator(AtomicJudge.ANSWER_CORRECTNESS)
    ]
    runner_arguments: dict[str, Any] = {
        "data": [row.to_datapoint() for row in rows],
        "evaluators": selected_evaluators,
        "path": experiment_path,
        "inference": False,
        "datapoint_parallelism": datapoint_parallelism,
        "llm_parallelism": llm_parallelism,
        "print_results": print_results,
    }
    if experiment_url_out is not None:
        runner_arguments["_experiment_url_out"] = experiment_url_out
    return await native_runner(
        experiment_name,
        **runner_arguments,
    )


__all__ = [
    "AtomicJudge",
    "DEFAULT_JUDGES",
    "SCHEMA_VERSION",
    "TraceBackedEvaluationRow",
    "TraceImportError",
    "VERDICT_LABELS",
    "build_atomic_evaluator",
    "build_atomic_evaluators",
    "import_orq_trace",
    "import_run_audit",
    "orq_evaluator",
    "replay_trace_response",
    "run_trace_evaluation",
]
