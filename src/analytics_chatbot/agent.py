"""Bounded local analytics agent with exact trajectory capture."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Sequence
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from analytics_chatbot.config import Settings, TraceContext
from analytics_chatbot.gateway import OrqGateway
from analytics_chatbot.insights import InsightStore, SaveInsightArgs
from analytics_chatbot.models import (
    AgentResponse,
    Conversation,
    GatewayClient,
    GatewayFunctionCall,
    StateChange,
    ToolCallRecord,
    ToolResult,
)
from analytics_chatbot.prompts import QUERY_SQL_TOOL, SAVE_INSIGHT_TOOL
from analytics_chatbot.run_store import RunStore
from analytics_chatbot.sql_tool import SqlTool

_SAVE_INTENT = re.compile(r"\b(save|saved|remember|preserve|store|keep)\b", re.IGNORECASE)


class AgentLoopError(RuntimeError):
    """Raised when a bounded agent run cannot finish safely."""


class AnalyticsChatbot:
    """Public Python API for one observable analytics agent."""

    def __init__(
        self,
        settings: Settings | None = None,
        gateway: GatewayClient | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.gateway = gateway or OrqGateway(self.settings)

    def new_conversation(self) -> Conversation:
        return Conversation()

    def _tool_result(
        self,
        call: GatewayFunctionCall,
        *,
        sql_tool: SqlTool,
        insight_store: InsightStore,
        allow_save: bool,
    ) -> tuple[dict[str, Any], ToolResult, StateChange | None]:
        try:
            arguments = json.loads(call.arguments)
            if not isinstance(arguments, dict):
                raise ValueError("tool arguments must be a JSON object")
        except (json.JSONDecodeError, ValueError) as error:
            return {}, ToolResult.failure("malformed_arguments", str(error)), None

        if call.name == "query_sql":
            query = arguments.get("query")
            if not isinstance(query, str):
                return arguments, ToolResult.failure(
                    "malformed_arguments", "query must be a string"
                ), None
            return arguments, sql_tool.execute(query), None

        if call.name == "save_insight" and allow_save:
            try:
                validated = SaveInsightArgs.model_validate(arguments)
            except ValidationError as error:
                return arguments, ToolResult.failure(
                    "malformed_arguments", str(error)[:1_000]
                ), None
            before = insight_store.snapshot()
            result = insight_store.save(validated)
            after = insight_store.snapshot()
            return arguments, result, StateChange(
                tool_name="save_insight", before=before, after=after
            )

        return arguments, ToolResult.failure(
            "unknown_tool", f"Tool {call.name!r} is not available for this request"
        ), None

    def ask(
        self,
        message: str,
        conversation: Conversation | None = None,
        context: TraceContext | None = None,
    ) -> AgentResponse:
        conversation = conversation or self.new_conversation()
        context = context or TraceContext(
            dataset_version=self.settings.dataset_version,
            agent_version=self.settings.agent_version,
        )
        run_id = f"run-{uuid4().hex}"
        run_store = RunStore(self.settings.runs_path, run_id)
        insight_store = InsightStore(run_store.directory)
        sql_tool = SqlTool(
            self.settings.database_path,
            max_rows=self.settings.max_query_rows,
            timeout_seconds=self.settings.query_timeout_seconds,
        )
        allow_save = bool(_SAVE_INTENT.search(message))
        tools: Sequence[dict[str, Any]] = (
            [QUERY_SQL_TOOL, SAVE_INSIGHT_TOOL] if allow_save else [QUERY_SQL_TOOL]
        )
        tool_calls: list[ToolCallRecord] = []
        state_changes: list[StateChange] = []
        usage: Counter[str] = Counter()
        seen_calls: set[tuple[str, str]] = set()
        input_items: str | Sequence[dict[str, Any]] = message
        started = perf_counter()
        final_response_id: str | None = None

        run_store.append(
            {
                "type": "run_started",
                "run_id": run_id,
                "thread_id": conversation.thread_id,
                "message": message,
                "trace_context": context.model_dump(),
                "save_enabled": allow_save,
            }
        )

        try:
            for step in range(self.settings.max_tool_steps + 1):
                if step == self.settings.max_tool_steps:
                    raise AgentLoopError(
                        f"Agent tool step limit ({self.settings.max_tool_steps}) reached"
                    )

                run_store.append(
                    {
                        "type": "gateway_request",
                        "step": step,
                        "previous_response_id": conversation.previous_response_id,
                        "input": input_items,
                        "tools": [tool["name"] for tool in tools],
                    }
                )
                response = self.gateway.create_response(
                    input_items=input_items,
                    conversation=conversation.model_copy(),
                    trace_context=context,
                    tools=tools,
                )
                final_response_id = response.response_id
                conversation.previous_response_id = response.response_id
                usage.update(response.usage)
                run_store.append(
                    {
                        "type": "gateway_response",
                        "step": step,
                        "response_id": response.response_id,
                        "text": response.text,
                        "function_calls": [call.model_dump() for call in response.function_calls],
                        "usage": response.usage,
                    }
                )

                if not response.function_calls:
                    artifact = run_store.finalize(
                        {
                            "status": "succeeded",
                            "duration_ms": (perf_counter() - started) * 1_000,
                            "response_id": final_response_id,
                            "tool_call_count": len(tool_calls),
                            "usage": dict(usage),
                        }
                    )
                    return AgentResponse(
                        answer=response.text,
                        run_id=run_id,
                        thread_id=conversation.thread_id,
                        response_id=final_response_id,
                        tool_calls=tool_calls,
                        state_changes=state_changes,
                        usage=dict(usage),
                        artifact_path=str(artifact),
                    )

                outputs: list[dict[str, Any]] = []
                for call in response.function_calls:
                    try:
                        canonical = json.dumps(json.loads(call.arguments), sort_keys=True)
                    except json.JSONDecodeError:
                        canonical = call.arguments
                    signature = (call.name, canonical)
                    if signature in seen_calls:
                        arguments: dict[str, Any] = {}
                        result = ToolResult.failure(
                            "repeated_tool_call",
                            "The same tool call was already executed in this run",
                        )
                        state_change = None
                    else:
                        seen_calls.add(signature)
                        arguments, result, state_change = self._tool_result(
                            call,
                            sql_tool=sql_tool,
                            insight_store=insight_store,
                            allow_save=allow_save,
                        )

                    record = ToolCallRecord(
                        call_id=call.call_id,
                        name=call.name,
                        arguments=arguments,
                        result=result,
                    )
                    tool_calls.append(record)
                    if state_change is not None:
                        state_changes.append(state_change)
                    run_store.append(
                        {
                            "type": "tool_call",
                            "step": step,
                            **record.model_dump(),
                            "state_change": (
                                state_change.model_dump() if state_change is not None else None
                            ),
                        }
                    )
                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": result.model_dump_json(),
                        }
                    )
                input_items = outputs

            raise AssertionError("unreachable")
        except Exception as error:
            run_store.abort(str(error))
            raise
