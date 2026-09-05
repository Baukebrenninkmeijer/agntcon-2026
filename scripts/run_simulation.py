#!/usr/bin/env python3
"""Run evaluatorq simulations against the hosted/local analytics target."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


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
    parser.add_argument(
        "--evaluation-name",
        default="pydata2026-analytics-chatbot-simulation",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path, default=Path("runs/evaluatorq-simulation.jsonl"))
    return parser


def _load(path: Path) -> list[Any]:
    from evaluatorq.simulation import SimulationDatapoint

    return [
        SimulationDatapoint.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    load_dotenv(override=True)

    from evaluatorq.contracts import LLMCallConfig
    from evaluatorq.simulation import simulate
    from evaluatorq.simulation.utils.dataset_export import export_results_to_jsonl

    from analytics_chatbot.config import Settings
    from analytics_chatbot.evaluation_ops.target import AnalyticsChatbotTarget

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
            evaluation_name=args.evaluation_name,
            target=target,
            datapoints=datapoints,
            max_turns=args.max_turns,
            llm_config=LLMCallConfig(
                model="openai/gpt-5.6-luna",
                api="responses",
                retry_count=1,
            ),
            evaluator_names=["goal_achieved", "criteria_met"],
            datapoint_parallelism=10,
            llm_parallelism=10,
            max_target_retries=2,
            per_simulation_timeout_s=180,
            upload_results=True,
            save=True,
            report=args.report,
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
