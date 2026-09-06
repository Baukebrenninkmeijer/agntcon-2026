"""Validated repository definitions for hosted Orq resources."""

from __future__ import annotations

import ast
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from yaml.nodes import MappingNode, ScalarNode


class ResourceError(ValueError):
    """Raised when repository resource definitions are incomplete or inconsistent."""


class ProjectResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["project"]
    key: str
    project_id: str


class FunctionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    strict: bool = True
    parameters: dict[str, Any]


class ToolResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["tool"]
    key: str
    display_name: str
    path: str = "tools"
    execution: Literal["local"]
    description: str
    function: FunctionDefinition


class ModelSelector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_id: str
    requires_tool_calling: bool = True

    @property
    def full_id(self) -> str:
        return self.model_id if "/" in self.model_id else f"{self.provider}/{self.model_id}"


class AgentSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_iterations: int = Field(ge=1, le=100)
    max_execution_time: int = Field(ge=1, le=600)
    tool_approval_required: Literal["all", "respect_tool", "none"] = "none"
    chat_exposed: bool = False
    tools: list[str]


class AgentResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["agent"]
    key: str
    display_name: str
    role: str
    description: str
    path: str = "agents"
    instructions: str
    model: ModelSelector
    settings: AgentSettings


class EvaluatorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["boolean", "number", "categorical"]
    labels: list[dict[str, str]] = Field(default_factory=list)
    passing: list[bool | str]

    @model_validator(mode="after")
    def validate_verdict_space(self) -> EvaluatorOutput:
        if self.type == "categorical":
            values = [label.get("value") for label in self.labels]
            if not values or len(values) != len(set(values)):
                raise ValueError("categorical output labels must be non-empty and unique")
            if not set(self.passing).issubset(set(values)):
                raise ValueError("passing categorical verdicts must be declared labels")
        elif self.labels:
            raise ValueError("labels are supported only for categorical evaluators")
        return self


MIN_GATING_LABELS = 30


class EvaluatorValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending_human_labels", "shadow", "validated"]
    human_labeled_examples: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_sample_count(self) -> EvaluatorValidation:
        # ponytail: two tiers only. `shadow` may sync with zero labels because a hosted
        # evaluator must exist before it can be aligned; `validated` is the gating tier.
        if self.status == "validated" and self.human_labeled_examples < MIN_GATING_LABELS:
            raise ValueError(
                f"validated LLM evaluators require at least {MIN_GATING_LABELS} human labels"
            )
        return self


class EvaluatorBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["evaluator"]
    key: str
    display_name: str
    description: str
    path: str
    output: EvaluatorOutput
    input_mapping: dict[str, str]


class PythonEvaluatorResource(EvaluatorBase):
    type: Literal["python_eval"]
    code: str

    @model_validator(mode="after")
    def validate_python(self) -> PythonEvaluatorResource:
        if self.output.type not in {"boolean", "number"}:
            raise ValueError("Python evaluators support boolean or number output")
        try:
            tree = ast.parse(self.code)
        except SyntaxError as error:
            raise ValueError(f"invalid evaluator Python: {error}") from error
        forbidden_nodes = (ast.Import, ast.ImportFrom, ast.AsyncFunctionDef, ast.ClassDef)
        forbidden_calls = {"compile", "eval", "exec", "getattr", "globals", "open", "__import__"}
        for node in ast.walk(tree):
            if isinstance(node, forbidden_nodes):
                raise ValueError("evaluator Python cannot import modules or declare classes")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in forbidden_calls
            ):
                raise ValueError(f"forbidden evaluator call: {node.func.id}")
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        if not functions or functions[-1].name != "evaluate":
            raise ValueError("the last evaluator function must be evaluate(log)")
        return self


class LlmEvaluatorResource(EvaluatorBase):
    type: Literal["llm_eval"]
    mode: Literal["single", "jury"]
    model: str | None = None
    judges: list[str] | None = None
    min_successful_judges: int = Field(default=2, ge=1)
    repetitions: int = Field(ge=1, le=10)
    validation: EvaluatorValidation
    prompt: str

    @model_validator(mode="after")
    def validate_mode_shape(self) -> LlmEvaluatorResource:
        # `model` and `judges` may both be declared so switching between a single
        # judge and a jury is a one-word `mode:` edit. Only the active mode is sent.
        if self.judges is not None:
            if len(self.judges) < 2:
                raise ValueError("a declared jury requires at least two judges")
            if len(set(self.judges)) != len(self.judges):
                raise ValueError("jury judges must be distinct models")
            if self.min_successful_judges > len(self.judges):
                raise ValueError("min_successful_judges cannot exceed the judge count")
        if self.mode == "jury" and not self.judges:
            raise ValueError("jury mode requires a `judges` list")
        if self.mode == "single" and not self.model:
            raise ValueError("single mode requires a `model`")
        return self

    @model_validator(mode="after")
    def validate_prompt_contract(self) -> LlmEvaluatorResource:
        variables = {match.strip() for match in re.findall(r"{{\s*([^{}]+?)\s*}}", self.prompt)}
        missing = variables - set(self.input_mapping)
        if missing:
            raise ValueError(f"prompt variables lack input mappings: {sorted(missing)}")
        secret_tokens = {"ORQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
        if any(token in self.prompt or token in str(self.input_mapping) for token in secret_tokens):
            raise ValueError("evaluator resources cannot contain credential variables")
        if self.key == "analytics-decision-support-quality":
            required = {"input.all_messages", "output.response"}
            if not required.issubset(variables):
                raise ValueError(
                    "decision support quality requires the full conversation and final response"
                )

            subjective_contract = f"{self.prompt}\n{self.input_mapping}".lower()
            mapped_variables = set(self.input_mapping)
            reference_family_variables = {
                variable
                for variable in variables | mapped_variables
                if {"expected", "hidden", "ideal", "oracle", "reference"}
                & set(re.split(r"[._-]", variable.lower()))
            }
            claims_reference = re.sub(
                r"\bno reference answer or ideal response\b", "", subjective_contract
            )
            if (
                reference_family_variables
                or "input.decision_context" in subjective_contract
                or "reference_sql" in subjective_contract
                or "query_requirements" in subjective_contract
                or re.search(
                    r"\b(?:reference|ideal)\s+(?:answer|response)\b", claims_reference
                )
            ):
                raise ValueError("decision support quality must remain reference-free")
            if variables != required or mapped_variables != required:
                raise ValueError(
                    "decision support quality accepts only the full conversation and final response"
                )
        return self


EvaluatorResource = Annotated[
    PythonEvaluatorResource | LlmEvaluatorResource,
    Field(discriminator="type"),
]


class ResourceBundle(BaseModel):
    project: ProjectResource
    tools: list[ToolResource]
    agent: AgentResource
    evaluators: list[EvaluatorResource] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> ResourceBundle:
        tool_keys = [tool.key for tool in self.tools]
        if len(tool_keys) != len(set(tool_keys)):
            raise ValueError("tool keys must be unique")
        missing = set(self.agent.settings.tools) - set(tool_keys)
        if missing:
            raise ValueError(f"agent references unknown tools: {sorted(missing)}")
        evaluator_keys = [evaluator.key for evaluator in self.evaluators]
        if len(evaluator_keys) != len(set(evaluator_keys)):
            raise ValueError("evaluator keys must be unique")
        return self

    def _project_path(self, resource_path: str) -> str:
        if resource_path == self.project.key or resource_path.startswith(f"{self.project.key}/"):
            return resource_path
        return f"{self.project.key}/{resource_path.strip('/')}"

    def tool_payloads(self) -> list[dict[str, Any]]:
        by_key = {tool.key: tool for tool in self.tools}
        payloads = []
        for key in self.agent.settings.tools:
            tool = by_key[key]
            payloads.append(
                {
                    "path": self._project_path(tool.path),
                    "key": tool.key,
                    "display_name": tool.display_name,
                    "description": tool.description,
                    "type": "function",
                    "status": "live",
                    "function": tool.function.model_dump(),
                }
            )
        return payloads

    def agent_payload(self, resolved_model_id: str) -> dict[str, Any]:
        settings = self.agent.settings
        return {
            "key": self.agent.key,
            "display_name": self.agent.display_name,
            "role": self.agent.role,
            "description": self.agent.description,
            "instructions": self.agent.instructions,
            "path": self._project_path(self.agent.path),
            "model": {"id": resolved_model_id},
            "settings": {
                "max_iterations": settings.max_iterations,
                "max_execution_time": settings.max_execution_time,
                "tool_approval_required": settings.tool_approval_required,
                "chat_exposed": settings.chat_exposed,
                "tools": [
                    {"type": "function", "key": key, "requires_approval": False}
                    for key in settings.tools
                ],
            },
        }

    def evaluator_payloads(self) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for evaluator in self.evaluators:
            body: dict[str, Any] = {
                "type": evaluator.type,
                "key": evaluator.key,
                "description": evaluator.description,
                # ponytail: the evals API rejects `path` alongside `project_id`
                # ("Provide either `path` or `project_id`, not both. Prefer `project_id`.")
                "project_id": self.project.project_id,
                "output_type": evaluator.output.type,
            }
            if evaluator.output.type == "categorical":
                body["categories"] = [label["value"] for label in evaluator.output.labels]
                body["categorical_labels"] = evaluator.output.labels
                body["guardrail_config"] = {
                    "type": "categorical",
                    "values": evaluator.output.passing,
                    "enabled": True,
                    "alert_on_failure": False,
                }
            elif evaluator.output.type == "boolean":
                body["guardrail_config"] = {
                    "type": "boolean",
                    "value": True,
                    "enabled": True,
                    "alert_on_failure": False,
                }
            if isinstance(evaluator, PythonEvaluatorResource):
                body["code"] = evaluator.code
            else:
                body.update(
                    {
                        "mode": evaluator.mode,
                        "repetitions": evaluator.repetitions,
                        "prompt": evaluator.prompt,
                    }
                )
                if evaluator.mode == "jury":
                    body["jury"] = {
                        "judges": [{"model": model} for model in evaluator.judges or []],
                        "min_successful_judges": evaluator.min_successful_judges,
                    }
                else:
                    body["model"] = evaluator.model
            payloads.append(body)
        return payloads

    def assert_llm_evaluators_syncable(self, keys: Sequence[str] | None = None) -> None:
        pending = [
            evaluator.key
            for evaluator in self.evaluators
            if isinstance(evaluator, LlmEvaluatorResource)
            and evaluator.validation.status not in {"shadow", "validated"}
            and (keys is None or evaluator.key in keys)
        ]
        if pending:
            raise ResourceError(
                "LLM evaluators must be `shadow` or `validated` before remote sync: "
                f"{', '.join(sorted(pending))}"
            )


def _load_yaml(path: Path, *, require_instructions_block: bool = False) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if require_instructions_block:
        root = yaml.compose(text)
        if not isinstance(root, MappingNode):
            raise ResourceError(f"{path}: expected a YAML mapping")
        instructions_node = None
        for key_node, value_node in root.value:
            if isinstance(key_node, ScalarNode) and key_node.value == "instructions":
                instructions_node = value_node
                break
        if not isinstance(instructions_node, ScalarNode) or instructions_node.style not in {
            "|",
            ">",
        }:
            raise ResourceError(f"{path}: instructions must use a YAML block scalar")
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ResourceError(f"{path}: expected a YAML mapping")
    return loaded


def load_resource_bundle(root: Path) -> ResourceBundle:
    """Load and cross-validate one repository resource bundle."""

    root = Path(root)
    project_path = root / "project.yaml"
    agent_paths = sorted((root / "agents").glob("*.yaml"))
    tool_paths = sorted((root / "tools").glob("*.yaml"))
    evaluator_paths = sorted((root / "evaluators").glob("**/*.yaml"))
    if len(agent_paths) != 1:
        raise ResourceError(f"{root}: expected exactly one agent YAML")
    try:
        return ResourceBundle(
            project=ProjectResource.model_validate(_load_yaml(project_path)),
            tools=[ToolResource.model_validate(_load_yaml(path)) for path in tool_paths],
            agent=AgentResource.model_validate(
                _load_yaml(agent_paths[0], require_instructions_block=True)
            ),
            evaluators=[
                # The discriminated union is validated through ResourceBundle.
                _load_yaml(path)
                for path in evaluator_paths
            ],
        )
    except (OSError, yaml.YAMLError, ValueError) as error:
        if isinstance(error, ResourceError):
            raise
        raise ResourceError(str(error)) from error
