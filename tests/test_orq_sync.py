from pathlib import Path

import pytest

from analytics_chatbot.orq_resources import load_resource_bundle
from analytics_chatbot.orq_sync import (
    OrqReconciler,
    RemoteEntity,
    RemoteSnapshot,
    SyncError,
    normalize_remote_agent,
    normalize_remote_evaluator,
    normalize_remote_tool,
)

RESOURCE_ROOT = Path(__file__).parents[1] / "orq" / "resources"


def empty_snapshot() -> RemoteSnapshot:
    return RemoteSnapshot(
        project_key="pydata2026",
        project_id="${ORQ_PROJECT_ID}",
        models={
            "deepseek/deepseek-v4-flash": True,
            "openai/gpt-5.6-luna": True,
            "google-ai/gemini-3.5-flash-lite": True,
            "tensorix/qwen/qwen3.8-flash-next": True,
            "wafer/DeepSeek-V4-Flash-0731-Fast": True,
        },
    )


def test_sync_plan_orders_tools_agent_and_mixed_evaluators() -> None:
    reconciler = OrqReconciler(load_resource_bundle(RESOURCE_ROOT))

    plan = reconciler.plan(empty_snapshot())

    assert [(action.operation, action.kind, action.key) for action in plan.actions] == [
        ("create", "tool", "query-sql"),
        ("create", "tool", "save-insight"),
        ("create", "agent", "analytics-chatbot"),
        ("create", "evaluator", "analytics-state-change-policy"),
        ("create", "evaluator", "analytics-tool-execution-integrity"),
        ("create", "evaluator", "analytics-answer-correctness"),
        ("create", "evaluator", "analytics-evidence-faithfulness"),
        ("create", "evaluator", "analytics-multi-turn-consistency"),
        ("create", "evaluator", "analytics-query-semantics"),
    ]


def test_sync_plan_is_noop_when_remote_semantics_match() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    reconciler = OrqReconciler(bundle)
    tools = bundle.tool_payloads()
    agent = bundle.agent_payload("deepseek/deepseek-v4-flash")
    evaluators = bundle.evaluator_payloads()
    snapshot = empty_snapshot().model_copy(
        update={
            "tools": [
                RemoteEntity(kind="tool", key=body["key"], entity_id=f"id-{index}", body=body)
                for index, body in enumerate(tools)
            ],
            "agents": [
                RemoteEntity(
                    kind="agent",
                    key=agent["key"],
                    entity_id="agent-id",
                    body=agent,
                )
            ],
            "evaluators": [
                RemoteEntity(
                    kind="evaluator",
                    key=body["key"],
                    entity_id=f"eval-{index}",
                    body=body,
                )
                for index, body in enumerate(evaluators)
            ],
        }
    )

    plan = reconciler.plan(snapshot)

    assert all(action.operation == "noop" for action in plan.actions)


def test_sync_plan_rejects_project_mismatch() -> None:
    reconciler = OrqReconciler(load_resource_bundle(RESOURCE_ROOT))
    snapshot = empty_snapshot().model_copy(update={"project_id": "wrong-project"})

    with pytest.raises(SyncError, match="project mismatch"):
        reconciler.plan(snapshot)


def test_sync_plan_rejects_duplicate_remote_keys() -> None:
    reconciler = OrqReconciler(load_resource_bundle(RESOURCE_ROOT))
    duplicate = RemoteEntity(kind="tool", key="query-sql", entity_id="one", body={})
    snapshot = empty_snapshot().model_copy(
        update={"tools": [duplicate, duplicate.model_copy(update={"entity_id": "two"})]}
    )

    with pytest.raises(SyncError, match="duplicate remote tool"):
        reconciler.plan(snapshot)


def test_sync_plan_rejects_missing_or_incapable_model() -> None:
    reconciler = OrqReconciler(load_resource_bundle(RESOURCE_ROOT))

    with pytest.raises(SyncError, match="tool-capable model"):
        reconciler.plan(empty_snapshot().model_copy(update={"models": {}}))


def test_remote_sdk_shapes_normalize_to_repository_semantics() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    tool = bundle.tool_payloads()[0]
    agent = bundle.agent_payload("deepseek/deepseek-v4-flash")

    noisy_tool = {**tool, "_id": "opaque", "project_id": bundle.project.project_id}
    noisy_agent = {
        **agent,
        "_id": "opaque",
        "project_id": bundle.project.project_id,
        "settings": {
            **agent["settings"],
            "evaluators": [],
            "tools": [
                {
                    **reference,
                    "id": f"opaque-{index}",
                    # The current SDK retrieve response omits this discriminator.
                    "type": None,
                }
                for index, reference in enumerate(agent["settings"]["tools"])
            ],
        },
    }

    assert normalize_remote_tool(noisy_tool) == tool
    assert normalize_remote_agent(noisy_agent) == agent


def test_remote_evaluator_shapes_normalize_to_repository_semantics() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    expected = next(
        body
        for body in bundle.evaluator_payloads()
        if body["key"] == "analytics-answer-correctness"
    )
    noisy = {
        **expected,
        "_id": "opaque",
        "created": "later",
        "categorical_labels": [
            {**label, "color": "ignored"} for label in expected["categorical_labels"]
        ],
    }

    assert normalize_remote_evaluator(noisy) == expected
