"""Semantic, idempotent reconciliation for repository-owned Orq resources."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any, Literal

from pydantic import BaseModel, Field

from analytics_chatbot.orq_resources import ResourceBundle


class SyncError(RuntimeError):
    """Raised when live state cannot be reconciled safely."""


ResourceKind = Literal["tool", "agent", "evaluator"]
Operation = Literal["create", "update", "noop"]


class RemoteEntity(BaseModel):
    kind: ResourceKind
    key: str
    entity_id: str
    body: dict[str, Any]


class RemoteSnapshot(BaseModel):
    project_key: str
    project_id: str
    models: dict[str, bool] = Field(default_factory=dict)
    tools: list[RemoteEntity] = Field(default_factory=list)
    agents: list[RemoteEntity] = Field(default_factory=list)
    evaluators: list[RemoteEntity] = Field(default_factory=list)


class SyncAction(BaseModel):
    operation: Operation
    kind: ResourceKind
    key: str
    body: dict[str, Any]
    entity_id: str | None = None


class SyncPlan(BaseModel):
    project_key: str
    project_id: str
    model_id: str
    actions: list[SyncAction]

    @property
    def changed(self) -> bool:
        return any(action.operation != "noop" for action in self.actions)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class OrqReconciler:
    """Compare repository intent with a normalized live snapshot."""

    def __init__(self, bundle: ResourceBundle) -> None:
        self.bundle = bundle

    @staticmethod
    def _by_key(entities: list[RemoteEntity], kind: ResourceKind) -> dict[str, RemoteEntity]:
        result: dict[str, RemoteEntity] = {}
        for entity in entities:
            if entity.key in result:
                raise SyncError(f"duplicate remote {kind} key {entity.key!r}")
            result[entity.key] = entity
        return result

    def plan(self, snapshot: RemoteSnapshot) -> SyncPlan:
        expected = self.bundle.project
        if snapshot.project_key != expected.key or snapshot.project_id != expected.project_id:
            raise SyncError(
                "project mismatch: expected "
                f"{expected.key}/{expected.project_id}, got "
                f"{snapshot.project_key}/{snapshot.project_id}"
            )

        model_id = self.bundle.agent.model.full_id
        if not snapshot.models.get(model_id, False):
            raise SyncError(f"required tool-capable model {model_id!r} is unavailable")

        remote_tools = self._by_key(snapshot.tools, "tool")
        remote_agents = self._by_key(snapshot.agents, "agent")
        remote_evaluators = self._by_key(snapshot.evaluators, "evaluator")
        actions: list[SyncAction] = []

        for body in self.bundle.tool_payloads():
            remote = remote_tools.get(body["key"])
            operation: Operation = "create"
            if remote is not None:
                operation = "noop" if _canonical(remote.body) == _canonical(body) else "update"
            actions.append(
                SyncAction(
                    operation=operation,
                    kind="tool",
                    key=body["key"],
                    body=body,
                    entity_id=remote.entity_id if remote else None,
                )
            )

        agent_body = self.bundle.agent_payload(model_id)
        remote_agent = remote_agents.get(agent_body["key"])
        agent_operation: Operation = "create"
        if remote_agent is not None:
            agent_operation = (
                "noop" if _canonical(remote_agent.body) == _canonical(agent_body) else "update"
            )
        actions.append(
            SyncAction(
                operation=agent_operation,
                kind="agent",
                key=agent_body["key"],
                body=agent_body,
                entity_id=remote_agent.entity_id if remote_agent else None,
            )
        )

        evaluator_bodies = sorted(
            self.bundle.evaluator_payloads(),
            key=lambda body: (body["type"] != "python_eval", body["key"]),
        )
        for body in evaluator_bodies:
            if body["type"] == "llm_eval":
                for required in _evaluator_models(body):
                    if not snapshot.models.get(required, False):
                        raise SyncError(f"required evaluator model {required!r} is unavailable")
            remote = remote_evaluators.get(body["key"])
            operation: Operation = "create"
            if remote is not None:
                operation = "noop" if _canonical(remote.body) == _canonical(body) else "update"
            actions.append(
                SyncAction(
                    operation=operation,
                    kind="evaluator",
                    key=body["key"],
                    body=body,
                    entity_id=remote.entity_id if remote else None,
                )
            )
        return SyncPlan(
            project_key=expected.key,
            project_id=expected.project_id,
            model_id=model_id,
            actions=actions,
        )


def _model_dump(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return value.model_dump(mode="json", by_alias=True, exclude_none=True)


def normalize_remote_tool(value: Any) -> dict[str, Any]:
    """Project a live SDK tool onto the repository-owned semantic fields."""

    body = _model_dump(value)
    function = body.get("function") or {}
    return {
        "path": body.get("path"),
        "key": body.get("key"),
        "display_name": body.get("display_name"),
        "description": body.get("description"),
        "type": body.get("type"),
        "status": body.get("status"),
        "function": {
            "name": function.get("name"),
            "description": function.get("description"),
            "strict": function.get("strict", False),
            "parameters": function.get("parameters") or {},
        },
    }


def normalize_remote_agent(value: Any) -> dict[str, Any]:
    """Project a live SDK agent onto the repository-owned semantic fields."""

    body = _model_dump(value)
    model = body.get("model") or {}
    settings = body.get("settings") or {}
    tools = []
    for tool in settings.get("tools") or []:
        if not isinstance(tool, dict):
            tool = _model_dump(tool)
        tools.append(
            {
                "type": tool.get("type") or "function",
                "key": tool.get("key"),
                "requires_approval": tool.get("requires_approval", False),
            }
        )
    return {
        "key": body.get("key"),
        "display_name": body.get("display_name"),
        "role": body.get("role"),
        "description": body.get("description"),
        "instructions": body.get("instructions"),
        "path": body.get("path"),
        "model": {"id": model.get("id")},
        "settings": {
            "max_iterations": settings.get("max_iterations"),
            "max_execution_time": settings.get("max_execution_time"),
            "tool_approval_required": settings.get("tool_approval_required"),
            "chat_exposed": settings.get("chat_exposed", False),
            "tools": tools,
        },
    }


def normalize_remote_evaluator(
    value: Any, model_slugs: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Project a hydrated evaluator onto repository-owned semantic fields."""

    body = _model_dump(value)
    result: dict[str, Any] = {
        "type": body.get("type"),
        "key": body.get("key"),
        "description": body.get("description") or "",
        "project_id": body.get("project_id"),
        "output_type": body.get("output_type"),
    }
    guardrail = body.get("guardrail_config") or {}
    if body.get("output_type") == "categorical":
        labels = []
        for label in body.get("categorical_labels") or []:
            if not isinstance(label, dict):
                label = _model_dump(label)
            labels.append({"value": label.get("value"), "description": label.get("description")})
        result.update(
            {
                "categories": list(body.get("categories") or []),
                "categorical_labels": labels,
                "guardrail_config": {
                    "type": guardrail.get("type"),
                    "values": list(guardrail.get("values") or []),
                    "enabled": guardrail.get("enabled", False),
                    "alert_on_failure": guardrail.get("alert_on_failure", False),
                },
            }
        )
    elif body.get("output_type") == "boolean":
        result["guardrail_config"] = {
            "type": guardrail.get("type"),
            "value": guardrail.get("value"),
            "enabled": guardrail.get("enabled", False),
            "alert_on_failure": guardrail.get("alert_on_failure", False),
        }
    if body.get("type") == "python_eval":
        result["code"] = body.get("code")
    else:
        result.update(
            {
                "mode": body.get("mode"),
                "repetitions": body.get("repetitions"),
                "prompt": body.get("prompt"),
            }
        )
        if body.get("mode") == "jury":
            jury = body.get("jury") or {}
            if not isinstance(jury, dict):
                jury = _model_dump(jury)
            # The API resolves catalog slugs to opaque model IDs, so translate them
            # back before the semantic diff; otherwise every plan reports an update.
            slugs = model_slugs or {}
            result["jury"] = {
                "judges": [
                    {"model": slugs.get(model, model)}
                    for model in _judge_models(jury.get("judges"))
                ],
                "min_successful_judges": jury.get("min_successful_judges", 2),
            }
        else:
            model = body.get("model")
            if isinstance(model, dict):
                model = model.get("id")
            result["model"] = (model_slugs or {}).get(str(model), model)
    return result


def _judge_models(judges: Any) -> list[str]:
    models: list[str] = []
    for judge in judges or []:
        if not isinstance(judge, dict):
            judge = _model_dump(judge)
        model = judge.get("model")
        if isinstance(model, dict):
            model = model.get("id")
        if model:
            models.append(str(model))
    return models


def _evaluator_models(body: dict[str, Any]) -> list[str]:
    if body.get("mode") == "jury":
        return _judge_models((body.get("jury") or {}).get("judges"))
    return [body["model"]] if body.get("model") else []


class OrqSdkGateway:
    """Narrow adapter around orq-ai-sdk 4.14.x used by the reconciler."""

    def __init__(self, api_key: str, *, timeout_ms: int = 30_000, client: Any = None) -> None:
        if not api_key:
            raise SyncError("ORQ_API_KEY is required")
        if client is None:
            from orq_ai_sdk import Orq

            client = Orq(api_key=api_key, timeout_ms=timeout_ms)
        self.client = client
        self._api_key = api_key
        self._catalog_base = "https://my.orq.ai"

    def _model_slugs(self) -> dict[str, str]:
        """Map opaque model IDs to catalog slugs.

        The SDK model list exposes only slugs and the evaluator API stores only IDs,
        so the `/v2/models` catalog is the one place both appear together.
        """

        import httpx  # local import keeps the offline test path free of network deps

        try:
            response = httpx.get(
                f"{self._catalog_base}/v2/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            rows = response.json()
        except Exception:  # ponytail: slug translation is a diff nicety, not a gate
            return {}
        slugs: dict[str, str] = {}
        for row in rows if isinstance(rows, list) else []:
            model_id, ref = row.get("id"), row.get("refId")
            if model_id and ref:
                slugs[str(model_id)] = str(ref)
        return slugs

    @staticmethod
    def _paginate(method: Any, *, limit: int = 200) -> list[Any]:
        rows: list[Any] = []
        cursor: str | None = None
        while True:
            response = method(limit=limit, starting_after=cursor)
            page = list(response.data)
            rows.extend(page)
            if not response.has_more:
                return rows
            if not page:
                raise SyncError("Orq pagination reported has_more with an empty page")
            last = _model_dump(page[-1])
            cursor = str(last.get("id") or last.get("_id") or last.get("project_id") or "")
            if not cursor:
                raise SyncError("Orq pagination cursor is missing")

    def snapshot(self, bundle: ResourceBundle) -> RemoteSnapshot:
        projects = self._paginate(self.client.projects.list)
        matches = [p for p in projects if _model_dump(p).get("key") == bundle.project.key]
        if len(matches) != 1:
            raise SyncError(
                f"expected exactly one Orq project with key {bundle.project.key!r}, "
                f"found {len(matches)}"
            )
        project = _model_dump(matches[0])
        project_id = str(project.get("project_id"))
        if project_id != bundle.project.project_id:
            raise SyncError(
                f"project mismatch: expected {bundle.project.project_id}, got {project_id}"
            )

        model_rows = list(self.client.models.list().data)
        models = {str(_model_dump(row).get("id")): True for row in model_rows}
        model_slugs = self._model_slugs()
        # The SDK list only carries workspace-enabled models; the /v2/models catalog
        # also lists provider-routed refIds (e.g. tencent/deepseek-v4-flash) that
        # evaluators accept directly, so both count as available.
        models.update({slug: True for slug in model_slugs.values()})
        tool_rows = [
            row
            for row in self._paginate(self.client.tools.list)
            if _model_dump(row).get("project_id") == project_id
        ]
        desired_agent_keys = {bundle.agent.key}
        agent_rows = []
        for row in self._paginate(self.client.agents.list):
            listed = _model_dump(row)
            if listed.get("key") not in desired_agent_keys:
                continue
            hydrated = self.client.agents.retrieve(agent_key=str(listed["key"]))
            if _model_dump(hydrated).get("project_id") == project_id:
                agent_rows.append(hydrated)
        evaluator_rows = []
        for listed in self._paginate(self.client.evals.all):
            listed_body = _model_dump(listed)
            if listed_body.get("project_id") != project_id:
                continue
            evaluator_id = str(listed_body.get("id") or listed_body.get("_id"))
            hydrated_body = _model_dump(self.client.evals.get(id=evaluator_id))
            # List carries the public key and model reference; retrieve carries source text.
            hydrated_body["key"] = listed_body.get("key")
            if listed_body.get("model"):
                hydrated_body["model"] = listed_body["model"]
            evaluator_rows.append(hydrated_body)
        return RemoteSnapshot(
            project_key=bundle.project.key,
            project_id=project_id,
            models=models,
            tools=[
                RemoteEntity(
                    kind="tool",
                    key=str(_model_dump(row).get("key")),
                    entity_id=str(_model_dump(row).get("id") or _model_dump(row).get("_id")),
                    body=normalize_remote_tool(row),
                )
                for row in tool_rows
            ],
            agents=[
                RemoteEntity(
                    kind="agent",
                    key=str(_model_dump(row).get("key")),
                    entity_id=str(_model_dump(row).get("id") or _model_dump(row).get("_id")),
                    body=normalize_remote_agent(row),
                )
                for row in agent_rows
            ],
            evaluators=[
                RemoteEntity(
                    kind="evaluator",
                    key=str(row.get("key")),
                    entity_id=str(row.get("id") or row.get("_id")),
                    body=normalize_remote_evaluator(row, model_slugs),
                )
                for row in evaluator_rows
            ],
        )

    def apply(self, actions: Iterable[SyncAction]) -> None:
        """Apply a reviewed plan in dependency order; no deletes are supported."""

        for action in actions:
            if action.operation == "noop":
                continue
            if action.kind == "tool":
                if action.operation == "create":
                    self.client.tools.create(request=action.body)
                else:
                    assert action.entity_id is not None
                    update_body = {**action.body, "versionIncrement": "patch"}
                    self.client.tools.update(tool_id=action.entity_id, request_body=update_body)
            elif action.kind == "agent" and action.operation == "create":
                self.client.agents.create(**action.body)
            elif action.kind == "agent":
                update_body = {**action.body}
                update_body.pop("key", None)
                self.client.agents.update(agent_key=action.key, **update_body)
            elif action.operation == "create":
                self.client.evals.create(request=action.body)
            else:
                assert action.entity_id is not None
                update_body = {**action.body}
                evaluator_type = update_body.pop("type")
                self.client.evals.update(
                    id=action.entity_id,
                    type_=evaluator_type,
                    version_increment="patch",
                    **update_body,
                )
