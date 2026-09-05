# Single-Evaluator Replay and Alignment Design

## Decision

The next evaluation increment replays all 50 **existing, observed** edge-v2
conversations with one rubric: `answer_correctness`. It does not rerun the
analytics agent or treat case definitions as observations. Alignment and prompt
iteration use development rows only; test results stay quarantined until the
final pinned-version comparison.

After this design was drafted, the user explicitly approved one bounded run of
all 50 definitions. That run is now the single ingestion source: raw evaluatorq
`SimulationResult` data keeps the transcript, tool calls, tool results, final
answer, and case identity together. Orq traces are optional enrichment only;
the earlier two-record source comparison is no longer a prerequisite.

## Dataset boundary

The edge-v2 corpus contains 50 unique case definitions with a stable
30-development/20-test assignment. The ignored local run directory contains one
raw output for every definition. All 50 normalize into structurally valid replay
rows; ten behavioral failures and five expected-save QC warnings remain in the
immutable corpus and are not filtered.
These quantities must remain named separately:

- **case definition**: an input scenario and optional oracle;
- **observation**: one completed agent conversation for a case;
- **stability repetition**: one evaluator judgment of an observation;
- **human label**: a reviewed reference verdict and explanation.

The initial alignment discussion may use a deterministic ten-row pilot sampled
from the oracle-bearing development rows. Human labeling stays inside the
30-case `dev` split. This is prompt-development/calibration, not held-out
evaluation. The frozen 30/20 assignment remains unchanged. Baseline test scores
may be stored by the all-row replay, but they are not displayed, aggregated,
labeled, or used for prompt decisions.

Each row has an immutable comparison identity derived from
`(case_id, transcript_fingerprint)`. Duplicate transcripts for the same case are
identified; distinct attempts remain distinct. Acceptance is intentionally light:
complete ordered messages, a final assistant response, a resolvable case, and
paired tool calls/results. Behavioral outcomes and expected-tool misses are
retained as metadata and warnings.

## Native evaluatorq replay

Evaluatorq 1.33.0 is the sole runner. The recorded assistant output is replayed
with `inference=False`, with no target job supplied. The scorer consumes
`params["output"]`, proving it judges evaluatorq's recorded output boundary.

Only `answer_correctness` runs in this increment. The existing plural builder
may remain for future work, but the focused path selects exactly one evaluator
and must not interpret an empty evaluator list as an instruction to run all
four.

The live `analytics-answer-correctness` resource matches tracked YAML and has
one version, `1.0.0`, as of 2026-09-05. The baseline scorer is pinned to its
runtime `id@1.0.0` selector; the opaque ID is resolved at runtime and never
tracked. After human-guided alignment, an approved prompt update creates a new
immutable evaluator version. evaluatorq then receives both pinned selectors in
one run with distinct names such as `answer_correctness@1.0.0` and
`answer_correctness@1.0.1`, producing side-by-side columns over identical rows.
Never resolve `latest` during a comparison.

The comparison joins results by `(case_id, transcript_fingerprint)`, never by
`case_id` alone, and reports paired verdict transitions, pass-rate delta,
disagreements, and errors separately. Same-row development evidence is not
generalization. Machine evaluator results stay in evaluatorq/Orq Experiments;
only human verdicts and references enter alignment label artifacts or the
annotations API.

## Hosted evaluator boundary

A thin scorer factory maps answer-correctness evidence into
`orq.evals.invoke_async` and converts `value`, `explanation`, and `passed` into
evaluatorq's `EvaluationResult`. The installed SDK 4.14.7 response model exposes
the typed `result` field; fake-client tests cover mapping and missing-result
failures. Applicability is decided locally, so rows without an oracle return
`not_applicable` without invoking Orq.

The local YAML stable key resolves to a hosted evaluator in `pydata2026`; a fresh
semantic plan is a no-op, and version history contains `1.0.0`. The run key in
the primary ignored `.env` can resolve the resource. Runtime IDs and selectors
remain ignored. Changing the prompt and creating a new version still requires
the explicit alignment approval gate.

## Grey-zone alignment track

The evaluator-alignment skill is applied only after ten canonical observations,
human answer-correctness labels, a fetchable evaluator version, and cost
approval for repeated judge calls exist. An adapter materializes the skill's
run-directory inputs from the canonical rows and evaluatorq results; it does not
create a second evaluation ledger.

The grey-zone assembly and policy-application path is executed twice against
the same stability evidence. The artifacts must be byte-for-byte reproducible,
or the difference must be explained. Derived grey-zone labels remain distinct
from human-confirmed labels.

The preliminary no-cost audit ran the skill's fixture-backed flow twice and
produced identical payload and guidance hashes. A direct repository run failed
because `queue.json` was absent and exposed an uncaught `FileNotFoundError`.
The implementation plan therefore includes an actionable prerequisite error,
clear conversion documentation, and a repeatability check. A genuine alignment
claim remains blocked until real observations and repeated evaluator outputs
exist.

## Non-goals

- rerunning the completed simulation corpus merely to replace failed outputs;
- evaluating all four rubrics;
- allocating a micro test split or changing the frozen 30/20 split;
- labeling, sampling, or inspecting any of the 20 frozen `test` observations
  during this increment;
- claiming promotion readiness from same-row retesting;
- building a custom evaluation execution loop or JSONL result ledger;
- creating, rewriting, or promoting a hosted evaluator without its explicit
  approval and cost gates.
