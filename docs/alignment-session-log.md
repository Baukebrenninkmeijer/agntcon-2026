# Answer-correctness alignment session log

Running log of the judge-alignment sessions for `analytics-answer-correctness`
(orq evaluator `01M1RF70QY6TXQ4YF67CA8EKJG`). One entry per session, newest last.
Questions, answers, and findings are recorded verbatim enough to be replayed; artifacts
live under `runs/alignment-<corpus>-<date>/` (gitignored) and are named per entry.

## 2026-09-05, session 1: corpus v2 (edge-v2), judge 1.0.7

**Setup.** 30 dev rows x 8 repeats, temperature 1, judge `wafer/DeepSeek-V4-Flash-0731-Fast`.
Judge reference-free (no oracle in prompt), sees the full conversation with tool calls and
results.

**Findings.**
- 26 of 30 rows fully consistent; 4 unstable. Three of the four were the same scenario
  (`gross-net-software`) under different personas. Conclusion: the persona x scenario grid
  bought rows, not situations. Led to corpus v3 (one persona, fifty situations).
- 12 of 240 calls timed out at 120 s under concurrency 8.
- The oracle-graded correctness block is empty by construction: the oracle is an expected
  answer, not a pass/fail label, so the skill cannot grade the judge with it.
- Gateway PII masking was enabled on the hosted agent path. The agent saw `<LOCATION_1>`
  for country names and placeholder tokens for years, refused to answer, and several v2
  "behavioural failures" were this rather than reasoning errors. Masking disabled before v3.

## 2026-09-05, session 2: corpus v3, judge 1.0.7

**Setup.** v3 rerun with masking off: 50 rows, 49 goal successes, one failure. Replay through
`answer_correctness@1.0.7`: 49 pass, one `not_applicable`. Stability: 30 dev rows x 8,
temperature 1, concurrency 4, 240 calls, zero failures. Artifacts: `runs/alignment-v3-20260905/`.

**Consistency.** 28 of 30 rows identical across all 8 repeats. Two wobblers:
`ambiguous-best-product` (pass 6 / fail 2) and `software-share` (pass 7 / fail 1).
Mean instability 0.028.

**Stable spot-check (5 random rows, all 8/8 pass).** `save-top-region`,
`category-region-drill`, `avg-discount-smb`, `top-product-2025`, `germany-vs-france`. All
five match the oracle. The random draw did not surface any stable-wrong row.

**Oracle sweep (outside the skill).** Comparing every recorded answer with its oracle found
at least five rows where the agent computed `SUM(net_revenue - refund_amount)`, deducting
refunds twice: the two wobblers plus `top3-countries-then-segment`, `canada-quarters`,
`q4-months-then-mom`. The judge passed the last three 8/8. This is the stable-and-wrong
blind spot; stability measurement cannot find it, only the oracle or a human who knows the
schema can. Caveat: the simulated user sometimes narrows scope mid-conversation, so not every
oracle mismatch is an agent error.

**Grey-zone question 1.** When the agent's derivation is internally consistent with its own
query results but contradicts the data model (re-subtracting refunds from an already-net
column), is that a fail, and is the judge responsible for knowing the column semantics?

**Answer.** Yes. The judge should indicate failures of the agent, and this is one, so the judge
must know the schema.

**Grey-zone question 2 (withdrawn).** Whether the verdict differs when the user asked for
the flawed derivation. Withdrawn after discussion: that is a question about the agent, not the
evaluator. For a correctness judge only the reported figure matters; who introduced the double
deduction belongs to a different rubric.

**Resolved rule.** The judge knows the schema: `net_revenue` is realized revenue, already zero
for cancelled and pending orders and already net of refunds; `gross_revenue` is quantity times
unit price before discount; `refund_amount` is never subtracted from `net_revenue` again.
Derive the correct figure from the request under these semantics and the recorded tool results,
then compare. A figure obtained by re-subtracting refunds fails, whoever asked for it, unless
the response states refunds are already included and reports the undeducted figure. This stays
reference-free: the judge needs the data model, not an oracle.

**Which rubric is the right example.** Considered moving the case to another evaluator.
Query semantics would catch it as a lint rule but takes reference SQL and grades SQL, so it is
not a grey zone there. Evidence faithfulness passes it: every claim is entailed by the tool
output. Multi-turn consistency has its own grey zone but no stability data and is out of scope.
Answer correctness stays the example: the answer is internally consistent and only schema
knowledge exposes it.

**Labels.** `ambiguous-best-product` fail, `software-share` fail (human confirmed). Five
spot-checks pass, held separately.

**Proposed rewrite.** `new_prompt.md` adds a `<data_model_semantics>` section and the
user-premise clause; verdict space and template variables unchanged. Pending approval.

**Applied as version 1.0.8.** The accepted prompt went into
`orq/resources/evaluators/jury/answer-correctness.yaml` and was synced with
`scripts/sync_orq_resources.py --apply --kinds evaluator --keys analytics-answer-correctness`,
which produces a new version of the same evaluator id rather than a separate evaluator. The
skill's own `create_eval.py` was not used, because a second evaluator id would break the pinned
`answer_correctness@<version>` replay path. One manual edit before syncing: the rewrite ended
with "return exactly one of pass, fail, or not_applicable", and an output-format instruction of
that kind previously competed with the hosted grader's forced tool call and lost 2 to 3 rows per
run to `tool call result missing 'value' field`.

**Paired replay, all 50 v3 rows, both versions.**

| Version | pass | fail | not_applicable |
| --- | --- | --- | --- |
| 1.0.7 | 49 | 0 | 1 |
| 1.0.8 | 45 | 5 | 0 |

Five verdicts changed. Four are the double-refund rows the oracle had already flagged:
`ambiguous-best-product`, `software-share`, `top3-countries-then-segment`, `canada-quarters`.
A fifth, `category-then-yoy`, was not in the oracle sweep list and is a genuine catch: the agent
defined "realized net" as `SUM(net_revenue) - SUM(refund_amount)` and reported 4,718,667.35 for
Data 2024 where the oracle says 5,003,926.92.

Two rows deserve follow-up. `q4-months-then-mom` still passes, correctly: its final query uses a
plain `SUM(net_revenue)`, so the earlier exploratory query that subtracted refunds never reached
the answer. And `unknown-region` moved from `not_applicable` to `pass`. The agent correctly
refused to invent a Nordics segment; both verdicts are defensible, but the rubric should say which
one a correct refusal earns, or the metric will drift between them.
