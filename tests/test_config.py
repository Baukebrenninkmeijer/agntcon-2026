from analytics_chatbot.config import Settings, TraceContext


def test_settings_use_current_gateway_endpoint() -> None:
    assert Settings().gateway_base_url == "https://api.orq.ai/v3/router"


def test_settings_default_to_sphere_versions() -> None:
    settings = Settings()

    assert settings.dataset_version == "sphere-orders-v1"
    assert settings.agent_version == "sphere-baseline-v1"
    assert settings.max_tool_steps == 30


def test_trace_context_defaults_to_sphere_versions() -> None:
    context = TraceContext()

    assert context.dataset_version == "sphere-orders-v1"
    assert context.agent_version == "sphere-baseline-v1"


def test_trace_context_uses_bounded_tags_and_string_metadata() -> None:
    context = TraceContext(run_kind="eval", evaluation_split="test", case_id="case-7")

    body = context.extra_body(thread_id="thread-1")

    assert body["name"] == "PyData2026-AnalyticsChatbot"
    assert "tags" not in body
    assert body["thread"] == {
        "id": "thread-1",
        "tags": ["pydata2026", "analytics-chatbot", "eval"],
    }
    assert body["metadata"]["evaluation_split"] == "test"
    assert body["metadata"]["case_id"] == "case-7"
    assert all(isinstance(value, str) for value in body["metadata"].values())


def test_trace_context_omits_identity_when_not_supplied() -> None:
    body = TraceContext().extra_body(thread_id="thread-1")

    assert "identity" not in body


def test_trace_context_includes_identity_as_distinct_attribution() -> None:
    body = TraceContext(identity_id="eval-actor").extra_body(thread_id="thread-1")

    assert body["identity"] == {"id": "eval-actor"}
    assert "identity_id" not in body["metadata"]
