from analytics_chatbot.models import Conversation, ToolResult


def test_conversation_has_stable_thread_id() -> None:
    conversation = Conversation()

    assert conversation.thread_id
    assert conversation.previous_response_id is None


def test_tool_result_error_is_structured() -> None:
    result = ToolResult.failure("unsafe_sql", "Only read-only queries are allowed")

    assert result.ok is False
    assert result.error_code == "unsafe_sql"
    assert result.error == "Only read-only queries are allowed"
    assert result.data == {}
