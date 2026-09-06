#!/usr/bin/env python3
"""Run the decision-support jury against stored responses only."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from analytics_chatbot.evaluation_ops import (
    AtomicJudge,
    build_atomic_evaluator,
    run_trace_evaluation,
)
from analytics_chatbot.evaluation_ops.simulation_artifacts import load_simulation_replay

EXPECTED_JUDGES = 3
EXPECTED_REPETITIONS = 3
EVALUATOR_NAME = AtomicJudge.DECISION_SUPPORT_QUALITY.value


class JuryReplayError(RuntimeError):
    """Raised when a stored replay cannot produce a complete jury artifact."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay observed v4 responses through the decision-support jury."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--approve-calls",
        action="store_true",
        help="Explicitly approve the printed number of paid jury model calls.",
    )
    return parser


def expected_calls(row_count: int) -> int:
    return row_count * EXPECTED_JUDGES * EXPECTED_REPETITIONS


def validate_jury_record(raw_output: object) -> dict[str, Any]:
    if not isinstance(raw_output, dict) or not isinstance(raw_output.get("jury"), dict):
        raise JuryReplayError("decision-support score is missing raw_output.jury")
    jury = raw_output["jury"]
    votes = jury.get("votes")
    if not isinstance(votes, list) or len(votes) != EXPECTED_JUDGES:
        raise JuryReplayError("decision-support jury must retain exactly three votes")
    if any(
        not isinstance(vote, Mapping)
        or not isinstance(vote.get("repetitions"), list)
        or len(vote["repetitions"]) != EXPECTED_REPETITIONS
        for vote in votes
    ):
        raise JuryReplayError("each decision-support vote must retain three repetitions")
    return jury


def _validated_scores(results: Sequence[Any], *, expected_rows: int) -> list[Any]:
    if len(results) != expected_rows:
        raise JuryReplayError(
            f"expected {expected_rows} evaluatorq results, received {len(results)}"
        )

    validated: list[Any] = []
    for index, result in enumerate(results):
        if getattr(result, "error", None):
            raise JuryReplayError(f"row {index} contains an evaluatorq error")
        jobs = list(getattr(result, "job_results", None) or [])
        if len(jobs) != 1 or getattr(jobs[0], "error", None):
            raise JuryReplayError(f"row {index} must contain one successful replay job")
        scores = list(getattr(jobs[0], "evaluator_scores", None) or [])
        if len(scores) != 1:
            raise JuryReplayError(
                f"row {index} must contain exactly one decision-support score"
            )
        evaluator_score = scores[0]
        if str(getattr(evaluator_score, "evaluator_name", "")) != EVALUATOR_NAME:
            raise JuryReplayError(
                f"row {index} score must be named {EVALUATOR_NAME!r}"
            )
        if getattr(evaluator_score, "error", None):
            raise JuryReplayError(f"row {index} contains a decision-support evaluator error")
        score = getattr(evaluator_score, "score", None)
        if score is None:
            raise JuryReplayError(f"row {index} is missing its decision-support score")
        validate_jury_record(getattr(score, "raw_output", None))
        validated.append(score)
    return validated


def _write_results(
    output_path: Path,
    *,
    samples: Sequence[Any],
    scores: Sequence[Any],
) -> None:
    records: list[str] = []
    for sample, score in zip(samples, scores, strict=True):
        row = sample.row
        decision_context = row.decision_context
        jury = validate_jury_record(score.raw_output)
        records.append(
            json.dumps(
                {
                    "schema_version": "decision-support-jury-v1",
                    "case_id": sample.case_id,
                    "evaluation_split": row.evaluation_split,
                    "transcript_fingerprint": sample.transcript_fingerprint,
                    "decision_context": (
                        decision_context.model_dump(mode="json")
                        if decision_context is not None
                        else None
                    ),
                    "recorded_output": row.assistant_response,
                    "value": score.value,
                    "explanation": score.explanation,
                    "pass": score.pass_,
                    "jury": jury,
                },
                sort_keys=True,
                default=str,
            )
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text("\n".join(records) + "\n", encoding="utf-8")
    temporary_path.replace(output_path)


async def run(
    args: argparse.Namespace,
    *,
    replay_loader: Callable[..., Any] = load_simulation_replay,
    evaluator_builder: Callable[..., Any] = build_atomic_evaluator,
    evaluation_runner: Callable[..., Any] = run_trace_evaluation,
    printer: Callable[[str], object] = print,
) -> int:
    corpus = replay_loader(cases_path=args.cases, results_path=args.results)
    if corpus.rejected or corpus.duplicates:
        raise JuryReplayError(
            "v4 replay must not contain rejected or duplicate observations"
        )
    if not corpus.samples:
        raise JuryReplayError("v4 replay contains no accepted observations")

    row_count = len(corpus.samples)
    budget = expected_calls(row_count)
    budget_text = (
        f"{row_count} rows × {EXPECTED_JUDGES} judges × "
        f"{EXPECTED_REPETITIONS} repetitions = {budget} model calls"
    )
    if not args.approve_calls:
        printer(f"{budget_text}; rerun with --approve-calls to execute.")
        return 0
    printer(f"{budget_text}; approved, executing stored-response replay.")

    evaluator = evaluator_builder(
        AtomicJudge.DECISION_SUPPORT_QUALITY,
        repetitions=EXPECTED_REPETITIONS,
    )
    results = await evaluation_runner(
        [sample.row for sample in corpus.samples],
        evaluators=[evaluator],
        inference=False,
        print_results=False,
    )
    scores = _validated_scores(results, expected_rows=row_count)
    _write_results(args.output, samples=corpus.samples, scores=scores)
    printer(f"Saved {row_count} complete jury record(s) to {args.output}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(run(args))
    except JuryReplayError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
