# Per-case jury signals, v4 corpus

`case-signals-v4.json` holds one record per Sphere v4 case, derived from the canonical
jury run (`runs/v4-jury-20260907.jsonl`, 2026-09-07):

- `disagree` — the three judges did not vote unanimously (`raw_agreement < 1.0`). Six cases.
- `wobble` — one judge changed its own vote across its three repetitions. Eight cases.
- `raw_agreement` — the panel's raw agreement for the case.

Twelve of the fifty cases carry at least one signal. The talk's review-queue slide draws
its rings and its queue order from this file; the deck build reads
`slides/case-signals-v4.json`, which is the same content.

These are annotation signals, not ground truth. No human labels exist for these cases yet.

## Trajectories

`trajectories-v4.json` holds one record per observed run from the same canonical observation
set (`runs/v4-observations-retry-20260907.jsonl`): the case id, turn count, total tokens, and
the ordered message segments as `[kind, size_in_characters]`, where kind is one of `user`,
`assistant`, `call` (tool-call arguments) or `result` (tool output).

Order is reconstructed, not stored: the observation record hangs a whole round on one assistant
message that carries both the tool calls and the answer text, with every tool result appended
after it. Tool call ids and result ids match one-to-one and in the same order in all fifty runs,
so each call is paired with its own result and the assistant's recorded content is placed where
it actually occurred — after the results came back. Every run therefore starts on a user turn and
ends on an assistant answer.

The talk's "What changes with agents" slide draws one bar per run from this file, sorted by
total size. Across the fifty runs: 77 user turns, 77 assistant messages, 70 of which carry tool
calls, and 237 tool results; the shortest run is 1,418 characters and the longest 16,542.

## Replay contrast

`replay-trace.json` holds the single frozen trace used by the talk's "Replay the trace" slide:
the `business-analyst--v3-ambiguous-best-product` conversation, its segment sizes, and the two
verdicts that the same recorded run received from two versions of the correctness evaluator —
1.0.7 passes it, 1.0.8 fails it as double-subtracting refunds. Both explanations are verbatim
sources from `runs/evaluatorq-correctness-v1.0.7-vs-v1.0.8-v3-joined-20260906.jsonl`, condensed
to one line each for the slide.

Tool-call arguments are not preserved in that joined record, so the bar shows user turns,
assistant turns and tool results only — no orange call segments, unlike the trajectory slide.

## replay-trace.json (updated 2026-09-07)

Replaced the v3 `ambiguous-best-product` record with the v4 case
`sphere-stakeholder--v4-yoy-net-growth`, which preserves tool-call arguments, so the
frozen bar shows real call segments and not results alone.

One recorded trace, one recorded answer (net revenue 2024 to 2025: -3.16%, -$1.32M),
scored twice with the same three judges and three repetitions each:

- `decision_support_quality` v1 (`runs/v4-jury-20260907.jsonl`): 9/9 pass, raw agreement 1.0.
- `decision_support_quality` v2, rules rewritten from human notes
  (`runs/v4-jury-human-rules-20260907.jsonl`): 5/9 pass, raw agreement 0.67. `gpt-5.6-luna`
  rejects all three repetitions over an unsupported claim that `net_revenue` is already
  net of refunds; `qwen3.8-27b` rejects one.

Both records carry the same `transcript_fingerprint`, so the trace was replayed and never
re-run. Neither verdict nor explanation was authored or edited.
