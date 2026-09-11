#!/usr/bin/env python3
"""Upload the three stored jury prompt versions as one colourable experiment."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Awaitable, Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

from evaluatorq import DataPoint, EvaluationResult, evaluatorq

from analytics_chatbot.evaluation_ops.jury_annotation import analyze_jury

EXPERIMENT_NAME = "decision-support-quality-prompt-comparison"
EXPERIMENT_PATH = "pydata2026"
DESCRIPTION = (
    "Development-only comparison of decision-support jury prompt v1, v2, and v3. "
    "Boolean scores make human alignment, panel consensus, and within-judge stability "
    "colourable in the Orq Experiments view. Replays stored results; zero judge calls."
)
VERSION_FILES = (
    ("Prompt v1 · baseline", "baseline"),
    ("Prompt v2 · human rules", "human_rules"),
    ("Prompt v3 · materiality", "prompt_v3"),
)

EvaluatorRunner = Callable[..., Awaitable[list[Any]]]


class Comparison(NamedTuple):
    data: list[DataPoint]
    jobs: list[Callable[..., Awaitable[dict[str, Any]]]]
    evaluators: list[dict[str, Any]]
    summary: dict[str, Any]
    source_hashes: dict[str, str]


def build_parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[1]
    data = root / "orq/resources/datasets/decision-support-v4"
    parser = argparse.ArgumentParser(
        description="Upload a dev-only, three-version boolean jury comparison to Orq."
    )
    parser.add_argument("--labels", type=Path, default=data / "human-labels-dev-v1.jsonl")
    parser.add_argument("--baseline", type=Path, default=data / "jury-baseline/jury-results.jsonl")
    parser.add_argument(
        "--human-rules",
        type=Path,
        default=data / "jury-human-rules-v1/jury-results.jsonl",
    )
    parser.add_argument(
        "--prompt-v3", type=Path, default=data / "jury-prompt-v3/jury-results.jsonl"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--approve-upload",
        action="store_true",
        help="Approve one hosted evaluatorq upload. No judge models are called.",
    )
    return parser


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"source is not a file: {resolved}")
    rows = []
    for line_number, line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{resolved}:{line_number} must contain an object")
        rows.append(value)
    return rows


def _identity(row: Mapping[str, Any]) -> tuple[str, str]:
    case_id = row.get("case_id")
    fingerprint = row.get("transcript_fingerprint")
    if not isinstance(case_id, str) or not isinstance(fingerprint, str):
        raise ValueError("every row requires case_id and transcript_fingerprint")
    return case_id, fingerprint


def _index(rows: Sequence[dict[str, Any]], *, source: str) -> dict[tuple[str, str], dict[str, Any]]:
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        identity = _identity(row)
        if identity in indexed:
            raise ValueError(f"duplicate identity in {source}: {identity[0]}")
        indexed[identity] = row
    return indexed


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.expanduser().resolve(strict=True).read_bytes()).hexdigest()


def redact_experiment_url(url: str) -> str:
    """Strip workspace slug and hosted identifiers so the tracked receipt carries no IDs.

    The operator still sees the live URL on stdout; only the committed artifact is redacted.
    """

    redacted = re.sub(r"(my\.orq\.ai/)[^/]+/", r"\1<workspace>/", url)
    redacted = re.sub(r"\b01[0-9A-HJKMNP-TV-Z]{24}\b", "<orq-id>", redacted)
    return re.sub(r"(\?runId=)[^&]+", r"\1<run-id>", redacted)


def _version_job(function_name: str, display_name: str) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def version_job(_data: DataPoint, _row: int = 0) -> dict[str, Any]:
        return {"name": display_name, "output": display_name}

    version_job.__name__ = function_name
    return version_job


def _version_result(params: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    output = params.get("output")
    data = params.get("data")
    if not isinstance(output, str) or not isinstance(data, DataPoint):
        raise ValueError("comparison scorer requires a version label and DataPoint")
    versions = data.inputs.get("versions")
    if not isinstance(versions, Mapping) or not isinstance(versions.get(output), Mapping):
        raise ValueError(f"comparison row has no result for {output!r}")
    return output, versions[output]


async def _aligned_with_human(params: Mapping[str, Any]) -> EvaluationResult:
    version, result = _version_result(params)
    passed = result["jury_label"] == result["human_label"]
    return EvaluationResult(
        value=passed,
        explanation=(
            f"{version}: jury={result['jury_label']}; human={result['human_label']}. "
            f"{result['jury_explanation']}"
        ),
    )


async def _panel_consensus(params: Mapping[str, Any]) -> EvaluationResult:
    version, result = _version_result(params)
    passed = bool(result["panel_consensus"])
    return EvaluationResult(
        value=passed,
        explanation=f"{version}: {'consensus' if passed else 'judges disagree'}.",
    )


async def _within_judge_stability(params: Mapping[str, Any]) -> EvaluationResult:
    version, result = _version_result(params)
    passed = bool(result["within_judge_stability"])
    return EvaluationResult(
        value=passed,
        explanation=f"{version}: {'stable' if passed else 'a judge flipped across repetitions'}.",
    )


def load_comparison(args: argparse.Namespace) -> Comparison:
    source_paths = {
        "labels": Path(args.labels),
        "baseline": Path(args.baseline),
        "human_rules": Path(args.human_rules),
        "prompt_v3": Path(args.prompt_v3),
    }
    labels = _index(_load_jsonl(source_paths["labels"]), source="labels")
    if len(labels) != 30 or any(row.get("evaluation_split") != "dev" for row in labels.values()):
        raise ValueError("comparison requires exactly 30 labelled development rows")

    jury_indexes = {
        key: _index(_load_jsonl(source_paths[key]), source=key) for _, key in VERSION_FILES
    }
    full_identity_sets = {frozenset(index) for index in jury_indexes.values()}
    if len(full_identity_sets) != 1 or len(next(iter(full_identity_sets))) != 50:
        raise ValueError("the three jury versions must contain the same 50 identities")
    if any(not set(labels).issubset(index) for index in jury_indexes.values()):
        raise ValueError("every human-labelled identity must exist in every jury version")

    data: list[DataPoint] = []
    summary_versions = {
        display_name: {
            "aligned_with_human": 0,
            "panel_consensus": 0,
            "within_judge_stability": 0,
        }
        for display_name, _ in VERSION_FILES
    }
    for identity, label_row in sorted(labels.items()):
        human_label = label_row.get("label")
        if human_label not in {"pass", "fail"}:
            raise ValueError(f"human label must be binary: {identity[0]}")
        versions: dict[str, dict[str, Any]] = {}
        recorded_output: str | None = None
        for display_name, key in VERSION_FILES:
            jury_row = jury_indexes[key][identity]
            jury_label = jury_row.get("value")
            if jury_label not in {"pass", "fail"}:
                raise ValueError(f"jury aggregate must be binary for comparison: {identity[0]}")
            signals = analyze_jury(jury_row["jury"])
            if (
                signals.mechanical_errors
                or signals.tie
                or signals.abstention
                or signals.inconclusive
            ):
                raise ValueError(f"jury row cannot be represented as boolean: {identity[0]}")
            aligned = jury_label == human_label
            consensus = not signals.panel_disagreement
            stability = not signals.within_judge_wobble
            summary_versions[display_name]["aligned_with_human"] += int(aligned)
            summary_versions[display_name]["panel_consensus"] += int(consensus)
            summary_versions[display_name]["within_judge_stability"] += int(stability)
            versions[display_name] = {
                "jury_label": jury_label,
                "human_label": human_label,
                "jury_explanation": str(jury_row.get("explanation") or ""),
                "panel_consensus": consensus,
                "within_judge_stability": stability,
            }
            output = jury_row.get("recorded_output")
            if not isinstance(output, str) or not output:
                raise ValueError(f"jury row requires recorded_output: {identity[0]}")
            if recorded_output is not None and output != recorded_output:
                raise ValueError(f"recorded output differs between prompt versions: {identity[0]}")
            recorded_output = output
        data.append(
            DataPoint(
                inputs={
                    "case_id": identity[0],
                    "transcript_fingerprint": identity[1],
                    "human_label": human_label,
                    "recorded_output": recorded_output,
                    "versions": versions,
                }
            )
        )

    jobs = [
        _version_job("prompt_v1_baseline", VERSION_FILES[0][0]),
        _version_job("prompt_v2_human_rules", VERSION_FILES[1][0]),
        _version_job("prompt_v3_materiality", VERSION_FILES[2][0]),
    ]
    evaluators = [
        {"name": "aligned_with_human", "scorer": _aligned_with_human},
        {"name": "panel_consensus", "scorer": _panel_consensus},
        {"name": "within_judge_stability", "scorer": _within_judge_stability},
    ]
    return Comparison(
        data=data,
        jobs=jobs,
        evaluators=evaluators,
        summary={"development_rows": len(data), "versions": summary_versions},
        source_hashes={key: _sha256(path) for key, path in source_paths.items()},
    )


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    target = path.expanduser().resolve(strict=False)
    if target.exists() or target.is_symlink():
        raise ValueError(f"output already exists; refusing to overwrite: {target}")
    parent = target.parent.resolve(strict=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


async def run(
    args: argparse.Namespace,
    *,
    evaluator_runner: EvaluatorRunner = evaluatorq,
) -> dict[str, Any] | None:
    comparison = load_comparison(args)
    output = Path(args.output).expanduser().resolve(strict=False)
    if output.exists() or output.is_symlink():
        raise ValueError(f"output already exists; refusing to overwrite: {output}")
    print("30 development rows × 3 prompt versions × 3 boolean evaluators")
    print("270 local boolean scores · 0 judge calls")
    if not args.approve_upload:
        print("Dry run only. Add --approve-upload to create the hosted comparison.")
        return None

    experiment_urls: list[str] = []
    results = await evaluator_runner(
        EXPERIMENT_NAME,
        data=comparison.data,
        jobs=comparison.jobs,
        evaluators=comparison.evaluators,
        datapoint_parallelism=10,
        print_results=True,
        description=DESCRIPTION,
        path=EXPERIMENT_PATH,
        inference=True,
        _experiment_url_out=experiment_urls,
    )
    if len(results) != 30:
        raise RuntimeError(f"expected 30 uploaded comparison rows, received {len(results)}")
    if len(experiment_urls) != 1:
        raise RuntimeError("evaluatorq did not confirm one hosted experiment URL")

    receipt = {
        "schema_version": "decision-support-jury-comparison-v1",
        "experiment_name": EXPERIMENT_NAME,
        "experiment_path": EXPERIMENT_PATH,
        "experiment_url": redact_experiment_url(experiment_urls[0]),
        "development_rows": 30,
        "prompt_versions": 3,
        "boolean_evaluators": 3,
        "local_scores": 270,
        "judge_calls": 0,
        "source_hashes": comparison.source_hashes,
        "summary": comparison.summary,
    }
    _write_json_atomic(output, receipt)
    print(f"Experiment: {experiment_urls[0]}")
    print(f"Receipt: {output}")
    return receipt


def main() -> None:
    asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    main()
