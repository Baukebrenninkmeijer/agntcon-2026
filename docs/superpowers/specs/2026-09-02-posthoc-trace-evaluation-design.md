# Post-hoc Trace Evaluation Design

## Purpose

Add a project-local workflow that retrieves an existing orq trace, maps its
recorded generation into the current evaluator invocation contract, invokes an
existing orq evaluator after the source run has completed, and persists a local
link between the source trace and the separate evaluation trace.

The workflow must not require the source trace to contain an evaluator span and
must not represent a machine verdict as a human annotation. The implementation
is intentionally local to this repository for now, but its core mapping and
service boundaries should be movable into the shared evaluator-alignment skill
later.

## API Shapes and Mapping

The orq SDK exposes hydrated spans through `orq.traces.get_span`. A span has a
summary containing its trace and span identities and open-ended attributes. The
generation payload is recorded under `attributes.gen_ai`, commonly as:

- `input`: conversation messages or structured input fields;
- `output`: the generated assistant response;
- optional system instructions, retrievals, tool calls, and expected output.

`orq.evals.invoke_async` accepts an evaluator ID and a structured evaluation
context:

- `messages`: the conversation being graded;
- `input.user_query`;
- `input.system_instructions`;
- `input.retrievals`;
- `input.expected_output`;
- `output.response`;
- `output.tools_called`;
- `variables`: additional evaluator template variables.

When messages are supplied, the evaluator API treats them as authoritative. The
mapper will therefore construct a canonical conversation from the source input
and append the current assistant output exactly once. It will also populate the
structured input and output fields so evaluators using either modern
`input.*`/`output.*` variables or legacy `log.*` variables receive the expected
content.

The mapper will support the observed chat-style and structured trace shapes. It
will extract the latest textual user request, the generated assistant response,
system instructions, retrieval chunks, expected output, and tool calls when
present. Empty optional fields are omitted. A missing user request or generated
response is an explicit mapping error rather than a partially populated
evaluation.

## Components

### Mapping module

`src/analytics_chatbot/evaluation.py` will define typed project models for the
normalized invocation and linked result. Its public
`map_trace_to_evaluation_context` function is a pure transformation from a
hydrated SDK span (or equivalent mapping) to the evaluator context. It will have
no network or filesystem dependencies.

### Post-hoc evaluation service

`PosthocTraceEvaluator` will accept an injected Orq client and evaluation
ledger. Its public `evaluate(trace_id, evaluator_id, span_id=None)` operation
will:

1. retrieve the trace summary;
2. resolve the explicit span or the trace's leading/root generation span;
3. retrieve the hydrated span;
4. map it into the evaluator context;
5. invoke the stored evaluator with `orq.evals.invoke_async`;
6. validate the returned result; and
7. persist and return a linked evaluation record.

An explicit span ID always wins. Automatic resolution fails clearly when the
trace exposes no suitable span or several equally suitable spans.

### Evaluation ledger

An append-only JSONL ledger at `runs/evaluations.jsonl` will preserve one record
per invocation. Each record contains:

- a local invocation ID and UTC timestamp;
- source trace ID and source span ID;
- evaluator ID;
- the exact normalized invocation context;
- evaluation trace ID and evaluation span ID returned by orq;
- evaluator result fields including type, value, passed, explanation, status,
  categories, and confidence.

Repeated invocations are intentionally retained because evaluator alignment
uses repeated judgments to measure stability. The ledger does not deduplicate or
overwrite earlier results.

### CLI

The existing Typer application will add:

```text
analytics-chatbot evaluate-trace TRACE_ID --evaluator EVALUATOR_ID
                                   [--span-id SPAN_ID]
```

It will load the existing project settings, create the SDK client, invoke the
service, and print the linked record as JSON. Credentials remain environment
driven and are never written to the ledger.

## Errors and Safety

The command will fail before evaluator invocation for an unknown trace, unknown
span, ambiguous automatic span selection, or unmappable content. It will fail
after invocation if the response lacks a result or the evaluation trace/span
identities required for linking. API exceptions remain visible with enough
context to identify the source trace and evaluator, but without logging the API
key.

The source trace is read-only. This workflow does not create annotations or
modify source trace data. Evaluator invocations can incur model cost, which is
why unit tests use an injected fake client and the live test remains opt-in.

## Testing Seams

Tests exercise two approved public seams:

1. `map_trace_to_evaluation_context` maps known chat-style and structured span
   fixtures, appends the final response once, preserves optional evaluator
   inputs, and rejects missing required content.
2. `PosthocTraceEvaluator.evaluate` uses an injected fake Orq client to verify
   trace/span resolution, the exact evaluator invocation, returned ID linkage,
   and JSONL persistence through the public service result.

CLI tests cover argument wiring and JSON output without duplicating service
behavior. One opt-in live smoke test may retrieve and evaluate an explicitly
configured trace/evaluator pair; it is skipped unless all required environment
variables are present.

## Documentation and Dependencies

Add `orq-ai-sdk` to the project dependencies. Update `README.md` with the command
and ledger contract. Add concise project guidance to `CLAUDE.md` and `AGENTS.md`
so future coding agents know that post-hoc trace evaluation exists, where linked
results are stored, and that human annotations remain a separate source of
ground truth.

## Out of Scope

- Writing evaluator results back as annotations.
- Changing the shared evaluator-alignment skill in this iteration.
- Running evaluatorq or creating an orq Experiment from the linked ledger.
- Creating, updating, or deleting evaluators.
- Automatically treating machine evaluator output as a human correctness label.
