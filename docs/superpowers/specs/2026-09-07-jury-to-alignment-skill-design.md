# Jury-to-Alignment Annotation Skill Design

## Decision

Build a jury-native annotation accelerator with two bounded components:

1. a repository-local skill at `.agents/skills/orq-jury-to-alignment/` in this
   project, backed by a project script that converts completed evaluatorq jury
   evidence into a human-review queue; and
2. a backward-compatible jury view in the existing `orq-evaluator-alignment`
   skill in `orq-ai/assistant-plugins`.

The handoff stops after human annotation. The existing alignment skill's prompt
rewrite, evaluator creation, and retest stages are single-judge workflows and
must not be presented as a valid 3-by-3 jury retest. A later jury-native prompt
comparison can consume the human labels, but it is not part of this increment.

This serves the abstract's **Align an LLM-as-a-judge** section and the manual
outline's agreement-versus-accuracy beat. It adds no talk section: disagreement
and wobble accelerate the human-first walkthrough already promised.

## Inputs and identity

The producer takes:

1. the canonical 50-case v4 definition JSONL;
2. one accepted evaluatorq simulation observation for every definition; and
3. one `decision-support-jury-v1` record for every observation.

It reuses `load_simulation_replay` and the existing typed jury validation rather
than implementing another replay normalizer. It enforces the exact canonical
case-ID set, exactly one observation and jury row per case, the frozen 30-dev /
20-test split, matching recorded output, and matching
`(case_id, transcript_fingerprint)` identities.

Each development item receives a stable `annotation_id` equal to the SHA-256 of
`case_id + "\0" + transcript_fingerprint`. Human annotations are keyed by this
ID. A positional `source_index` may be included for display and legacy tooling,
but it is never the annotation identity.

## Reviewer-safe evidence

Only these agent-visible fields may enter a review item:

- case ID and transcript fingerprint;
- decision context;
- ordered conversation and tool events;
- recorded final response; and
- the complete jury result: panel state, every vote, and every retained
  repetition value and explanation.

The producer uses an allowlist. Oracle SQL, expected output, reference, ideal
answer, hidden answer, success criterion, and equivalent reference-family data
must not enter `queue.json` or `annotations.json`.

The development run directory contains no test verdict, explanation,
conversation, decision context, or output. `test_manifest.json` contains only
the 20 test case IDs, transcript fingerprints, annotation IDs, and split name so
the frozen set can be identified later without exposing its outcomes.

## Signal semantics

The queue distinguishes evaluator ambiguity from evaluator failure.

- **Within-judge wobble:** normalized categorical entropy across the non-null
  repetition verdicts of one successful judge, using the existing three-label
  `pass` / `fail` / `not_applicable` verdict space. At least two non-null
  repetitions are required; otherwise that judge is unmeasurable.
- **Panel disagreement:** at least two successful, non-abstaining aggregate
  judge verdicts exist and are not all equal.
- **Abstention:** any successful vote has `abstained=true` or a null aggregate
  verdict. This is high-signal ambiguity.
- **Tie:** the released jury has `tie=true`. This is high-signal ambiguity.
- **Inconclusive:** the released jury has `inconclusive=true`. This is retained
  with the tie/abstention tier when it is not caused by a mechanical failure.
- **Mechanical error:** a failed judge, failed repetition, replacement, provider
  error, malformed record, or fewer than two successful judges. It is written to
  `jury_errors.json` and excluded from the annotation ranking.

The current guarded jury runner rejects mechanical errors before publication,
so `jury_errors.json` will normally be empty. Keeping the category separate
prevents a future transport failure from masquerading as useful ambiguity.

## Deterministic priority

Development rows are ordered in these tiers:

1. tie, abstention, or genuine inconclusive outcome;
2. panel disagreement and within-judge wobble;
3. panel disagreement only;
4. within-judge wobble only; and
5. unanimous, internally stable controls.

Within tiers 1–4, sort by the number of present high-signal flags descending,
then maximum measurable per-judge instability descending, then normalized panel
agreement ascending (`null` sorts before numeric values), then `annotation_id`.
Tier 5 is a deterministic sample of at most five rows selected with seed 42 from
the annotation-ID-sorted eligible pool. A row selected in tiers 1–4 cannot also
be a control.

## Output contract

The producer publishes one new run directory atomically by writing every file
to a sibling staging directory, fsyncing files and the staging directory,
writing `manifest.json` last with `status: "ready"`, and renaming the staging
directory to a destination that must not already exist. A failed or competing
publication leaves no destination that looks ready.

`queue.json` has `meta.mode: "jury"`, the categorical verdict space, algorithm
version, seed, counts, and input fingerprints. Every item carries:

- `annotation_id`, `case_id`, `transcript_fingerprint`, rank, and control flag;
- explicit priority reasons and derived signal values;
- the reviewer-safe decision evidence; and
- the full released jury object inline.

The run directory also contains `test_manifest.json`, `jury_errors.json`, and
the ready `manifest.json`. It does not fabricate single-judge `stability.json`,
`metrics.json`, `cross_model.json`, `evaluator.json`, or `traces.jsonl` files.

## Annotation-view compatibility

The assistant-plugins change is backward-compatible:

- legacy queue items continue to render and save by `source_index`;
- jury items require a unique `annotation_id` and save by that ID;
- the main decision evidence renders before any jury output;
- jury evidence is collapsed by default to reduce anchoring;
- expanding it shows panel state, each model's aggregate verdict and
  explanation, and all retained repetition verdicts and explanations; and
- tie, abstention, inconclusive, disagreement, wobble, and control badges are
  visually distinct from mechanical errors.

The server validates unique annotation identities before serving and copies
`case_id` plus `transcript_fingerprint` into each saved annotation record. It
never serves a separate evidence file or dereferences an arbitrary path supplied
by `queue.json`.

## Scope and safety

- No network, evaluator, target-agent, hosted-resource, or credential access.
- No model calls and no rerun of the completed jury.
- No prompt rewrite, evaluator creation, promotion, or retest.
- No test evidence in the development annotation directory.
- Runtime artifacts remain Git-ignored unless separately sanitized and approved.
- The assistant-plugins work happens in an isolated worktree based on current
  `origin/main`, and the verified build is installed locally for Codex testing.

## Acceptance evidence

The project producer is accepted only when focused tests prove exact corpus
coverage, strict identity joins, oracle exclusion, signal classification,
mechanical-error separation, deterministic ranking/control sampling, test
sealing, lossless inline 3-by-3 evidence, and atomic no-clobber publication.

The assistant-plugins consumer is accepted only when its existing legacy tests
remain green and new tests prove jury identity validation, jury annotation
round-tripping, reviewer-safe evidence ordering, complete panel/repetition
rendering, collapsed-by-default jury details, and visible high-signal badges.

The first real execution remains blocked on accepted v4 observations and the
separately approved jury operations. The adapter and view can be implemented and
verified entirely with synthetic fixtures before those artifacts exist.
