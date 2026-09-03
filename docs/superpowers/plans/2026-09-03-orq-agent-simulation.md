# Analytics Chatbot: Hosted Orq Agent and Evaluation Operations Plan

> **Execution:** use `executing-plans`, `orq-cli`, `evaluatorq`, and `orq-simulate-agent`. Never use `orqi`.

**Goal:** Run the analytics chatbot as a hosted Orq Agent whose functions execute locally, then build the human-reviewed, multi-turn evaluation workflow promised by `abstract.md`: atomic trace-backed evaluation, LLM-judge alignment, nondeterminism measurement, CI, and online trace import.

**Boundary:** Orq owns model selection, instructions, and function declarations. A local session owns DuckDB, insight state, authorization, function execution, and the exact audit record. evaluatorq owns simulated users, multi-turn orchestration, jury execution, experiment upload, and standard simulation scorers.

## Implementation checkpoint — 2026-09-03

This plan remains the target architecture. Local `main` contains a smaller, verified foundation
and deliberately stops at its review and alignment gates:

- Repository YAML plus an idempotent `orq-ai-sdk` reconciler now own the two local function
  declarations, the hosted `analytics-chatbot` agent, two deterministic Python evaluator drafts,
  and four atomic LLM evaluator drafts. `make sync-orq` is the safe dry-run and
  `make sync-orq-apply` is the explicit mutation target.
- The live `pydata2026` project contains the two tools and hosted agent. A second plan reports them
  as no-ops. It contains no evaluator or dataset resources yet.
- LLM evaluator apply fails closed until each YAML validation record documents at least 100 human
  labels. The current atomic drafts are answer correctness, query semantics, evidence
  faithfulness, and multi-turn consistency; they are not aligned or production gates.
- The hosted/local function handshake and explicit-save behavior work in live smoke runs. An
  ambiguity smoke exposed a prompt gap, which was corrected and reverified. The prompt now also
  requires every reported number to be returned directly by successful SQL.
- Fifty deterministic evaluatorq-native case definitions exist as five personas by ten scenarios,
  with executable DuckDB oracles where calculation is applicable and a stable 30-dev/20-test
  split. They are generated from a reproducible grid, not yet from evaluatorq's LLM generator, and
  have not completed human acceptance review.
- `AnalyticsChatbotTarget` preserves a hosted Responses conversation per evaluatorq clone and
  returns native evaluatorq tool/output items. A conversation-scoped `AnalyticsSession`, persistent
  cross-turn insight store, row-aware cache, and timeout registry remain open work from Task 3/5.
- Four direct smoke scenarios (five turns) pass. The one-case simulation pilot required three
  iterations: manual review rejected an arithmetic error the first automated judge missed; the
  second judge rejected unsupported derived claims; the third is the candidate transcript awaiting
  explicit user review. The remaining 49 simulations must not start before that approval.
- Current Orq CLI trace hydration exposes identity, thread, response-chain, status, and metadata but
  omits concrete assistant messages and tool arguments/results. The local `runs/*/events.jsonl`
  audit must enrich trace imports before `inference=False` replay is possible.

Unchecked items below remain unchecked unless the complete planned behavior—not merely this
foundation—has been delivered.

## Relationship to existing specs

- This plan and the revision note in `docs/superpowers/specs/2026-09-02-analytics-chatbot-design.md` supersede that spec's original exclusions of a hosted agent and evaluators. The local execution and safety boundaries remain authoritative.
- `docs/superpowers/specs/2026-09-03-evaluator-native-trace-evaluation-design.md` supersedes the post-hoc evaluator-executor architecture. Online samples reuse the trace importer and the same evaluatorq row contract; there is no separate judge runner or ledger-driven scoring path.
- Simulation and evaluator-native code lives in `src/analytics_chatbot/evaluation_ops/`.
- “Use only the Orq CLI” applies to platform control-plane CRUD and stored-evaluator invocation. The user explicitly approved the Responses runtime and evaluatorq Experiment upload; those are the two non-CLI runtime paths.
- No self-learning or unreviewed automatic prompt mutation is in scope. Natural-language failure feedback may drive a manual, versioned prompt revision.

## Locked decisions

- Workspace/project: `<workspace>` / `pydata2026`.
- Distribution/import: `analytics-chatbot` / `analytics_chatbot`.
- Hosted agent / Responses model: `analytics-chatbot` / `agent/analytics-chatbot`.
- Target model selector: provider `deepseek`, `model_id=deepseek-v4-flash`, function calling required. Current UUID: `6c88a908-a85f-4f9a-83af-31cf11292599`.
- Generator and simulated user: `openai/gpt-5.6-luna` through Responses.
- Four atomic categorical rubrics: `answer_correctness`, `query_semantics`, `evidence_faithfulness`, and `multi_turn_consistency`. Each is aligned independently; correctness and faithfulness must not share oracle/evidence inputs.
- Each applicable rubric uses the same three-model strict-majority jury:
  - `openai/gpt-5.6-luna`, UUID `45a6f5c0-e3ac-416e-9538-d48d80f2b68d`, enabled;
  - `groq/qwen/qwen3.8-27b`, UUID `e30d9593-a54f-5b83-a716-16d707ebfe2f`, currently disabled;
  - `google-ai/gemini-3.5-flash-lite`, UUID `589e98c5-f88f-4e68-9b94-c9f015787a49`, enabled.
- evaluatorq `explanation` is the canonical critique field. Repository JSON exports may alias it to `critique`, but must round-trip without loss.
- Repository YAML is authoritative. Sync is semantic-diff-only by default and mutates only with `--apply`.
- Local Python is 3.13.2; package support stays `>=3.11`; `evaluatorq==1.33.0` remains exact.
- Freeze 50 accepted simulation cases and a 30-dev/20-test split before target inference.
- Generate organically, then enforce explicit coverage presence—not numeric quotas—for every failure mode listed below.
- One canonical observed conversation per case forms the 50 hand-reviewed examples. Dev has one reviewer; test has two independent reviewers and an adjudicated result.
- Trust a jury rubric only if held-out κ ≥ 0.70, balanced accuracy ≥ 0.80, and false-pass rate ≤ 0.10. Exclude deterministically routed `not_applicable` rows from binary metrics and report their coverage separately. All four must qualify before automated jury gating.
- Run a five-case generation pilot, then a distinct five-case live simulation pilot. Name them explicitly; never call both merely “pilot.”
- Stability baseline: 50 cases × 3 independent target runs = 150 conversations.
- CI: offline tests per PR, fixed five-case live canary on demand for trusted PRs, full baseline scheduled/manual.

## Required failure-mode coverage

Every accepted batch must contain at least one human-approved case for each of:

- wrong SQL/filter/join;
- right query with wrong aggregation, denominator, period boundary, gross/net choice, refunds, or cancellations;
- fabricated number without a successful supporting query;
- correct final number reached through an invalid or failed trajectory;
- explicit save intent with the expected state mutation;
- no save intent with attempted/avoided mutation;
- multi-turn context retention and context loss;
- ambiguity that should trigger clarification rather than invented assumptions.

Cases may cover several modes. The coverage report is a presence check and review aid, not a quota allocator.

## Telemetry contract

- Preserve the existing trace name and bounded base tags from `TraceContext`.
- Identity is the actual actor. Interactive calls use the supplied caller identity; simulations use `pydata2026-agent-simulator`; jury calls use `pydata2026-evaluator-jury`. Identity is never a generic grouping surrogate.
- Bounded tags: `pydata2026`, `analytics-chatbot`, plus one run mode (`interactive`, `generation`, `simulation`, `jury`, `posthoc`) and, where useful, one split tag (`dev`, `test`, `mixed`).
- Metadata: `dataset_version`, `agent_version`, `run_kind`, `experiment_slug`, `corpus_version`, `case_id`, `evaluation_split`, `repetition`, `target_model`, `simulator_model`, `jury_version`, and `git_sha`.
- High-cardinality values stay in metadata or thread IDs, never tags.
- Target requests receive per-case metadata from a task-local evaluation context. evaluatorq jury calls receive stable run/jury metadata; case and repetition remain on the parent evaluator span and Experiment row when evaluatorq cannot inject dynamic request metadata. Do not promise unsupported per-row metadata on each child model request.

## Resource layout

```text
orq/resources/
  agents/analytics-chatbot.yaml
  tools/query-sql.yaml
  tools/save-insight.yaml
  evaluators/python/tool-execution-integrity.yaml
  evaluators/python/state-change-policy.yaml
  evaluators/jury/final-response.yaml
  evaluators/jury/trajectory.yaml
  evaluators/jury/state-change.yaml
  evaluators/jury/overall.yaml
  datasets/analytics-chatbot-simulation.yaml
  datasets/simulation-cases.jsonl
  datasets/gold-labels.jsonl
  alignment/status.yaml
  alignment/reports/<jury-version>.json
```

Prompts live as YAML block scalars in their owning resource. Accepted cases, gold labels, and immutable alignment reports are tracked. Candidate pools, transient packets, raw exports, and run caches are ignored.

## Task 1: Resource schemas, runtime pin, and safe Orq reconciliation

**Files:** `.python-version`, `.env.example`, `.gitignore`, `orq/resources/**`, `src/analytics_chatbot/orq_resources.py`, `src/analytics_chatbot/orq_sync.py`, `scripts/sync_orq_resources.py`, and focused tests.

- [ ] Define Pydantic resource models. Agent YAML selects the model by provider/model ID/capabilities; it does not hardcode the current UUID as desired state. Sync resolves the live UUID and records it in generated state.
- [ ] Keep local-only fields (`execution: local`, jury runtime options, model selectors) out of compiled Orq bodies.
- [ ] Store native Python evaluator source in YAML only because Orq requires source upload. Restrict it to deterministic stdlib-only `def evaluate(log)` code, AST-lint disallowed imports/calls, unit-execute it against fixtures, and hash it in reconciliation state.
- [ ] Validate YAML scalar style with `yaml.compose` node metadata rather than assuming a loaded string preserves block-scalar style.
- [ ] Resolve the CLI from `ORQ_CLI` or `shutil.which("orq")`; verify version 6.2.0. The local expected path is `/Users/baukebrenninkmeijer/.local/bin/orq`, but CI is portable.
- [ ] Call `load_dotenv(override=True)` before credential consumers. Never log, serialize, or commit credentials/session content.
- [ ] Implement a reusable subprocess boundary that sends bodies over stdin and always uses `--json --no-input`. No direct resource REST calls and no `orqi`.
- [ ] Follow every list cursor/page until exhaustion before matching stable keys. Detect duplicates before mutation.
- [ ] Dry-run prints normalized semantic diffs. `--apply` reconciles tools, agent, native evaluators, and dataset rows. Enabling disabled models requires the additional explicit `--enable-models` flag; report Qwen's status and estimated jury use before enabling it.
- [ ] Dataset synchronization reuses evaluatorq's `SimulationDatapoint`, `to_orq_dataset_rows`, and JSONL utilities, then uses `orq datasets create-datapoint/update-datapoint`; do not invent a second platform row format.
- [ ] Test pagination, duplicate keys, create/update/no-op, interrupted resume, disabled model, stdin bodies, sanitized output, and CLI portability.

## Task 2: Prove the hosted-Agent/local-function protocol before migration

This is a blocking compatibility spike, not an assumption.

- [ ] Provision only the two function declarations and a draft/sandbox `analytics-chatbot` agent through the dry-run/apply reconciler.
- [ ] Invoke `agent/analytics-chatbot` through Responses with no per-request tool schemas. Verify the response exposes function calls with call IDs, names, and JSON arguments to the client.
- [ ] Execute `query_sql` locally, send `function_call_output` with `previous_response_id`, and verify the hosted agent produces a grounded final answer.
- [ ] Repeat with `save_insight`; verify the client can reject execution and continue the hosted response without remote mutation.
- [ ] Record the exact wire fixture as a scrubbed contract test.
- [ ] If any handshake step fails, stop. Do not remove locally supplied instructions/tools or proceed with the hosted migration until the contract is corrected.

## Task 3: Refactor the local executor into a conversation-scoped session

**Files:** existing agent/gateway/config/models modules plus `src/analytics_chatbot/session.py` and tests.

- [ ] Introduce `AnalyticsSession`: one `Conversation`, one run/audit directory, one `InsightStore`, and one bounded local executor for the full multi-turn conversation. `AnalyticsChatbot.new_session()` creates it; existing `ask()` remains a compatibility convenience.
- [ ] Move model/instructions/tool declaration ownership to the hosted agent only after Task 2 passes. Initial Responses calls do not resend them; continuations use `previous_response_id` and function outputs.
- [ ] Preserve the exact user/assistant/tool transcript, raw arguments, structured results, state snapshots, response IDs, usage, and trace handles across all turns in one session artifact.
- [ ] Use a distinct `save_not_authorized` result when the current turn lacks explicit save intent. Earlier-turn intent never authorizes a later save.
- [ ] Define separate caps: maximum 8 gateway/tool rounds per user turn and maximum 16 executed local calls per turn. Count every call in a multi-call response before executing; fail closed if the total cap would be exceeded.
- [ ] Keep SDK/client retries disabled inside the target. evaluatorq's outer target retry budget owns two retries.
- [ ] Extend `TraceContext` compatibly rather than replacing its established name/tags/identity behavior.
- [ ] Test multi-turn state persistence, intent reset, malformed calls, repeated calls, multi-call cap, round cap, SQL safety, error continuation, and metadata isolation under concurrency.

## Task 4: Generate and freeze cases with executable DuckDB oracles

**Files:** `src/analytics_chatbot/evaluation_ops/cases.py`, `generate.py`, dataset resources, and tests.

- [ ] Reuse evaluatorq `Persona`, `Scenario`, `Criterion`, `SimulationDatapoint`, and JSONL serializers. Add a thin repository envelope only for stable ID, split, coverage labels, oracle, review/provenance, and corpus version.
- [ ] Generate candidate personas/scenarios/opening messages with evaluatorq's generator and `LLMCallConfig(model="openai/gpt-5.6-luna", api="responses")`.
- [ ] Treat generation as necessarily eager because evaluatorq returns `list[SimulationDatapoint]`. Convert the returned batch once to Polars; use lazy `scan_ndjson`/streaming sinks for validation, deduplication, review joins, promotion, and reports. Never claim the LLM generation itself is lazy.
- [ ] Run the five-case **generation pilot**, inspect every row, then generate an oversized candidate pool. Candidate files remain ignored.
- [ ] Every analytics case must carry an executable read-only `reference_sql`, expected typed result, comparison/tolerance/rounding/unit policy, and any required query constraints. Compute expected values from the pinned DuckDB manifest during promotion; never ask the generating LLM to invent ground truth.
- [ ] Every state case carries expected pre/post state and authorization expectation.
- [ ] Human-review candidate inputs for realism, solvability, oracle correctness, and required failure-mode presence. Promote exactly 50 accepted cases.
- [ ] Assign the stable 30/20 split before target inference. Hash the corpus, split seed, dataset manifest, and oracle output.
- [ ] Test deterministic IDs/splits, evaluatorq JSONL round-trip, oracle execution, decimal/date comparison, invalid SQL, coverage gaps, deduplication, and test leakage.

## Task 5: Implement a row-aware evaluatorq simulation job

Do not use `wrap_simulation_agent(target=callable)` for this stateful target; its callback loses row context and local session artifacts.

- [ ] Implement `AnalyticsChatbotTarget(AgentTarget)` with `respond(messages)` and `new()`. Each clone owns one `AnalyticsSession` and returns evaluatorq's existing `AgentResponse`/output item types. Reuse evaluatorq message and tool-call conversion; do not rebuild OpenResponses models.
- [ ] Implement a task-local `EvaluationContext(case_id, split, repetition, experiment_slug, corpus_version)` that the row-aware job binds before `SimulationRunner.run()`. `AnalyticsChatbotTarget.new()` reads it when the runner clones a per-conversation target.
- [ ] Use public `SimulationRunner(target_agent=..., target_agent_timeout_ms=60_000, max_target_retries=2, max_turns=5, llm_config=...)`.
- [ ] Wrap public `runner.run()` in `asyncio.timeout(180)`. Convert timeout/cancellation into an explicit failed row and always close runner/targets.
- [ ] Maintain a concurrency-safe audit registry keyed by evaluatorq run ID and row. The target clone registers its session artifact; after `runner.run()`, the job caches `{SimulationResult, session audit, case oracle}` by `id(DataPoint)` for scorers.
- [ ] Return evaluatorq's `to_open_responses(result, runner.model)` as the job output. Scorers that need trajectory/state use the raw cache instead of expecting the converted output to retain local-only fields.
- [ ] Reuse evaluatorq's `goal_achieved` and `criteria_met` simulation scorers against the cached `SimulationResult`; add only the genuinely project-specific tool-integrity and state-policy scorers.
- [ ] Test clone isolation, cache correlation under parallel completion, timeout cleanup, retry count, transcript/tool conversion, result-less calls, and missing-cache failure.

## Task 6: Import the 50 trace-backed observed examples

- [ ] Run the fixed five-case **live simulation pilot** sequentially. Verify hosted/local handshake, one shared session per conversation, state isolation, trace linkage, and raw-cache scoring.
- [ ] Run one canonical calibration conversation for every frozen case with juries disabled. Import each completed trace into `TraceBackedEvaluationRow` (`trace-eval-v1`) with complete conversation, raw tools/results, retrievals, state snapshots, oracle, split, and source trace/span IDs. This produces the 50 observed examples that humans label; cases alone are not treated as labeled examples.
- [ ] Pre-register the canonical run/row mapping and do not rerun selectively based on output quality.
- [ ] Build review packets from the exact observed final answer, tool trajectory/results, state snapshots, executable oracle, and trace link.
- [ ] For each applicable atomic rubric, store `{value, explanation}` using the exact `pass`/`fail`/`not_applicable` verdict space. One reviewer labels dev; two reviewers independently label test before adjudication. Reject empty explanations.
- [ ] Commit only accepted `gold-labels.jsonl` and provenance hashes. Keep reviewer packets and transient trace exports ignored.

## Task 7: Run and align native evaluatorq atomic judges

- [ ] Feed imported `TraceBackedEvaluationRow.to_datapoint()` rows to one native `evaluatorq(...)` call with the replay job and four routed evaluators. Do not build a bespoke post-hoc evaluator executor or invoke one evaluator per loop.
- [ ] Build each rubric with evaluatorq 1.33 `llm_jury`: categorical labels `pass`, `fail`, `not_applicable`; three exact model refs; `assignment="all"`; `aggregator="majority"`; `min_successful_judges=2`; structured output; Responses routing; and one repetition.
- [ ] Route before inference: correctness needs an expected answer; query semantics needs an executed query and semantic reference; faithfulness needs raw evidence; consistency needs two user turns. Routed rows return `not_applicable`, `pass=None`, and a reason without making judge calls.
- [ ] Project raw trace-backed evidence per rubric. Correctness sees the oracle but no execution evidence; faithfulness sees execution/retrieval evidence but no oracle; query semantics sees executed SQL plus semantic constraints; consistency sees full conversation, tools, and state.
- [ ] Preserve evaluatorq's supported template variables and `{value, explanation, pass}` result contract. Four aggregate Experiment columns are first-class; child judgments remain auditable in jury deliberation rather than being falsely promised as columns.
- [ ] Jury ties, quorum failures, timeouts, and malformed outputs are inconclusive, never passing.
- [ ] Acknowledge Luna's generator/simulator/judge overlap in the alignment report. Mitigate it with hidden generation provenance, executable non-LLM oracles, independent human gold, two other model families, per-model error analysis, and majority voting; do not claim model independence.
- [ ] Align prompts on imported dev rows only using the same evaluator builders and native evaluatorq experiment/scoring lifecycle. On the frozen imported test rows, compute per-rubric confusion matrix, balanced accuracy, false-pass rate, jury-vs-gold κ, human-human κ, and per-model disagreement with Polars. Report routed coverage separately.
- [ ] `alignment/status.yaml` stays `shadow` unless all thresholds pass. Promotion to `gating` is an explicit reviewed repository edit.
- [ ] Test evidence projection, rubric isolation, 3–0/2–1/tie/quorum outcomes, explanation preservation, imbalanced labels, zero denominators, exact thresholds, and tamper hashes.

## Task 8: Measure stability with budgets and failure controls

- [ ] Before a live run, print a deterministic upper bound for target turns, simulator/judge calls, and jury calls. For 150 rows and four three-model juries, the jury ceiling is 1,800 calls; show it explicitly.
- [ ] Require `--confirm-large-run`, configurable `--max-estimated-requests`, and bounded `datapoint_parallelism`/`llm_parallelism` for anything larger than five rows. Abort before inference if the estimate exceeds the configured ceiling.
- [ ] Stop scheduling new rows if authentication/rate-limit errors exceed the configured failure threshold. Preserve completed rows and report partial status honestly.
- [ ] Run 50 × 3 only after calibration labels and alignment reporting exist. Human alignment claims apply to the canonical 50 observed examples; report the 150-run jury stability as a separate generalization/nondeterminism analysis, not additional human-labeled accuracy.
- [ ] Report per-case/rubric pass variance, judge disagreement, tool/state invariant failure, termination reason, token use, latency, and available cost.

## Task 9: Add online trace import and reviewed prompt iteration

- [ ] Reuse the trace importer to produce `trace-eval-v1` rows, then evaluate them with `run_trace_evaluation` and the native evaluatorq experiment flow. Do not add a post-hoc evaluator service, ledger-driven scorer, or machine-as-human annotation path.
- [ ] Treat public trace replay as capability-gated. Import only a hydrated, non-evaluator span lineage that contains the exact user conversation and final assistant output. Hosted Responses-agent traces may expose JSON-encoded `gen_ai.input`/`gen_ai.output` with tool evidence, while observed Analytics Chatbot trace payloads expose only summaries and identifiers.
- [ ] Do not stitch `thread_id`/`previous_response_id` roots into a valid-looking conversation when message or tool-result values are absent. Those identifiers can establish order, but they cannot recover omitted evidence; Responses retrieval alone is also not an exact fallback because it omits submitted continuation inputs/tool results.
- [ ] When the public trace payload lacks exact replay evidence, import the successfully finalized local run-audit JSONL artifact. Fail clearly when neither an exact hydrated trace nor the corresponding audit artifact is available.
- [ ] Select production samples by actual identity and bounded tags; use metadata for trace filtering/joins. Mark post-hoc results as machine evaluations.
- [ ] Preserve source trace/span IDs in every imported evaluatorq row so Experiment results remain joinable to source traces.
- [ ] Add an operator error-analysis command/report that clusters written critiques with Polars and emits proposed prompt changes. It never edits prompts.
- [ ] Apply prompt changes manually in YAML, bump agent/jury versions, review the semantic Orq diff, rerun dev, then evaluate the frozen test once. This is the abstract's feedback-driven optimization loop without self-learning.

## Task 10: CI, runbook, and completion

- [ ] Offline unit tests and Ruff run on every PR.
- [ ] A protected, explicitly triggered PR job runs the fixed five-case live canary and publishes the Experiment URL. Never expose secrets to untrusted forks.
- [ ] A scheduled/manual workflow runs the confirmed 150-row baseline with concurrency locking and request ceilings.
- [ ] Before alignment promotion, CI gates only deterministic invariants/infrastructure; juries report shadow scores. After reviewed promotion, apply the documented jury gate.
- [ ] README covers dotenv override behavior, portable CLI resolution, dry-run/apply/model-enable steps, both pilots, oracle generation, human labeling, alignment, request estimates, Experiment links, telemetry queries, post-hoc evaluation, and recovery from partial runs.

## End-to-end order

```bash
uv run ruff check .
uv run pytest -m "not live and not simulation_live and not alignment_live" -q
uv run analytics-chatbot sync-orq                         # semantic diff only
uv run analytics-chatbot sync-orq --apply --enable-models # reviewed resources + explicit Qwen enable
uv run analytics-chatbot verify-hosted-local-contract
uv run analytics-chatbot generate-cases --count 5         # generation pilot
uv run analytics-chatbot generate-cases --candidate-count 80
uv run analytics-chatbot promote-cases --accepted-count 50
uv run analytics-chatbot sync-orq                         # review the accepted dataset-row diff
uv run analytics-chatbot sync-orq --apply                 # publish accepted dataset rows
uv run analytics-chatbot simulate-live --mode live-pilot --cases 5 --repetitions 1
uv run analytics-chatbot simulate-live --mode calibration --cases 50 --repetitions 1
uv run analytics-chatbot export-label-packets
# humans label dev/test; accepted gold-labels.jsonl is reviewed and committed
uv run analytics-chatbot import-simulation-traces         # validate trace-eval-v1 rows
uv run analytics-chatbot align-evaluators --split dev     # native evaluatorq replay; no target rerun
uv run analytics-chatbot align-evaluators --split test --frozen
uv run analytics-chatbot simulate-live --mode baseline --cases 50 --repetitions 3 --confirm-large-run
```

## Completion evidence

- Hosted-agent/local-function contract fixture passes before migration.
- Live Orq resources and repository YAML have no semantic diff.
- Hosted agent uses the resolved DeepSeek V4 Flash catalog entry; functions execute only locally.
- Conversation-scoped state persists across turns; unauthorized saves cannot mutate state.
- Fifty cases have executable, reproducible oracles and a frozen 30/20 split.
- Fifty observed conversations have accepted human labels with explanations.
- Experiments expose built-in simulation scores, deterministic invariant scores, and four independently routed atomic majority-jury columns.
- Alignment reports reproduce from accepted JSONL with the locked thresholds and clearly separate canonical accuracy from 150-run stability.
- Traces preserve actor identity and are filterable/joinable through the documented metadata.
- Online trace imports use the same evaluatorq-native scoring path without representing machine verdicts as human labels.
- No secret, candidate pool, transient review packet, or raw temporary export is committed.

## Authoritative implementation references

- evaluatorq v1.33 `SimulationRunner(target_agent=...)`, `AgentTarget.new()`, `SimulationDatapoint`, JSONL export utilities, `to_open_responses`, built-in simulation scorers, and `llm_jury`.
- evaluatorq v1.33 production Experiment example `examples/agent_simulation/05_wrap_and_experiment.py`; use its `evaluatorq(...)` lifecycle, while replacing its stateless wrapper with the row-aware job required here.
- Orq CLI 6.2 command help for models, agents, tools, evals, and dataset datapoints. Re-check command help during implementation.
