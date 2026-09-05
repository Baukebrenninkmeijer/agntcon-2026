# Simulation Artifact Pipeline Design

## Decision

Evaluatorq's raw `SimulationResult` JSONL is the immutable source artifact for
the simulation corpus. The repository does not manually reconstruct transcripts
from Orq traces and does not maintain a second hand-authored dataset ledger.

A small offline adapter validates each raw result, joins its frozen case
definition by `metadata.datapoint_id`, and emits the existing evaluator-native
row/`DataPoint` contract. A complete simulation result is sufficient by itself;
Orq trace IDs, span IDs, and reasoning summaries are optional enrichment.

## Minimal flow

```text
frozen cases + evaluatorq simulate()
                |
                v
       immutable SimulationResult JSONL
                |
          validate + normalize
                |
        evaluator-native DataPoints
                |
             evaluatorq
```

The adapter performs only the transformations required downstream:

- join `split`, oracle, coverage, and state expectations from the frozen case;
- move the recorded final assistant answer after its tool results so evaluatorq
  no-inference replay sees an assistant message last;
- preserve tool name, parsed arguments, result, and error as `ToolEvent`s;
- preserve bounded simulation provenance in row metadata;
- use the oracle result as `expected_output` when one exists.

The adapter must not call an agent, retrieve a trace, upload a dataset, rewrite
the raw artifact, or invent missing evidence.

## Light acceptance checks

A result is accepted only when:

- it has a stable case ID that resolves to exactly one frozen case;
- it ended normally, achieved its goal, and has a non-empty final assistant
  response;
- every tool call has exactly one matching result and arguments are a JSON
  object;
- oracle-backed analytics cases call `query_sql`;
- explicit-save cases call `save_insight`, while no-save cases do not;
- normalized conversation ordering ends with the recorded assistant response;
- an oracle is present for case definitions that require one.

Exact duplicates use `(case_id, transcript_fingerprint)` and are dropped. Two
different attempts for the same case are retained. Rejected results retain
machine-readable reasons in a validation report; the raw source remains
unchanged.

## Evidence sufficiency

The raw evaluatorq artifact already contains the downstream essentials: case
identity, persona/scenario metadata, goal and criterion outcomes, ordered
messages, function calls, function outputs, final assistant content, token
usage (including reasoning-token counts when reported), and run/thread
provenance.

Reasoning summaries are not present in the raw artifact and are not required by
the four current evaluators. When an Orq Responses trace is available, a later
enrichment step may add reasoning and trace linkage without changing acceptance
or overwriting the source artifact.

## Generated review views

Human-readable pilot or review packets are generated projections of accepted
rows. They are useful for inspection but are not sources of truth and should not
duplicate or replace the raw evaluatorq JSONL.
