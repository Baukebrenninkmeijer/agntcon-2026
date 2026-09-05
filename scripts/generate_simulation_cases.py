#!/usr/bin/env python3
import argparse
from pathlib import Path

from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation_ops.cases import build_cases, build_edge_cases, write_cases

DEFAULT_OUTPUT = Path("orq/resources/datasets/simulation-cases.jsonl")
EDGE_V2_OUTPUT = Path("orq/resources/datasets/simulation-cases-v2.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant",
        choices=("standard", "edge-v2"),
        default="standard",
        help="simulation corpus variant to generate",
    )
    parser.add_argument("--output", type=Path, help="output JSONL path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    builder = build_edge_cases if args.variant == "edge-v2" else build_cases
    output = args.output or (EDGE_V2_OUTPUT if args.variant == "edge-v2" else DEFAULT_OUTPUT)
    records = builder(settings.database_path)
    write_cases(records, output)
    print(f"Wrote {len(records)} oracle-backed evaluatorq simulation datapoints to {output}")


if __name__ == "__main__":
    main()
