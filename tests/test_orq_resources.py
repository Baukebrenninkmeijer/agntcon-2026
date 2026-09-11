from pathlib import Path

import pytest
from conftest import TEST_PROJECT_ID

from analytics_chatbot.evaluation_ops import DEFAULT_JUDGES
from analytics_chatbot.orq_resources import (
    EvaluatorValidation,
    LlmEvaluatorResource,
    ResourceError,
    load_resource_bundle,
)

RESOURCE_ROOT = Path(__file__).parents[1] / "orq" / "resources"


def test_repository_resources_compile_to_sdk_payloads() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)

    assert bundle.project.key == "pydata2026"
    assert bundle.project.project_id == TEST_PROJECT_ID
    assert [tool.key for tool in bundle.tools] == ["query-sql", "save-insight"]
    assert len(bundle.evaluators) == 4

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
    instructions = " ".join(agent["instructions"].lower().split())
    assert "sphere.com" in instructions
    assert "wholesale home-appliance orders" in instructions
    assert "use query_sql before making factual claims" in instructions
    assert "never claim a save succeeded unless the tool result confirms it" in instructions
    assert "do not recommend an action unless the user explicitly asks for one" in instructions
    for coaching_phrase in (
        "foreground",
        "decision impact",
        "adapt detail",
        "recommend next steps",
        "board narrative",
    ):
        assert coaching_phrase not in instructions

    llm_resources = [
        evaluator
        for evaluator in bundle.evaluators
        if isinstance(evaluator, LlmEvaluatorResource)
    ]
    llm_keys = {evaluator.key for evaluator in llm_resources}
    assert llm_keys == {"analytics-decision-support-quality", "podcast-claudish"}
    decision_support_resources = [
        evaluator
        for evaluator in llm_resources
        if evaluator.key == "analytics-decision-support-quality"
    ]
    assert len(decision_support_resources) == 1
    for evaluator in decision_support_resources:
        assert evaluator.mode == "jury"
        assert evaluator.judges == list(DEFAULT_JUDGES)
        assert evaluator.min_successful_judges == 2
        assert evaluator.repetitions == 3
        assert evaluator.validation.status == "shadow"
        assert evaluator.validation.human_labeled_examples == 30
        assert evaluator.input_mapping == {
            "input.all_messages": "full ordered conversation including tool calls and results",
            "output.response": "final assistant response",
        }
        assert [label["value"] for label in evaluator.output.labels] == [
            "pass",
            "fail",
            "not_applicable",
        ]
        serialized = str(evaluator.model_dump()).lower()
        for reference_family in (
            "input.decision_context",
            "input.expected_output",
            "input.expected_answer",
            "input.oracle",
            "reference_sql",
            "query_requirements",
        ):
            assert reference_family not in serialized

    evaluator_payloads = {body["key"]: body for body in bundle.evaluator_payloads()}
    decision_support = evaluator_payloads["analytics-decision-support-quality"]
    assert decision_support["output_type"] == "categorical"
    assert decision_support["mode"] == "jury"
    assert decision_support["repetitions"] == 3
    assert [judge["model"] for judge in decision_support["jury"]["judges"]] == list(
        DEFAULT_JUDGES
    )
    assert decision_support["jury"]["min_successful_judges"] == 2
    assert "{{input.all_messages}}" in decision_support["prompt"]
    assert "{{output.response}}" in decision_support["prompt"]
    assert "Human-aligned boundary rules" in decision_support["prompt"]
    assert "Lack of exhaustive proof is not itself a failure" in decision_support["prompt"]
    assert "Grade the analytical step the user actually requested" in decision_support["prompt"]
    assert "A visible factual issue forces a fail only when" in decision_support["prompt"]
    assert "direct arithmetic with visible tool results" in decision_support["prompt"]
    assert "unsupported data-definition claim" not in decision_support["prompt"]
    assert (
        "Evaluate the full conversation, not the latest response in isolation"
        in decision_support["prompt"]
    )
    assert "input_mapping" not in decision_support
    assert "validation" not in decision_support


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


def test_project_id_placeholder_requires_its_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ORQ_PROJECT_ID", raising=False)

    with pytest.raises(ResourceError, match="ORQ_PROJECT_ID"):
        load_resource_bundle(RESOURCE_ROOT)


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


def test_decision_support_prompt_requires_subjective_trace_evidence() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    evaluator = next(
        evaluator
        for evaluator in bundle.evaluators
        if evaluator.key == "analytics-decision-support-quality"
    )
    source = evaluator.model_dump()

    for missing_variable in ("input.all_messages", "output.response"):
        invalid = source | {
            "prompt": evaluator.prompt.replace(f"{{{{{missing_variable}}}}}", "missing evidence")
        }
        with pytest.raises(ValueError, match="requires the full conversation and final response"):
            LlmEvaluatorResource.model_validate(invalid)


@pytest.mark.parametrize(
    "forbidden_reference",
    [
        "{{input.decision_context}}",
        "{{input.expected_output}}",
        "{{input.expected_answer}}",
        "{{input.oracle}}",
        "{{input.reference_answer}}",
        "{{input.hidden_answer}}",
        "reference_sql",
        "query_requirements",
        "A reference answer exists.",
        "Compare against the ideal answer.",
    ],
)
def test_decision_support_prompt_rejects_reference_evidence(
    forbidden_reference: str,
) -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    evaluator = next(
        evaluator
        for evaluator in bundle.evaluators
        if evaluator.key == "analytics-decision-support-quality"
    )
    source = evaluator.model_dump()
    forbidden_mapping = (
        {forbidden_reference[2:-2]: "forbidden"}
        if forbidden_reference.startswith("{{")
        else {}
    )
    invalid = source | {
        "input_mapping": evaluator.input_mapping | forbidden_mapping,
        "prompt": f"{evaluator.prompt}\n{forbidden_reference}",
    }

    with pytest.raises(ValueError, match="must remain reference-free"):
        LlmEvaluatorResource.model_validate(invalid)


def test_decision_support_prompt_rejects_any_additional_evidence_mapping() -> None:
    bundle = load_resource_bundle(RESOURCE_ROOT)
    evaluator = next(
        evaluator
        for evaluator in bundle.evaluators
        if evaluator.key == "analytics-decision-support-quality"
    )
    source = evaluator.model_dump()
    invalid = source | {
        "input_mapping": evaluator.input_mapping | {"input.user_query": "last user request"},
        "prompt": f"{evaluator.prompt}\n{{{{input.user_query}}}}",
    }

    with pytest.raises(ValueError, match="only the full conversation and final response"):
        LlmEvaluatorResource.model_validate(invalid)
