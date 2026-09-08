# Prompt v3 decision-support jury

This directory is the immutable tracked copy of the prompt v3 evaluatorq jury run completed on
8 September 2026. The run replayed the 50 frozen Sphere.com responses without target inference and
used the configured three judges with three repetitions each.

- Experiment: `01M1Y60F67NA0G94AVBPGF8VA8`
- Run: `01M20F16K491SBD344Z5T2S63Q`
- Workload: 50 rows, 450 judge calls
- Result contract: 50 complete `decision-support-jury-v1` records
- Operational outcome: zero failed judges, failed repetitions, replacements, malformed rows, ties,
  abstentions, or inconclusive outcomes
- Retry note: one Qwen request was rate-limited on its first attempt and succeeded on evaluatorq's
  bounded retry

## Development-only alignment result

The aggregate jury still predicts `pass` for all 30 human-labelled development cases. Against the
27 human passes and three human failures, prompt v3 therefore remains unaligned:

- raw accuracy: 90%
- failure recall: 0%
- false-pass rate on human failures: 100%
- balanced accuracy: 0.50
- Cohen's kappa: 0

Prompt v3 reduced panel disagreement from eight development cases to three and within-judge wobble
from eight to three. The three prioritized cases are `best-month-net`, `save-staged-emea`, and
`product-drill`. The first two are human failures; `product-drill` is a human pass. The third human
failure, `segment-then-2024-check`, remains a stable unanimous miss.

## Panel diagnosis

Luna detects `best-month-net` and `save-staged-emea`, misses `segment-then-2024-check`, and
incorrectly fails `product-drill`. Its aggregate development result is 28/30 correct, 66.7% failure
recall, 0.815 balanced accuracy, and kappa 0.630. Qwen and Gemini each return `pass` on all 30 cases
and on all 90 of their repetitions. Majority aggregation therefore removes both evidence-backed
Luna failures.

The remaining problem is not another unresolved human definition of correctness. The prompt says
judges *may* compare claims and direct arithmetic with visible evidence, but two panel members
consistently summarize clarity and decision fit without performing that check. All three judges
also accept the stable double-deduction case because they do not test its stated revenue formula
against the visible refunded-row evidence.

The next design decision is whether to make a claim-to-evidence audit mandatory in the prompt,
recalibrate the panel, or do both in separately attributable steps. Do not measure the held-out test
split or promote the evaluator until that decision is made and the revised candidate is selected on
development evidence.

During artifact validation, a summary command computed the aggregate distribution before filtering
to development rows. No test case, explanation, row-level verdict, or human label was inspected, but
the aggregate jury distribution can be inferred and must not inform development decisions. Future
test labeling must use independent reviewers who have not seen jury outcomes.

## Files

- `jury-results.jsonl` — complete 50-row jury record; row-level test evidence remains uninspected,
  but the aggregate distribution was inadvertently summarized during validation
- `evaluator-prompt.txt` — exact prompt passed to evaluatorq by the local scorer
- `evaluator-resource.yaml` — exact repository evaluator resource at run time
- `annotation/` — development-only residual queue containing three prioritized cases, five stable
  controls, zero mechanical errors, and an identity-only test manifest

## Hashes

- Jury JSONL: `1dfb054684d89cfaebe6342385e4967e24f9801aa2c3eb874bb80c2307145fe4`
- Evaluator prompt: `8011acd31590d123afd0a560e523819d8f61888e966fe4635e57f384afc25604`
- Evaluator resource: `33837ff9d318b107e889e5bebde814a78111d1a6a4617f36b131caa5b18afcd0`
