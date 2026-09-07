#!/usr/bin/env python3
"""Prepare a human annotation queue from stored decision-support jury results."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from analytics_chatbot.evaluation_ops.jury_annotation import (
    build_annotation_bundle,
    publish_annotation_bundle,
)
from analytics_chatbot.evaluation_ops.simulation_artifacts import load_simulation_replay


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL object stream with line-specific failures."""
    source = Path(path)
    rows = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            message = f"invalid JSONL in {source} on line {line_number}: {error.msg}"
            raise ValueError(message) from error
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record in {source} on line {line_number} is not an object")
        rows.append(value)
    return rows


def prepare(
    cases_path: str | Path,
    results_path: str | Path,
    jury_path: str | Path,
    output_dir: str | Path,
    *,
    seed: int = 42,
    control_count: int = 5,
    replay_loader: Callable[..., Any] = load_simulation_replay,
) -> Path:
    """Validate stored evidence, build the dev queue, and publish it atomically."""
    destination = Path(output_dir).expanduser().resolve()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"output already exists: {destination}")
    cases = Path(cases_path).expanduser().resolve(strict=True)
    results = Path(results_path).expanduser().resolve(strict=True)
    jury = Path(jury_path).expanduser().resolve(strict=True)
    corpus = replay_loader(cases_path=cases, results_path=results)
    bundle = build_annotation_bundle(
        corpus,
        load_jsonl(jury),
        seed=seed,
        control_count=control_count,
    )
    return publish_annotation_bundle(bundle, destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a dev-only human annotation queue from a stored evaluatorq jury."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--jury", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--control-count", type=int, default=5)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        destination = prepare(
            args.cases,
            args.results,
            args.jury,
            args.output_dir,
            seed=args.seed,
            control_count=args.control_count,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    queue = json.loads((destination / "queue.json").read_text(encoding="utf-8"))
    meta = queue["meta"]
    print(
        f"Saved {meta['n_items']} dev review items "
        f"({meta['n_prioritized']} prioritized, {meta['control_count']} controls, "
        f"{meta['n_errors']} errors excluded) to {destination}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
