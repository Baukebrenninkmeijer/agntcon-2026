#!/usr/bin/env python3
"""Replay frozen simulation transcripts through pinned hosted evaluators."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

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
EVALUATOR_KEY = "analytics-answer-correctness"
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


async def run(
    args: argparse.Namespace,
    *,
    dotenv_loader: DotenvLoader = load_dotenv,
    gateway_factory: Callable[[str], Any] = OrqSdkGateway,
    bundle_loader: Callable[[Path], Any] = load_resource_bundle,
    replay_loader: Callable[..., Any] = load_simulation_replay,
    scorer_factory: Callable[..., Any] = orq_evaluator,
    evaluation_runner: Callable[..., Any] = run_trace_evaluation,
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

    evaluators = [
        scorer_factory(
            client=gateway.client,
            evaluator_selector=f"{evaluator_id}@{version}",
            scorer_name=f"answer_correctness@{version}",
        )
        for version in versions
    ]

    corpus = replay_loader(cases_path=args.cases, results_path=args.results)
    if len(corpus.samples) != EXPECTED_SAMPLE_COUNT:
        raise ReplayPreparationError(
            f"Expected {EXPECTED_SAMPLE_COUNT} replay samples, found {len(corpus.samples)}."
        )

    printer(
        f"Running {len(corpus.samples)} stored replay samples with "
        f"{len(corpus.warnings)} QC warning(s) retained."
    )
    await evaluation_runner(
        [sample.row for sample in corpus.samples],
        evaluators=evaluators,
        experiment_name=args.experiment_name,
        datapoint_parallelism=args.datapoint_parallelism,
        llm_parallelism=args.llm_parallelism,
        print_results=args.print_results,
    )
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(run(args))
    except ReplayPreparationError as exc:
        raise SystemExit(f"error: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
