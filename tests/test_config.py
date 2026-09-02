from analytics_chatbot.config import TraceContext


def test_trace_context_uses_bounded_tags_and_string_metadata() -> None:
    context = TraceContext(run_kind="eval", evaluation_split="test", case_id="case-7")

    body = context.extra_body(thread_id="thread-1")

    assert body["name"] == "PyData2026-AnalyticsChatbot"
    assert body["tags"] == ["pydata2026", "analytics-chatbot", "eval"]
    assert body["thread"] == {"id": "thread-1"}
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
