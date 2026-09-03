#!/usr/bin/env python3
from pathlib import Path

from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation_ops.cases import build_cases, write_cases


def main() -> None:
    settings = Settings()
    output = Path("orq/resources/datasets/simulation-cases.jsonl")
    records = build_cases(settings.database_path)
    write_cases(records, output)
    print(f"Wrote {len(records)} oracle-backed evaluatorq simulation datapoints to {output}")


if __name__ == "__main__":
    main()
