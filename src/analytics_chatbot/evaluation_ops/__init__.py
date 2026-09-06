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

    DECISION_SUPPORT_QUALITY = "decision_support_quality"


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


class DecisionContextEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stakeholder: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    delivery_setting: str = Field(min_length=1)
    communication_need: str = Field(min_length=1)


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
    decision_context: DecisionContextEvidence | None = None
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


def _subjective_evidence(row: TraceBackedEvaluationRow) -> dict[str, Any]:
    assert row.decision_context is not None
    return {
        "decision_context": row.decision_context.model_dump(mode="json"),
        "conversation": _conversation(row),
        "tool_events": [event.model_dump(mode="json") for event in row.tool_events],
        "final_response": row.assistant_response,
    }


_SPECS = (
    _JudgeSpec(
        judge=AtomicJudge.DECISION_SUPPORT_QUALITY,
        criterion=(
            "Does the response turn the analysis into a clear, appropriately scoped input to "
            "the stakeholder's stated decision, using sound judgment about emphasis, "
            "explanation, caveats, and next steps?\n\n"
            "A response passes when it:\n\n"
            "- foregrounds the result or comparison that matters to the stated decision;\n"
            "- distinguishes observed evidence from interpretation;\n"
            "- includes assumptions or caveats that could materially change the decision;\n"
            "- gives enough explanation for the stated stakeholder and setting without "
            "obscuring the answer;\n"
            "- recommends an action only when explicitly asked, and keeps that recommendation "
            "within the evidence.\n\n"
            "A response fails when it materially impairs the decision by dumping results without "
            "a takeaway, burying the relevant result in SQL or secondary detail, adding generic "
            "business advice, claiming a cause or implication the evidence does not support, "
            "omitting decision-changing uncertainty, or making an unsolicited prescriptive "
            "recommendation.\n\n"
            "The evaluator does not independently recompute the answer or grade SQL semantics. "
            "A factual issue matters only when it is visible in the supplied conversation and "
            "makes the decision support misleading."
        ),
        applies=lambda row: row.decision_context is not None,
        project=_subjective_evidence,
        not_applicable_reason="The required decision context is absent.",
    ),
)


_PROMPT = """# Criterion
{criterion}

# Raw scoped evidence
{{{{input.all_messages}}}}

# Assistant response
{{{{output.response}}}}

You have no reference answer or ideal response. Do not recompute the analysis or grade SQL.
Judge only the named criterion from the stated stakeholder, decision, delivery setting,
conversation, visible execution evidence, and final response. Return pass or fail.
Return not_applicable only when the required decision context is absent or the criterion itself
does not apply to the request.
"""


def _project_datapoint(row: TraceBackedEvaluationRow, spec: _JudgeSpec) -> DataPoint:
    evidence = spec.project(row)
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
    )


def build_atomic_evaluator(
    judge: AtomicJudge,
    *,
    judges: Sequence[str] = DEFAULT_JUDGES,
    repetitions: int = 3,
    jury_factory: Callable[..., Evaluator] = llm_jury,
) -> Evaluator:
    """Build one routed evaluatorq jury for an independently selectable rubric."""

    selected_judge = AtomicJudge(judge)
    spec = next(spec for spec in _SPECS if spec.judge is selected_judge)
    jury = jury_factory(
        name=spec.judge.value,
        prompt=_PROMPT.format(criterion=spec.criterion),
        judges=list(judges),
        repetitions=repetitions,
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
    repetitions: int = 3,
    jury_factory: Callable[..., Evaluator] = llm_jury,
) -> list[Evaluator]:
    """Build the routed decision-support jury with a stable verdict space."""

    return [
        build_atomic_evaluator(
            spec.judge,
            judges=judges,
            repetitions=repetitions,
            jury_factory=jury_factory,
        )
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
    inference: bool = False,
) -> list[DataPointResult]:
    """Score imported rows through evaluatorq's native experiment lifecycle."""

    if inference:
        raise ValueError("trace replay inference must remain False")
    if not rows:
        raise ValueError("at least one trace-backed row is required")
    if evaluators is not None and not evaluators:
        raise ValueError("at least one evaluator is required when evaluators are provided")
    selected_evaluators = evaluators or [
        build_atomic_evaluator(AtomicJudge.DECISION_SUPPORT_QUALITY)
    ]
    runner_arguments: dict[str, Any] = {
        "data": [row.to_datapoint() for row in rows],
        "evaluators": selected_evaluators,
        "path": experiment_path,
        "inference": inference,
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
    "DecisionContextEvidence",
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
