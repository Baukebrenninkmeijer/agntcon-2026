# Single-Evaluator Replay and Alignment Design

## Decision

The next evaluation increment uses ten **existing, observed** development
conversations and one rubric: `answer_correctness`. It does not rerun the
analytics agent, generate new simulation cases, or treat case definitions as
observations.

Two matched pilot attempts are first compared between the retained simulation
representation and their Orq Responses traces. The more complete representation
becomes the single ingestion source for all ten rows. Raw evaluatorq
`SimulationResult` data is preferred when it can be recovered because it keeps
the transcript, tool calls, tool results, final answer, and case identity
together. Orq traces are the fallback when they preserve the same evidence.
Reasoning summaries are useful enrichment, not an acceptance requirement.

If ten distinct existing, oracle-bearing observations cannot be recovered, the
workflow stops with an explicit data prerequisite. It must not silently run new
simulations to fill the gap.

## Dataset boundary

The repository currently contains 50 unique case definitions with a stable
30-development/20-test assignment, but no retained raw `SimulationResult`
files. The tracked pilot review contains three attempts for one case. These are
different quantities and must remain named separately:

- **case definition**: an input scenario and optional oracle;
- **observation**: one completed agent conversation for a case;
- **stability repetition**: one evaluator judgment of an observation;
- **human label**: a reviewed reference verdict and explanation.

The ten-row increment uses only oracle-bearing cases already assigned to the
development split. It is a prompt-development/calibration pilot, not a held-out
evaluation. The frozen 30/20 assignment remains unchanged for the later full
run; the test split is not inspected or scored during this increment.

Each accepted row has an immutable comparison identity derived from
`(case_id, transcript_fingerprint)`. Duplicate transcripts for the same case are
dropped; distinct attempts remain distinct. Acceptance is intentionally light:
complete ordered messages, a final assistant response, a resolvable case and
oracle, paired tool calls/results, and expected `query_sql` activity.

## Native evaluatorq replay

Evaluatorq 1.33.0 is the sole runner. The recorded assistant output is replayed
with `inference=False`, with no target job supplied. The scorer consumes
`params["output"]`, proving it judges evaluatorq's recorded output boundary.

Only `answer_correctness` runs in this increment. The existing plural builder
may remain for future work, but the focused path selects exactly one evaluator
and must not interpret an empty evaluator list as an instruction to run all
four.

Baseline and candidate evaluator versions run as separate singleton
experiments over the same ordered rows and corpus digest. Hosted evaluator
references use immutable `id@version` selectors. The comparison joins results
by sample identity and reports paired verdict transitions, pass-rate delta,
disagreements, and errors separately. Same-row improvement is development
evidence only and must not be described as generalization.

## Hosted evaluator boundary

A thin scorer factory maps the answer-correctness evidence into
`orq.evals.invoke_async` and converts the returned value, explanation, and pass
state into evaluatorq's `EvaluationResult`. Applicability is decided locally;
non-applicable rows do not invoke Orq.

The local YAML currently has a stable evaluator key but no confirmed hosted
evaluator ID. Creating or changing a hosted evaluator remains a separate,
explicitly reviewed mutation. A healthy Orq CLI OAuth session is not evidence
that evaluatorq or the SDK has the required project-scoped `ORQ_API_KEY`.

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

- generating or rerunning simulations to reach ten observations;
- evaluating all four rubrics;
- allocating a ten-row micro test split or changing the frozen 30/20 split;
- claiming promotion readiness from same-row retesting;
- building a custom evaluation execution loop or JSONL result ledger;
- creating, rewriting, or promoting a hosted evaluator without its explicit
  approval and cost gates.
