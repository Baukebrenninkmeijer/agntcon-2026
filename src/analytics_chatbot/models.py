"""Shared models and the injectable gateway boundary."""

from collections.abc import Sequence
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from analytics_chatbot.config import TraceContext


class Conversation(BaseModel):
    """State required to continue a Responses API conversation."""

    thread_id: str = Field(default_factory=lambda: f"pydata2026-{uuid4().hex}")
    previous_response_id: str | None = None


class ToolResult(BaseModel):
    """Result returned to the model for every local tool invocation."""

    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error: str | None = None
    execution_ms: float = 0.0

    @classmethod
    def success(cls, data: dict[str, Any], execution_ms: float = 0.0) -> "ToolResult":
        return cls(ok=True, data=data, execution_ms=execution_ms)

    @classmethod
    def failure(cls, code: str, message: str, execution_ms: float = 0.0) -> "ToolResult":
        return cls(ok=False, error_code=code, error=message, execution_ms=execution_ms)


class GatewayFunctionCall(BaseModel):
    call_id: str
    name: str
    arguments: str


class GatewayResponse(BaseModel):
    response_id: str
    text: str = ""
    function_calls: list[GatewayFunctionCall] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)


class ToolCallRecord(BaseModel):
    call_id: str
    name: str
    arguments: dict[str, Any]
    result: ToolResult


class StateChange(BaseModel):
    tool_name: str
    before: dict[str, Any]
    after: dict[str, Any]


class AgentResponse(BaseModel):
    answer: str
    run_id: str
    thread_id: str
    response_id: str | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    state_changes: list[StateChange] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)
    artifact_path: str | None = None


class GatewayClient(Protocol):
    """Small boundary that makes the agent loop deterministic in tests."""

    def create_response(
        self,
        *,
        input_items: str | Sequence[dict[str, Any]],
        conversation: Conversation,
        trace_context: TraceContext,
        tools: Sequence[dict[str, Any]],
    ) -> GatewayResponse: ...
