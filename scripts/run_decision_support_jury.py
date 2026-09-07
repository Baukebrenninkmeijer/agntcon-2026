#!/usr/bin/env python3
"""Run the decision-support jury against stored responses only."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from evaluatorq.contracts import (
    EVAL_ERROR_RAW_OUTPUT_KEY,
    JURY_RAW_OUTPUT_KEY,
    JuryResult,
)
from pydantic import ValidationError

from analytics_chatbot.evaluation_ops import (
    DEFAULT_JUDGES,
    AtomicJudge,
    TraceBackedEvaluationRow,
    build_atomic_evaluator,
    run_trace_evaluation,
)
from analytics_chatbot.evaluation_ops.simulation_artifacts import load_simulation_replay

EXPECTED_JUDGES = 3
EXPECTED_REPETITIONS = 3
EVALUATOR_NAME = AtomicJudge.DECISION_SUPPORT_QUALITY.value
EXPERIMENT_PATH = "pydata2026"
V4_CASE_PREFIX = "sphere-stakeholder--v4-"
_FINGERPRINT_PATTERN = re.compile(r"[0-9a-f]{64}")
_JURY_RESULT_FIELDS = frozenset(
    {
        "judges_configured",
        "judges_succeeded",
        "judges_failed",
        "replacements_used",
        "tie",
        "inconclusive",
        "votes",
        "stats",
        "raw_agreement",
    }
)
_JURY_VOTE_FIELDS = frozenset(
    {
        "model",
        "replacement",
        "success",
        "abstained",
        "value",
        "explanation",
        "error",
        "repetitions",
        "repetitions_failed",
    }
)
_JURY_REPETITION_FIELDS = frozenset({"value", "explanation"})


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
        "--case-id",
        action="append",
        help=(
            "Run only this development case ID. Repeat for a bounded smoke run; "
            "omit to run the complete corpus."
        ),
    )
    parser.add_argument(
        "--approve-calls",
        action="store_true",
        help="Explicitly approve the printed number of paid jury model calls.",
    )
    return parser


def expected_calls(row_count: int) -> int:
    return row_count * EXPECTED_JUDGES * EXPECTED_REPETITIONS


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    try:
        cases_path = Path(args.cases).expanduser().resolve(strict=True)
        results_path = Path(args.results).expanduser().resolve(strict=True)
    except OSError as error:
        raise JuryReplayError(f"input path cannot be resolved: {error}") from error
    if not cases_path.is_file() or not results_path.is_file():
        raise JuryReplayError("cases and results paths must be files")

    output_argument = Path(args.output).expanduser()
    output_exists = output_argument.exists() or output_argument.is_symlink()
    try:
        output_path = output_argument.resolve(strict=output_exists)
    except OSError as error:
        raise JuryReplayError(f"output path cannot be resolved safely: {error}") from error
    for input_path in (cases_path, results_path):
        aliases_input = output_path == input_path
        if output_exists and not aliases_input:
            try:
                aliases_input = output_argument.samefile(input_path)
            except OSError:
                aliases_input = False
        if aliases_input:
            raise JuryReplayError("output path must not alias the cases or results input")
    if output_exists:
        raise JuryReplayError(f"output already exists; refusing to overwrite: {output_argument}")
    try:
        output_parent = output_path.parent.resolve(strict=True)
    except OSError as error:
        raise JuryReplayError(f"output parent cannot be resolved: {error}") from error
    if not output_parent.is_dir():
        raise JuryReplayError("output parent must be an existing directory")
    return cases_path, results_path, output_parent / output_path.name


def _validate_v4_samples(corpus: Any) -> list[Any]:
    if corpus.rejected or corpus.duplicates:
        raise JuryReplayError("v4 replay must not contain rejected or duplicate observations")
    samples = list(corpus.samples)
    if not samples:
        raise JuryReplayError("v4 replay contains no accepted observations")

    seen: set[tuple[str, str]] = set()
    for sample in samples:
        row = sample.row
        if not isinstance(row, TraceBackedEvaluationRow):
            raise JuryReplayError("v4 replay sample must contain a trace-backed row")
        if not row.case_id.startswith(V4_CASE_PREFIX):
            raise JuryReplayError("decision-support replay requires a v4 Sphere case ID")
        if row.decision_context is None:
            raise JuryReplayError("decision-support replay requires decision_context")
        if row.evaluation_split not in {"dev", "test"}:
            raise JuryReplayError("decision-support replay requires a dev/test split")
        if not row.assistant_response:
            raise JuryReplayError("decision-support replay requires a recorded output")
        case_id = str(sample.case_id)
        if case_id != row.case_id:
            raise JuryReplayError("sample case identity does not match its trace-backed row")
        fingerprint = str(sample.transcript_fingerprint)
        if _FINGERPRINT_PATTERN.fullmatch(fingerprint) is None:
            raise JuryReplayError(
                "decision-support replay requires a SHA-256 transcript fingerprint"
            )
        if row.metadata.get("transcript_fingerprint") != fingerprint:
            raise JuryReplayError("sample fingerprint does not match its trace-backed row")
        identity = (case_id, fingerprint)
        if identity in seen:
            raise JuryReplayError("v4 replay contains a duplicate sample identity")
        seen.add(identity)
    return samples


def _select_samples(samples: Sequence[Any], case_ids: Sequence[str] | None) -> list[Any]:
    if not case_ids:
        return list(samples)
    if len(set(case_ids)) != len(case_ids):
        raise JuryReplayError("requested case IDs must be unique")

    by_case_id = {str(sample.case_id): sample for sample in samples}
    selected: list[Any] = []
    for case_id in case_ids:
        sample = by_case_id.get(case_id)
        if sample is None:
            raise JuryReplayError(f"requested case ID is unknown: {case_id}")
        if sample.row.evaluation_split != "dev":
            raise JuryReplayError(
                f"explicit jury smoke rows must be development cases: {case_id}"
            )
        selected.append(sample)
    return selected


def _require_raw_fields(
    value: object,
    *,
    fields: frozenset[str],
    context: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JuryReplayError(
            f"invalid evaluatorq jury record: {context} must be a mapping"
        )
    missing = sorted(fields.difference(value))
    if missing:
        raise JuryReplayError(
            f"invalid evaluatorq jury record: {context} is missing required raw fields: "
            f"{', '.join(missing)}"
        )
    return value


def validate_jury_record(raw_output: object) -> dict[str, Any]:
    if not isinstance(raw_output, dict) or not isinstance(
        raw_output.get(JURY_RAW_OUTPUT_KEY), dict
    ):
        raise JuryReplayError("decision-support score is missing raw_output.jury")
    if EVAL_ERROR_RAW_OUTPUT_KEY in raw_output:
        raise JuryReplayError("decision-support score contains raw_output.evaluation_error")
    jury = raw_output[JURY_RAW_OUTPUT_KEY]

    _require_raw_fields(jury, fields=_JURY_RESULT_FIELDS, context="jury panel")
    raw_votes = jury["votes"]
    if not isinstance(raw_votes, list) or len(raw_votes) != EXPECTED_JUDGES:
        raise JuryReplayError("decision-support jury must retain exactly three votes")
    for vote_index, raw_vote in enumerate(raw_votes):
        vote = _require_raw_fields(
            raw_vote,
            fields=_JURY_VOTE_FIELDS,
            context=f"jury vote {vote_index}",
        )
        repetitions = vote["repetitions"]
        if not isinstance(repetitions, list):
            raise JuryReplayError("each decision-support vote must retain repetitions")
        if vote["success"] and len(repetitions) != EXPECTED_REPETITIONS:
            raise JuryReplayError(
                "each successful decision-support vote must retain three repetitions"
            )
        if not vote["success"] and len(repetitions) > EXPECTED_REPETITIONS:
            raise JuryReplayError(
                "a failed decision-support vote cannot retain more than three repetitions"
            )
        for repetition_index, repetition in enumerate(repetitions):
            _require_raw_fields(
                repetition,
                fields=_JURY_REPETITION_FIELDS,
                context=f"jury repetition {vote_index}:{repetition_index}",
            )
    try:
        typed_jury = JuryResult.model_validate(jury, strict=True)
    except ValidationError as error:
        raise JuryReplayError(f"invalid evaluatorq jury record: {error}") from error

    if typed_jury.judges_configured != EXPECTED_JUDGES:
        raise JuryReplayError("decision-support jury must configure exactly three judges")
    if [vote.model for vote in typed_jury.votes] != list(DEFAULT_JUDGES):
        raise JuryReplayError("decision-support jury must retain the ordered configured models")
    return jury


def _validated_scores(results: Sequence[Any], *, samples: Sequence[Any]) -> list[Any]:
    if len(results) != len(samples):
        raise JuryReplayError(
            f"expected {len(samples)} evaluatorq results, received {len(results)}"
        )

    expected = {
        (sample.case_id, sample.transcript_fingerprint): sample for sample in samples
    }
    validated: dict[tuple[str, str], Any] = {}
    for index, result in enumerate(results):
        if getattr(result, "error", None):
            raise JuryReplayError(f"row {index} contains an evaluatorq error")
        data_point = getattr(result, "data_point", None)
        if data_point is None:
            raise JuryReplayError(f"row {index} is missing its returned data point")
        try:
            returned_row = TraceBackedEvaluationRow.from_datapoint(data_point)
        except (TypeError, ValueError, ValidationError) as error:
            raise JuryReplayError(f"row {index} returned an invalid data point") from error
        fingerprint = str(returned_row.metadata.get("transcript_fingerprint") or "")
        identity = (returned_row.case_id, fingerprint)
        if identity in validated:
            raise JuryReplayError(f"duplicate returned result identity: {identity}")
        sample = expected.get(identity)
        if sample is None:
            raise JuryReplayError(f"row {index} returned an unknown result identity")
        if returned_row != sample.row:
            raise JuryReplayError(
                f"row {index} returned data point does not match its source row"
            )
        jobs = list(getattr(result, "job_results", None) or [])
        if len(jobs) != 1 or getattr(jobs[0], "error", None):
            raise JuryReplayError(f"row {index} must contain one successful replay job")
        if getattr(jobs[0], "output", None) != sample.row.assistant_response:
            raise JuryReplayError(f"row {index} replay job changed the recorded output")
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
        validated[identity] = score
    if validated.keys() != expected.keys():
        raise JuryReplayError("evaluatorq results did not cover every source row identity")
    return [validated[(sample.case_id, sample.transcript_fingerprint)] for sample in samples]


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
            )
        )
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write("\n".join(records) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, output_path)
        except FileExistsError as error:
            raise JuryReplayError(
                f"output already exists; refusing to overwrite: {output_path}"
            ) from error
        temporary_path.unlink()
        temporary_path = None
        directory_descriptor = os.open(output_path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


async def run(
    args: argparse.Namespace,
    *,
    replay_loader: Callable[..., Any] = load_simulation_replay,
    evaluator_builder: Callable[..., Any] = build_atomic_evaluator,
    evaluation_runner: Callable[..., Any] = run_trace_evaluation,
    printer: Callable[[str], object] = print,
) -> int:
    cases_path, results_path, output_path = _resolve_paths(args)
    corpus = replay_loader(cases_path=cases_path, results_path=results_path)
    samples = _select_samples(
        _validate_v4_samples(corpus),
        getattr(args, "case_id", None),
    )

    row_count = len(samples)
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
    experiment_urls: list[str] = []
    results = await evaluation_runner(
        [sample.row for sample in samples],
        evaluators=[evaluator],
        inference=False,
        experiment_path=EXPERIMENT_PATH,
        print_results=False,
        experiment_url_out=experiment_urls,
    )
    scores = _validated_scores(results, samples=samples)
    _write_results(output_path, samples=samples, scores=scores)
    printer(f"Saved {row_count} complete jury record(s) to {output_path}")
    if experiment_urls:
        printer(f"Experiment: {experiment_urls[-1]}")
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
