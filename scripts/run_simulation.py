#!/usr/bin/env python3
"""Run evaluatorq simulations against the hosted/local analytics target."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from evaluatorq.contracts import LLMCallConfig
from evaluatorq.simulation import SimulationDatapoint, simulate
from evaluatorq.simulation.utils.dataset_export import export_results_to_jsonl

from analytics_chatbot.config import Settings
from analytics_chatbot.evaluation_ops.target import AnalyticsChatbotTarget


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("orq/resources/datasets/simulation-cases.jsonl"),
    )
    parser.add_argument("--case-id", help="run exactly one stable case id")
    parser.add_argument("--limit", type=int, default=1, help="maximum cases to run")
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("runs/evaluatorq-simulation.jsonl"))
    return parser


def _load(path: Path) -> list[SimulationDatapoint]:
    return [
        SimulationDatapoint.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    args = build_parser().parse_args()
    datapoints = _load(args.cases)
    if args.case_id:
        datapoints = [point for point in datapoints if point.id == args.case_id]
        if len(datapoints) != 1:
            raise ValueError(f"expected exactly one case with id {args.case_id!r}")
    else:
        datapoints = datapoints[: args.limit]
    if not datapoints:
        raise ValueError("at least one simulation case is required")

    settings = Settings(model=Settings().hosted_agent_model)
    target = AnalyticsChatbotTarget(
        settings,
        {point.first_message: point.id for point in datapoints},
    )
    results = asyncio.run(
        simulate(
            evaluation_name="pydata2026-analytics-chatbot-simulation",
            target=target,
            datapoints=datapoints,
            max_turns=args.max_turns,
            llm_config=LLMCallConfig(
                model="openai/gpt-5.6-luna",
                api="responses",
                retry_count=1,
            ),
            datapoint_parallelism=1,
            llm_parallelism=2,
            max_target_retries=2,
            upload_results=True,
            save=True,
            executive_summary=False,
            recommendations=False,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_results_to_jsonl(results, str(args.output))
    for point, result in zip(datapoints, results, strict=True):
        print(
            json.dumps(
                {
                    "case_id": point.id,
                    "terminated_by": result.terminated_by,
                    "reason": result.reason,
                    "goal_achieved": result.goal_achieved,
                    "turn_count": result.turn_count,
                    "criteria_verified": result.criteria_verified,
                    "messages": [message.model_dump(mode="json") for message in result.messages],
                },
                indent=2,
                default=str,
            )
        )
    print(f"Exported {len(results)} simulation result(s) to {args.output}")


if __name__ == "__main__":
    main()
