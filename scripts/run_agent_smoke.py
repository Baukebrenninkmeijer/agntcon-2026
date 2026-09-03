#!/usr/bin/env python3
"""Run bounded hosted-agent smoke scenarios against local tools."""

from __future__ import annotations

import json
from pathlib import Path

from analytics_chatbot.agent import AnalyticsChatbot
from analytics_chatbot.config import Settings, TraceContext


def _context(case_id: str) -> TraceContext:
    return TraceContext(
        run_kind="smoke",
        evaluation_split="smoke",
        case_id=case_id,
        interface="python",
        identity_id="pydata2026-agent-simulator",
    )


def _record(case_id: str, response: object) -> dict[str, object]:
    return {
        "case_id": case_id,
        "answer": response.answer,
        "run_id": response.run_id,
        "thread_id": response.thread_id,
        "response_id": response.response_id,
        "tool_calls": [call.model_dump(mode="json") for call in response.tool_calls],
        "state_changes": [change.model_dump(mode="json") for change in response.state_changes],
        "usage": response.usage,
        "artifact_path": response.artifact_path,
    }


def main() -> None:
    settings = Settings(model=Settings().hosted_agent_model)
    chatbot = AnalyticsChatbot(settings)
    records: list[dict[str, object]] = []

    read_only = chatbot.ask(
        "Compare total net revenue across all regions for the full dataset. Do not save it.",
        context=_context("smoke-read-only"),
    )
    assert any(call.name == "query_sql" and call.result.ok for call in read_only.tool_calls)
    assert not read_only.state_changes
    records.append(_record("smoke-read-only", read_only))

    multi_step = chatbot.ask(
        "Inspect the orders schema and available regions first, then identify the region with "
        "the highest full-dataset net revenue and compare it with the runner-up.",
        context=_context("smoke-multi-step"),
    )
    successful_queries = [
        call for call in multi_step.tool_calls if call.name == "query_sql" and call.result.ok
    ]
    assert len(successful_queries) >= 2
    records.append(_record("smoke-multi-step", multi_step))

    clarification_conversation = chatbot.new_conversation()
    clarification = chatbot.ask(
        "Tell me our revenue for the best region.",
        conversation=clarification_conversation,
        context=_context("smoke-clarification"),
    )
    assert not clarification.tool_calls
    records.append(_record("smoke-clarification-turn-1", clarification))
    clarified = chatbot.ask(
        "Use net revenue across the full dataset, and define best as the highest total.",
        conversation=clarification_conversation,
        context=_context("smoke-clarification"),
    )
    assert clarified.thread_id == clarification.thread_id
    assert any(call.name == "query_sql" and call.result.ok for call in clarified.tool_calls)
    records.append(_record("smoke-clarification-turn-2", clarified))

    saved = chatbot.ask(
        "Calculate net revenue for EMEA in the later calendar year and save the finding.",
        context=_context("smoke-explicit-save"),
    )
    assert any(call.name == "query_sql" and call.result.ok for call in saved.tool_calls)
    assert len(saved.state_changes) == 1
    assert saved.state_changes[0].tool_name == "save_insight"
    records.append(_record("smoke-explicit-save", saved))

    output = Path("runs/smoke-summary.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Smoke checks passed for 4 scenarios / {len(records)} turns; details: {output}")


if __name__ == "__main__":
    main()
