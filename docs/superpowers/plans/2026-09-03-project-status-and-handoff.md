# PyData 2026 Evaluation Delivery Plan and Task Log

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maintain one accurate handoff view from the verified analytics chatbot through trace import, hosted-resource synchronization, evaluatorq simulation, judge alignment, and CI.

**Architecture:** The chatbot executes guarded analytics tools locally while Orq provides hosted agent configuration and trace storage. evaluatorq is the only evaluation runner: imported traces become evaluatorq `DataPoint`s, recorded outputs are replayed without target inference, and four atomic judges receive independently scoped evidence.

**Tech stack:** Python 3.11+, DuckDB, Polars, Pydantic, Orq SDK and Responses API, evaluatorq 1.33.0, pytest, Ruff, YAML, and Make.

## Global Constraints

- Target the existing Orq project named `pydata2026`; do not create a replacement project.
- The chatbot's DuckDB queries and insight persistence execute locally. Hosted function resources are declarations, not remote tool execution.
- Repository YAML is the source of truth for hosted resources. Transformation and synchronization must be idempotent and safe by default.
- The same YAML/Orq SDK reconciliation path owns the hosted agent, tools, two deterministic evaluators, and four LLM-as-a-judge evaluators. Keep one YAML file per evaluator and do not manage evaluator resources through an ad hoc side path.
- evaluatorq owns evaluation execution, concurrency, tracing, result presentation, and Experiment upload. Do not add a bespoke evaluator execution loop.
- Trace replay must not rerun the source agent or infer a replacement answer.
- Keep the four judges independently routed and aligned: answer correctness, query semantics, evidence faithfulness, and multi-turn consistency.
- Never commit credentials, temporary trace exports, private trace content, or runtime-resolved opaque identifiers.
- A temporary trace-access key may exist only in a verified Git-ignored local environment file and must be rotated after the trace-validation work.
- Completed, verified task branches are integrated into local `main`. Do not push to a remote unless separately requested.

---

## Document Maintenance

**Status date:** 2026-09-05, Europe/Amsterdam.

**Last-updated rule:** Change the status date whenever a checkbox, workstream state, dependency, acceptance result, remote-state observation, or decision changes. Add one compact changelog entry containing the date, affected workstream, evidence, and next handoff. Do not mark work complete from code presence alone.

**Status taxonomy:**

| Status | Meaning | Required evidence |
|---|---|---|
| `VERIFIED` | Implemented, reviewed to the appropriate level, checks pass, and integrated into local `main` | Commit on local `main` plus recorded test/lint or live evidence |
| `ACTIVE` | Work is in progress in an isolated task/worktree and is not yet integrated | Named owner/task, dependency state, and explicit acceptance criteria |
| `BLOCKED` | Work cannot make safe progress without a missing decision, credential, compatible API, or dependency | Blocker, owner, and unblock condition |
| `NOT STARTED` | Planned work has no accepted implementation yet | Dependencies and first concrete action |
| `SUPERSEDED` | Retained only as historical context; must not be implemented | Link to the replacing decision or design |

## Current Snapshot

| Area | Status | What is true now | Next gate |
|---|---|---|---|
| Analytics chatbot core | `VERIFIED` | Deterministic data, guarded SQL, insight state, agent loop, CLI, local run audit, and Orq tracing are implemented on local `main` | Preserve behavior while introducing hosted configuration |
| evaluatorq-native judge framework | `VERIFIED` | Stable trace-backed row contract, rubric routing, evidence projection, evaluatorq experiment entry point, and focused tests are on local `main` | Importer must emit the same row contract |
| Orq trace importer | `ACTIVE` | Multi-format trace and exact run-audit normalization are integrated on local `main`; the importer still emits a generic evaluatorq `DataPoint` rather than the accepted `trace-eval-v1` row | Adapt the importer to the stable row contract, add the Orq scorer factory, and validate against genuine multi-step agent traces |
| Hosted resources and simulation | `ACTIVE` | Local `main` contains the YAML/SDK reconciler, hosted agent/tools, six gated evaluator drafts, an initial target adapter, 50 deterministic candidate cases, a three-attempt pilot review, and a lightweight raw-simulation normalizer; all three ignored pilot artifacts pass the adapter's downstream sufficiency checks | Remove the tracked project ID, obtain a fresh read-only remote plan, then human-review/freeze the cases before any bulk live run |
| Offline CI | `VERIFIED` | The credential-free GitHub Actions workflow is integrated on local `main` with pinned actions, explicit live-marker exclusion, lint, tests, package build, and an optional YAML-validation hook | Re-run the same gate after dependency or hosted-resource changes; remote-run evidence awaits publication |
| Human labeling and judge alignment | `NOT STARTED` | Rubrics and thresholds are designed, but accepted labels and alignment reports do not exist | Requires frozen cases and canonical observed traces |
| Live stability baseline and post-hoc operations | `NOT STARTED` | The run shape is designed, but no accepted baseline or operations report exists | Requires aligned judges, budgets, and live-run controls |

The latest local verification for the integrated tree is `71 passed, 1 deselected` for the non-live pytest selection, `All checks passed` from Ruff, and a successful sdist/wheel build on 2026-09-03. Resource loading found one agent, two tools, two deterministic evaluators, and four human-label-gated LLM evaluators. The 50-case corpus reproduced exactly from freshly executed DuckDB oracles with a 30-dev/20-test split. The primary checkout had no `.env`, so a fresh remote dry-run was unavailable; no remote request or mutation occurred.

## Objectives

- Provide a small, observable analytics agent suitable for the PyData 2026 evaluation narrative.
- Keep execution safety visible: read-only SQL, bounded local tool execution, explicit authorization for saved insights, and deterministic data/oracles.
- Make hosted agent, tool, and evaluator configuration reproducible from reviewed YAML and synchronize it to the existing Orq project without duplicates.
- Generate and freeze exactly 50 evaluatorq simulation cases with stable IDs, executable DuckDB oracles, required failure-mode coverage, and a fixed 30-dev/20-test split.
- Import genuine Orq agent traces into a durable evidence contract without guessing missing content or rerunning the agent.
- Align four atomic judges independently against human labels and retain the raw evidence each rubric needs.
- Keep offline CI independent from live credentials and make live canaries/baselines explicit, budgeted operations.
- Make every handoff answerable from Git: current status, evidence, dependency, owner/task name, risk, and next action.

## Non-goals

- A self-learning system, automatic evaluator rewriting, or unreviewed prompt mutation.
- A second evaluation runner, project-specific `PosthocTraceEvaluator`, custom row-by-row execution loop, or evaluation JSONL ledger.
- Treating machine evaluator output as human annotation.
- Remote execution of `query_sql` or `save_insight`.
- Creating another Orq project or relying on hard-coded remote identifiers.
- A web UI, source-dataset mutation, external data access, or a production deployment.
- Pushing commits, opening a pull request, or changing remote Orq state as part of documentation maintenance.

## Sources of Truth

Use these documents by precedence rather than copying their full contents here:

1. [Evaluator-native trace evaluation design](../specs/2026-09-03-evaluator-native-trace-evaluation-design.md) — current trace row, atomic judge, evidence-routing, replay, and alignment contract.
2. [Hosted Orq agent and evaluation operations plan](2026-09-03-orq-agent-simulation.md) — detailed resource, simulation, corpus, alignment, stability, and operations tasks. Its evaluator-native revision governs over older post-hoc steps.
3. [Analytics chatbot design](../specs/2026-09-02-analytics-chatbot-design.md) — local execution, safety, dataset, trace attribution, and public API boundaries, subject to its hosted-agent/evaluation revision note.
4. [Analytics chatbot implementation plan](2026-09-02-analytics-chatbot.md) — completed core implementation history.
5. [Post-hoc trace evaluation design](../specs/2026-09-02-posthoc-trace-evaluation-design.md) — `SUPERSEDED` for evaluator execution, service, CLI loop, and evaluation ledger. Consult only for still-relevant read-only mapping and provenance concerns.
6. [Original post-hoc implementation plan](2026-09-02-posthoc-trace-evaluation.md) — `SUPERSEDED`; do not execute it as written.

The existing chatbot run JSONL audit under the configured runs directory remains part of the operational core. Only the proposed evaluation-specific ledger and bespoke evaluation service are superseded.

## Architecture Decisions and Rationale

| Decision | Rationale | Consequence |
|---|---|---|
| Keep tool execution local | DuckDB and insight state need enforceable local safety and observable state transitions | Hosted Orq tools declare schemas; a local bridge executes and returns function outputs |
| Define hosted resources in YAML | Reviewable desired state is easier to diff, reproduce, and hand off | YAML is validated and transformed into current Orq SDK entities before sync |
| Reconcile evaluators with the shared resource sync | Evaluator prompts, deterministic source, models, and settings need the same review and drift controls as agents/tools | Store each of the two deterministic and four LLM-as-a-judge evaluators in its own YAML file; dry-run/apply them through the same idempotent pipeline |
| Resolve remote entities by stable keys | Remote identifiers are environment-specific and unsafe to copy into plans or desired state | IDs are resolved at runtime and, if cached, stored only in ignored generated state |
| Make sync dry-run-first and idempotent | Remote state can drift and repeated runs must not create duplicates | Preview semantic changes; explicit apply; immediately prove a second pass is a no-op |
| Use evaluatorq as the sole runner | evaluatorq already owns experiments, concurrency, scorer execution, display, and upload | No `PosthocTraceEvaluator`, custom execution CLI loop, or evaluation ledger |
| Adapt traces into `DataPoint`s | evaluatorq can replay datasets/experiments but does not directly load arbitrary observability traces | Add a thin read-only Orq trace-to-row/`DataPoint` adapter |
| Replay the recorded assistant output | Post-hoc evaluation must assess what happened, not create a new response | The final assistant message is preserved exactly and the target agent is never called |
| Preserve raw evidence in a versioned row | Lossy response conversions and process-local caches cannot support reliable later scoring | Conversation, ordered tools/results/errors, retrievals, state, source linkage, and oracle remain serializable |
| Treat evaluatorq simulation JSONL as canonical | SimulationResult already contains the observed transcript, calls/results, criteria, usage, and case identity | Normalize offline, join the frozen case oracle/split, and keep Orq trace linkage/reasoning as optional enrichment |
| Route four atomic judges independently | Correctness, query validity, evidence support, and conversational consistency fail differently | Each rubric has separate applicability, evidence projection, prompt, labels, and alignment metrics |
| Keep human labels distinct | Machine judgments are not annotations and should not contaminate gold data | Humans label canonical observations; evaluator outputs live in evaluatorq experiments |
| Separate offline CI from live operations | PR validation must be deterministic, safe for forks, and credential-free | Live canaries and baselines are protected explicit jobs, not default CI |
| Integrate locally before any remote push | The repository currently uses local `main` as the accepted integration point | Merge only verified work; remote publication needs a separate request |

## Component and File Boundaries

The paths below are ownership boundaries, not claims that every active file is already integrated.

| Component | Primary paths | Responsibility |
|---|---|---|
| Core runtime | `src/analytics_chatbot/agent.py`, `gateway.py`, `sql_tool.py`, `insights.py`, `run_store.py` | Local agent/tool loop, guarded execution, conversation state, and exact operational audit |
| Core interfaces/config | `src/analytics_chatbot/cli.py`, `config.py`, `models.py`, `README.md` | CLI/Python surfaces, runtime settings, trace context, operator documentation |
| Native evaluation contract | `src/analytics_chatbot/evaluation_ops/__init__.py` | Trace-backed row, atomic evidence projections, deterministic applicability, evaluatorq runner |
| Trace import | `src/analytics_chatbot/evaluation_ops/trace_import.py`, sanitized fixtures, focused tests | Read Orq agent traces, find the correct non-evaluator lineage, normalize messages/tools/state, emit accepted replay input |
| Hosted desired state | `orq/resources/agents/`, `orq/resources/tools/`, `orq/resources/evaluators/`, later datasets/alignment resources | Reviewable agent, local function declarations, one-file-per-evaluator definitions, corpus, and accepted alignment artifacts |
| Resource transform/sync | `src/analytics_chatbot/orq_resources.py`, `orq_sync.py`, `scripts/sync_orq_resources.py`, `Makefile` | Validate agent/tool/evaluator YAML, build SDK requests, semantic diff, safe apply, repeat-run no-op verification |
| Stateful simulation bridge | Focused modules under `src/analytics_chatbot/evaluation_ops/` | Row-aware evaluatorq `AgentTarget`, per-conversation local session, trace/audit correlation |
| Offline automation | `.github/workflows/` and test/lint configuration | Network-free PR verification with no live secrets |
| Architecture communication | `docs/assets/evaluation-flywheel.svg`, `README.md` | Canonical presentation-ready view of the production trace-evaluation loop and its integrated, active, and gated boundaries |
| Agent guidance | `CLAUDE.md`, with `AGENTS.md` as a relative symlink | Require coding agents to keep this living plan synchronized with implementation and verification reality |

When active branches are integrated, prefer focused modules over expanding `evaluation_ops/__init__.py` indefinitely. Preserve the public row and evaluator interfaces while splitting by responsibility.

## Workstreams and Dependencies

“Owner” identifies the task/handoff unit, not a permanent person.

| ID | Owner / task name | Status | Deliverable | Depends on | Can run with |
|---|---|---|---|---|---|
| WS0 | `analytics-chatbot-core` | `VERIFIED` | Deterministic local chatbot, safety boundaries, CLI, traces, run audit | None | All later work |
| WS1 | `evaluator-native-trace-judging` | `VERIFIED` | Versioned trace evidence row and four routed evaluatorq judges | WS0 | WS2, WS3, WS4 |
| WS2 | `trace-import-adapter` | `ACTIVE` | Thin Orq trace-to-evaluatorq adapter plus Orq evaluator scorer factory and no-inference replay validation | WS1 contract; trace access | WS3, WS4 |
| WS3a | `hosted-agent-yaml-sync` | `ACTIVE` | Agent/tool YAML plus one YAML file for each of two deterministic and four LLM-as-a-judge evaluators, shared YAML-to-Orq SDK transform, idempotent Make target, and remote reconciliation evidence | WS0; WS1 evaluator contract; compatible SDK; project access | WS2, WS4 |
| WS3b | `row-aware-simulation-corpus` | `ACTIVE` | Local-tool bridge and exactly 50 accepted simulation cases | WS3a hosted/local protocol; WS0 data/oracles | WS2 after row contract agreement |
| WS4 | `offline-ci` | `VERIFIED` | Credential-free Ruff, pytest, package-build, and optional resource-validation workflow | Integrated dependency set | WS2, WS3 |
| WS5 | `human-labels-and-alignment` | `NOT STARTED` | Canonical observations, accepted human labels, rubric-specific alignment reports | WS2, WS3b | None on frozen test evaluation |
| WS6 | `stability-and-operations` | `NOT STARTED` | Budgeted 50×3 baseline, protected canary, post-hoc sampling, reviewed prompt loop | WS5 qualification | Offline maintenance |

## Status Checklists

### Completed and verified

- [x] Core deterministic dataset generation and known aggregates.
- [x] Read-only SQL validation, row/time bounds, and structured failures.
- [x] Explicitly authorized insight persistence and local state snapshots.
- [x] Mockable analytics agent loop, CLI, trace attribution, and local run audit.
- [x] Opt-in live gateway smoke coverage exists; the default suite remains network-free.
- [x] evaluatorq 1.33.0 is pinned.
- [x] The evaluator-native trace-backed row contract is integrated on local `main`.
- [x] The four atomic judges have deterministic applicability and isolated evidence projections.
- [x] The bespoke post-hoc evaluation service/loop/ledger architecture is marked superseded in the current design.
- [x] Offline CI is integrated on local `main` with pinned actions, no credentials, explicit live-marker exclusion, lint, tests, package build, and an optional hosted-resource YAML validation hook.
- [x] Root agent guidance requires maintaining this living plan in the same task and commit whenever delivery reality changes; `AGENTS.md` resolves to the canonical `CLAUDE.md`.
- [x] Chat Completions, Responses API, and OpenTelemetry GenAI trace shapes plus successfully finalized local run audits normalize into evaluatorq replay inputs without guessing missing messages or rerunning a target.
- [x] The README includes a canonical, accessible SVG of the production evaluation flywheel; it distinguishes integrated, active, and dependency-gated boundaries without presenting the architecture as a status dashboard.
- [x] Repository YAML, SDK transformation/reconciliation, safe Make targets, two deterministic evaluator definitions, and four atomic LLM evaluator drafts are integrated; LLM evaluator apply fails closed until each definition records at least 100 human labels.
- [x] Recorded live evidence establishes the hosted agent/tool handshake and explicit-save behavior; the hosted prompt includes the ambiguity and SQL-returned-number corrections found during smoke and pilot review.
- [x] Exactly 50 deterministic candidate cases are integrated with stable unique IDs, executable DuckDB oracles, required coverage labels, evaluatorq serialization, and a reproducible 30-dev/20-test split.
- [x] Raw evaluatorq `SimulationResult` JSONL normalizes into replay-ready rows with final-assistant ordering, joined oracle/split, paired tool evidence, exact-transcript deduplication, and explicit quality rejection reasons; Orq trace linkage is optional for self-contained simulation rows.
- [x] Integrated-tree validation passed on 2026-09-03: 71 non-live tests passed, one live test was deselected, Ruff passed, and the sdist/wheel build succeeded.

### Active

- [ ] WS2: Adapt the integrated generic evaluatorq replay `DataPoint` output to the accepted `TraceBackedEvaluationRow` / `trace-eval-v1` contract without losing normalized evidence.
- [ ] WS2: Validate on genuine multi-step agent traces from unscoped or populated research projects; response-only traces are insufficient.
- [ ] WS2: Ensure recorded final assistant output is replayed without a target-agent call and source linkage remains in `DataPoint` inputs.
- [ ] WS2: Provide a small Orq evaluator scorer factory; retain evaluator invocation linkage locally only if it is truly required.
- [ ] WS3a: Remove the tracked opaque project ID from desired state and preserve fail-closed project selection through the stable `pydata2026` key before M3 acceptance.
- [ ] WS3a: Obtain a fresh credentialed read-only semantic plan from integrated `main`; the integration checkout had no `.env`, and no remote apply is authorized.
- [ ] WS3a: Keep the four LLM evaluator resources blocked from apply until their independent human-label and alignment gates pass; do not create remote evaluator or dataset resources yet.
- [ ] WS3b: Finish the row-aware, conversation-scoped local-tool bridge for future live generation; the raw artifact-to-evaluation adapter is complete.
- [ ] WS3b: Human-review and freeze the 50 integrated candidate cases; code/oracle validation does not make them accepted cases.

### Blocked

No workstream is currently confirmed blocked. The earlier absence of hosted resources was resolved by authorizing WS3a. Dependency gates below are not blockers until an acceptance check fails. If one fails, move the affected item here with the observed evidence and explicit unblock condition.

### Not started

- [ ] Produce one canonical observed conversation for every frozen case.
- [ ] Human-label the four rubrics with explanations; use independent test reviewers and adjudication as specified.
- [ ] Align each judge on dev only and evaluate the frozen test split once after prompt selection.
- [ ] Promote alignment status only if every rubric meets all locked quality thresholds.
- [ ] Run the protected five-case live canary.
- [ ] Run and analyze the budgeted 50-case × 3-run stability baseline.
- [ ] Add post-hoc operational sampling and a reviewed, manual prompt-improvement loop.

## Milestones, Acceptance Criteria, and Evidence

### M0 — Core runtime baseline (`VERIFIED`)

Acceptance criteria:

- The package installs and the CLI exposes seed, ask/chat, and run-inspection flows.
- Deterministic data generation, guarded SQL, tool-loop behavior, insight authorization, tracing, and atomic run persistence are covered offline.
- The live gateway check remains opt-in.

Required evidence:

- Passing non-live pytest output and Ruff output from the integrated tree.
- A reviewed commit on local `main`.
- For live trace claims, a scrubbed result summary containing human-readable trace characteristics, never trace identifiers or content.

### M1 — Native evaluation contract (`VERIFIED`)

Acceptance criteria:

- `TraceBackedEvaluationRow` round-trips through evaluatorq `DataPoint` without losing conversation, tool, retrieval, state, source, or oracle evidence.
- The recorded assistant response equals the final assistant message.
- Each atomic judge sees only its permitted evidence; inapplicable rows return `not_applicable` without an LLM call.
- A single evaluatorq experiment invocation owns scorer execution and reporting.

Required evidence:

- Focused unit tests for row round-trip, applicability routing, evidence isolation, jury configuration, and native runner delegation.
- Passing integrated non-live test/lint suite.
- Current evaluator-native design linked above.

### M2 — Trace import and no-inference replay (`ACTIVE`)

Acceptance criteria:

- The adapter selects the latest suitable non-evaluator agent span and walks the lineage when messages live on parent spans or separate entities/events.
- Chat Completions, Responses, and OpenTelemetry GenAI message/tool shapes normalize into the accepted row/`DataPoint` contract.
- Missing user messages, missing final assistant output, ambiguous terminal spans, or unsupported shapes fail explicitly; the adapter never guesses.
- The final recorded assistant message is the replay output, and the source target/model is never invoked.
- `orq_evaluator(...)` or an equivalently small factory maps evaluatorq scorer inputs into the stored Orq evaluator call and returns value, explanation, and pass state.
- Validation includes at least two genuine multi-step agent traces with ordered tool activity, sourced from unscoped or populated research projects. Response-only traces do not satisfy this criterion.
- Committed fixtures contain only synthetic or structurally sanitized data.

Required evidence:

- Focused offline tests for all three formats, evaluator-span exclusion, parent walking, multiple tool calls/results, malformed inputs, and no-inference behavior.
- A scrubbed validation matrix: source class, message format, user-turn count, tool-step count, selected lineage behavior, and result. Do not include trace content or identifiers.
- Passing full non-live suite and Ruff after rebasing onto local `main`.
- Temporary trace-access key rotation recorded as a handoff action after validation.

### M3 — Hosted resource sync and local-function protocol (`ACTIVE`)

Acceptance criteria:

- YAML defines the analytics agent, both local function declarations, two deterministic evaluators, and four LLM-as-a-judge evaluators with no credential or hard-coded remote identifier; every evaluator has its own file.
- The four judge resources preserve the WS1 rubric split—answer correctness, query semantics, evidence faithfulness, and multi-turn consistency—without broadening any judge's evidence projection.
- The transformation layer validates YAML shape, block-scalar prompts, cross-resource references, model capability, evaluator kind/configuration, and local-only fields before constructing current Orq SDK entities.
- Deterministic evaluator source is linted and fixture-tested under the restricted execution contract; LLM judge prompts, label space, jury/model configuration, and evidence bindings are validated offline.
- Selection uses stable human-readable keys; runtime-resolved IDs are not committed.
- The default Make target produces one semantic plan across tools, agent, and evaluators. The explicit apply target operates only on the verified existing project, creates/updates in dependency order, never deletes, and refuses duplicates or project mismatch.
- After an apply, an immediate second plan is a no-op.
- The hosted agent returns function calls; the bridge executes `query_sql` and authorized `save_insight` locally, returns function outputs, and obtains a grounded continuation.
- An unauthorized save is rejected locally and does not mutate state.

Required evidence:

- Offline tests for YAML parsing, one-file-per-evaluator discovery, deterministic-source restrictions, judge configuration/evidence bindings, transformation, pagination, duplicate detection, create/update/no-op planning, project mismatch, sanitized errors, and mocked SDK calls.
- A reviewed dry-run summary and a post-apply human-readable inventory by stable resource name and resource kind only, including all six evaluators.
- A second dry-run showing no semantic changes.
- A scrubbed hosted/local contract fixture proving call IDs are correlated without exposing live IDs.
- Passing full non-live suite and Ruff on the rebased integration candidate.

### M4 — Row-aware bridge and frozen 50-case corpus (`ACTIVE`)

Acceptance criteria:

- Each evaluatorq target clone owns one isolated conversation-scoped local session; case/split/repetition context is bound before simulation.
- The bridge preserves complete multi-turn transcript, ordered raw tool calls/results/errors, state before/after, and trace linkage.
- Timeouts, retry ownership, tool-round/call caps, cancellation cleanup, and parallel correlation fail closed and are tested.
- A five-case generation pilot is reviewed before bulk generation; it is distinct from the live simulation pilot.
- Exactly 50 accepted cases have stable IDs, executable read-only DuckDB oracles, expected typed results, comparison policy, human review/provenance, required failure-mode coverage, and a frozen 30-dev/20-test split assigned before target inference.
- Candidate pools and review packets remain ignored; only accepted corpus artifacts are committed.

Required evidence:

- Offline bridge isolation/concurrency/timeout tests.
- Corpus validation report with counts, split, duplicate check, failure-mode presence, manifest/oracle hashes, and evaluatorq serialization round-trip.
- Successful oracle execution against the pinned deterministic dataset.
- Passing full non-live suite and Ruff after integration.

### M5 — Offline CI (`VERIFIED`)

Acceptance criteria:

- A pull-request workflow installs the locked environment and runs the repository's non-live pytest selection plus Ruff.
- Default CI has no Orq credential, performs no network inference or remote mutation, and does not expose secrets to forks.
- Live markers are excluded explicitly and remain separate protected/manual jobs.
- Dependency caching does not cache `.env`, run artifacts, traces, or credentials.

Required evidence:

- Workflow lint/static validation where available.
- A local reproduction using the exact CI commands.
- One successful CI run after integration, or a clearly recorded reason this evidence awaits remote publication.

### M6 — Canonical observations, human labels, and judge alignment (`NOT STARTED`)

Acceptance criteria:

- The fixed five-case live simulation pilot passes hosted/local handshake, state isolation, row correlation, and trace import.
- Exactly one preregistered canonical observation exists for every frozen case before human labeling.
- Each rubric label includes a verdict and explanation. Dev has one reviewer; test has two independent reviewers and an adjudicated result.
- Prompt work uses dev only. Frozen test is evaluated once after prompt selection.
- Per-rubric confusion matrix, balanced accuracy, false-pass rate, jury-vs-gold agreement, human-human agreement, per-model disagreement, and `not_applicable` coverage reproduce from accepted artifacts.
- No rubric is promoted to gating unless it independently satisfies the thresholds in the detailed operations plan; all four must qualify before aggregate automated gating.

Required evidence:

- Accepted, immutable gold-label artifact and provenance hashes.
- evaluatorq Experiment links recorded in an operator report without copying opaque identifiers into this plan.
- Reproducible rubric-specific alignment reports and reviewed status change.

### M7 — Stability and operations (`NOT STARTED`)

Acceptance criteria:

- Live-run request ceilings, explicit large-run confirmation, bounded parallelism, auth/rate-limit circuit breaking, and partial-result preservation are active.
- The 50 × 3 target stability baseline runs only after M6 and is reported separately from canonical human-label accuracy.
- Post-hoc sampling uses the same trace importer, row contract, and evaluatorq judges; it does not write machine results as annotations.
- Error analysis proposes prompt changes; humans review and edit versioned YAML before dev rerun and one frozen-test evaluation.

Required evidence:

- Pre-run budget estimate and operator confirmation.
- evaluatorq results with per-case/rubric variance, disagreement, invariant failures, termination, usage, latency, and available cost.
- Reviewed prompt/evaluator version change, semantic resource diff, and updated changelog entry.

## Remote-State Considerations

- The target is the existing Orq project named `pydata2026`. Before WS3a began it was observed to contain no agent, tool, evaluator, or dataset resources; treat that observation as historical because remote state is mutable.
- Git is the desired-state and evidence boundary, but it cannot prove current remote state. Re-query immediately before every dry-run/apply and record only stable names and semantic outcomes.
- Synchronization must fail if the authenticated workspace/project does not match the expected stable name, if duplicate keys exist, or if the required tool-capable model is unavailable.
- Never create or delete a project as a side effect of resource sync.
- Remote mutations require an explicit reviewed apply operation. Documentation, offline tests, and importer fixture work do not authorize remote changes.
- Resource order is tools first, then agent references, evaluator resources, and accepted dataset rows. A failed partial apply must be safe to resume, and evaluator reconciliation must share the same plan/apply state model.
- Runtime Responses calls and evaluatorq Experiment upload are intentional live data-plane operations; they are not substitutes for control-plane reconciliation.
- Store live validation reports as scrubbed structure/count summaries. Raw traces, prompts containing private data, and remote exports remain outside Git.

## Credentials and Security

- `.env` is the only repository-local environment file currently verified as ignored by Git. Re-run `git check-ignore -v .env` before writing any temporary key.
- Put a temporary trace-access key only in that verified ignored file. Do not place it in shell history, Markdown, fixtures, `.env.example`, YAML, test snapshots, command output pasted into Git, or generated reports.
- Rotate the temporary trace-access key immediately after real-trace validation and record rotation as completed without recording the key or its identifier.
- Keep `.env.example` to empty placeholders and non-secret defaults.
- Sanitize exceptions and mocked SDK recordings; authentication headers, session payloads, trace contents, and runtime-resolved IDs must not appear in logs.
- Human-readable project/resource keys are acceptable for planning. Opaque project, agent, tool, trace, span, Experiment, and model identifiers are runtime data and stay out of this document and tracked desired state.
- Before every commit, inspect staged content with `git diff --cached` and scan for likely secret patterns and unexpected IDs.

## Merge and Integration Order

1. Keep WS0 and WS1 as the baseline on local `main`; rerun the non-live suite before integrating other branches.
2. Rebase or transplant WS2 onto current local `main`. Resolve its output against `TraceBackedEvaluationRow` and the four-judge API, then run focused and full offline checks. Merge only after real agent-trace validation evidence is scrubbed and the temporary key is queued for rotation.
3. WS3a resource schemas/transformation/sync are integrated, including the agent, tools, two deterministic evaluators, and four atomic LLM judge drafts. Remove the tracked project ID and review a fresh unified semantic plan before any separately authorized apply; evaluator creation remains label-gated.
4. The initial WS3b target adapter and 50 candidate cases are integrated. Accept or reject pilot attempt three before any remaining-case run, then finish the row-aware bridge so simulation emits the accepted trace/evidence contract and freeze the corpus only after human review.
5. Keep the integrated WS4 workflow logically independent and network-free; rerun it after dependency-lock or resource-schema changes from WS2/WS3.
6. Create and integrate human labels/alignment reports only after the corpus and canonical-observation mappings are frozen.
7. Add protected live canary and scheduled/manual baseline operations last, after alignment qualification and budget controls.
8. Merge each verified task into local `main`. Stop there unless the user separately requests a remote push.

Each integration candidate should be a focused commit or reviewable commit series. Do not copy dirty worktree state wholesale, and do not overwrite unrelated changes in the primary checkout.

## Risks and Mitigations

| Risk | Impact | Mitigation / evidence |
|---|---|---|
| Active branches started before WS1 landed | Importer or simulation emits an incompatible `DataPoint` shape | Rebase first; add an explicit round-trip contract test against `TraceBackedEvaluationRow` |
| A response-only span is mistaken for an agent trace | Tool and multi-turn evidence is absent, producing false confidence | Require real multi-step agent traces and report turn/tool counts in the scrubbed matrix |
| Trace fields differ across Orq/OTel encodings | Silent evidence loss or guessed conversation order | Support three known formats, walk lineage, preserve raw evidence, and fail explicitly on ambiguity |
| “No inference” is implemented by accidentally calling the target | Evaluation changes the answer being judged and incurs cost | Spy/mock target boundary; prove zero target calls and byte-for-byte recorded response replay |
| Rubric evidence leaks | Correctness, semantics, or faithfulness scores become entangled | Unit-test exact evidence projections and align every judge separately |
| Hosted evaluator YAML drifts from the evaluatorq-native contract | Platform resources judge different labels or evidence than local experiments | Validate all four judge YAML files against WS1 rubric names, label space, evidence projections, and model/jury settings before planning changes |
| Deterministic evaluator source is unsafe or changes invisibly | Synced code can import dependencies, perform side effects, or evade semantic review | Restrict and AST-lint source, execute it against fixtures, include normalized source hashes in semantic diffs, and keep one evaluator per YAML file |
| Tracked YAML contains environment-specific IDs | Desired state becomes non-portable and leaks runtime data | Select by stable keys/model attributes; resolve IDs during sync into ignored state only |
| Partial or repeated sync duplicates remote resources | Remote configuration drifts and recovery becomes unsafe | Paginate fully, reject duplicate keys, order dependencies, resume idempotently, prove second-pass no-op |
| Hosted function declarations are mistaken for remote execution | SQL/state safety moves outside the tested local boundary | Contract-test function call → local validation/execution → function output continuation |
| Corpus oracle is LLM-invented or assigned after inference | Gold answers or splits are unreliable | Execute reference SQL against pinned data; freeze IDs/splits/oracles before target inference |
| Stateful simulations leak across rows | Multi-turn and save-policy labels become invalid | One session per target clone; concurrency-safe row/audit correlation and isolation tests |
| Offline CI gains a hidden live dependency | Forks fail or expose credentials | Explicit marker exclusion, no secrets, fake clients, and protected separate live jobs |
| Remote state changes while tasks run | A stale plan overwrites newer resources | Fresh snapshot immediately before apply; semantic diff; fail on unexpected duplicates/mismatch |
| Temporary key survives after validation | Credential exposure window remains open | Named rotation handoff and explicit completion entry in the task log |
| Local `main` diverges further from remote | Publication becomes a separate integration problem | Keep local integration evidence; do not claim remote availability or push without a new request |

## Reproducibility Commands

Run these from the repository root. They are the accepted offline baseline:

```bash
uv run pytest -m "not live and not simulation_live and not alignment_live" -q
uv run ruff check .
```

Before using any temporary local credential:

```bash
git check-ignore -v .env
git status --short
```

After WS3a is integrated, the intended operator flow is:

```bash
make sync-orq
# Review the semantic plan and authenticated project name.
make sync-orq-apply
make sync-orq
# Expected: no semantic changes.
```

Do not run the apply command from this documentation task. Live simulation/alignment commands remain governed by the detailed [hosted-agent operations plan](2026-09-03-orq-agent-simulation.md) and should be used only after their prerequisite milestones are accepted.

## Decision Log

| Date | Decision | Status / rationale |
|---|---|---|
| 2026-09-02 | Build the operational analytics chatbot with local tools, deterministic DuckDB data, Orq gateway tracing, and local run audit | Accepted and verified |
| 2026-09-03 | Move model instructions and function declarations into a hosted Orq agent while retaining local execution | Active; hosted/local protocol must be proven before migration |
| 2026-09-03 | Use evaluatorq natively for post-hoc replay and experiments | Accepted; supersedes the bespoke evaluator service, custom loop, CLI executor, and evaluation ledger |
| 2026-09-03 | Add only a thin Orq trace-to-evaluatorq adapter | Active; must support real multi-step agent traces and refuse inference/guessing |
| 2026-09-03 | Judge four atomic concerns independently with rubric-specific raw evidence | Accepted and integrated at the contract/framework level; alignment remains outstanding |
| 2026-09-03 | Manage hosted agent, tools, and evaluator resources via YAML transformed through the Orq SDK with repeatable Make targets | Active; each of two deterministic and four LLM judge evaluators gets one YAML file, and runtime IDs remain untracked |
| 2026-09-03 | Target the existing `pydata2026` project rather than creating another project | Accepted; live state must be freshly reconciled |
| 2026-09-03 | Build offline CI as an independent workstream | Accepted and integrated locally; live checks remain protected/manual, and remote-run evidence awaits publication |
| 2026-09-03 | Keep one hand-authored SVG as the architecture visual source of truth | Accepted; the README embeds the same slide-ready asset, with semantic text and status encoded accessibly |
| 2026-09-03 | Make the project status document a required living plan for every relevant coding task | Accepted and integrated through canonical root `CLAUDE.md` guidance plus an `AGENTS.md` symlink |
| 2026-09-03 | Integrate verified work into local `main` and do not push by default | Accepted |
| 2026-09-05 | Keep evaluatorq's raw simulation JSONL as the canonical corpus artifact and require no trace linkage for complete offline rows | Accepted; use only light deduplication/tool-quality gates and optional Orq trace enrichment |

## Changelog / Task Log

Keep entries newest first and compact. Include evidence, not activity narration.

| Date | Workstream | Change and evidence | Handoff |
|---|---|---|---|
| 2026-09-05 | Planning | Removed the superseded process-local simulation cache and mandatory simulation-trace import steps from the detailed operations plan; stored `SimulationResult` normalization is now the single simulation-to-evaluatorq path | Do not rebuild a cache/ledger or require trace IDs for self-contained simulation rows |
| 2026-09-05 | WS3b | Added the lightweight raw `SimulationResult` adapter and optional-source row contract. All three local pilot artifacts were accepted independently (zero rejects/duplicates), retained one/two/one ordered `query_sql` events, ended with the exact assistant output, joined an oracle, and produced evaluatorq `DataPoint`s; 78 non-live tests passed with one deselection, Ruff passed, and package build passed | Keep raw JSONL immutable; human-review/freeze cases before bulk generation, and add trace/reasoning only as optional enrichment |
| 2026-09-04 | WS3b | Retrieved all six Responses steps for the three pilot attempts from Orq, matched them to the ignored evaluatorq exports, and expanded the tracked review artifact so every attempt preserves ordered reasoning summaries, tool calls/results, and final output without runtime identifiers | Review the now-complete attempt-three transcript before authorizing any remaining-case run |
| 2026-09-03 | WS3a/WS3b | Integrated the hosted-resource reconciler, corrected agent prompt, two deterministic and four gated LLM evaluator definitions, initial evaluatorq target, 50-case candidate corpus, and three-attempt pilot review on local `main`; fresh offline evidence: resource bundle/gate validation, exact oracle reproduction, 30/20 split, 71 non-live tests, Ruff, and package build. A fresh remote dry-run was unavailable because the checkout has no `.env`; no remote mutation occurred | Remove the tracked project ID, run a fresh credentialed read-only plan, obtain explicit review of pilot attempt three, and do not create evaluators/datasets or run the remaining 49 before their gates |
| 2026-09-03 | Architecture communication | Added the canonical SVG evaluation flywheel and README narrative; inspected rendered output at README and 16:9 slide scales, and verified SVG structure/accessibility locally | Reuse the SVG directly in talk materials; update it when architecture or delivery boundaries materially change |
| 2026-09-03 | WS2 | Integrated multi-format trace and exact finalized-run-audit normalization on local `main`; synthetic fixtures cover Chat Completions, Responses API, OpenTelemetry GenAI, lineage/evaluator exclusion, tool evidence, explicit malformed-input failures, and audit fallback; integrated checks passed with 57 non-live tests, one deselection, Ruff, and package build | Convert the generic replay `DataPoint` to `trace-eval-v1`, add the Orq scorer factory, validate genuine multi-step traces, then rotate the temporary trace-access key |
| 2026-09-03 | WS0/WS1 | Confirmed local `main` contains the verified chatbot core and evaluator-native judge framework; non-live suite passed with 45 tests and one deselection; Ruff passed | Preserve baseline while rebasing active work |
| 2026-09-03 | WS2 | Trace importer is active in an isolated worktree with multi-format fixtures/tests under development | Reconcile to the integrated row contract; validate real agent traces; do not mark complete yet |
| 2026-09-03 | WS3 | Hosted YAML/SDK sync now explicitly covers agent/tools plus two deterministic and four LLM judge evaluator resources, one YAML file each; Make targets, row-aware bridge, and 50-case corpus remain active in an isolated task | Finish offline validation for every resource kind, remove tracked runtime IDs, then review the unified remote plan before any apply |
| 2026-09-03 | WS4 | Integrated the credential-free offline CI workflow on local `main`; it pins actions, excludes all live markers, runs Ruff/tests/package build, and exposes no Orq credential | Revalidate after dependency or hosted-resource integration; remote-run evidence awaits publication |
| 2026-09-03 | Planning | Consolidated status, acceptance evidence, security, remote-state, evaluator-resource scope, and integration order; added canonical root guidance requiring this plan to stay current | Update this table in the same task and commit whenever status or decisions change |

## Next Actions

1. WS2 owner: adapt the integrated generic replay `DataPoint` to the accepted trace-backed row contract, add the small Orq scorer factory, validate no-inference replay on genuine multi-step agent traces, and rotate the temporary trace-access key afterward.
2. WS3a owner: remove the tracked project ID while retaining stable-key project checks, then produce a fresh credentialed read-only plan against `pydata2026`; do not create remote evaluators or datasets before their gates and separate authorization.
3. WS3b owner: use the raw evaluatorq artifacts as the source of truth, finish the live bridge only when another run is needed, and human-review/freeze the 50-case corpus before bulk generation.
4. Coordinator: keep WS4's offline workflow aligned with integrated dependency commands and rerun it after each dependency boundary.
5. Coordinator: integrate verified branches in the order above, rerun full offline checks after each dependency boundary, rotate the temporary trace-access key after WS2 validation, and update this log.

Do not begin human alignment or the 50 × 3 stability baseline until the trace adapter, hosted/local bridge, frozen corpus, and offline validation gates are all accepted.
