from pathlib import Path

import pytest

from analytics_chatbot.orq_resources import (
    EvaluatorValidation,
    ResourceError,
    load_resource_bundle,
)

RESOURCE_ROOT = Path(__file__).parents[1] / "orq" / "resources"


def test_repository_resources_compile_to_sdk_payloads() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)

    assert bundle.project.key == "pydata2026"
    assert bundle.project.project_id == "${ORQ_PROJECT_ID}"
    assert [tool.key for tool in bundle.tools] == ["query-sql", "save-insight"]
    assert len(bundle.evaluators) == 6

    query = bundle.tool_payloads()[0]
    assert query["path"] == "pydata2026/tools"
    assert query["function"]["name"] == "query_sql"
    assert query["function"]["strict"] is True
    assert "execution" not in query

    agent = bundle.agent_payload("deepseek/deepseek-v4-flash")
    assert agent["key"] == "analytics-chatbot"
    assert agent["model"] == {"id": "deepseek/deepseek-v4-flash"}
    assert [tool["key"] for tool in agent["settings"]["tools"]] == [
        "query-sql",
        "save-insight",
    ]
    assert "Use query_sql before making factual claims" in agent["instructions"]

    evaluator_payloads = {body["key"]: body for body in bundle.evaluator_payloads()}
    correctness = evaluator_payloads["analytics-answer-correctness"]
    faithfulness = evaluator_payloads["analytics-evidence-faithfulness"]
    assert correctness["output_type"] == "categorical"
    assert "model" not in correctness
    assert correctness["mode"] == "jury"
    assert correctness["jury"] == {
        "judges": [
            {"model": "openai/gpt-5.6-luna"},
            {"model": "google-ai/gemini-3.5-flash-lite"},
            {"model": "tensorix/qwen/qwen3.8-flash-next"},
        ],
        "min_successful_judges": 2,
    }
    assert "{{input.expected_output}}" in correctness["prompt"]
    assert "{{output.tools_called}}" not in correctness["prompt"]
    assert "{{output.tools_called}}" in faithfulness["prompt"]
    assert "{{input.expected_output}}" not in faithfulness["prompt"]
    assert "input_mapping" not in correctness
    assert "validation" not in correctness


def test_python_evaluators_execute_against_documented_log_shape() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    evaluators = {body["key"]: body for body in bundle.evaluator_payloads()}

    query_namespace: dict[str, object] = {}
    exec(evaluators["analytics-tool-execution-integrity"]["code"], query_namespace)
    assert query_namespace["evaluate"](
        {
            "input": "calculate revenue",
            "tool_calls": [
                {
                    "tool_name": "query_sql",
                    "response": {"raw_response": {"rows": [[42]]}},
                }
            ],
        }
    )

    state_namespace: dict[str, object] = {}
    exec(evaluators["analytics-state-change-policy"]["code"], state_namespace)
    assert state_namespace["evaluate"]({"input": "calculate revenue", "tool_calls": []})
    assert not state_namespace["evaluate"](
        {
            "input": "calculate revenue",
            "tool_calls": [{"tool_name": "save_insight", "response": {}}],
        }
    )


def test_pending_llm_evaluators_are_blocked_from_remote_sync(tmp_path: Path) -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    pending = [
        evaluator
        for evaluator in bundle.evaluators
        if getattr(evaluator, "validation", None) is not None
        and evaluator.validation.status == "pending_human_labels"
    ]
    if not pending:
        pytest.skip("no pending LLM evaluators in the tracked bundle")

    with pytest.raises(ResourceError, match=r"`shadow` or `validated`"):
        bundle.assert_llm_evaluators_syncable()


def test_shadow_llm_evaluators_may_sync_with_zero_labels() -> None:
    validation = EvaluatorValidation(status="shadow", human_labeled_examples=0)

    assert validation.human_labeled_examples == 0


def test_validated_llm_evaluators_require_the_gating_label_floor() -> None:
    with pytest.raises(ValueError, match=r"at least 30 human labels"):
        EvaluatorValidation(status="validated", human_labeled_examples=29)


def test_agent_instructions_must_use_yaml_block_scalar(tmp_path: Path) -> None:
    root = tmp_path / "resources"
    (root / "agents").mkdir(parents=True)
    (root / "tools").mkdir()
    (root / "project.yaml").write_text(
        "kind: project\nkey: pydata2026\nproject_id: test-project\n",
        encoding="utf-8",
    )
    (root / "agents" / "agent.yaml").write_text(
        "kind: agent\nkey: a\ndisplay_name: A\nrole: analyst\n"
        "description: test\npath: agents\ninstructions: inline\n"
        "model:\n  provider: p\n  model_id: m\n  requires_tool_calling: true\n"
        "settings:\n  max_iterations: 2\n  max_execution_time: 30\n  tools: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ResourceError, match="block scalar"):
        load_resource_bundle(root)


def test_evaluator_mode_switches_between_single_judge_and_jury() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    correctness = next(
        evaluator
        for evaluator in bundle.evaluators
        if evaluator.key == "analytics-answer-correctness"
    )
    # Both shapes stay declared, so flipping `mode` is the only edit needed.
    assert correctness.model is not None
    assert correctness.judges is not None

    jury_body = next(
        body for body in bundle.evaluator_payloads() if body["key"] == correctness.key
    )
    assert jury_body["mode"] == "jury"
    assert "model" not in jury_body
    assert [judge["model"] for judge in jury_body["jury"]["judges"]] == correctness.judges

    single = correctness.model_copy(update={"mode": "single"})
    single_bundle = bundle.model_copy(
        update={
            "evaluators": [
                single if evaluator.key == correctness.key else evaluator
                for evaluator in bundle.evaluators
            ]
        }
    )
    single_body = next(
        body for body in single_bundle.evaluator_payloads() if body["key"] == correctness.key
    )
    assert single_body["mode"] == "single"
    assert single_body["model"] == correctness.model
    assert "jury" not in single_body
