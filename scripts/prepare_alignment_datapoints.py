"""Convert a joined evaluatorq replay JSONL into orq-evaluator-alignment seed datapoints.

Mirrors the hosted scorer's input shaping (`evaluation_ops.hosted_evaluators.orq_evaluator`):
the full conversation including tool turns is the judge's evidence, the last user turn is the
query, and the oracle is kept OUT of the judge inputs so the skill grades the judge against it.

    uv run python scripts/prepare_alignment_datapoints.py \
        runs/evaluatorq-correctness-v1.0.7-joined-20260905.jsonl \
        <run_dir>/synthetic_datapoints.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from analytics_chatbot.evaluation_ops.hosted_evaluators import _reference_text


def to_datapoint(row: dict) -> dict:
    messages = row["conversation"]
    user_query = next(m["content"] for m in reversed(messages) if m["role"] == "user")
    return {
        "inputs": {
            "user_query": user_query,
            "all_messages": json.dumps(messages, ensure_ascii=False),
            "response": row["recorded_output"],
        },
        "messages": messages,
        "expected_output": _reference_text(row["expected_output"]),
        # ponytail: rationale is the only free-text field the seed loader keeps per row;
        # abuse it to carry identity so labels can be joined back to case_id/split.
        "rationale": f"{row['case_id']} | split={row['evaluation_split']} | "
        + " | ".join(f"{name}={score['value']}" for name, score in row["scores"].items()),
    }


def main(src: str, dst: str) -> None:
    rows = [json.loads(line) for line in Path(src).read_text().splitlines() if line.strip()]
    datapoints = [to_datapoint(r) for r in rows]
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(json.dumps(datapoints, indent=1))
    print(f"{len(datapoints)} datapoints -> {dst}")


if __name__ == "__main__":
    assert (
        to_datapoint(
            {
                "conversation": [
                    {"role": "user", "content": "q1"},
                    {"role": "tool", "content": "x"},
                    {"role": "assistant", "content": "a1"},
                    {"role": "user", "content": "q2"},
                    {"role": "assistant", "content": "a2"},
                ],
                "expected_output": {"b": 1, "a": 2},
                "recorded_output": "a2",
                "case_id": "c",
                "evaluation_split": "dev",
                "scores": {"answer_correctness@1.0.0": {"value": "pass"}},
            }
        )["inputs"]["user_query"]
        == "q2"
    )
    main(*sys.argv[1:3])
