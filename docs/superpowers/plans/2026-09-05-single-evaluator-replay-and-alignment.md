# Single-Evaluator Replay and Alignment Implementation Plan

> **Status:** proposed; execution has not started.

**Goal:** Recover ten existing development observations, replay them through
evaluatorq without target inference, compare two immutable versions of the
answer-correctness evaluator, and validate the evaluator-alignment skill's
grey-zone workflow twice.

**Design:** [Single-Evaluator Replay and Alignment Design](../specs/2026-09-05-single-evaluator-replay-and-alignment-design.md)

**Constraints:** Do not rerun simulation, inspect the frozen test split, create
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

## Task 1: Re-establish live-run authentication safely

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

## Task 2: Choose one existing-observation source

**Files:** `src/analytics_chatbot/evaluation_ops/trace_import.py`,
`src/analytics_chatbot/evaluation_ops/simulation_artifacts.py`,
`tests/test_trace_import.py`, `tests/test_simulation_artifacts.py`, ignored run
artifacts

1. Add two failing comparison fixtures that represent the same completed
   attempts in simulation and Responses-trace form.
2. Retrieve the two latest matching multi-step agent traces using OAuth read
   access and hydrate their Responses steps. Keep runtime identifiers and raw
   content out of Git.
3. Compare ordered messages, final output, tool call arguments, tool results,
   call errors, case linkage, and reasoning availability in a scrubbed matrix.
4. Select raw simulation results when they are recoverable and complete;
   otherwise select trace import only if it preserves all required acceptance
   evidence. Document one canonical path and leave the other optional.
5. Add regression tests for every material format gap found. Explicitly reject
   response-only or summary-only records that cannot reconstruct the agent
   conversation without guessing.

## Task 3: Recover and freeze ten development observations

**Files:** `src/analytics_chatbot/evaluation_ops/simulation_artifacts.py` or
`src/analytics_chatbot/evaluation_ops/trace_import.py`,
`tests/test_simulation_artifacts.py` or `tests/test_trace_import.py`, ignored
canonical run directory

1. Locate existing raw results or complete traces; do not invoke the target
   agent or simulation generator.
2. Add failing tests that require a stable transcript fingerprint to survive
   normalization and use `(case_id, transcript_fingerprint)` as sample identity.
3. Normalize only distinct, oracle-bearing observations whose case definition
   is already assigned to `dev`.
4. Apply light checks: final assistant output, ordered tool pairing, expected
   `query_sql`, resolvable oracle, and exact-transcript deduplication.
5. Produce a scrubbed manifest with 10 distinct sample identities, source type,
   case split, tool counts, acceptance result, and corpus digest. If fewer than
   10 existing observations are available, stop and mark the workstream blocked;
   do not manufacture the remainder.

## Task 4: Make replay genuinely no-inference and single-rubric

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

## Task 5: Add the versioned hosted-evaluator scorer

**Files:** `src/analytics_chatbot/evaluation_ops/hosted_evaluators.py`,
`src/analytics_chatbot/evaluation_ops/__init__.py`,
`tests/test_hosted_evaluators.py`

1. Write failing fake-client tests for an immutable `id@version` selector,
   answer-correctness context routing, result mapping, missing-result failure,
   SDK error propagation, and local non-applicability without an SDK call.
2. Implement the small `orq_evaluator(...)` factory around
   `client.evals.invoke_async` and return evaluatorq `EvaluationResult` values.
3. Resolve the YAML stable key to a runtime evaluator ID only through ignored
   state or a fresh remote lookup; never add an opaque ID to tracked YAML.
4. If the evaluator does not exist, stop at the explicit hosted-resource
   creation gate. Do not bypass the current human-label gate implicitly.

## Task 6: Label the development pilot and compare two versions

**Files:** accepted human-label artifact under `orq/resources/alignment/`,
comparison/report module and tests, ignored evaluatorq run artifacts

1. Define and validate one answer-correctness verdict and explanation per sample,
   bound to the sample identity and corpus digest. Machine scores never populate
   this artifact.
2. Fetch the baseline evaluator and record its immutable version selector.
3. Estimate the cost of both singleton ten-row runs and obtain explicit approval
   before invoking the hosted judge.
4. Run evaluatorq once for the baseline and once for the candidate with
   `inference=False`, identical ordered rows, and exactly one evaluator per
   experiment.
5. Join results one-to-one by sample identity. Report pass/fail transitions,
   disagreement count, pass-rate delta, and errors; exclude N/A and errors from
   pass-rate denominators.
6. Label the report as development-only same-row evidence and leave evaluator
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
