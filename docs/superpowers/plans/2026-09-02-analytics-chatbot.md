# Analytics Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, observable business analytics chatbot that uses DuckDB tools and the orq AI Gateway, with exact trajectories and state changes available for the PyData 2026 evaluation examples.

**Architecture:** A small Python package owns a deterministic synthetic dataset, two guarded local tools, a typed OpenAI Responses-compatible gateway boundary, and a bounded agent loop. Gateway requests are attributed to the project-scoped key, fixed tags, a conversation thread, and filterable metadata; a local run store preserves the complete multi-request trajectory.

**Tech Stack:** Python 3.11+, uv, Polars lazy/streaming execution, DuckDB, OpenAI Python SDK, Pydantic Settings, Typer, Rich, sqlglot, pytest.

## Global Constraints

- Distribution name: `analytics-chatbot`; import package: `analytics_chatbot`; CLI: `analytics-chatbot`.
- Default gateway model: `deepseek/deepseek-v4-flash` (`DeepSeek-V4-Flash-0731`).
- Gateway base URL: `https://my.orq.ai/v3/router`.
- Generate exactly 25,000 orders covering 24 complete months from a fixed seed.
- Source data is read-only; `save_insight` is available only when the user explicitly requests persistence.
- Gateway trace name: `PyData2026-AnalyticsChatbot`; bounded base tags: `pydata2026`, `analytics-chatbot`.
- Arbitrary metadata is for trace filtering; project, identity, thread, and tag remain their distinct attribution mechanisms.
- Default tests make no network calls. The live test is opt-in.
- Use `orq`, never `orqi`, for platform provisioning.
- Never print, log, or commit an API key.

---

## File Map

- `pyproject.toml`: package metadata, dependencies, CLI entry point, pytest and Ruff configuration.
- `.env.example`: documented non-secret runtime settings.
- `.gitignore`: generated database, run artifacts, `.env`, caches, and virtual environment.
- `src/analytics_chatbot/config.py`: validated settings and trace-context construction.
- `src/analytics_chatbot/models.py`: shared Pydantic models and gateway protocol.
- `src/analytics_chatbot/data.py`: deterministic Polars `LazyFrame` generation, streaming Parquet staging, and DuckDB creation.
- `src/analytics_chatbot/sql_tool.py`: SQL validation and bounded read-only execution.
- `src/analytics_chatbot/insights.py`: run-scoped structured insight persistence.
- `src/analytics_chatbot/run_store.py`: partial JSONL audit log and atomic finalization.
- `src/analytics_chatbot/gateway.py`: OpenAI Responses adapter for the orq gateway.
- `src/analytics_chatbot/agent.py`: bounded tool loop and public `AnalyticsChatbot` API.
- `src/analytics_chatbot/cli.py`: `seed-data`, `ask`, `chat`, and `show-run` commands.
- `src/analytics_chatbot/prompts.py`: system instructions and tool schemas.
- `tests/`: focused offline tests plus a marked live smoke test.
- `README.md`: talk context, setup, use, trace semantics, and demo commands.

### Task 1: Package skeleton, settings, and shared models

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/analytics_chatbot/__init__.py`
- Create: `src/analytics_chatbot/config.py`
- Create: `src/analytics_chatbot/models.py`
- Create: `tests/test_config.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces: `Settings`, `TraceContext`, `Conversation`, `ToolCallRecord`, `AgentResponse`, `GatewayResponse`, and `GatewayClient.create_response(...)`.
- Consumes: environment variables only.

- [ ] **Step 1: Write failing configuration and model tests**

```python
def test_trace_context_uses_bounded_tags_and_string_metadata():
    context = TraceContext(run_kind="eval", evaluation_split="test", case_id="case-7")
    body = context.extra_body(thread_id="thread-1")
    assert body["name"] == "PyData2026-AnalyticsChatbot"
    assert body["tags"] == ["pydata2026", "analytics-chatbot", "eval"]
    assert body["thread"] == {"id": "thread-1"}
    assert all(isinstance(value, str) for value in body["metadata"].values())


def test_conversation_has_stable_thread_id():
    conversation = Conversation()
    assert conversation.thread_id
    assert conversation.previous_response_id is None
```

- [ ] **Step 2: Run tests and confirm imports fail**

Run: `uv run pytest tests/test_config.py tests/test_models.py -q`

Expected: collection fails because `analytics_chatbot` does not exist.

- [ ] **Step 3: Add package metadata and dependencies**

Define Python `>=3.11` and dependencies `duckdb`, `openai`, `pydantic`, `pydantic-settings`, `typer`, `rich`, and `sqlglot`; add `pytest` and `pytest-mock` to the dev group. Register `analytics-chatbot = "analytics_chatbot.cli:app"`.

- [ ] **Step 4: Implement settings and shared models**

`Settings` defaults:

```python
gateway_base_url = "https://my.orq.ai/v3/router"
model = "deepseek/deepseek-v4-flash"
database_path = Path("data/analytics.duckdb")
runs_path = Path("runs")
max_tool_steps = 8
max_query_rows = 200
query_timeout_seconds = 10.0
dataset_version = "revenue-v1"
agent_version = "v1"
```

`TraceContext.extra_body(thread_id)` returns fixed `name`, bounded tags, `thread`, optional `identity`, and string-only metadata keys `dataset_version`, `agent_version`, `evaluation_split`, `case_id`, `interface`, and `run_kind`.

- [ ] **Step 5: Run tests and type/import smoke check**

Run: `uv run pytest tests/test_config.py tests/test_models.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit the package foundation**

```bash
git add pyproject.toml .env.example .gitignore src/analytics_chatbot tests/test_config.py tests/test_models.py
git commit -m "feat: scaffold analytics chatbot package"
```

### Task 2: Deterministic business dataset

**Files:**
- Create: `src/analytics_chatbot/data.py`
- Create: `tests/test_data.py`

**Interfaces:**
- Consumes: `Path` database destination and integer seed.
- Produces: `DatasetManifest`, `generate_orders(count=25_000, seed=2026)`, and `seed_database(path, count=25_000, seed=2026)`.

- [ ] **Step 1: Write failing deterministic generation tests**

```python
def test_seed_database_is_deterministic(tmp_path):
    first = seed_database(tmp_path / "first.duckdb")
    second = seed_database(tmp_path / "second.duckdb")
    assert first.row_count == second.row_count == 25_000
    assert first.content_hash == second.content_hash
    assert first.min_order_date.isoformat() == "2024-01-01"
    assert first.max_order_date.isoformat() == "2025-12-31"


def test_seeded_orders_cover_business_dimensions(tmp_path):
    path = tmp_path / "analytics.duckdb"
    seed_database(path)
    with duckdb.connect(str(path), read_only=True) as connection:
        result = connection.execute(
            "SELECT count(DISTINCT region), count(DISTINCT product_category), "
            "count(DISTINCT customer_segment) FROM orders"
        ).fetchone()
    assert result == (4, 4, 3)
```

- [ ] **Step 2: Run the data tests and confirm failure**

Run: `uv run pytest tests/test_data.py -q`

Expected: import or symbol failure.

- [ ] **Step 3: Implement deterministic row generation**

Use `random.Random(2026)` and standard-library dates. Generate order dates across every date from `2024-01-01` through `2025-12-31`, then deterministically assign region/country, category/product, segment, quantities, price, discount, status, refund, gross revenue, net revenue, and cost. Ensure cancelled orders contribute zero net revenue and refunds reduce net revenue.

- [ ] **Step 4: Create DuckDB and manifest atomically**

Create a temporary database beside the destination, insert typed rows in batches, create the `orders` table and useful date/region/category indexes, compute a stable aggregate hash, then replace the destination. Write `<database>.manifest.json` with schema version, seed, row count, date range, and content hash.

- [ ] **Step 5: Run dataset tests**

Run: `uv run pytest tests/test_data.py -q`

Expected: all tests pass in under five seconds.

- [ ] **Step 6: Commit dataset generation**

```bash
git add src/analytics_chatbot/data.py tests/test_data.py
git commit -m "feat: generate deterministic analytics dataset"
```

### Task 3: Guarded SQL and insight tools

**Files:**
- Create: `src/analytics_chatbot/sql_tool.py`
- Create: `src/analytics_chatbot/insights.py`
- Create: `tests/test_sql_tool.py`
- Create: `tests/test_insights.py`

**Interfaces:**
- Consumes: DuckDB path, run directory, `QuerySqlArgs`, and `SaveInsightArgs`.
- Produces: `SqlTool.execute(query) -> ToolResult` and `InsightStore.save(args) -> ToolResult`.

- [ ] **Step 1: Write failing SQL safety tests**

```python
@pytest.mark.parametrize("query", [
    "DELETE FROM orders",
    "SELECT 1; SELECT 2",
    "COPY orders TO '/tmp/orders.csv'",
    "SELECT * FROM read_csv_auto('/tmp/private.csv')",
])
def test_rejects_unsafe_sql(sql_tool, query):
    result = sql_tool.execute(query)
    assert result.ok is False
    assert result.error_code == "unsafe_sql"


def test_caps_query_rows(sql_tool):
    result = sql_tool.execute("SELECT * FROM orders ORDER BY order_id")
    assert result.ok is True
    assert len(result.data["rows"]) == 200
    assert result.data["truncated"] is True
```

- [ ] **Step 2: Write failing insight-state tests**

```python
def test_saves_structured_insight_and_changes_state(tmp_path):
    store = InsightStore(tmp_path)
    before = store.snapshot()
    result = store.save(SaveInsightArgs(title="EMEA growth", summary="Revenue rose.", supporting_sql="SELECT 1"))
    after = store.snapshot()
    assert result.ok is True
    assert before["count"] == 0
    assert after["count"] == 1
```

- [ ] **Step 3: Implement SQL validation and execution**

Parse with `sqlglot.parse(..., read="duckdb")`, require exactly one statement, allow query/describe/explain shapes, reject mutation commands and external/file functions, and execute through a read-only DuckDB connection. Fetch `max_rows + 1` rows to report truncation. Use a timer that calls `connection.interrupt()` at the configured timeout.

- [ ] **Step 4: Implement insight persistence**

Store one JSON object per insight in `insights.jsonl`, reject empty fields and paths outside the run directory, and compute `snapshot()` as a count plus SHA-256 digest of current contents.

- [ ] **Step 5: Run tool tests**

Run: `uv run pytest tests/test_sql_tool.py tests/test_insights.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit guarded tools**

```bash
git add src/analytics_chatbot/sql_tool.py src/analytics_chatbot/insights.py tests/test_sql_tool.py tests/test_insights.py
git commit -m "feat: add guarded analytics tools"
```

### Task 4: Gateway adapter and atomic run store

**Files:**
- Create: `src/analytics_chatbot/prompts.py`
- Create: `src/analytics_chatbot/gateway.py`
- Create: `src/analytics_chatbot/run_store.py`
- Create: `tests/test_gateway.py`
- Create: `tests/test_run_store.py`

**Interfaces:**
- Consumes: `Settings`, `TraceContext`, conversation thread/response IDs, tool schemas, and response input items.
- Produces: `OrqGateway.create_response(...) -> GatewayResponse` and `RunStore` event/finalization methods.

- [ ] **Step 1: Write failing gateway contract test**

```python
def test_gateway_sends_orq_attribution(mocker, settings):
    create = mocker.Mock(return_value=fake_text_response("ok"))
    client = mocker.Mock(responses=mocker.Mock(create=create))
    gateway = OrqGateway(settings, client=client)
    gateway.create_response(
        input_items="question",
        conversation=Conversation(thread_id="thread-1"),
        trace_context=TraceContext(run_kind="eval"),
        tools=[],
    )
    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "deepseek/deepseek-v4-flash"
    assert kwargs["extra_body"]["tags"] == ["pydata2026", "analytics-chatbot", "eval"]
    assert kwargs["extra_body"]["thread"] == {"id": "thread-1"}
```

- [ ] **Step 2: Write failing atomic-run test**

```python
def test_finalize_atomically_promotes_partial_run(tmp_path):
    store = RunStore(tmp_path, run_id="run-1")
    store.append({"type": "user_message", "content": "hello"})
    final_path = store.finalize({"status": "completed"})
    assert final_path.name == "events.jsonl"
    assert not (final_path.parent / "events.partial.jsonl").exists()
```

- [ ] **Step 3: Implement prompt and tool schemas**

The system prompt requires factual claims to be supported by SQL, instructs the model to distinguish gross/net/refund/cancelled semantics, and tells it that `save_insight` appears only for explicit persistence requests. Define Responses API function tools for `query_sql` and `save_insight`.

- [ ] **Step 4: Implement the orq gateway adapter**

Initialize `OpenAI(api_key=..., base_url="https://my.orq.ai/v3/router")`. Call `responses.create` with model, instructions, input, tools, `previous_response_id`, `store=True`, and `extra_body=trace_context.extra_body(thread_id)`. Normalize text, function calls, usage, response ID, and provider errors into shared models.

- [ ] **Step 5: Implement atomic run storage**

Append canonical JSON events to `events.partial.jsonl`, flushing each line. On completion, append the terminal event, close the handle, and `Path.replace()` it to `events.jsonl`. Preserve partial files after errors for diagnosis but mark their run status separately.

- [ ] **Step 6: Run gateway and persistence tests**

Run: `uv run pytest tests/test_gateway.py tests/test_run_store.py -q`

Expected: all tests pass with no network calls.

- [ ] **Step 7: Commit gateway boundary**

```bash
git add src/analytics_chatbot/prompts.py src/analytics_chatbot/gateway.py src/analytics_chatbot/run_store.py tests/test_gateway.py tests/test_run_store.py
git commit -m "feat: add orq gateway and run tracing"
```

### Task 5: Bounded analytics agent loop

**Files:**
- Create: `src/analytics_chatbot/agent.py`
- Create: `tests/test_agent.py`

**Interfaces:**
- Consumes: `GatewayClient`, `SqlTool`, `InsightStore`, `RunStore`, `Settings`, and `TraceContext`.
- Produces: `AnalyticsChatbot.new_conversation(...)` and `AnalyticsChatbot.ask(message, conversation=None, context=None) -> AgentResponse`.

- [ ] **Step 1: Write failing tool-loop tests**

```python
def test_executes_sql_then_returns_answer(chatbot, fake_gateway):
    fake_gateway.queue_function_call("query_sql", {"query": "SELECT sum(net_revenue) AS revenue FROM orders"})
    fake_gateway.queue_text("Net revenue is 123.45.")
    response = chatbot.ask("What is total net revenue?")
    assert response.answer == "Net revenue is 123.45."
    assert [call.name for call in response.tool_calls] == ["query_sql"]


def test_save_tool_is_not_exposed_without_explicit_request(chatbot, fake_gateway):
    chatbot.ask("What is EMEA revenue?")
    assert "save_insight" not in fake_gateway.calls[0].tool_names


def test_save_tool_is_exposed_for_explicit_request(chatbot, fake_gateway):
    chatbot.ask("Calculate EMEA revenue and save that insight.")
    assert "save_insight" in fake_gateway.calls[0].tool_names
```

- [ ] **Step 2: Add failure tests**

Cover malformed tool JSON, unknown tool names, repeated identical tool calls, gateway errors, and the eight-step limit. Assert each error remains in the returned trajectory and local run record.

- [ ] **Step 3: Implement public API and loop**

Create/resume `Conversation`, build run-specific `InsightStore` and `RunStore`, select tools from explicit save-intent detection, and repeatedly call the gateway. Execute function calls, append `function_call_output` items using their `call_id`, and pass the preceding response ID into the next call. Detect repeated `(name, canonical_arguments)` pairs and stop after `max_tool_steps`.

- [ ] **Step 4: Capture trajectory and state**

Record user input, every gateway request/response summary, tool arguments/results, duration, errors, and insight snapshot before/after each state-changing tool. Return `AgentResponse` with answer, run ID, thread ID, response ID, tool calls, state changes, usage, and artifact path.

- [ ] **Step 5: Run agent tests and full offline suite**

Run: `uv run pytest -m "not live" -q`

Expected: all offline tests pass.

- [ ] **Step 6: Commit the agent loop**

```bash
git add src/analytics_chatbot/agent.py tests/test_agent.py
git commit -m "feat: implement analytics agent tool loop"
```

### Task 6: CLI and documentation

**Files:**
- Create: `src/analytics_chatbot/cli.py`
- Create: `tests/test_cli.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `Settings`, `seed_database`, `AnalyticsChatbot`, and saved run paths.
- Produces: terminal and JSON interfaces for `seed-data`, `ask`, `chat`, and `show-run`.

- [ ] **Step 1: Write failing CLI tests**

```python
def test_seed_data_command(runner, tmp_path):
    result = runner.invoke(app, ["seed-data", "--database", str(tmp_path / "analytics.duckdb")])
    assert result.exit_code == 0
    assert "25,000" in result.stdout


def test_ask_json_output_uses_injected_chatbot(runner, fake_chatbot):
    result = runner.invoke(app, ["ask", "total revenue", "--json"])
    assert result.exit_code == 0
    assert '"thread_id"' in result.stdout
```

- [ ] **Step 2: Implement Typer commands**

`seed-data` generates the database; `ask` supports `--json`, `--show-trajectory`, identity, split, case ID, and run kind; `chat` reuses one conversation until `/quit`; `show-run` reads finalized or partial JSONL and renders ordered events.

- [ ] **Step 3: Rewrite README as a runnable example**

Document `uv sync`, `uv run analytics-chatbot seed-data`, credential setup, `ask` and `chat`, Python usage, trace attribution semantics, run artifacts, safety limits, tests, and the opt-in live command. Link the talk abstract and design spec.

- [ ] **Step 4: Run CLI tests and lint**

Run: `uv run pytest -m "not live" -q`

Run: `uv run ruff check .`

Expected: all tests and lint checks pass.

- [ ] **Step 5: Commit CLI and docs**

```bash
git add src/analytics_chatbot/cli.py tests/test_cli.py README.md
git commit -m "feat: add analytics chatbot CLI"
```

### Task 7: Provision orq project and verify live tracing

**Files:**
- Create: `tests/test_live_gateway.py`
- Create locally but never commit: `.env`

**Interfaces:**
- Consumes: authenticated `orq` CLI session/management credential and the completed CLI.
- Produces: `pydata2026` project, project-scoped inference key, local `.env`, and one identifiable live trace.

- [ ] **Step 1: Confirm workspace and existing project state**

Run generated commands with `ORQ_API_KEY` unset and the refreshed `<workspace>` workspace token supplied to `ORQ_TOKEN` in-memory:

```bash
orq doctor --json
orq projects list --limit 200 --json
```

Expected: active workspace is `<workspace>`; no existing project named `pydata2026`, or reuse exactly one existing match.

- [ ] **Step 2: Create the project if absent**

```bash
orq projects create \
  --name pydata2026 \
  --description "Analytics chatbot for the PyData 2026 agent-evaluation talk" \
  --json
```

Capture the returned project ID without printing credentials.

- [ ] **Step 3: Create a least-privilege project key**

First read the live capability catalog. Then create a project-scoped key with response-write and model-read access:

```bash
orq api-keys create \
  --name pydata2026-analytics-chatbot \
  --project-scope '{"single":{"project_id":"<PROJECT_ID>"}}' \
  --permission-mode PERMISSION_MODE_RESTRICTED \
  --access '{"responses":"ACCESS_LEVEL_WRITE","model":"ACCESS_LEVEL_READ"}' \
  --json
```

Write the one-time token to ignored `.env` along with the base URL and model. Set file mode `0600`; never emit its contents.

- [ ] **Step 4: Add opt-in live smoke test**

```python
@pytest.mark.live
def test_live_agent_queries_sql_and_returns_trace_identity(seeded_settings):
    response = AnalyticsChatbot(settings=seeded_settings).ask(
        "What was net revenue by region in 2025?",
        context=TraceContext(run_kind="smoke", interface="pytest"),
    )
    assert response.answer
    assert any(call.name == "query_sql" and call.result.ok for call in response.tool_calls)
    assert response.thread_id
```

- [ ] **Step 5: Run local seed and live smoke**

Run: `uv run analytics-chatbot seed-data`

Run: `ANALYTICS_CHATBOT_LIVE_TEST=1 uv run pytest tests/test_live_gateway.py -m live -q`

Expected: database generation succeeds; live test passes and returns a thread ID.

- [ ] **Step 6: Verify trace through the orq CLI**

Use `orq traces search` or `orq traces query-oql` to find the recent trace by `PyData2026-AnalyticsChatbot`, confirm project attribution, tags `pydata2026` and `analytics-chatbot`, thread ID, model `deepseek/deepseek-v4-flash`, and string-valued metadata. Do not expose raw credentials or user content in the report.

- [ ] **Step 7: Run final verification and commit the live test**

Run: `uv run pytest -q`

Run: `uv run ruff check .`

Run: `git status --short`

Expected: all default tests pass with the live test skipped unless enabled; lint passes; only the user’s pre-existing untracked files remain.

```bash
git add tests/test_live_gateway.py
git commit -m "test: verify live orq gateway tracing"
```

## Final Verification

- [ ] `uv run analytics-chatbot seed-data` creates 25,000 deterministic orders spanning exactly 24 months.
- [ ] `uv run analytics-chatbot ask "What was month-over-month EMEA net revenue growth in Q3 2025?" --show-trajectory` performs SQL and answers from its result.
- [ ] An explicit “save this insight” request produces a verifiable state transition; ordinary questions cannot access `save_insight`.
- [ ] `uv run pytest -q` and `uv run ruff check .` pass.
- [ ] The orq CLI finds the live trace under project `pydata2026`, fixed tags, stable thread, and expected metadata.
- [ ] `.env`, DuckDB files, and run artifacts are ignored; no credential appears in Git history or command output.
