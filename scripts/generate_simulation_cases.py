#!/usr/bin/env python3
import argparse
from pathlib import Path

from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation_ops.cases import build_cases, build_edge_cases, write_cases
from analytics_chatbot.evaluation_ops.cases_v3 import build_v3_cases

DEFAULT_OUTPUT = Path("orq/resources/datasets/simulation-cases.jsonl")
EDGE_V2_OUTPUT = Path("orq/resources/datasets/simulation-cases-v2.jsonl")
V3_OUTPUT = Path("orq/resources/datasets/simulation-cases-v3.jsonl")
BUILDERS = {
    "standard": (build_cases, DEFAULT_OUTPUT),
    "edge-v2": (build_edge_cases, EDGE_V2_OUTPUT),
    "v3": (build_v3_cases, V3_OUTPUT),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant",
        choices=tuple(BUILDERS),
        default="standard",
        help="simulation corpus variant to generate",
    )
    parser.add_argument("--output", type=Path, help="output JSONL path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    builder, default_output = BUILDERS[args.variant]
    output = args.output or default_output
    records = builder(settings.database_path)
    write_cases(records, output)
    print(f"Wrote {len(records)} oracle-backed evaluatorq simulation datapoints to {output}")


if __name__ == "__main__":
    main()
