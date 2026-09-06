# analytics-chatbot

The operational data-analysis agent for the PyData 2026 talk, [Evaluating Agents at Scale](abstract.md).
It answers business questions against a deterministic local DuckDB dataset, calls the model through
the orq AI Gateway, and records the final response, tool trajectory, and state changes needed by the
evaluation loop. Improvements remain human-reviewed and versioned; there is no self-learning loop.

## The production evaluation flywheel

![Production evaluation flywheel: interactions with the Sphere.com analytics agent create traces; recorded responses are replayed as evaluatorq DataPoints and assessed by deterministic checks plus one pending decision-support-quality jury before human alignment and reviewed improvements.](docs/assets/evaluation-flywheel.svg)

Production interactions call guarded local tools, emit Orq traces, and write exact local run audits.
A read-only adapter imports hydrated supported traces—or a successfully finalized audit when the
public trace omits replay evidence—into an evaluatorq `DataPoint` without guessing. Its current
generic replay input is being adapted to the versioned row that preserves retrievals, errors, and
state. evaluatorq replays the recorded answer without calling the target agent. The current
subjective path routes only the full agent-visible conversation and final response to one repeated
three-model `decision_support_quality` jury. Human labels and disagreement analysis must calibrate
that jury before reviewed changes return to the agent or evaluator.

The visual also marks delivery state without conflating it with architecture: the local runtime,
trace capture, DataPoint contract, and evaluator framework are integrated; trace import, hosted
resources, and the hosted/local bridge are active; human alignment and the improvement loop remain
dependency-gated. The SVG is the canonical, slide-ready asset.

## Setup

Requirements: Python 3.11+, `uv`, and an orq project API key with Responses write access.
The package loads `.env` with `python-dotenv` using `override=True`, so its project-scoped key wins
over a stale inherited shell value.

```bash
uv sync
cp .env.example .env
# Add the pydata2026 project's ORQ_API_KEY to .env.
uv run analytics-chatbot seed-data
```

## Sync hosted Orq resources

Repository-owned definitions for the hosted agent, its two local function tools, and evaluators
live under `orq/resources/`. Preview the semantic reconciliation plan first, then apply it
explicitly:

```bash
make sync-orq
make sync-orq-apply
```

Both commands require the existing `pydata2026` project's `ORQ_API_KEY` in `.env`. The sync verifies
the locked project key and ID, follows list pagination, refuses duplicate resource keys, and never
creates a project. Repeating the apply command is safe: a successful second pass reports only
no-op resources.

The repository contains one pending `analytics-decision-support-quality` LLM jury and two
historical Python evaluator definitions. The jury is reference-free, uses the approved three-model
panel with three repetitions, and accepts only the full ordered conversation plus final response.
Its `pending_human_labels` status blocks remote apply; it has zero human labels, and no hosted apply
is authorized by the repository change. An authenticated read-only snapshot and dry-run semantic
plan remain allowed; applying hosted changes requires separate, explicit operator authorization.
The Python evaluators are stdlib-only, AST-checked, and unit-executed locally. To reconcile only an
already-reviewed subset, pass `--kinds tool`, `--kinds agent`, or `--kinds evaluator` to the sync
script; the Makefile target always covers the complete bundle.

## Current v4 review pool

The current Sphere.com v4 corpus contains 50 decision-context-enriched definitions with the frozen
30-development/20-test assignment. It has zero observations, zero jury results, and zero human
labels. Do not describe these definitions as reviewed examples or run them without the separate
simulation, evaluatorq-release, and paid-call approvals recorded in the living delivery plan.

## Historical v1-v3 execution evidence

Generate the deterministic 50-case evaluatorq input corpus and run a bounded simulation with:

```bash
uv run python scripts/generate_simulation_cases.py
uv run python scripts/run_agent_smoke.py
uv run python scripts/run_simulation.py \
  --limit 50 \
  --max-turns 3 \
  --output runs/evaluatorq-simulation-50-20260905.jsonl
```

These commands and the following replay results document the superseded v1-v3 correctness-first
work; they are not the current v4 execution path. The historical harder multi-turn corpus is
generated separately:

```bash
uv run python scripts/generate_simulation_cases.py --variant edge-v2
```

Its single approved live run used the tracked v2 definitions, a distinct
evaluation name, and distinct ignored output/report paths. It produced 50
unique rows: eight one-turn, 22 two-turn, and 20 three-turn conversations.
Forty rows achieved their simulated goal and ten behavioral failures were
retained. Do not rerun the frozen v2 corpus to replace failures.

`scripts/run_simulation.py` loads `.env` with `override=True` before importing evaluatorq, passes
`save=True`, and exports the returned raw `SimulationResult` rows to `--output`. Datapoints run with
bounded concurrency while each conversation retains isolated state. On 2026-09-05 the explicitly
approved baseline run produced 50 unique local outputs. The separate edge-v2
run produced 50 more. Simulation outcomes are not structural validity gates:
the adapter retains failed behavior and reports expected-tool misses as QC
warnings. Preserve and replay all 50 v2 rows; warnings are informational and do
not filter the corpus. Simulation outputs and exact local run artifacts remain
under ignored runtime directories.

Historically, the frozen edge-v2 observations were replayed through an explicit hosted evaluator
version with:

```bash
uv run python scripts/run_evaluatorq_replay.py \
  --evaluator-version 1.0.0 \
  --output runs/evaluatorq-correctness-v1.0.0-20260905.jsonl \
  --datapoint-parallelism 10 \
  --llm-parallelism 10
```

The command resolves the stable `analytics-answer-correctness` key at runtime,
verifies the requested version exists, rejects `latest`, and runs all 50 stored
responses with evaluatorq `inference=False`. It uploads a native Orq Experiment
with `pydata2026` as the requested project path and hides local score output by
default. As of 2026-09-05, production still has the known backend issue
[BOPS-1180](https://linear.app/orqai/issue/BOPS-1180/evaluatorq-experiments-ignore-path-always-land-in-the-default-project):
the evaluatorq ingest route accepts but ignores that path and places the Experiment
in the workspace's Default project. Do not retry merely to change placement until
that fix leaves Testing. The latest uniquely named 50-row run is retained only as a
[diagnostic run with an invalid empty correctness column](https://my.orq.ai/<workspace>/experiments/01M1RGTTZV0XPJ1DWHE0EASXYZ?runId=01M1RGTTZTBA7FSQV07K85HGG8):
its export contains zero populated scores. The replay scorer now calls the pinned
evaluator through one shared asynchronous HTTP client because orq-ai-sdk 4.14.7 drops
the current top-level v3 evaluator response. Run a fresh uniquely named baseline and
verify 50/50 exported scores before using it for alignment.
The async scorer has been validated end to end with a
[three-row evaluatorq smoke Experiment](https://my.orq.ai/<workspace>/experiments/01M1RJ2TZR2WMEEED158F5V72W?runId=01M1RJ2TZQF4QVGRAC10BN0R34):
the Orq JSONL export contains three rows and three populated
`answer_correctness@1.0.0` values.
The accepted [50-row correctness baseline](https://my.orq.ai/<workspace>/experiments/01M1RJVCF5SGV97CRZBWC993BQ?runId=01M1RJVCF5NCTVMFXEX1FB28TX)
also exports 50/50 populated scores: 47 `pass` and three `fail`. Its validated
local alignment artifact is written to
`runs/evaluatorq-correctness-v1.0.0-20260905.jsonl`; `runs/` is gitignored.
Repeat `--evaluator-version` after an
approved evaluator update to create distinct side-by-side columns such as
`answer_correctness@1.0.0` and `answer_correctness@1.0.1` over identical rows.
Runtime evaluator IDs remain untracked.

Data generation uses a Polars `LazyFrame`, streams 25,000 fixed-seed orders to Parquet, then
materializes explicitly typed decimal columns in DuckDB. The generated database and manifest are
ignored by Git.

## Run it

```bash
uv run analytics-chatbot ask "What was net revenue by region in 2025?"
uv run analytics-chatbot ask \
  "Calculate EMEA revenue and save that insight" \
  --show-trajectory
uv run analytics-chatbot chat
uv run analytics-chatbot show-run RUN_ID
```

For evaluation cases, attach stable attribution without creating high-cardinality tags:

```bash
uv run analytics-chatbot ask "What is month-over-month EMEA growth in Q3 2025?" \
  --run-kind eval \
  --split test \
  --case-id revenue-growth-07 \
  --identity evaluation-runner \
  --json
```

Python usage:

```python
from analytics_chatbot import AnalyticsChatbot
from analytics_chatbot.config import TraceContext

agent = AnalyticsChatbot()
conversation = agent.new_conversation()
result = agent.ask(
    "What was net revenue by product category in 2025?",
    conversation=conversation,
    context=TraceContext(run_kind="eval", evaluation_split="dev", case_id="case-01"),
)
print(result.answer)
print(result.tool_calls)
```

## Observability and safety

Every gateway request uses model `deepseek/deepseek-v4-flash`, trace name
`PyData2026-AnalyticsChatbot`, and a stable conversation thread tagged `pydata2026`,
`analytics-chatbot`, and the bounded run kind. Identity is used for caller/evaluation-actor grouping. String metadata
contains dataset version, agent version, evaluation split, case ID, interface, and run kind. The
public reporting surface can aggregate by project, identity, and tag; arbitrary metadata is useful
for filtering traces rather than `group_by`.

Each turn also writes an exact ordered JSONL record beneath `runs/RUN_ID/`. Successful runs atomically
become `events.jsonl`; interrupted runs retain `events.partial.jsonl`. This local artifact joins the
gateway steps, tool inputs/results, token usage, failures, and insight snapshots into one evaluation
record.

SQL is parsed before execution, restricted to one read-only statement, executed through a read-only
DuckDB connection, capped at 200 rows, and interrupted after 10 seconds by default. The source data
is never mutated. `save_insight` is only exposed when the user explicitly asks to save, remember,
store, keep, or preserve a finding, and it writes only within the active run directory.

## Tests

The offline CI gate requires no Orq credentials and runs the same checks on pull requests and pushes
to `main`. Run it locally with the locked environment:

```bash
uv sync --locked --dev
uv run --no-sync ruff check .
uv run --no-sync pytest -m "not live and not simulation_live and not alignment_live" -q
uv build
```

CI also loads and validates `orq/resources` when the repository's local resource loader is present.
It never runs resource synchronization or any other command that contacts Orq. Live tests remain
explicitly opt-in:

```bash
ANALYTICS_CHATBOT_LIVE_TEST=1 uv run pytest tests/test_live_gateway.py -m live -q
```

See the [design specification](docs/superpowers/specs/2026-09-02-analytics-chatbot-design.md) for the
component boundaries and trace semantics, or [open the flywheel SVG directly](docs/assets/evaluation-flywheel.svg)
for presentation use.
