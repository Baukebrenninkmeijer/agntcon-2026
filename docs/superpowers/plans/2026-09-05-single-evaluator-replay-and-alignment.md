# Single-Evaluator Replay and Alignment Implementation Plan

> **Status:** `ACTIVE`. The 50-case simulation and local artifact validation are
> complete. `analytics-answer-correctness` is applied in `pydata2026` at version
> `1.0.0` in `shadow` status. All 50 edge-v2 observations were replayed through
> that pinned version with `inference=False` and uploaded as one Orq Experiment.
> Remaining gates are human labels, repeated-run cost approval, and an approved
> evaluator update.

**Goal:** Replay all 50 existing edge-v2 observations through evaluatorq without
target inference using pinned answer-correctness evaluator versions, align from
human feedback on development rows, and compare baseline and updated versions
side by side on identical datapoints.

**Design:** [Single-Evaluator Replay and Alignment Design](../specs/2026-09-05-single-evaluator-replay-and-alignment-design.md)

**Constraints:** Do not rerun the completed simulation corpus, inspect the frozen test split, create
remote resources without explicit approval, or make paid repeated judge calls
before presenting their cost estimate.

## Parallel execution shape

After the prerequisite audit, three independent tracks can run concurrently:

1. canonical observation recovery and validation;
2. evaluatorq no-inference/single-rubric runner changes;
3. offline grey-zone adapter and error-handling tests.

The hosted version comparison waits for tracks 1 and 2, a fetchable evaluator,
human labels, a project key, and cost approval. Integration and full verification
run only after all accepted tracks land on the same branch.

## Task 1: Re-establish live-run authentication safely (`COMPLETE`)

**Files:** `.env` (ignored), `CLAUDE.md`,
`docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

1. Verify `.env` is ignored and untracked before writing any secret.
2. Check OAuth trace-read access and project-key SDK access independently.
3. If no usable project key exists, mint a least-privilege `pydata2026` key
   without printing it, store it in the primary checkout's `.env`, and set mode
   `0600`. Account for the observed CLI/API mismatch that rejected
   `expires_at`; do not assume the key exists after a failed command.
4. Run the documented run-key preflight without exposing identifiers or tokens.
5. Record only the authentication outcome and rotation obligation in the living
   plan.
6. Confirmed working on 2026-09-05 through the SDK sync path, which loads the
   key with `load_dotenv(override=True)`. Two operator traps were observed and
   must not be mistaken for a bad key: a different `ORQ_API_KEY` exported from
   the shell profile shadows `.env` for bare `orq` CLI calls and fails every
   read with `API key is not valid for this workspace`; and
   `orq evals --project pydata2026` returns `404 Project not found` for this key
   while the SDK resolves the same project correctly. Diagnose the CLI and the
   run path independently, in both directions.

## Task 2: Choose one existing-observation source (`SUPERSEDED`)

Retained as historical context only; must not be implemented.

The explicitly approved 50-case evaluatorq run settled the canonical source: the
raw local `SimulationResult` export. Orq traces remain optional enrichment. The
originally planned two-record simulation-versus-trace comparison, its fixtures,
its scrubbed comparison matrix, and its format-gap regression tests were
cancelled by that approval and were never executed. The rejection of
response-only or summary-only records survives in the simulation-artifact
pipeline acceptance checks and in M2 of the living plan.

## Task 3: Load and freeze the observation set (`COMPLETE`)

**Files:** `src/analytics_chatbot/evaluation_ops/simulation_artifacts.py` or
`src/analytics_chatbot/evaluation_ops/trace_import.py`,
`tests/test_simulation_artifacts.py` or `tests/test_trace_import.py`, ignored
canonical run directory

1. Load the completed 50-row edge-v2 evaluatorq export; do not rerun the target.
2. Preserve `(case_id, transcript_fingerprint)` as sample identity.
3. Normalize all distinct structurally valid rows, including behavioral
   failures, max-turn outcomes, and expected-tool warnings.
4. Fresh evidence: 50 samples, 50 unique identities, zero structural rejects,
   zero duplicates, five non-filtering warnings, and exact recorded-response
   extraction for 50/50 evaluatorq `DataPoint`s.

## Task 4: Make replay genuinely no-inference and single-rubric (`COMPLETE`)

**Files:** `src/analytics_chatbot/evaluation_ops/__init__.py`,
`tests/test_evaluation_ops.py`

1. Replace the current positive-inference test with a failing test proving an
   exploding target job is never called, no jobs are supplied, and
   `inference=False` reaches evaluatorq.
2. Add a failing byte-for-byte assertion that `params["output"]` is the recorded
   final assistant message scored by the evaluator.
3. Add a singular `build_atomic_evaluator(AtomicJudge.ANSWER_CORRECTNESS, ...)`
   path and test that exactly one evaluator runs per row. Reject an explicitly
   empty evaluator collection instead of silently expanding it to four.
4. Remove tool-role contents from the answer-correctness evidence projection and
   cover the boundary exactly; correctness may see the conversation and oracle,
   but not recorded tool results.
5. Implement the minimal runner changes and run the focused tests.

## Task 5: Add the versioned hosted-evaluator scorer (`COMPLETE`)

**Files:** `src/analytics_chatbot/evaluation_ops/hosted_evaluators.py`,
`src/analytics_chatbot/evaluation_ops/__init__.py`,
`tests/test_hosted_evaluators.py`

1. Write failing fake-client tests for an immutable `id@version` selector,
   answer-correctness context routing, result mapping, missing-result failure,
   SDK error propagation, and local non-applicability without an SDK call.
2. Implement the small `orq_evaluator(...)` factory on SDK 4.14.7
   `client.evals.invoke_async` and return evaluatorq `EvaluationResult` values.
   The installed response models expose typed result/value/explanation/passed
   fields; fake-client tests cover success and malformed responses.
3. Resolve the YAML stable key to a runtime evaluator ID only through ignored
   state or a fresh remote lookup; never add an opaque ID to tracked YAML.
4. `analytics-answer-correctness` was applied on 2026-09-05 in `shadow` status
   after a reviewed single-key dry-run; the immediate second plan was a no-op.
   It is the only evaluator in `pydata2026`; the other five remain unapplied.
5. The immutable selector is verified working: `orq evals list-versions` reports
   version `1.0.0` with checksum `fc82a2611ea2877a`, and
   `orq evals invoke <id>@1.0.0` returned `value: pass`, `passed: true`, and an
   explanation. Evaluator `name` is null workspace-wide; `key` is the identity
   field, and the runtime ID stays out of tracked files.
6. The replay CLI requires explicit versions, rejects `latest`, resolves the
   stable key at runtime, verifies version history, and assigns distinct
   versioned evaluatorq column names.

## Task 6: Label, align, and compare two versions (`ACTIVE`)

**Files:** accepted human-label artifact under `orq/resources/alignment/`,
comparison/report module and tests, ignored evaluatorq run artifacts

1. Define and validate one answer-correctness verdict and explanation per sample,
   bound to the sample identity and corpus digest. Machine scores never populate
   this artifact.
2. [x] Resolve the baseline evaluator at runtime and pin `id@1.0.0`.
3. [x] Replay all 50 rows once with `inference=False`, no jobs, one pinned scorer,
   and ten-way bounded concurrency. evaluatorq uploaded all 50 Experiment rows;
   local result printing stayed disabled.
4. Produce human labels only from development rows. Machine scores never
   populate this artifact, and test outcomes stay out of prompt decisions.
5. Estimate the repeated alignment job and obtain explicit approval before
   stability calls.
6. After approval of the rewritten prompt, create a new immutable evaluator
   version and run both pinned versions together over identical ordered rows.
7. Join results one-to-one by the `(case_id, transcript_fingerprint)` sample
   identity, never by `case_id` alone. Report pass/fail transitions,
   disagreement count, pass-rate delta, and errors; exclude N/A and errors from
   pass-rate denominators.
8. Label development evidence separately from the frozen-test result and leave evaluator
   status `shadow`.

## Task 7: Bridge and repeat the grey-zone workflow

**Files:** focused adapter/report code under
`src/analytics_chatbot/evaluation_ops/`, tests, ignored alignment run directory;
optionally the upstream skill scripts in a separate approved change

1. Add failing tests that transform canonical rows, human labels, evaluator
   versions, and repeated scores into the evaluator-alignment skill's documented
   run-directory contract without duplicating the evaluation ledger.
2. Add a prerequisite test proving a missing queue/stability artifact produces
   a concise actionable error rather than an uncaught `FileNotFoundError`.
3. Materialize the run directory from the ten real development observations.
4. Run the required stability repetitions only after the skill's cost approval.
5. Run grey-zone `assemble` and policy `apply` twice against the same evidence.
   Compare payload and guidance hashes, token/drop/truncation statistics, zone
   counts, derived-label counts, and warnings.
6. Record any nondeterminism, unsupported project fields, duplicate CLI output,
   or policy ambiguity as issues. Keep derived and human-confirmed labels
   separate and do not mutate the hosted evaluator automatically.

## Task 8: Integrate, document, and verify

**Files:** `README.md`, `CLAUDE.md`,
`docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`, focused source
and tests above

1. Update operator documentation with the selected data path, the distinction
   between definitions/observations/repetitions/labels, singleton versioned run
   commands, credential preflight, and grey-zone prerequisites.
2. Update every affected status, decision, risk, evidence item, changelog entry,
   and next action in the living plan.
3. Run focused tests, then `uv run ruff check .`,
   `uv run pytest -m "not live and not simulation_live and not alignment_live" -q`,
   and `uv build`.
4. Review the diff for credentials, opaque runtime identifiers, raw trace
   content, accidental test-split access, and unrelated changes.
5. Commit the coherent implementation and evidence. Push only when explicitly
   requested.
