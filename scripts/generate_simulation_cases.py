#!/usr/bin/env python3
"""Generate the fifty Sphere.com simulation cases with executable DuckDB oracles."""

import argparse
from pathlib import Path

from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation_ops.cases import build_v4_cases, write_cases

DEFAULT_OUTPUT = Path("orq/resources/datasets/simulation-cases-v4.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="output JSONL path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    records = build_v4_cases(Settings().database_path)
    write_cases(records, args.output)
    print(f"Wrote {len(records)} oracle-backed evaluatorq simulation datapoints to {args.output}")


if __name__ == "__main__":
    main()
