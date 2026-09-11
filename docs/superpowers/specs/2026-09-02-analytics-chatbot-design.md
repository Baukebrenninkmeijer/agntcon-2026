# Analytics Chatbot Design

> **Revision, 2026-09-03:** The operational loop and function execution remain local, but the model, instructions, and function declarations now live in a hosted orq Agent. The evaluation layer is now in scope; its current state lives in the [delivery plan](../plans/2026-09-03-project-status-and-handoff.md). This revision supersedes the original hosted-agent and evaluator exclusions below; it does not introduce remote function execution or a self-learning loop.

## Purpose

Build the operational data-analysis agent used throughout the PyData 2026 talk. The example must be small enough to teach from, realistic enough to produce meaningful agent failures, and observable enough to evaluate its final answer, tool trajectory, multi-turn behavior, and state changes.

The orchestration loop, DuckDB access, and function execution run locally. Model configuration lives in a hosted orq Agent, and model requests use the orq AI Gateway Responses API so the platform captures traces. The repository and orq project are named `pydata2026`; the Python distribution is `analytics-chatbot`, the import package is `analytics_chatbot`, and the CLI command is `analytics-chatbot`.

## Scope

The first version includes:

- A local agent loop using the OpenAI-compatible orq AI Gateway Responses API.
- A deterministic synthetic business dataset stored in DuckDB.
- A read-only SQL tool.
- A tool that saves structured analysis insights to run-scoped local state.
- A Python API and terminal CLI.
- Gateway trace attribution and a local JSONL audit trail.
- Unit, integration, and opt-in live smoke tests.

The initial implementation excluded evaluators and hosted configuration. The 2026-09-03 evaluation plan adds hosted Agent configuration, evaluators, judge alignment, and reviewed prompt iteration as a separate operational layer. A self-learning loop, unreviewed prompt mutation, a web UI, and the previous flight-delay dataset remain excluded.

## Architecture

The implementation has six focused components:

1. `config`: validates environment-based gateway and runtime settings.
2. `data`: generates a fixed-seed synthetic order dataset and opens it read-only through DuckDB.
3. `tools`: validates and executes `query_sql` and `save_insight` calls.
4. `gateway`: wraps the OpenAI client configured for the orq Responses API.
5. `agent`: owns the bounded model/tool loop and exposes the public Python API.
6. `runs`: persists local messages, tool calls, timings, errors, and state snapshots as JSONL.

The boundaries remain framework-neutral. The agent depends on a gateway protocol rather than a concrete client in tests, and tools expose typed request/result models. This keeps model calls mockable and allows the operational mechanics to remain visible during the talk.

## Dataset

The setup command generates 25,000 reproducible synthetic orders covering 24 months from a fixed seed. Generation returns a Polars `LazyFrame`; derived financial columns remain lazy and are streamed to Parquet before DuckDB materializes explicitly typed decimal columns. This contains enough variation and edge cases to support realistic business questions without external downloads while remaining fast and memory-conscious on a laptop.

The primary `orders` table includes:

- order and customer identifiers;
- order date and month;
- region and country;
- product and product category;
- customer segment;
- quantity, unit price, discount, gross revenue, net revenue, and cost;
- order status and refund amount.

Generation includes partial months, discounts, refunds, cancellations, and uneven regional/product distributions. These create useful failure modes such as using gross instead of net revenue, including cancelled orders, averaging percentages incorrectly, and comparing incomplete periods.

The generated database is an artifact, not committed source data. A small manifest records the seed, schema version, row count, and date range. Tests generate temporary databases.

## Tools

### `query_sql`

Executes one read-only DuckDB query and returns column names, rows, truncation status, and execution time.

Guardrails:

- exactly one statement;
- only `SELECT`, `WITH`, `DESCRIBE`, or `EXPLAIN` entry points;
- mutation and filesystem-related statements are rejected;
- execution uses a read-only connection;
- result rows are capped;
- tool failures become structured results that the model can correct on the next step.

This is deliberately a safety boundary in code rather than a prompt-only instruction.

### `save_insight`

Stores a structured record containing a title, summary, supporting SQL, and optional tags. Records are written beneath the active run directory and never mutate the source dataset. The run log captures state before and after the call, providing a concrete state transition for evaluation. The system prompt permits this tool only when the user explicitly asks to save, remember, or preserve a finding; ordinary analysis must remain read-only.

## Agent Flow

For each user turn:

1. Create or resume a conversation with a stable thread ID.
2. Add the user message to local history.
3. Send history, system instructions, and tool definitions to the orq Gateway Responses API.
4. Attach consistent trace attribution to every model step.
5. If the response requests tools, validate and execute them locally, append results, and call the model again.
6. Stop when the model returns a final answer, reaches the configured step limit, or encounters a terminal gateway error.
7. Persist the complete local run record and return a typed response containing the answer, thread ID, tool trajectory, state changes, and usage where available.

Multi-turn calls reuse the same thread ID and conversation object. Each model step is independently traced by the gateway but remains associated with the same thread.

## Trace Attribution

Gateway requests use:

- `name`: `PyData2026-AnalyticsChatbot`;
- project: the orq project `pydata2026` when project attribution is supported by the selected API key;
- thread: one stable ID per conversation, with tags `pydata2026`, `analytics-chatbot`, plus one
  bounded run-mode tag such as `interactive` or `eval`;
- identity: the actual caller or evaluation actor when supplied, not a substitute for arbitrary grouping;
- metadata: string-valued `dataset_version`, `agent_version`, `evaluation_split`, `case_id`, `interface`, and `run_kind` fields.

Tags, identity, and project are aggregation dimensions in the public reporting API. Arbitrary metadata is intended for trace filtering, not reporting `group_by`. Dynamic request and case identifiers remain in the thread or metadata rather than tags to avoid high-cardinality tag sets.

The local JSONL log is the exact operational record used by offline tests. It includes information that may span several gateway traces: ordered messages, raw tool arguments, structured tool results, duration, model usage, errors, and insight-state snapshots. Secrets and personal data are never written to request attributes or local logs.

## Interfaces

### Python API

`AnalyticsChatbot` provides:

- `ask(message, conversation=None, context=None)`;
- `new_conversation(context=None)`;
- access to the typed response, trajectory, and saved state.

Gateway and tool dependencies can be injected for deterministic testing.

### CLI

The `analytics-chatbot` command provides:

- `seed-data`: build or rebuild the deterministic DuckDB dataset;
- `ask`: run one question and print the answer with an optional trajectory view;
- `chat`: start a multi-turn terminal session;
- `show-run`: inspect a saved local run and its state transitions.

CLI output is readable by default and offers JSON output for scripts and later evaluation workflows.

## Configuration

Configuration is environment-driven and documented in `.env.example`:

- `ORQ_API_KEY`;
- `ORQ_GATEWAY_BASE_URL`, defaulting to `https://api.orq.ai/v3/router`;
- `ANALYTICS_CHATBOT_MODEL`, defaulting to the Model Garden identifier `deepseek/deepseek-v4-flash` (`DeepSeek-V4-Flash-0731`);
- database and run-artifact paths;
- maximum tool steps, query rows, and query duration;
- dataset and agent versions.

The application fails early with an actionable message when live gateway credentials are missing. Offline data generation, run inspection, and tests do not require credentials.

## Error Handling

- Invalid SQL returns a structured tool error and remains visible in the trajectory.
- DuckDB execution errors are sanitized but specific enough for model self-correction.
- Gateway authentication, rate-limit, timeout, and provider errors map to typed application errors.
- A repeated-tool-call detector and maximum-step limit prevent infinite loops.
- Run artifacts are written atomically so an interrupted call does not leave a valid-looking partial record.
- `save_insight` validates required fields and writes only within the configured run directory.

## Testing

The default test suite performs no network calls and covers:

- deterministic dataset generation and known aggregate values;
- SQL allow/deny cases, row caps, and read-only enforcement;
- single-step answers and multi-step tool loops with a fake gateway;
- malformed arguments, tool errors, repeated calls, and step limits;
- saved-insight state before and after mutation;
- fixed trace name, bounded tags, thread reuse, and string-only metadata;
- Python API and CLI behavior;
- atomic local run persistence.

An opt-in live smoke test sends one cheap question through the orq gateway, confirms the response uses SQL, and reports the thread and trace attribution needed for manual verification in orq. It is skipped unless credentials and an explicit live-test flag are present.

## External Project Setup

After implementation begins, use the `orq` CLI—not `orqi`—to create a project named `pydata2026` in the `<workspace>` workspace. The command must first confirm the active workspace and whether a project with that key already exists. If the CLI session cannot authenticate without an environment API key, repair CLI authentication without persisting or exposing a workspace key in repository files.

## Completion Criteria

The work is complete when:

- the package installs with `uv` and the CLI starts;
- the deterministic dataset can be generated locally;
- mocked tests pass without network access;
- a local conversation can execute SQL, return a final answer, save an insight, and expose its ordered trajectory and state transition;
- every gateway request applies the agreed project, name, tags, thread, identity, and metadata semantics;
- the `pydata2026` project exists in the `<workspace>` workspace;
- an opt-in live smoke test confirms gateway connectivity and leaves easily distinguishable traces.
