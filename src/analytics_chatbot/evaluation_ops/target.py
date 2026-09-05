"""Evaluatorq AgentTarget backed by the hosted Orq agent and local tools."""

from __future__ import annotations

import asyncio
import json

from evaluatorq.contracts import AgentResponse as EvaluatorqAgentResponse
from evaluatorq.contracts import AgentTarget, Message, Usage
from evaluatorq.openresponses.convert_models import FunctionCall, OutputTextContent

from analytics_chatbot.agent import AnalyticsChatbot
from analytics_chatbot.config import Settings, TraceContext
from analytics_chatbot.models import Conversation


class AnalyticsChatbotTarget(AgentTarget):
    """One isolated hosted/local analytics conversation per evaluatorq clone."""

    def __init__(
        self,
        settings: Settings,
        case_by_first_message: dict[str, str],
        *,
        chatbot: AnalyticsChatbot | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.case_by_first_message = dict(case_by_first_message)
        self.chatbot = chatbot or AnalyticsChatbot(settings)
        self.conversation: Conversation = self.chatbot.new_conversation()
        self.case_id: str | None = None
        self.artifact_paths: list[str] = []

    def new(self) -> AnalyticsChatbotTarget:
        return type(self)(self.settings, self.case_by_first_message)

    async def respond(self, messages: list[Message]) -> EvaluatorqAgentResponse:
        if not messages or messages[-1].role != "user" or not isinstance(messages[-1].content, str):
            raise ValueError("AnalyticsChatbotTarget requires a final text user message")
        message = messages[-1].content
        if self.case_id is None:
            self.case_id = self.case_by_first_message.get(message, "unmapped-simulation-case")
        result = await asyncio.to_thread(
            self.chatbot.ask,
            message,
            conversation=self.conversation,
            context=TraceContext(
                run_kind="eval",
                interface="python",
                evaluation_split="mixed",
                case_id=self.case_id,
                identity_id="pydata2026-agent-simulator",
                dataset_version=self.settings.dataset_version,
                agent_version=self.settings.agent_version,
            ),
        )
        if result.artifact_path:
            self.artifact_paths.append(result.artifact_path)
        output = [
            FunctionCall(
                call_id=call.call_id,
                name=call.name,
                arguments=json.dumps(call.arguments, sort_keys=True),
                result=call.result.model_dump_json(),
            )
            for call in result.tool_calls
        ]
        output.append(OutputTextContent(text=result.answer))
        return EvaluatorqAgentResponse(
            output=output,
            usage=Usage.model_validate(result.usage),
            model=self.settings.hosted_agent_model,
            response_id=result.response_id,
        )
