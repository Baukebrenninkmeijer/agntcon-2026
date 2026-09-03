# Evaluator-native Trace Evaluation Design

## Decision

The evaluation corpus is produced by evaluatorq agent simulation against the
YAML-defined Orq agent. Completed simulation traces are imported into a stable,
trace-backed row contract. Evaluation and alignment then run as evaluatorq
experiments over those imported rows.

There is no project-specific post-hoc evaluator executor. The importer may read
Orq traces, but it does not invoke judges. `evaluatorq(...)` owns job execution,
scorer execution, concurrency, tracing, result reporting, and Experiment upload.
This design supersedes the execution architecture in
`2026-09-02-posthoc-trace-evaluation-design.md`; the older document remains useful
only for its read-only trace mapping and source/evaluation provenance concerns.

## Trace-backed row contract

The importer and simulation corpus must emit `trace-eval-v1` rows accepted by
`TraceBackedEvaluationRow`:

- `schema_version`: exactly `trace-eval-v1`;
- `case_id`: stable corpus case identity;
- `evaluation_split`: `dev` or `test`, assigned before target inference;
- `source.trace_id` and non-empty `source.span_ids`;
- `conversation`: the complete ordered user/assistant/system/tool transcript;
- `assistant_response`: byte-for-byte equal to the final assistant message;
- optional `oracle`: `expected_answer`, `reference_sql`, and semantic
  `query_requirements`;
- raw ordered `tool_events`: name, arguments, result, and error;
- raw `retrievals`;
- optional `state_before` and `state_after` snapshots;
- bounded experiment/corpus provenance in `metadata`.

The contract intentionally retains raw evidence. A scorer must not depend on an
in-process simulation cache or assume an OpenResponses conversion preserved
local tool/state fields. `TraceBackedEvaluationRow.to_datapoint()` stores the
complete row in `inputs.trace_evidence`, preserves the conversation in
`inputs.messages`, and uses the oracle answer as evaluatorq's
`expected_output`.

## Atomic judges and routing

The first evaluator version has four independently alignable judges:

1. `answer_correctness` receives the conversation, final response, and expected
   answer. It does not see query requirements, reference SQL, or tool evidence.
2. `query_semantics` receives the conversation, executed `query_sql` events,
   reference SQL, and semantic requirements. It grades the query rather than
   the prose answer.
3. `evidence_faithfulness` receives the conversation, final response, raw tool
   results/errors, and retrievals. It never receives the oracle answer or
   reference SQL. A response may therefore be faithful to incorrect evidence
   while failing correctness.
4. `multi_turn_consistency` receives the complete multi-turn conversation,
   ordered tool events, and state snapshots.

Applicability is deterministic and runs before an LLM call. Correctness requires
an expected answer. Query semantics requires an executed query plus a semantic
reference. Faithfulness requires a recorded tool result or retrieval. Multi-turn
consistency requires at least two user turns. A routed row produces
`not_applicable` with `pass=None` and an explanation; it is not forced through a
judge.

All judges use evaluatorq categorical labeled mode with the exact verdict space
`pass`, `fail`, `not_applicable`; only `pass` is passing. The three configured
models run with `assignment="all"`, strict-majority aggregation, and a quorum of
two. The prompt preserves evaluatorq's supported template variables
`{{input.all_messages}}`, `{{output.response}}`, and
`{{input.expected_output}}`. Scoped raw evidence is serialized into the input
messages so the native template engine passes it to the judge without adding a
private variable namespace.

## Native experiment and alignment flow

The replay job returns the already-observed `assistant_response`; it never calls
the target agent again. One call to `evaluatorq(...)` receives all imported
`DataPoint` rows, the replay job, and all applicable routed evaluators. This
creates the normal evaluatorq result table and Orq Experiment. Do not loop over
rows or judges and do not call a separate evaluator service.

Human labels use the same rubric names and verdict space. Prompt alignment runs
only on imported dev rows. The frozen test rows are evaluated once after prompt
selection, using the same evaluator builders and evaluatorq experiment path.
Compute confusion matrices, balanced accuracy, false-pass rate, Cohen's kappa,
human-human agreement, and per-model disagreement from evaluatorq experiment
results joined to the immutable human labels by `case_id`. Treat
`not_applicable` as routed coverage, not as a pass or fail, and report its count
per rubric. Alignment remains rubric-specific; no aggregate verdict can hide a
failed atomic judge.

Live corpus generation, judge calls, and platform resource mutation are separate
explicit operations and are not part of the offline implementation layer.
