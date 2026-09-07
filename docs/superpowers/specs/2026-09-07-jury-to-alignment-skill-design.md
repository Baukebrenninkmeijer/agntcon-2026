# Jury-to-Alignment Companion Skill Design

## Decision

Add a repository-local skill at `.agents/skills/orq-jury-to-alignment/`. It is a
small, offline adapter between the detailed evaluatorq
`decision-support-jury-v1` artifact and the existing
`orq-evaluator-alignment` skill. It does not call a model, rerun the jury,
create human labels, or replace the existing alignment workflow.

This change serves the abstract's **Align an LLM-as-a-judge** section and the
manual outline's agreement-versus-accuracy beat. It adds no talk section or
runtime promise: the companion makes the approved jury evidence usable for the
human-first alignment walkthrough.

## Preconditions and boundaries

The adapter requires three complete, immutable inputs:

1. the 50-case v4 definition JSONL;
2. one accepted observed conversation for every case; and
3. one complete `decision-support-jury-v1` row per observation, containing the
   ordered three-model panel and three detailed repetitions per model.

The adapter joins evidence only by `(case_id, transcript_fingerprint)`. It fails
before writing output when identities, split assignments, recorded outputs,
panel membership, repetition counts, or released jury fields are incomplete or
inconsistent. Definitions are not observations, and aggregate jury verdicts are
not human labels.

The first real run remains gated: v4 observations do not yet exist, and neither
the two-row jury smoke nor the 450-call jury has run. This design authorizes only
the credential-free adapter implementation and tests.

## Derived signals

For each observation, the adapter derives two different kinds of ambiguity:

- **within-judge wobble**: instability across a single model's three repetition
  verdicts, calculated independently for each judge with the existing
  categorical-instability definition;
- **between-judge disagreement**: disagreement among the three judges' aggregate
  verdicts, preserving each judge's model, verdict, explanation, and all three
  repetition records.

These signals prioritize annotation; they do not decide correctness. The
adapter must not pool all nine repetitions into one pseudo-judge, because doing
so erases the distinction between a judge disagreeing with itself and judges
disagreeing with one another.

## Output and handoff

The adapter writes a new no-clobber run directory containing:

- `jury_analysis.json`, the lossless joined evidence plus per-judge wobble and
  panel-disagreement summaries;
- `queue.json`, using the existing alignment skill's downstream queue contract
  but preserving the jury-specific priority order and evidence pointers;
- `stability.json`, `metrics.json`, and `cross_model.json`, transparent
  compatibility projections for inspection rather than inputs to another run;
- `evaluator.json`, the categorical verdict space and evaluator context required
  by the existing queue renderer; and
- `traces.jsonl`, the full reviewer-visible decision context, conversation, tool
  evidence, and final response indexed by `source_index`.

The compatibility files are projections, not the source of truth. The companion
writes `queue.json` directly because the existing builder orders all
self-instability before model disagreement and cannot express the approved jury
priority without losing meaning. Every queue item retains a pointer to its
corresponding `jury_analysis.json` record so the reviewer can inspect all nine
judgments and explanations. The companion hands the run directory to
`orq-evaluator-alignment` at its grey-zone/annotation stage; that skill continues
to own annotation, aggregation, prompt revision, and retesting.

No test row enters prompt development. The adapter produces the prioritization
queue from the 30 development rows and writes only the identities and evidence
fingerprints of the 20 test rows to a sealed inventory for later frozen
evaluation. It does not project, reveal, or aggregate test verdicts during
alignment.

## Prioritization

Development rows are ordered deterministically:

1. both panel disagreement and within-judge wobble;
2. panel disagreement only;
3. within-judge wobble only; and
4. a seeded, bounded sample of unanimous and internally stable controls.

Within a tier, higher maximum per-judge instability sorts first, followed by
lower panel agreement and stable source identity. Mechanical failures are
rejected rather than ranked. Queue reasons use explicit names instead of
calling every signal a "flip."

## Safety and error handling

- No network, evaluator, target-agent, hosted-resource, or credential access.
- No overwrite of an existing output directory or artifact.
- Atomic writes; partial output is removed or clearly marked invalid.
- Exact supported input schema: `decision-support-jury-v1` only.
- Deterministic output for identical inputs and seed.
- Full evidence remains local and Git-ignored unless the user separately chooses
  a sanitized artifact for version control.

## Acceptance evidence

Implementation is accepted only when focused tests prove:

- strict 50-row identity joins and preserved 30/20 split;
- rejection of missing, duplicate, mismatched, or mechanically failed records;
- correct independent wobble calculation for each of three judges;
- correct separation of panel disagreement from within-judge wobble;
- lossless retention of all three votes and all nine repetition records;
- deterministic prioritization and stable-control sampling;
- `queue.json` accepted by the existing grey-zone and annotation consumers;
- test rows excluded from the development review queue; and
- a no-network test fails if an evaluator or target call is attempted.

The first execution over real evidence can happen only after accepted v4
observations and the separately approved jury runs produce the required inputs.
