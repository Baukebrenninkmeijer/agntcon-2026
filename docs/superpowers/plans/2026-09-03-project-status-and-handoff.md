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
- Never commit credentials, temporary trace exports, private trace content, or runtime-resolved opaque identifiers, except for user-requested immutable Experiment deep-links needed to reach runs that the project sidebar cannot expose.
- A temporary trace-access key may exist only in a verified Git-ignored local environment file and must be rotated after the trace-validation work.
- Completed, verified task branches are integrated into local `main`. Do not push to a remote unless separately requested.

---

## Document Maintenance

**Status date:** 2026-09-06, Europe/Amsterdam.

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
| Decision-support evaluation implementation | `ACTIVE` | Task 1 is implemented in the isolated `feature/decision-support-evaluation` worktree: the source generator now uses Sphere.com's appliance catalog, retailer segments, category economics, and `sphere-orders-v1` / `sphere-baseline-v1` defaults. Focused tests pass 10/10, including deterministic content hashes and zero revenue-invariant violations. Tracked v1/v2/v3 corpora and run artifacts were not regenerated | Complete independent Task 1 review, then build the context-enriched v4 definitions from the frozen analytical situations |
| evaluatorq-native judge framework | `VERIFIED` | Stable trace-backed row contract, rubric routing, evidence projection, evaluatorq experiment entry point, and focused tests are on local `main` | Importer must emit the same row contract |
| Orq trace importer | `ACTIVE` | Multi-format trace and exact run-audit normalization are integrated on local `main`; the importer still emits a generic evaluatorq `DataPoint` rather than the accepted `trace-eval-v1` row | Adapt the importer to the stable row contract, add the Orq scorer factory, and validate against genuine multi-step agent traces |
| Hosted resources and simulation | `VERIFIED` | The hosted agent is live in `<workspace>/pydata2026`. The baseline, harder edge-v2, and single-persona v3 runs each produced 50 unique raw outputs. v3 (one `business-analyst` persona, 50 distinct situations) was run twice: the first run had gateway PII masking enabled and is archived as `*.pii-masked.*`; the accepted rerun reached two or more turns in 28/50 rows, achieved 49 goals, and retained one behavioral failure | Preserve the frozen raw artifacts; do not rerun again. v3 is the alignment corpus from here on |
| Offline CI | `VERIFIED` | The credential-free GitHub Actions workflow is integrated and published on `main`; its first remote run passed lint, offline tests, hosted-resource YAML validation, and package build | Re-run the same gate after dependency or hosted-resource changes |
| Human labeling and judge alignment | `ACTIVE` | The hosted correctness judge is now reference-free (no oracle in the prompt; full conversation including tool turns as evidence), single-judge on `wafer/DeepSeek-V4-Flash-0731-Fast`, XML-sectioned, at version `1.0.7`. A 50-row replay through pinned `answer_correctness@1.0.7` validated 50/50 populated scores: 48 pass and two fail; three verdicts differ from the oracle-bearing `1.0.0` run. The joined local JSONL is seeded into an evaluator-alignment run directory (50 rows, 0 rejected) with the oracle carried as ground truth, not judge input | Approve the paid stability run (50 × 8 repeats); decide whether the alignment input stays at all 50 rows or is cut to the 30 dev rows; placement still remains blocked by BOPS-1180 |
| Live stability baseline and post-hoc operations | `NOT STARTED` | The run shape is designed, but no accepted baseline or operations report exists | Requires aligned judges, budgets, and live-run controls |

The latest integrated-tree verification is `108 passed, 1 deselected`, Ruff clean, `git diff --check` clean, and successful sdist/wheel build on 2026-09-05. Resource loading found one agent, two tools, two deterministic evaluators, and four LLM evaluator definitions; only `analytics-answer-correctness` is applied remotely. The ignored `.env` key has all-project scope and the Orq CLI session selects Default; do not describe it as project-scoped. The one-time edge-v2 run created 50 observations: eight one-turn, 22 two-turn, and 20 three-turn outputs; 40 achieved their simulation goal. All ten behavioral failures and five missing-save warnings remain replayable. Earlier pinned `1.0.0` runs uploaded empty scores because of the SDK response mismatch. The corrected async-HTTP run produced 50 unique local result identities, preserved the 30/20 split, returned 47 pass and three fail, and exported 50/50 populated scores. Production BOPS-1180 still assigned the Experiment to Default despite `path="pydata2026"`. Evaluator versions `1.0.3`-`1.0.6` are diagnostic only: `1.0.3` (tensorix qwen) returned empty verdicts, `1.0.4` (`deepseek/deepseek-v4-flash`) fails because the hosted grader's forced `tool_choice` is rejected by DeepSeek thinking mode, `1.0.5` (tencent) and `1.0.6` (wafer) lost 2-3 of 50 rows to `tool call result missing 'value' field`, caused by the prompt's own JSON output-format section competing with the grader's tool schema. `1.0.7` drops that section; 30 concurrent-6 probe calls returned 0 errors and the replay validated 50/50 on the first pass with the scorer's new bounded retry. The v2 stability run (30 dev rows × 8 repeats, temperature 1, judge `wafer/DeepSeek-V4-Flash-0731-Fast`) found 26 rows fully consistent and four unstable, three of which were the same `gross-net-software` scenario under different personas; 12 of 240 calls timed out at 120 s. That clustering motivated corpus v3: one persona, fifty distinct situations (26 one-turn, 18 two-turn, 6 three-turn definitions; three deliberately unanswerable). The first v3 simulation (18/16/16 turns, 39 goals, 11 failures; `1.0.7` replay 41 pass / eight fail / one `not_applicable`) was invalidated: the hosted agent path had PII masking enabled, so the model saw `<LOCATION_1>` for `Japan`/`Canada` and placeholder tokens for years, refused to answer, and eight of the 11 goal failures (and several edge-v2 failures such as `<AGE_1>` for `2025`) trace to that masking rather than to agent reasoning. Those artifacts are archived under `runs/*v3*.pii-masked.*`. With masking disabled the accepted v3 rerun produced 50 unique rows (22/22/6 one/two/three user turns, 49 goal successes, one retained failure: `save-after-confirm` claimed more than the save tool returned, zero QC warnings) and the `1.0.7` replay validated 50/50: 49 pass, one `not_applicable` (`unknown-region`, correctly). Consequence: v3 is now almost entirely successes, so the judge has few negatives to be wrong about; the alignment loop will need harder or seeded-failure situations before human labelling is informative.

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

1. [Decision-support evaluation design](../specs/2026-09-06-decision-support-evaluation-design.md) and [implementation plan](2026-09-06-decision-support-evaluation.md) — current Sphere.com corpus-v4, subjective-jury, annotation-prioritization, and talk-delivery direction.
2. [Evaluator-native trace evaluation design](../specs/2026-09-03-evaluator-native-trace-evaluation-design.md) — current trace row and replay foundation, superseded by the decision-support design only for active rubric selection and evidence projection.
3. [Hosted Orq agent and evaluation operations plan](2026-09-03-orq-agent-simulation.md) — historical resource, simulation, corpus, alignment, stability, and operations tasks; its correctness-first alignment direction is superseded.
4. [Edge-case simulation v2 design](../specs/2026-09-05-edge-case-simulation-v2-design.md) — frozen hard-corpus provenance, one-run policy, observed evidence, and bounded QC-filtering contract.
5. [Analytics chatbot design](../specs/2026-09-02-analytics-chatbot-design.md) — local execution, safety, dataset, trace attribution, and public API boundaries, subject to the Sphere.com revision.
6. [Analytics chatbot implementation plan](2026-09-02-analytics-chatbot.md) — completed core implementation history.
7. [Post-hoc trace evaluation design](../specs/2026-09-02-posthoc-trace-evaluation-design.md) — `SUPERSEDED` for evaluator execution, service, CLI loop, and evaluation ledger. Consult only for still-relevant read-only mapping and provenance concerns.
8. [Original post-hoc implementation plan](2026-09-02-posthoc-trace-evaluation.md) — `SUPERSEDED`; do not execute it as written.

The existing chatbot run JSONL audit under the configured runs directory remains part of the operational core. Only the proposed evaluation-specific ledger and bespoke evaluation service are superseded.

## Architecture Decisions and Rationale

| Decision | Rationale | Consequence |
|---|---|---|
| Pivot the active alignment target to subjective decision-support quality | Reference-oriented correctness produced a data-model knowledge problem rather than the human-judgment boundary promised by the abstract | Preserve v3 and correctness artifacts as history; build a Sphere.com v4 corpus with explicit stakeholder decisions and align `decision_support_quality` first |
| Rebrand only the source generator before creating v4 | The appliance setting must be internally coherent without rewriting the historical evidence used to reach the pivot | New seeds use Sphere.com's appliance taxonomy and version defaults; tracked v1/v2/v3 corpora and existing run artifacts remain immutable, and only v4 will target the new baseline |
| Use evaluatorq's repeated three-model jury to prioritize annotation | Within-model wobble and between-model disagreement identify rows where scarce human review is most informative, but neither establishes correctness | Require full per-model and per-repetition jury data in local results; human labels remain the alignment authority |
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
| Start alignment with one development-only rubric | Ten rows are the skill's minimum signal floor, not a credible held-out split, and answer correctness has executable oracles | Recover 10 existing oracle-bearing dev observations; run only answer correctness; preserve the frozen 30/20 split for the later full evaluation |
| Make answer correctness reference-free | With no human labels yet, an oracle-in-prompt judge cannot be graded against that oracle (circular); withholding it turns `expected_output` into usable ground truth for the alignment skill's correctness block | The judge reads `user_query`, the full ordered conversation including tool calls/results (`all_messages`), and the final response; `input.expected_output` is forbidden by the resource validator |
| Run the correctness judge as a single model, not a jury | Hosted jury repetitions are unobservable and the alignment skill re-runs one model; a single judge keeps hosted and re-run behaviour comparable | `mode: single`, `model: wafer/DeepSeek-V4-Flash-0731-Fast`; the jury declaration stays in YAML for a one-word switch back |
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
| WS3b | `row-aware-simulation-corpus` | `ACTIVE` | Local-tool bridge, baseline definitions/observations, the 50-row edge-v2 observation set, and the 50-row single-persona v3 observation set | WS3a hosted/local protocol; WS0 data/oracles | WS2 after row contract agreement |
| WS4 | `offline-ci` | `VERIFIED` | Credential-free Ruff, pytest, package-build, and optional resource-validation workflow | Integrated dependency set | WS2, WS3 |
| WS5 | `human-labels-and-alignment` | `ACTIVE` | Dev-split answer-correctness development pilot (minimum 10 of 22 eligible rows), paired evaluator-version report, and repeated grey-zone workflow | Canonical observed rows; hosted `analytics-answer-correctness@1.0.7` (applied, `shadow`, reference-free single judge); human labels; cost approval | Offline adapter/error work can run with WS2/WS3b |
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

- [ ] Decision-support Task 1 review: independently inspect the Sphere generator/config change and its 10/10 focused-test evidence before proceeding to v4 corpus generation. Historical tracked corpora and run artifacts remain unchanged.
- [ ] WS2: Adapt the integrated generic evaluatorq replay `DataPoint` output to the accepted `TraceBackedEvaluationRow` / `trace-eval-v1` contract without losing normalized evidence.
- [ ] WS2: Validate on genuine multi-step agent traces from unscoped or populated research projects; response-only traces are insufficient.
- [x] WS2: Recorded final assistant output replays byte-for-byte with `inference=False`, no jobs, and no target-agent call.
- [x] WS2: Added the pinned Orq evaluator scorer factory; versioned names support side-by-side columns and optional invocation linkage remains local raw output.
- [ ] WS3a: Remove the tracked opaque project ID from desired state and preserve fail-closed project selection through the stable `pydata2026` key before M3 acceptance.
- [ ] WS3a: Obtain a fresh credentialed read-only semantic plan from integrated `main`; the integration checkout had no `.env`, and no remote apply is authorized.
- [x] WS3a: Replaced the flat 100-human-label apply gate with a two-tier gate: `shadow` status may sync with zero labels because a hosted evaluator must exist before it can be aligned; `validated` requires at least 30 human labels (`MIN_GATING_LABELS`) plus the kappa, balanced-accuracy, and false-pass thresholds measured once on the frozen `test` split.
- [x] WS3a: Applied hosted `analytics-answer-correctness` only, in `shadow` status, after a reviewed single-key dry-run; the immediate second plan verified it as a no-op. The other five evaluator resources remain unapplied and no dataset resource was created.
- [ ] WS3a: Document the shell-vs-`.env` key shadowing trap and the `orq evals --project` CLI 404 in operator docs; sync requires `ORQ_API_KEY` and has no OAuth fallback.
- [ ] WS3b: Finish the row-aware, conversation-scoped local-tool bridge for future live generation; the raw artifact-to-evaluation adapter is complete.
- [x] WS3b: Freeze all 50 v2 rows for replay. Keep the five expected-save warnings informational and preserve all behavioral outcome metadata.
- [x] WS5: Freeze all 50 edge-v2 observations with immutable `(case_id, transcript_fingerprint)` identities; all are oracle-bearing after deterministic staged-reference correction. Human labeling remains development-only.
- [x] WS5: The focused runner uses evaluatorq `inference=False`, no jobs, one pinned answer-correctness scorer, and forwards an explicit Experiment path. Its hosted scorer now uses one shared async HTTP client and maps the current top-level v3 evaluator response; one live pinned call returned a populated verdict and explanation.
- [x] WS5: Ran a fresh uniquely named 50-row replay through the async HTTP scorer. Both local results and the exact Orq export contain 50/50 populated correctness scores; the local artifact is `runs/evaluatorq-correctness-v1.0.0-20260905.jsonl`.
- [x] WS5: Rewrote the hosted correctness judge reference-free with XML prompt sections, single-judge mode, and full-conversation evidence; the resource validator now forbids `input.expected_output` and requires `input.all_messages`. Synced through the standard apply path; `1.0.7` is the accepted version.
- [x] WS5: The hosted scorer sends the full conversation (tool turns included) as `input.all_messages` plus `messages`, no longer withholds tool content, and retries 5xx/transport failures three times with backoff; the replay writer now embeds `conversation` (`evaluatorq-replay-joined-v1`) and the validator prints distinct evaluator error texts.
- [x] WS5: Ran the 50-row replay through pinned `answer_correctness@1.0.7`: 50/50 validated, 48 pass / two fail, local artifact `runs/evaluatorq-correctness-v1.0.7-joined-20260905.jsonl`. `scripts/prepare_alignment_datapoints.py` converts it into the evaluator-alignment skill's seed shape; `seed_inputs.py convert` accepted 50/50 rows.
- [x] WS5: Ran the approved v2 stability job on the 30 dev rows only (`stability.py`, 30 × 8 at temperature 1, 240 calls): 26 stable, four unstable (`data-analyst`, `executive`, `auditor` × `gross-net-software`; `data-analyst--do-not-save`), 12 timed-out repetitions, majority verdict flipped two single-shot passes to fail. The oracle-graded `correctness` block is empty by construction: the oracle is an expected answer, not a `pass`/`fail` label, so the skill cannot grade the judge against it. Dev/test split files: `runs/evaluatorq-correctness-v1.0.7-joined-{dev,test}-20260905.jsonl`.
- [x] WS3b: Added corpus v3 (`evaluation_ops/cases_v3.py`, `--variant v3`): one `business-analyst` persona, 50 hand-authored situations with executable oracles (47) or explicit unanswerability (3), frozen 30/20 split. First run was contaminated by gateway PII masking (archived as `*.pii-masked.*`); accepted rerun (10-way, `max_turns=3`, masking off): 50/50 unique rows, 22/22/6 turn histogram, 49 goal successes, one retained failure, zero QC warnings; raw artifact `runs/evaluatorq-simulation-v3-20260905.jsonl`.
- [x] WS5: Ran the grey-zone step, accepted the rewrite, and applied it as `analytics-answer-correctness@1.0.8` through `scripts/sync_orq_resources.py --apply --kinds evaluator --keys analytics-answer-correctness`. Paired replay of `1.0.7` and `1.0.8` over all 50 v3 rows validated 50/50 for both: 49 pass / one `not_applicable` against 45 pass / five fail. Artifact `runs/evaluatorq-correctness-v1.0.7-vs-v1.0.8-v3-joined-20260906.jsonl`.
- [x] WS5: Replayed all 50 accepted v3 rows through pinned `answer_correctness@1.0.7`: 50/50 validated, 49 pass / one `not_applicable`; joined artifact `runs/evaluatorq-correctness-v1.0.7-v3-joined-20260905.jsonl` plus `-dev-`/`-test-` split files. Seeded a fresh alignment run directory from the 30 dev rows (30/30 accepted); estimate 240 calls / ~200k tokens for 8 repeats.
- [x] WS5: Ran the approved v3 stability job (30 dev rows × 8, temperature 1, concurrency 4, 240 calls, 0 failed repetitions): 28 rows fully consistent, two unstable (`ambiguous-best-product` pass 6 / fail 2, `software-share` pass 7 / fail 1). Mean instability 0.028. Artifacts copied to `runs/alignment-v3-20260905/` (skill run directory `01m1rf70qy6txq4yf67ca8ekjg_20260905_132025`).
- [ ] WS5: The oracle exposes a consistently-wrong judge pattern the stability run cannot: in at least five v3 rows (`ambiguous-best-product`, `software-share`, `top3-countries-then-segment`, `canada-quarters`, `q4-months-then-mom`) the agent computed `net_revenue - refund_amount`, double-deducting refunds already netted in `net_revenue`, and the judge passed the answer in 6-8 of 8 repetitions. Decide whether the rubric must state the column semantics (`net_revenue` is already realized/net of refunds) or whether that knowledge belongs to the human labeller only. Caveat when comparing to the oracle: the simulated user sometimes narrows scope mid-conversation (for example "completed orders only"), so not every oracle mismatch is an agent error.
- [ ] WS5: Materialize real grey-zone inputs and repeat assembly/application twice after the evaluator, labels, key, stability evidence, and cost gates exist.

### Blocked

Experiment placement under `pydata2026` is blocked by [BOPS-1180](https://linear.app/orqai/issue/BOPS-1180/evaluatorq-experiments-ignore-path-always-land-in-the-default-project), currently in Linear status `Testing`. On 2026-09-05, both a same-name retry and a unique-name retry sent `path="pydata2026"`; direct API reads showed that both Experiment objects still had Default's project ID and that `pydata2026` contained zero experiments. Do not spend more evaluator calls retrying placement until the backend fix is released; then create a fresh uniquely named Experiment and verify its returned `project_id`.

Because the Experiment is absent from the `pydata2026` sidebar, the latest uniquely named 50-row run is reachable only by [direct link](https://my.orq.ai/<workspace>/experiments/01M1RGTTZV0XPJ1DWHE0EASXYZ?runId=01M1RGTTZTBA7FSQV07K85HGG8). It is diagnostic evidence, not a usable baseline: an exact JSONL export contains 50 rows and zero non-empty `answer_correctness@1.0.0` values.

The empty score column was caused by a response-contract mismatch tracked as [BOPS-1195](https://linear.app/orqai/issue/BOPS-1195/orq-python-sdk-drops-v3-evaluator-verdicts-causing-evaluatorq-to), related to BOPS-961. Production's v3 invoke route returns a valid verdict at the response top level, while orq-ai-sdk 4.14.7 expects a nested `result` object and yields `response.result is None`. The local scorer bypass now posts through one shared `httpx.AsyncClient`, holds evaluatorq's global LLM slot for every request, and rejects missing or blank verdicts. The replay CLI validates every returned row, replay job, evaluator name, error, and score before returning success. evaluatorq uploads before returning results, so this guard fails the local command loudly but cannot prevent evaluatorq from creating a malformed remote run; exact export validation remains the acceptance gate. A [three-row evaluatorq smoke Experiment](https://my.orq.ai/<workspace>/experiments/01M1RJ2TZR2WMEEED158F5V72W?runId=01M1RJ2TZQF4QVGRAC10BN0R34) returned three non-empty scores with no scorer errors, and its exact JSONL export confirmed three rows with three populated `answer_correctness@1.0.0` values. This resolves the local transport path but does not repair the invalid uploaded Experiment or the separate project-placement bug.

The accepted [50-row correctness baseline](https://my.orq.ai/<workspace>/experiments/01M1RJVCF5SGV97CRZBWC993BQ?runId=01M1RJVCF5NCTVMFXEX1FB28TX) returned 50 locally validated scores and its exact Orq export independently confirmed 50/50 populated values. The distribution is 47 pass and three fail across the frozen 30/20 split. The gitignored local alignment input is `runs/evaluatorq-correctness-v1.0.0-20260905.jsonl`.

Staging is not an accepted workaround: its ingress has not allowlisted the operator's IP. The 2026-09-05 decision is to keep this delivery on production, not create a staging project, and not add staging credentials or a replay profile switch.

The earlier evaluator-resource blocker remains resolved: `analytics-answer-correctness` is applied to `pydata2026` in `shadow` status at version `1.0.7` (reference-free single judge), and the `.env` key works through the SDK sync path. WS5 still depends on human labels and cost approval, which are gates rather than blockers.

Dependency gates elsewhere are not blockers until an acceptance check fails. If one fails, move the affected item here with the observed evidence and explicit unblock condition.

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
- A generation pilot is reviewed before bulk generation. As executed, this was a one-case, three-attempt simulation pilot: manual review rejected an arithmetic error the first automated judge missed, and the second judge rejected unsupported derived claims. The originally planned five-case generation pilot and the separate five-case live simulation pilot were both superseded by that review plus the explicitly approved bounded 50-case run.
- Exactly 50 edge-v2 definitions have stable IDs, deterministic read-only DuckDB oracles covering their full staged requests, expected typed results, required failure-mode coverage, and a frozen 30-dev/20-test split. **Recorded deviation:** five staged oracle families were corrected after simulation but before correctness replay; recorded conversations and IDs were unchanged, and the corrected definitions reproduce byte-for-byte.
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

### M6 — Canonical observations, human labels, and judge alignment (`ACTIVE`)

Acceptance criteria:

- The simulation pilot passes hosted/local handshake, state isolation, and row correlation. Satisfied by the three-attempt pilot and the 50-case run; trace import is optional enrichment, not a gate, since raw `SimulationResult` JSONL is the canonical source.
- One canonical observation exists for every edge-v2 case before human labeling. All 50 are structurally valid and retain behavioral failures plus QC warnings. Sample identity is `(case_id, transcript_fingerprint)`, so distinct attempts remain distinct observations.
- Each rubric label includes a verdict and explanation. Dev has one reviewer; test has two independent reviewers and an adjudicated result.
- Prompt work uses dev only. Frozen test is evaluated once after prompt selection.
- Per-rubric confusion matrix, balanced accuracy, false-pass rate, jury-vs-gold agreement, human-human agreement, per-model disagreement, and `not_applicable` coverage reproduce from accepted artifacts, joined by `(case_id, transcript_fingerprint)` and never by `case_id` alone.
- No rubric is promoted to gating unless it independently satisfies the thresholds in the detailed operations plan. The current increment explicitly focuses only on `answer_correctness`; the other LLM and deterministic evaluators remain outside this alignment run.

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
| Case definitions are mistaken for observed datapoints | Counts become misleading across inputs, outputs, replay rows, repetitions, and labels | Report each separately; edge-v2 has 50 definitions, 50 raw observations, 50 structurally valid replay rows, and zero human labels |
| A ten-row development retest is presented as held-out validation | Same-row prompt iteration overstates generalization | Use only existing `dev` cases, retain the frozen 30/20 split, keep status `shadow`, and label paired results as development-only |
| Grey-zone prerequisites fail opaquely | Operators see a Python traceback or fabricate missing queue/stability artifacts | Add an adapter from canonical rows, validate prerequisites up front, and return actionable errors without inventing project evidence |
| Hosted jury/repetition internals are assumed observable | A stability baseline is computed from a single aggregated verdict and reports false agreement | Hosted `repetitions` returns only the majority value; repeat the pinned invoke locally and persist each raw verdict alongside its sample identity |
| Remote state changes while tasks run | A stale plan overwrites newer resources | Fresh snapshot immediately before apply; semantic diff; fail on unexpected duplicates/mismatch |
| Temporary key survives after validation | Credential exposure window remains open | Named rotation handoff and explicit completion entry in the task log |
| Local `main` diverges from remote | Publication becomes a separate integration problem | `main` was published on explicit request on 2026-09-05; continue to integrate and verify locally before separately authorized pushes |

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
| 2026-09-03 | Build offline CI as an independent workstream | Accepted, integrated, and published; live checks remain protected/manual |
| 2026-09-03 | Keep one hand-authored SVG as the architecture visual source of truth | Accepted; the README embeds the same slide-ready asset, with semantic text and status encoded accessibly |
| 2026-09-03 | Make the project status document a required living plan for every relevant coding task | Accepted and integrated through canonical root `CLAUDE.md` guidance plus an `AGENTS.md` symlink |
| 2026-09-03 | Integrate verified work into local `main` and do not push by default | Accepted |
| 2026-09-05 | Keep evaluatorq's raw simulation JSONL as the canonical corpus artifact and require no trace linkage for complete offline rows | Accepted; use only light deduplication/tool-quality gates and optional Orq trace enrichment |
| 2026-09-05 | Use a ten-row answer-correctness development pilot before the full alignment | Accepted planning default; recover existing observations only, run baseline/candidate as singleton no-inference experiments, and preserve the frozen test split |
| 2026-09-05 | Replace the flat 100-human-label evaluator apply gate with a two-tier gate | Accepted; `shadow` may sync with zero labels because a hosted evaluator must exist before it can be aligned, `validated` requires >= 30 labels plus the alignment thresholds |
| 2026-09-05 | Exclude `multi_turn_consistency` from alignment and gating | Accepted on scope grounds: alignment effort is concentrated on `answer_correctness` first. The original coverage rationale (eight of 50 observations multi-turn) applied to the v1 corpus and is superseded by the frozen `edge-v2` corpus, where 42 of 50 rows are multi-turn and the locked thresholds are reachable. Code, routing, and YAML are retained unchanged as `NOT ALIGNED - deferred by scope` |
| 2026-09-05 | Mark the two deterministic Python evaluators out of scope | Accepted; `tool-execution-integrity` and `state-change-policy` have no runner in any design. YAML stays tracked as `NOT IN SCOPE`; no plan action targets them |
| 2026-09-05 | Use `(case_id, transcript_fingerprint)` as the single sample identity everywhere | Accepted; a `case_id`-only join would duplicate human labels across distinct attempts of one case |
| 2026-09-05 | Keep human labeling inside the 30-case `dev` split | Accepted; expected 10-20 labels. The 20 frozen `test` observations are not inspected, sampled, or labeled before prompt selection |
| 2026-09-05 | Preserve failed simulation outputs instead of rerunning for a clean corpus | Accepted; behavioral outcomes remain valid rows, while structural defects reject and expected-tool/state misses produce QC warnings |
| 2026-09-05 | Run the harder all-edge v2 corpus once and treat multi-turn coverage as diagnostic | Accepted; keep `max_turns=3`, retain failures, and do not rerun even if fewer than 60% reach two turns |
| 2026-09-05 | Measure judge stability by repeating the invoke client-side, not with hosted `repetitions` | Accepted; hosted repetitions run (nine judge spans at `repetitions: 3`) but the invoke response and spans expose only the aggregated majority verdict, so raw per-repetition values exist nowhere the platform returns |
| 2026-09-05 | Make the hosted correctness judge reference-free, single-model, XML-sectioned | Accepted; the oracle is withheld from the prompt so it can grade the judge, the full conversation with tool turns is the evidence, and `mode: single` keeps hosted and re-run judges comparable |
| 2026-09-05 | Judge model is `wafer/DeepSeek-V4-Flash-0731-Fast` | Accepted after probing: `tensorix` qwen returns empty content, native `deepseek/` rejects the grader's forced `tool_choice` in thinking mode, `baseten`/`alibaba`/`greenpt` variants fail to yield a label; `scaleway`, `wafer`, `tencent`, `tensorix` deepseek-v4-flash variants work, wafer chosen |
| 2026-09-05 | Never put an output-format instruction in a hosted LLM evaluator prompt | Accepted; orq extracts the verdict through a forced tool call with a `value` argument, and a competing JSON instruction produced `tool call result missing 'value' field` on 6-10% of calls |
| 2026-09-05 | Gateway PII masking must be off for simulation and evaluation runs | Accepted; with masking on, the hosted agent receives `<LOCATION_1>`-style placeholders for countries and years and refuses to answer, which produces failures that measure the plugin rather than the agent. Archived contaminated artifacts carry a `.pii-masked` suffix |
| 2026-09-05 | Replace the persona × scenario grid with corpus v3: one persona, fifty distinct situations | Accepted; the v2 stability run showed three of four unstable rows were one scenario family under different personas, so the grid bought rows but not situations. v3 varies metric, period, filter, grouping, and conversational shape per row; persona is held constant. edge-v2 artifacts stay frozen as evidence |
| 2026-09-05 | Keep QC warnings non-filtering | Accepted; preserve and replay all 50 v2 rows, including the five expected-save warnings and all behavioral failures |

## Changelog / Task Log

Keep entries newest first and compact. Include evidence, not activity narration. Same-day entries carry an explicit ordinal because several 2026-09-05 entries would otherwise appear to contradict each other. Historical counts remain evidence of earlier state; the current edge-v2 count is 50 raw and 50 structurally valid replay observations.

| Date | Workstream | Change and evidence | Handoff |
|---|---|---|---|
| 2026-09-06 (25, latest) | Decision-support / Task 1 | Implemented the Sphere.com source data model in isolated branch `feature/decision-support-evaluation`: exact eight-product appliance catalog, three retailer segments, category cost basis points, national-retailer quantity branch, `sphere-orders-v1` manifest/default, and `sphere-baseline-v1` agent default. TDD evidence: the new taxonomy/version tests first failed against the old software taxonomy and `revenue-v1` defaults, then all 10 focused data/config tests passed; existing deterministic-hash and financial-invariant checks stayed green. No tracked v1/v2/v3 corpus or run artifact was regenerated, and no live call or remote mutation occurred | Complete independent Task 1 review, then implement Task 2's context-enriched v4 definitions; do not seed or run live v4 observations |
| 2026-09-06 (24, latest) | Delivery / talk | Replaced the abstract `Findings and agent knowledge` slide with a concrete Sphere.com learning example. Slide 17 now shows one progression: the evaluator finds that declining revenue is reported without a CFO decision, diagnosis identifies missing Sphere decision criteria rather than a data or SQL error, the scoped Sphere skill gains explicit decision-support guidance, and `decision_support_quality` is rerun. This removes the competing system-prompt/evaluator/code branches and leaves the following software-factory slide to explain automation. Fresh evidence: Ruff passes, the 19-slide HTML deck regenerates successfully, and slide 17 was visually reviewed at 1280×720 with no clipping or overlap | Keep slide 17 concrete and use slide 18 for the generalized automation workflow |
| 2026-09-06 (23, latest) | Delivery / talk | Simplified slide 16 while preserving its two-loop lifecycle visual. The diagram now carries only four labels: `Build with humans`, `Alignment holds`, `Guard every commit`, and `Escapes become review cases`; detailed build and regression steps move to spoken narration. Removed the redundant `CI and the promotion gate` eyebrow. Fresh evidence: Ruff passes, the 19-slide HTML deck regenerates successfully, and slide 16 was visually reviewed at 1280×720 with no clipping or overlap | Keep operational detail in the speaker narrative; do not add step labels back into the diagram |
| 2026-09-06 (22, latest) | Delivery / talk | Rebuilt the generated HTML deck as a 19-slide analytics-only presentation following the approved Sphere.com and `decision_support_quality` outline. Removed the prior podcast/newsletter example slides and their claims; added a fictional Sphere.com vector wordmark; retained and widened the animated grey-zone visual; reframed the 50-dot visual around cross-model disagreement and self-wobble; kept the build-then-regression lifecycle immediately after offline/online/continuous; and added high-level agent-evaluation, finding-to-skill, and software-factory slides. The two evidence-dependent walkthrough areas remain explicitly marked as placeholders, and the deck makes no claim that the fifty cases have human labels or that a jury run exists. Mouse navigation is gated on document fullscreen, while keyboard navigation remains available and `F` toggles fullscreen. Fresh evidence: generated HTML contains 19 slides, Ruff passes for `slides/build_deck.py`, `git diff --check` passes apart from a non-fatal local fsmonitor warning, all slides plus the grey-zone animation midpoint were visually reviewed in an isolated 1280×720 browser session, and a synthetic right-side click left the windowed deck on `#s8` | Review the narrative and replace the two placeholders only when the corresponding Sphere response and detailed jury record exist; do not invent measured results |
| 2026-09-06 (21, latest) | Delivery / talk | Rewrote `outline.md` around the submitted abstract and the Sphere.com decision-support example. The alignment section now contrasts fully manual random review with disagreement-led annotation prioritization; binary verdicts are framed as both actionable and alignment-demanding because applicable cases have no ambiguity bucket. Agent evaluation stays high level around trajectory, tools, context drift, and state. Offline/online/continuous remain a separate operating-modes slide. The software factory is now its own section: findings are structurally analyzed, durable domain knowledge flows primarily into scoped skills, agents can prepare a PR and regression evidence, and a human retains merge authority. No slide build, live measurement, or implementation claim was added | Review and approve the revised outline; then update the deck and speaker notes separately. Keep the fifty cases described as a review pool until annotation exists |
| 2026-09-06 (20, latest) | Delivery / WS5 | Approved the analytics-only decision-support pivot and recorded it in `2026-09-06-decision-support-evaluation-design.md` plus its implementation plan. The fictional running company is Sphere.com, an Amsterdam-based B2B home-appliance wholesaler under board scrutiny over quality of growth. The planned v4 corpus preserves fifty distinct analytical situations and the 30/20 split while adding agent-visible stakeholder, decision, delivery, and communication context. This stage implements only `decision_support_quality`; assumption handling, audience-calibrated detail, and insightfulness without overreach remain unimplemented brainstorming options. No v4 code, observed responses, human labels, hosted mutation, or live jury run exists yet. evaluatorq 1.33.0 was source-audited: `llm_jury(assignment="all")` computes detailed votes internally but returns only aggregate result data; implementation Task 5 is gated on an exact future release that preserves `raw_output.jury` | Execute Tasks 1-4 from `2026-09-06-decision-support-evaluation.md`; stop at Task 5 until the user supplies the exact evaluatorq release; do not run the 450-call jury or claim fifty reviewed examples |
| 2026-09-06 (19, latest) | Delivery / WS5 | Replaced the talk's running example. The analytics agent's only grey zone (`schema-semantics-double-refund`) is a knowledge gap settled by the data dictionary, not a contested boundary, so it cannot carry the "who decides where the boundary goes?" argument; it survives as a single contrast slide. The new running example is the production newsletter-to-podcast pipeline in n8n, captured from execution 9308 (6 September 2026): ten newsletters, 310,647 characters, an eight-topic digest, and a delivered two-host `debate` script in which four topics survive. Artifacts committed under `docs/examples/podcast-run-2026-09-06/` (sources, digest, narration draft, delivered script, both prompts); the dialogue script was regenerated through the real code path, which is exact because the show config is seeded from `sha256(content + UTC date)`. Three structural findings drive the new slides: two prompts write the episode and only the first is visible in n8n; the show format, personas, voices and length are drawn from a seeded engine, so the target output is unstable by design; and `slop_filter.validate` is a real deterministic grader whose banned lists are injected into the generation prompt *and* used as the grader, vendored once from `~/.claude/skills/ai-slop/phrases.md` with six words hand-excluded (`paradigm` among them). The delivered script says "a complete paradigm shift" and passed. Deck rebuilt to 22 slides: pipeline replaces the analytics running example, a boundary-versus-gap contrast slide added, corpus counts dropped in favour of week shapes, the dev/test diagram reframed as the ideal-world version needing human annotations, a drift slide added (2023-24 vocabulary covered, em dash unchecked, 2026 "claudish" tells unknown to the list), the audience grey-zone slide now uses the cleared cliché, a preliminary faithfulness slide uses the invented "five hundred dollars", and the dot grid becomes inter-judge agreement. Deck decisions taken through a `/grilling` session; `outline.md` and `docs/talk-example-podcast.md` updated to match. Operational work supporting the run, in the monorepo: n8n `Transcribe` and `Generate weekly podcast audio` set to 5 retries at 30 s, and ai-api podcast concurrency raised from 1 to 5 with `_MAX_INFLIGHT` to match (commit `ed69941d`, 101 tests pass, not yet pushed) after concurrent triggers hit ai-api's own 429 admission bound | Land the three-model claudish agreement run (`google/gemini-3.6-flash` as generator self-preference probe, `wafer/DeepSeek-V4-Flash-0731-Fast`, `tensorix/qwen/qwen3.8-flash-next`) and replace the placeholder ring positions on the agreement slide; decide whether to push `ed69941d` to deploy |
| 2026-09-06 (18) | WS5 | Completed the grey-zone step and the first aligned rewrite. One grey zone recorded (`schema-semantics-double-refund`): the judge must know that `net_revenue` is realized and already net of refunds, `gross_revenue` is quantity times unit price before discount, and `refund_amount` is never subtracted again; a figure obtained by re-subtracting refunds fails whoever asked for it. Rows `ambiguous-best-product` and `software-share` labelled `fail` (human confirmed). `rewrite_eval.py` produced the new prompt; the trailing output-format sentence was dropped by hand because an output-format block previously broke forced tool-call verdict extraction. The accepted prompt was applied through the repository YAML sync path rather than the skill's `create_eval.py`, so it is version `1.0.8` of the same evaluator id and the pinned-version replay keeps working. Paired 50-row replay of `1.0.7` and `1.0.8` over the v3 corpus ([artifact](runs/evaluatorq-correctness-v1.0.7-vs-v1.0.8-v3-joined-20260906.jsonl)): `1.0.7` 49 pass / one `not_applicable`, `1.0.8` 45 pass / five fail. Four of the five oracle-confirmed double-refund rows now fail (`ambiguous-best-product`, `software-share`, `top3-countries-then-segment`, `canada-quarters`), plus one the oracle sweep had not flagged (`category-then-yoy`, oracle `Data 2024 = 5,003,926.92` against the agent's 4,718,667.35). Two behaviours to watch: `q4-months-then-mom` still passes because its final query uses a plain `SUM(net_revenue)`, and `unknown-region` moved from `not_applicable` to `pass`, which is a verdict-category regression on a row where the agent correctly declined. Session log added at `docs/alignment-session-log.md`; skill gaps filed as [RES-1523](https://linear.app/orqai/issue/RES-1523/orq-evaluator-alignment-improvements-from-pydata-2026-answer) | Decide whether `not_applicable` needs sharpening in the rubric after the `unknown-region` flip; label more dev rows (annotation webapp) so the retest scores against more than two labels; refresh outline section 6d with v3 numbers |
| 2026-09-05 (17) | WS5 | v3 stability job on the 30 dev rows (240 calls, 0 failures): 28 consistent, two unstable (`ambiguous-best-product` 6/2, `software-share` 7/1), mean instability 0.028. Both unstable rows and at least three stable-pass rows share one agent error the oracle catches and the judge does not: refunds deducted twice (`net_revenue - refund_amount`). Artifacts in `runs/alignment-v3-20260905/` | Decide with the user whether column semantics enter the rubric; then build the review queue (`build_queue.py --count N`) and start grey-zone labelling on the dev split |
| 2026-09-05 (16) | WS3b / WS5 | Completed the approved v2 stability run on the 30 dev rows (240 calls): 26 stable / four unstable, three of the four the `gross-net-software` scenario across personas; the oracle-graded correctness block is empty because the oracle is an answer, not a verdict label. Added corpus v3 (one persona, 50 distinct situations, `cases_v3.py`, generator `--variant v3`, one focused test) and ran it once: 50 rows, 18/16/16 turns, 39 goals, 11 retained failures, zero warnings. The first v3 run and its replay (41 pass / eight fail / one `not_applicable`, [experiment](https://my.orq.ai/<workspace>/experiments/01M1RVKVNQPHV51G19C3XD20WT?runId=01M1RVKVNQY35M0T82HZKTFQ2N)) were invalidated by gateway PII masking (`<LOCATION_1>` for country names); artifacts archived as `*.pii-masked.*`. Masking disabled, v3 rerun once: 50 rows, 22/22/6 turns, 49 goals, one failure; replay through `answer_correctness@1.0.7` 50/50 validated, 49 pass / one `not_applicable` ([experiment](https://my.orq.ai/<workspace>/experiments/01M1RW4897WZVKXP8GK5X7BRYZ?runId=01M1RW4897BZR0X9CXDFDQ1BPH)). Split the joined file into dev/test and seeded a fresh alignment run directory from the 30 dev rows. Talk outline updated: reference-free judge that sees tools and intermediate messages, answer correctness as the single aligned metric decomposed further, thresholds expressed only as human agreement. `109 passed, 1 skipped`, Ruff clean, `git diff --check` clean | Get explicit approval for the v3 stability job (30 × 8, ~240 calls) before running it; then continue the skill flow from the consistency report |
| 2026-09-05 (15) | WS5 | Rewrote `analytics-answer-correctness` reference-free (no `input.expected_output`; `input.all_messages` carries the full conversation including tool calls/results), single-judge `wafer/DeepSeek-V4-Flash-0731-Fast`, XML prompt sections, no output-format block; validator and tests updated. `orq_sync` now also accepts catalog `refId`s so provider-routed models pass the availability gate. Hosted scorer: full conversation, bounded retry on 5xx/transport errors; replay writer embeds `conversation`; validator prints distinct error texts. Versions `1.0.3`-`1.0.6` are failed diagnostics (see snapshot); `1.0.7` replayed 50/50 validated, 48 pass / two fail, three verdict changes versus `1.0.0` (`data-analyst--edge-v2-latest-emea-net` fail→pass, `sales-manager--edge-v2-save-latest-emea` fail→pass, `finance-lead--edge-v2-ambiguous-revenue` pass→fail). Seeded the evaluator-alignment run directory from the joined JSONL via `scripts/prepare_alignment_datapoints.py`: 50/50 rows accepted, oracle mapped to `reference`, judge model resolved, estimate ~400 calls / ~355k tokens for 8 repeats. `108 passed, 1 skipped`, Ruff clean, `git diff --check` clean | Get explicit approval for the stability run and settle whether all 50 rows or only the 30 dev rows enter the alignment loop before any labelling |
| 2026-09-05 (14) | WS5 | Corrected the stale rationale for excluding `multi_turn_consistency` from alignment. The recorded reason (eight of 50 observations multi-turn) described the v1 corpus, which was 42 one-turn, six two-turn, and two three-turn. The frozen `edge-v2` replay corpus inverts this: eight one-turn, 22 two-turn, 20 three-turn, so 42 of 50 rows are multi-turn and the locked thresholds are reachable. The exclusion decision is unchanged but now rests on scope (align `answer_correctness` first); the status label moves from `NOT ALIGNABLE` to `NOT ALIGNED - deferred by scope` in both this plan and the simulation plan | If multi-turn alignment is later brought into scope, no corpus work is required; 42 rows already support it |
| 2026-09-05 (13) | WS5 | Probed hosted evaluator `repetitions` on a throwaway `scratch-repetition-probe` clone of `analytics-answer-correctness` (jury, three judges, `repetitions: 3`) in `pydata2026`, then deleted it. Repetitions execute: the reps=3 trace has nine `chat` judge spans against three per reps=1, one trace per invoke. Repetitions are not observable in the result: `POST /v3/evaluators/<id>/invoke` returns only `{value, passed, status, explanation: "jury majority vote", type, categories, evaluator_id}` for both reps=1 and reps=3, with no per-judge or per-repetition values, no vote counts, and no `trace_id`/`span_id`. Spans carry only the aggregate verdict, and no message payloads (`logs list-trace` returns zero rows), so raw judge verdicts are unrecoverable from the platform. Latency is indistinguishable (2.1-3.5s both) because judges run in parallel | Do not source the stability baseline from hosted `repetitions`; repeat the pinned `id@version` invoke N times from evaluatorq and record each verdict locally |
| 2026-09-05 (12) | WS5 | Added atomic, sanitized local JSONL persistence for evaluatorq replay results, including immutable sample identity, split, recorded/reference outputs, Experiment URL, and versioned scores. Ran the full frozen corpus through pinned `answer_correctness@1.0.0`: 50 unique local rows, 30 dev/20 test, 47 pass/3 fail, and 50/50 populated scores in an independent Orq export | Use `runs/evaluatorq-correctness-v1.0.0-20260905.jsonl` for the next alignment step; do not rerun this baseline |
| 2026-09-05 (11) | WS5 | Ran a uniquely named three-row evaluatorq no-inference smoke Experiment through the pinned hosted evaluator and shared async HTTP scorer. evaluatorq returned three populated scores with zero errors; an Orq JSONL export independently confirmed 3/3 populated `answer_correctness@1.0.0` values. Added evaluatorq LLM-slot enforcement, blank-verdict rejection, and per-row fail-loud result validation; 17 focused tests cover the transport and safety contract. Fresh full verification: 108 offline tests passed with one deselection, Ruff and diff check passed, and both packages built. Recorded the direct Experiment URL in the README and handoff | Run the fresh 50-row baseline through the same path and require 50/50 exported scores; because evaluatorq uploads before returning, retain export validation as the remote acceptance gate |
| 2026-09-05 (10) | WS5 | Reproduced the empty Experiment column with an exact JSONL export: 50 rows, 0 non-empty `answer_correctness@1.0.0` scores. A direct v3 HTTP call returned a valid top-level verdict while orq-ai-sdk 4.14.7 expected `result` and produced `None`; evaluatorq then caught the scorer exception and uploaded empty values. Filed high-priority BOPS-1195 in Triage, replaced the local scorer transport with a shared async HTTP client, and verified one live pinned call returned a populated pass verdict and explanation | Run a fresh uniquely named 50-row replay, export it, and accept it only if all 50 correctness scores are non-empty; upstream SDK work continues under BOPS-1195 |
| 2026-09-05 (9) | WS5 | Added the direct Orq URL for the latest uniquely named 50-row correctness run to the README and living handoff because BOPS-1180 prevents discovery under the intended project; subsequent export validation proved this run is diagnostic only, not a valid baseline | Preserve the link as failure evidence; do not use its scores for alignment |
| 2026-09-05 (8) | WS5 | Investigated staging as a possible BOPS-1180 validation target, but staging ingress does not allowlist the operator IP. Explicitly kept the workflow production-only; no staging project, credential, or profile-switch implementation was created | Wait for the production BOPS-1180 release, then validate one fresh uniquely named Experiment in `pydata2026` |
| 2026-09-05 (7) | WS5 | Added explicit evaluatorq Experiment-path forwarding with `pydata2026` as the replay CLI default; focused tests failed before implementation and passed after it. Two live validation retries uploaded 50 rows each, but direct API reads proved both remained in Default and `pydata2026` still had zero experiments. Linear BOPS-1180 documents the exact ingest bug and is in Testing. Fresh verification: 103 offline tests passed with one deselection, Ruff and diff check passed, and both packages built | Do not rerun for placement until BOPS-1180 is released; then use a fresh unique name and verify the Experiment `project_id` directly |
| 2026-09-05 (6) | WS3b / WS5 | Corrected five inherited edge-v2 oracle families to cover staged final requests without changing or rerunning recorded conversations; 50 IDs still match, all 50 rows are now oracle-bearing, and regeneration is byte-for-byte stable. Added deterministic replay loading, fingerprint identities, non-filtering warnings, pinned hosted scorers, and a `latest`-rejecting CLI. evaluatorq then replayed all 50 rows with `inference=False` through `analytics-answer-correctness@1.0.0` at 10-way concurrency and uploaded 50 Experiment rows with local result printing disabled. Fresh verification: 102 offline tests passed with one deselection, Ruff and diff check passed, and both packages built | Prepare development-only alignment inputs and obtain explicit approval for the estimated repeated-call job before measuring judge stability |
| 2026-09-05 (5, latest) | Planning / WS3a / WS5 | Reconciled the specs and plans against reality and resolved 12 recorded contradictions. Superseded the cancelled two-record source comparison (Task 2), the pre-atomic jury filenames, and the stale trace-hydration claim; stripped four opaque model UUIDs from tracked desired state; corrected the simulation-artifact plan's "no live runs" scope note and its three-artifact count; rewrote the M4/M6 criteria that no execution could satisfy and logged the freeze-before-review deviation. Replaced the 100-label apply gate with the two-tier `shadow`/`validated` gate (`MIN_GATING_LABELS = 30`) and added per-key sync filtering. Fixed a real API-contract bug: evaluator create sent both `path` and `project_id`, which the evals API rejects with `invalid_request_body`. Applied `analytics-answer-correctness` to `pydata2026` in `shadow` status; the immediate second plan verified a no-op, `list-versions` reports version `1.0.0` with checksum `fc82a2611ea2877a`, and a pinned `evals invoke <id>@1.0.0` returned `value: pass`, `passed: true`, and an explanation. Verified corpus counts: 47 accepted of 50, 28 `dev`, 22 accepted and oracle-bearing. Offline evidence: Ruff passed, 88 non-live tests passed with one deselection | Select at least 10 of the 22 eligible `dev` observations, add the scorer factory around the pinned `id@version` selector, and obtain cost approval before repeated judge calls |
| 2026-09-05 (4) | WS3b | Completed the single approved 50-case edge-v2 evaluatorq simulation with 10-way concurrency and `max_turns=3`: 50/50 unique IDs, 8/22/20 one/two/three-turn rows, 42/50 multi-turn, 230/230 paired calls/results, 40 goal successes, ten retained behavioral failures, six max-turn terminations, and no duplicates. Updated normalization to retain behavioral failures and emit five expected-save misses as QC warnings; focused tests pass | Replay all 50 rows, preserve the ignored raw artifact with its recorded digest, and do not rerun |
| 2026-09-05 | WS3b | Added a reproducible simulation-case generator CLI with explicit `standard` / `edge-v2` variant selection, safe variant-specific defaults, and caller-selected output paths while preserving the argument-free v1 behavior; both new slices failed before implementation, then six focused tests, `83 passed, 1 deselected` offline, and Ruff passed | Keep the v1 and edge-v2 case/output paths separate; review generated corpora before any future live run |
| 2026-09-05 | WS3b | After explicit user approval, ran all 50 cases with `max_turns=3`, 10-way datapoint concurrency, dotenv override, evaluatorq `save=True`, raw local JSONL export, and one Orq Experiment. Coverage is exactly 50/50 unique IDs; 169/169 tool calls have paired results; 47 rows pass strict normalization; two reached max turns and one judge-terminated goal failure remains preserved | Review the three failures, select 10 accepted oracle-bearing dev rows for answer-correctness work, and do not rerun to remove negative examples |
| 2026-09-05 (1, earliest) | WS5 | Designed a ten-row, answer-correctness-only replay/alignment increment. Audits confirmed 50 definitions but zero retained raw observations; evaluatorq 1.33 replayed recorded output with zero target calls; two fixture-backed grey-zone passes produced identical artifacts, while a direct repo run exposed an uncaught missing-queue error | Recover 10 existing dev observations without rerunning simulation; then resolve the hosted evaluator/key and obtain cost approval before real stability calls |
| 2026-09-05 (2) | Operations | Added shared agent guidance distinguishing OAuth trace-read access from evaluatorq/SDK run-key access and requiring active project keys to be preserved in the primary checkout's ignored `.env` before worktree removal | Mint or restore a `pydata2026` project key in the primary `.env`; never infer run readiness from successful OAuth trace reads |
| 2026-09-05 (3) | Delivery | Published the fully integrated `main` history to `origin/main` on explicit request, verified the remote ref, and confirmed the first published Offline CI run passed lint, 78 offline tests, Orq YAML validation, and package build | Keep Orq resource mutation separately gated |
| 2026-09-05 (3) | Integration | Audited every registered worktree against `main`, preserved the sole uncommitted talk-outline change, recorded the already-integrated plan and superseded Mermaid visual branches as merged without overwriting newer content, and closed all secondary worktrees; only the clean primary `main` worktree remains | Retain source branches until ordinary branch cleanup is explicitly requested; start future work from primary `main` |
| 2026-09-05 (2) | Planning | Removed the superseded process-local simulation cache and mandatory simulation-trace import steps from the detailed operations plan; stored `SimulationResult` normalization is now the single simulation-to-evaluatorq path | Do not rebuild a cache/ledger or require trace IDs for self-contained simulation rows |
| 2026-09-05 (2) | WS3b | Added the lightweight raw `SimulationResult` adapter and optional-source row contract. All three local pilot artifacts were accepted independently (zero rejects/duplicates), retained one/two/one ordered `query_sql` events, ended with the exact assistant output, joined an oracle, and produced evaluatorq `DataPoint`s; 78 non-live tests passed with one deselection, Ruff passed, and package build passed | Keep raw JSONL immutable; human-review/freeze cases before bulk generation, and add trace/reasoning only as optional enrichment |
| 2026-09-04 | WS3b | Retrieved all six Responses steps for the three pilot attempts from Orq, matched them to the ignored evaluatorq exports, and expanded the tracked review artifact so every attempt preserves ordered reasoning summaries, tool calls/results, and final output without runtime identifiers | Review the now-complete attempt-three transcript before authorizing any remaining-case run |
| 2026-09-03 | WS3a/WS3b | Integrated the hosted-resource reconciler, corrected agent prompt, two deterministic and four gated LLM evaluator definitions, initial evaluatorq target, 50-case candidate corpus, and three-attempt pilot review on local `main`; fresh offline evidence: resource bundle/gate validation, exact oracle reproduction, 30/20 split, 71 non-live tests, Ruff, and package build. A fresh remote dry-run was unavailable because the checkout has no `.env`; no remote mutation occurred | Remove the tracked project ID, run a fresh credentialed read-only plan, obtain explicit review of pilot attempt three, and do not create evaluators/datasets or run the remaining 49 before their gates |
| 2026-09-03 | Architecture communication | Added the canonical SVG evaluation flywheel and README narrative; inspected rendered output at README and 16:9 slide scales, and verified SVG structure/accessibility locally | Reuse the SVG directly in talk materials; update it when architecture or delivery boundaries materially change |
| 2026-09-03 | WS2 | Integrated multi-format trace and exact finalized-run-audit normalization on local `main`; synthetic fixtures cover Chat Completions, Responses API, OpenTelemetry GenAI, lineage/evaluator exclusion, tool evidence, explicit malformed-input failures, and audit fallback; integrated checks passed with 57 non-live tests, one deselection, Ruff, and package build | Convert the generic replay `DataPoint` to `trace-eval-v1`, add the Orq scorer factory, validate genuine multi-step traces, then rotate the temporary trace-access key |
| 2026-09-03 | WS0/WS1 | Confirmed local `main` contains the verified chatbot core and evaluator-native judge framework; non-live suite passed with 45 tests and one deselection; Ruff passed | Preserve baseline while rebasing active work |
| 2026-09-03 | WS2 | Trace importer is active in an isolated worktree with multi-format fixtures/tests under development | Reconcile to the integrated row contract; validate real agent traces; do not mark complete yet |
| 2026-09-03 | WS3 | Hosted YAML/SDK sync now explicitly covers agent/tools plus two deterministic and four LLM judge evaluator resources, one YAML file each; Make targets, row-aware bridge, and 50-case corpus remain active in an isolated task | Finish offline validation for every resource kind, remove tracked runtime IDs, then review the unified remote plan before any apply |
| 2026-09-03 | WS4 | Integrated the credential-free offline CI workflow on local `main`; it pins actions, excludes all live markers, runs Ruff/tests/package build, and exposes no Orq credential | Revalidate after dependency or hosted-resource integration; remote-run evidence awaits publication |
| 2026-09-03 | Planning | Consolidated status, acceptance evidence, security, remote-state, evaluator-resource scope, and integration order; added canonical root guidance requiring this plan to stay current | Update this table in the same task and commit whenever status or decisions change |
| 2026-09-06 (2) | Delivery | Restructured the talk story on the alignment-decay thesis after a three-persona review (speaker, marketing, technical audience). Removed the internal n8n/service split from the deck and docs; retargeted the boundary-vs-gap material at the podcast run (OSWorld 72.6% as gap, invented $500 figure as boundary) and dropped the analytics agent from the narrative; corrected stale narration-run examples in `outline.md` (script now 371 words / four minutes / four of eight topics); removed the borrowed MT-Bench 81/85 agreement numbers and replaced the "agreement is the ceiling" claim with consensus labels plus separate false-pass reporting. Pre-review outline preserved at `story-outline-pre.md` | Three review findings remain open and are tracked in `story-outline.md`: the multi-judge run is still labelled real with no artifact, all measured evidence still comes from a different agent than the running example, and the critique-reading method has no stated sampling strategy at scale |
| 2026-09-06 (3) | WS5 | Completed five clean pipeline runs over the same inbox week and derived their delivered two-host scripts by running the script stage in the ai-api container without TTS. Five distinct digests, three formats (`deep_dive` x2, `debate`, `critique` x2), four host pairs and 3-6 minute targets came out of identical input; two runs needed a refine pass and all five shipped with zero residual deterministic-filter issues. Artifacts tracked in `docs/examples/podcast-corpus-2026-09-06/`, giving six real episodes with the captured production run. The temporary manual workflow `TALKmanual0000001` and all staged container files were removed | Six episodes, not the ten targeted; run four more before the multi-judge measurement, then apply `orq/resources/evaluators/jury/podcast-claudish.yaml` and replace the placeholder ring positions on the disagreement slide |
| 2026-09-06 (4) | Delivery | Dropped the boundary-vs-gap slide from the deck and reduced the corresponding story beat to the grey-zone framing alone. The gap/boundary distinction survives only as reference prose in `docs/talk-example-podcast.md` | Do not reintroduce the slide without a new decision; the deck no longer teaches the distinction explicitly |
| 2026-09-06 (5) | WS5 | Ran the three-model claudish measurement without any hosted mutation: `podcast-claudish.yaml` prompt unchanged, invoked directly through the router at temperature 0 over the six real episodes (18 calls). Four of six episodes returned split verdicts; pairwise agreement Gemini/Qwen 6/6, Gemini/DeepSeek 2/6, DeepSeek/Qwen 2/6. On the production episode two judges quote the same passages and return opposite labels, locating the threshold question the rubric never settles. No self-preference observed — the generating model failed all six. Qwen leaked reasoning into its output and required label parsing. Evidence in `docs/examples/claudish-jury-2026-09-06/` | Pre-alignment and unlabelled: no judge is established as correct. Obtain human labels before any agreement number is presented as alignment, and keep the hosted evaluator-creation gate closed |

## Next Actions

1. Review Task 1's isolated Sphere data-model commit, then execute Tasks 2-4 in `2026-09-06-decision-support-evaluation.md`: context-enriched v4 definitions, the single subjective local `decision_support_quality` jury, and its matching repository resource.
2. Stop at Task 5 until the user supplies the exact published evaluatorq version whose `llm_jury(assignment="all")` returns the complete jury record.
3. Review the 19-slide analytics-only deck and replace its two explicit walkthrough placeholders only after the corresponding Sphere response and full jury evidence exist.
4. Keep v4 live simulation, the 450-call jury, human annotation, hosted-resource apply, CI gating, and multi-agent prompt optimization behind separate explicit gates.

Do not resume the v3 correctness stability job; its artifacts remain historical evidence for why the active alignment target changed.
