# Three-version development comparison

This directory records the dev-only evaluatorq Experiment that places all three
`decision_support_quality` prompt versions side by side. It reuses the immutable stored jury
results and the 30 confirmed human labels. It does not call a judge model and does not include any
held-out test row.

- Experiment: `01M20HXBVGJGSP31DMJ2MXDQEG`
- Run: `01M20HXBVG64SBWTH5RZMDK0HS`
- Rows: 30 development identities
- Jobs: `Prompt v1 · baseline`, `Prompt v2 · human rules`, `Prompt v3 · materiality`
- Evaluators: `aligned_with_human`, `panel_consensus`, `within_judge_stability`
- Work: 270 local boolean scores, zero model calls

The resulting pass counts are:

| Version | Human alignment | Panel consensus | Within-judge stability |
|---|---:|---:|---:|
| Prompt v1 | 27/30 | 26/30 | 24/30 |
| Prompt v2 | 27/30 | 22/30 | 22/30 |
| Prompt v3 | 27/30 | 27/30 | 27/30 |

This makes the development conclusion visible: v3 is less wobbly, but it is not more aligned with
the human labels. All three versions still miss the same three human failures at aggregate level.

## Why the cells have colour

The Orq evaluatorq ingestion path infers an evaluator's output type from the runtime type of
`score.value`. A Python `bool` becomes `evaluator_output_type: boolean`; a string such as `"pass"`
does not. The Experiments comparison templates apply the green/red pass/fail treatment only to
boolean evaluator values.

The relevant source paths inspected on 8 September 2026 were:

- orquesta-web at `0b64f23069267815534fd3d67f5478caf923daae`:
  `apps/spreadsheets-api/src/handlers/evaluations/transform-evaluation.util.ts`
  (`resolveOutputType` and `inferEvaluatorTypes`)
- the same orquesta-web revision:
  `libs/features/workflows/experiments/models-comparison/src/lib/components/compare-review/compare-review.component.html`
- evaluatorq at `af28f622a2c68bbdb6b87ae256cd89f6719d33a5`: `src/evaluatorq/types.py` and
  `src/evaluatorq/send_results.py`

The comparison scorers therefore return literal booleans. They intentionally leave evaluatorq's
separate `pass` flag unset: a red cell is a diagnostic finding, not a failed experiment execution.

`receipt.json` binds the hosted run to the exact three jury hashes and human-label hash. The
reproducible uploader is `scripts/upload_decision_support_jury_comparison.py`.
