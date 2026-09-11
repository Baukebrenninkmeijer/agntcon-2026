# Per-case jury signals, v4 corpus

[`slides/case-signals-v4.json`](../../../slides/case-signals-v4.json) holds one record per
Sphere v4 case, derived from the baseline jury run
([`jury-baseline/jury-results.jsonl`](../../../orq/resources/datasets/decision-support-v4/jury-baseline/jury-results.jsonl),
2026-09-07):

- `disagree` — the three judges did not vote unanimously (`raw_agreement < 1.0`). Six cases.
- `wobble` — one judge changed its own vote across its three repetitions. Eight cases.
- `raw_agreement` — the panel's raw agreement for the case.

Twelve of the fifty cases carry at least one signal. The talk's review-queue slide draws
its rings and its queue order from this file.

These are annotation signals, not ground truth.

## Trajectories

[`slides/trajectories-v4.json`](../../../slides/trajectories-v4.json) holds one record per
observed run from the accepted observation set
([`observations.jsonl`](../../../orq/resources/datasets/decision-support-v4/observations.jsonl)): the case id, turn count, total tokens, and
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
