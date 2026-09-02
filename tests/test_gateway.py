from types import SimpleNamespace

from analytics_chatbot.config import Settings, TraceContext
from analytics_chatbot.gateway import OrqGateway
from analytics_chatbot.models import Conversation


def test_gateway_sends_orq_attribution(mocker) -> None:
    raw_response = SimpleNamespace(
        id="resp-1",
        output_text="ok",
        output=[],
        usage=SimpleNamespace(input_tokens=10, output_tokens=2, total_tokens=12),
    )
    create = mocker.Mock(return_value=raw_response)
    client = mocker.Mock(responses=mocker.Mock(create=create))
    settings = Settings(orq_api_key="test-key")
    gateway = OrqGateway(settings, client=client)

    response = gateway.create_response(
        input_items="question",
        conversation=Conversation(thread_id="thread-1"),
        trace_context=TraceContext(run_kind="eval"),
        tools=[],
    )

    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "deepseek/deepseek-v4-flash"
    assert kwargs["extra_body"]["thread"] == {
        "id": "thread-1",
        "tags": ["pydata2026", "analytics-chatbot", "eval"],
    }
    assert kwargs["store"] is True
    assert "previous_response_id" not in kwargs
    assert response.text == "ok"
    assert response.usage == {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}


def test_gateway_normalizes_function_calls(mocker) -> None:
    raw_response = SimpleNamespace(
        id="resp-2",
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                call_id="call-1",
                name="query_sql",
                arguments='{"query":"SELECT 1"}',
            )
        ],
        usage=None,
    )
    client = mocker.Mock(responses=mocker.Mock(create=mocker.Mock(return_value=raw_response)))
    gateway = OrqGateway(Settings(orq_api_key="test-key"), client=client)

    response = gateway.create_response(
        input_items="question",
        conversation=Conversation(previous_response_id="resp-1"),
        trace_context=TraceContext(),
        tools=[],
    )

    assert response.function_calls[0].name == "query_sql"
    assert response.function_calls[0].call_id == "call-1"
    assert client.responses.create.call_args.kwargs["previous_response_id"] == "resp-1"


def test_gateway_requires_api_key() -> None:
    settings = Settings(orq_api_key=None)

    try:
        OrqGateway(settings)
    except ValueError as error:
        assert "ORQ_API_KEY" in str(error)
    else:
        raise AssertionError("OrqGateway accepted missing credentials")
