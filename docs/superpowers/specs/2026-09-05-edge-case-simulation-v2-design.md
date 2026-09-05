# Edge-Case Simulation v2 Design

## Decision

The v2 simulation corpus is a separate, harder 50-case dataset. Every case is
marked `is_edge_case=true`, stages information across two or three user turns,
and runs once with evaluatorq at `max_turns=3`. The run is an observation
source, not a pass-rate gate: failed agent behavior remains valuable evaluation
data and never triggers quality-based replacement or reruns.

The tracked definitions live in
`orq/resources/datasets/simulation-cases-v2.jsonl`. The immutable raw result and
native evaluatorq report remain in ignored `runs/` storage. The v1 and v2
definitions, run names, reports, and outputs must never overwrite one another.

## Runtime boundary

The hosted `analytics-chatbot` remains the target, with local DuckDB-backed
tools executed through the existing conversation-scoped bridge. evaluatorq
owns simulated-user orchestration, ten-way datapoint concurrency, a Responses
API simulator, and the built-in `goal_achieved` and `criteria_met` simulation
judges. This is distinct from the later `inference=False` replay using the one
focused Orq answer-correctness evaluator.

The sole approved live run completed on 2026-09-05:

- 50 raw rows and 50 unique expected case IDs;
- eight one-turn, 22 two-turn, and 20 three-turn conversations, so 42/50 (84%)
  reached two or more target turns;
- 230 declared tool calls and 230 paired tool results, with no orphaned calls
  or results;
- 40 goal-achieved and ten goal-not-achieved outcomes;
- 44 judge terminations and six `max_turns` terminations;
- no exact transcript duplicates.

The raw JSONL digest is
`33a83b32ff32b706359764ea4565be0680a0ac031eb1a8b28e83c6370820f880`.
Before correctness replay, five inherited v1 oracle families were corrected to
cover the complete staged request. No conversation, case ID, or split changed;
all 50 IDs still join. The corrected definition digest is
`1b08037df28e1a0afd557edac4c2fee38a520b142dc4653bb4ca62580e7a6b1a`
and independent regeneration is byte-for-byte identical.
Runtime trace IDs, experiment IDs, credentials, and other opaque remote IDs are
not committed.

## Acceptance and filtering

Artifact validity is separate from agent success. The adapter rejects only
structurally unusable rows, such as malformed messages, unpaired tool calls, or
a missing final assistant response. It retains `goal_achieved=false`,
`criteria_verified=false`, and `max_turns` observations and carries those
outcomes as metadata.

Expected-tool and state-policy misses are lightweight QC warnings rather than
structural rejection reasons. Preserve and replay all 50 rows. This run has
exactly five warnings, all for an expected `save_insight` call that was not
observed; they remain datapoints because the missing action is precisely the
failed behavior the evaluator should see. Warnings never authorize another
simulation run.

## Reproduction

Generate definitions without making live calls:

```bash
uv run python scripts/generate_simulation_cases.py --variant edge-v2
```

The completed live command is retained for provenance, not as an instruction
to rerun the frozen corpus:

```bash
uv run python scripts/run_simulation.py \
  --cases orq/resources/datasets/simulation-cases-v2.jsonl \
  --limit 50 \
  --max-turns 3 \
  --evaluation-name pydata2026-analytics-chatbot-simulation-edge-v2 \
  --report runs/evaluatorq-simulation-v2-20260905.report.json \
  --output runs/evaluatorq-simulation-v2-20260905.jsonl
```

## Next boundary

All 50 stored rows now normalize to fingerprinted `TraceBackedEvaluationRow`
instances. evaluatorq replayed them with `inference=False` through pinned
`analytics-answer-correctness@1.0.0` and uploaded 50 Experiment rows. Alignment
next uses development-only human feedback; machine scores do not enter the
annotations API. No custom post-hoc execution service or ledger is needed.
