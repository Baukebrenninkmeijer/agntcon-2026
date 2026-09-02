"""OpenAI Responses adapter configured for the orq AI Gateway."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from openai import OpenAI

from analytics_chatbot.config import Settings, TraceContext
from analytics_chatbot.models import (
    Conversation,
    GatewayFunctionCall,
    GatewayResponse,
)
from analytics_chatbot.prompts import SYSTEM_PROMPT


class OrqGateway:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if not settings.orq_api_key:
            raise ValueError("ORQ_API_KEY is required for live gateway requests")
        self.settings = settings
        self.client = client or OpenAI(
            api_key=settings.orq_api_key,
            base_url=settings.gateway_base_url,
        )

    def create_response(
        self,
        *,
        input_items: str | Sequence[dict[str, Any]],
        conversation: Conversation,
        trace_context: TraceContext,
        tools: Sequence[dict[str, Any]],
    ) -> GatewayResponse:
        request: dict[str, Any] = {
            "model": self.settings.model,
            "instructions": SYSTEM_PROMPT,
            "input": input_items if isinstance(input_items, str) else list(input_items),
            "tools": list(tools),
            "store": True,
            "extra_body": trace_context.extra_body(conversation.thread_id),
        }
        if conversation.previous_response_id:
            request["previous_response_id"] = conversation.previous_response_id

        response = self.client.responses.create(**request)
        calls = [
            GatewayFunctionCall(
                call_id=item.call_id,
                name=item.name,
                arguments=item.arguments,
            )
            for item in response.output
            if getattr(item, "type", None) == "function_call"
        ]
        usage: dict[str, int] = {}
        if response.usage is not None:
            for name in ("input_tokens", "output_tokens", "total_tokens"):
                value = getattr(response.usage, name, None)
                if value is not None:
                    usage[name] = int(value)
        return GatewayResponse(
            response_id=response.id,
            text=response.output_text or "",
            function_calls=calls,
            usage=usage,
        )
