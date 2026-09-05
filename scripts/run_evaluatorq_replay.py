#!/usr/bin/env python3
"""Replay frozen simulation transcripts through pinned hosted evaluators."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

import httpx
from dotenv import load_dotenv

from analytics_chatbot.evaluation_ops import run_trace_evaluation
from analytics_chatbot.evaluation_ops.hosted_evaluators import orq_evaluator
from analytics_chatbot.evaluation_ops.simulation_artifacts import load_simulation_replay
from analytics_chatbot.orq_resources import load_resource_bundle
from analytics_chatbot.orq_sync import OrqSdkGateway

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESOURCES_PATH = REPOSITORY_ROOT / "orq" / "resources"
DEFAULT_CASES_PATH = DEFAULT_RESOURCES_PATH / "datasets" / "simulation-cases-v2.jsonl"
DEFAULT_RESULTS_PATH = REPOSITORY_ROOT / "runs" / "evaluatorq-simulation-v2-20260905.jsonl"
DEFAULT_OUTPUT_PATH = REPOSITORY_ROOT / "runs" / "evaluatorq-correctness-results.jsonl"
EVALUATOR_KEY = "analytics-answer-correctness"
DEFAULT_PROJECT_PATH = "pydata2026"
EXPECTED_SAMPLE_COUNT = 50


class ReplayPreparationError(RuntimeError):
    """Raised when a stored replay cannot be prepared safely."""


class DotenvLoader(Protocol):
    def __call__(self, path: object, *, override: bool) -> object: ...


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay the frozen 50-case simulation with pinned evaluator versions."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Local JSONL destination for validated evaluator scores.",
    )
    parser.add_argument("--resources", type=Path, default=DEFAULT_RESOURCES_PATH)
    parser.add_argument(
        "--evaluator-version",
        action="append",
        required=True,
        metavar="VERSION",
        help="Pinned evaluator version; repeat to compare versions (never 'latest').",
    )
    parser.add_argument(
        "--experiment-name",
        default="analytics-chatbot-stored-simulation-v2",
    )
    parser.add_argument(
        "--project-path",
        default=DEFAULT_PROJECT_PATH,
        help="Orq project/folder path for the uploaded Experiment.",
    )
    parser.add_argument("--datapoint-parallelism", type=_positive_int, default=5)
    parser.add_argument("--llm-parallelism", type=_positive_int, default=6)
    parser.add_argument(
        "--print-results",
        action="store_true",
        help="Print evaluatorq results locally (disabled by default for frozen test data).",
    )
    return parser


def _validate_requested_versions(versions: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(version.strip() for version in versions)
    if not normalized or any(not version for version in normalized):
        raise ReplayPreparationError("At least one explicit evaluator version is required.")
    if any(version.casefold() == "latest" for version in normalized):
        raise ReplayPreparationError("Evaluator version 'latest' is not allowed; pin a version.")
    if len(set(normalized)) != len(normalized):
        raise ReplayPreparationError("Evaluator versions must be distinct.")
    return normalized


def _find_evaluator_id(snapshot: object) -> str:
    matches = [
        evaluator
        for evaluator in getattr(snapshot, "evaluators", ())
        if getattr(evaluator, "key", None) == EVALUATOR_KEY
    ]
    if len(matches) != 1:
        raise ReplayPreparationError(
            f"Expected exactly one hosted evaluator with stable key {EVALUATOR_KEY!r}."
        )
    return str(matches[0].entity_id)


def _available_versions(evals_client: object, evaluator_id: str) -> set[str]:
    available: set[str] = set()
    cursor: str | None = None
    while True:
        page = evals_client.list_versions(
            id=evaluator_id,
            limit=200,
            starting_after=cursor,
        )
        records = list(getattr(page, "data", ()))
        available.update(str(record.version) for record in records)
        if not getattr(page, "has_more", False):
            return available
        if not records:
            raise ReplayPreparationError("Evaluator version pagination returned an empty page.")
        cursor = str(records[-1].id)


def _validate_evaluation_results(
    results: Sequence[Any],
    *,
    expected_rows: int,
    expected_evaluator_names: Sequence[str],
) -> None:
    row_errors = sum(bool(getattr(result, "error", None)) for result in results)
    jobs = [job for result in results for job in (getattr(result, "job_results", None) or [])]
    job_errors = sum(bool(getattr(job, "error", None)) for job in jobs)
    scores = [score for job in jobs for score in (getattr(job, "evaluator_scores", None) or [])]
    evaluator_errors = sum(bool(getattr(score, "error", None)) for score in scores)
    empty_scores = sum(
        value is None or (isinstance(value, str) and not value.strip())
        for score in scores
        for value in [getattr(getattr(score, "score", None), "value", None)]
    )
    expected_score_count = expected_rows * len(expected_evaluator_names)
    actual_names = [str(getattr(score, "evaluator_name", "")) for score in scores]
    expected_names = [name for _ in range(expected_rows) for name in expected_evaluator_names]
    expected_name_counts = Counter(expected_evaluator_names)
    row_job_shape_errors = 0
    row_score_set_errors = 0
    for result in results:
        result_jobs = list(getattr(result, "job_results", None) or [])
        if len(result_jobs) != 1:
            row_job_shape_errors += 1
            continue
        result_score_names = Counter(
            str(getattr(score, "evaluator_name", ""))
            for score in (getattr(result_jobs[0], "evaluator_scores", None) or [])
        )
        if result_score_names != expected_name_counts:
            row_score_set_errors += 1

    failures: list[str] = []
    if len(results) != expected_rows:
        failures.append(f"expected {expected_rows} rows, received {len(results)}")
    if len(jobs) != expected_rows:
        failures.append(f"expected {expected_rows} replay jobs, received {len(jobs)}")
    if len(scores) != expected_score_count:
        failures.append(f"expected {expected_score_count} scores, received {len(scores)}")
    if sorted(actual_names) != sorted(expected_names):
        failures.append("evaluator score names did not match the pinned request")
    if row_job_shape_errors:
        failures.append(f"{row_job_shape_errors} row replay-job shape error(s)")
    if row_score_set_errors:
        failures.append(f"{row_score_set_errors} row score-set error(s)")
    if row_errors:
        failures.append(f"{row_errors} row error(s)")
    if job_errors:
        failures.append(f"{job_errors} job error(s)")
    if evaluator_errors:
        distinct = sorted(
            {
                str(getattr(score, "error", ""))[:200]
                for score in scores
                if getattr(score, "error", None)
            }
        )
        failures.append(f"{evaluator_errors} evaluator error(s): {distinct}")
    if empty_scores:
        failures.append(f"{empty_scores} empty score(s)")
    if failures:
        raise ReplayPreparationError(
            "Evaluatorq replay failed result validation: " + "; ".join(failures)
        )


def _write_local_results(
    output_path: Path,
    *,
    rows: Sequence[Any],
    results: Sequence[Any],
    experiment_url: str | None,
) -> None:
    records: list[str] = []
    for row, result in zip(rows, results, strict=True):
        row_data = row.model_dump(mode="json") if hasattr(row, "model_dump") else dict(row)
        oracle = row_data.get("oracle") or {}
        scores = {
            str(score.evaluator_name): {
                "value": score.score.value,
                "explanation": getattr(score.score, "explanation", None),
                "pass": getattr(score.score, "pass_", None),
            }
            for job in result.job_results
            for score in job.evaluator_scores
        }
        records.append(
            json.dumps(
                {
                    "schema_version": "evaluatorq-replay-joined-v1",
                    "case_id": row_data["case_id"],
                    # Full transcript rides along so the file seeds alignment runs directly.
                    "conversation": row_data.get("conversation"),
                    "transcript_fingerprint": (row_data.get("metadata") or {}).get(
                        "transcript_fingerprint"
                    ),
                    "evaluation_split": row_data["evaluation_split"],
                    "recorded_output": row_data["assistant_response"],
                    "expected_output": oracle.get("expected_answer"),
                    "experiment_url": experiment_url,
                    "scores": scores,
                },
                sort_keys=True,
                default=str,
            )
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text("\n".join(records) + "\n")
    temporary_path.replace(output_path)


async def run(
    args: argparse.Namespace,
    *,
    dotenv_loader: DotenvLoader = load_dotenv,
    gateway_factory: Callable[[str], Any] = OrqSdkGateway,
    bundle_loader: Callable[[Path], Any] = load_resource_bundle,
    replay_loader: Callable[..., Any] = load_simulation_replay,
    scorer_factory: Callable[..., Any] = orq_evaluator,
    evaluation_runner: Callable[..., Any] = run_trace_evaluation,
    async_http_client_factory: Callable[..., Any] = httpx.AsyncClient,
    environ: Mapping[str, str] = os.environ,
    printer: Callable[[str], object] = print,
) -> int:
    versions = _validate_requested_versions(args.evaluator_version)

    dotenv_loader(REPOSITORY_ROOT / ".env", override=True)
    api_key = environ.get("ORQ_API_KEY")
    if not api_key:
        raise ReplayPreparationError("ORQ_API_KEY is missing from the primary checkout .env.")

    bundle = bundle_loader(args.resources)
    gateway = gateway_factory(api_key)
    snapshot = gateway.snapshot(bundle)
    evaluator_id = _find_evaluator_id(snapshot)

    available_versions = _available_versions(gateway.client.evals, evaluator_id)
    missing_versions = [version for version in versions if version not in available_versions]
    if missing_versions:
        missing = ", ".join(missing_versions)
        raise ReplayPreparationError(
            f"Pinned version(s) {missing} do not exist for evaluator key {EVALUATOR_KEY!r}."
        )

    corpus = replay_loader(cases_path=args.cases, results_path=args.results)
    if len(corpus.samples) != EXPECTED_SAMPLE_COUNT:
        raise ReplayPreparationError(
            f"Expected {EXPECTED_SAMPLE_COUNT} replay samples, found {len(corpus.samples)}."
        )

    printer(
        f"Running {len(corpus.samples)} stored replay samples with "
        f"{len(corpus.warnings)} QC warning(s) retained."
    )
    rows = [sample.row for sample in corpus.samples]
    experiment_urls: list[str] = []
    async with async_http_client_factory(timeout=600.0) as evaluator_http_client:
        evaluators = [
            scorer_factory(
                http_client=evaluator_http_client,
                api_key=api_key,
                evaluator_selector=f"{evaluator_id}@{version}",
                scorer_name=f"answer_correctness@{version}",
            )
            for version in versions
        ]
        results = await evaluation_runner(
            rows,
            evaluators=evaluators,
            experiment_name=args.experiment_name,
            experiment_path=args.project_path,
            datapoint_parallelism=args.datapoint_parallelism,
            llm_parallelism=args.llm_parallelism,
            print_results=args.print_results,
            experiment_url_out=experiment_urls,
        )
    _validate_evaluation_results(
        results,
        expected_rows=len(corpus.samples),
        expected_evaluator_names=tuple(f"answer_correctness@{version}" for version in versions),
    )
    _write_local_results(
        args.output,
        rows=rows,
        results=results,
        experiment_url=experiment_urls[-1] if experiment_urls else None,
    )
    printer(f"Saved validated evaluator results to {args.output}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(run(args))
    except ReplayPreparationError as exc:
        raise SystemExit(f"error: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
