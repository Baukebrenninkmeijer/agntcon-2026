# Single-Run Evaluation Execution Design

## Contract served

This execution supplies the submitted abstract's short LLM-judge walkthrough and the manual
outline's disagreement-led annotation example. It does not add another evaluator, rubric, agent,
or talk section. The only subjective evaluator remains `decision_support_quality` over the
Sphere.com analytics agent.

## Decisions

- Run one evaluatorq Experiment for the canonical 50 observations and one for the canonical
  50-row jury. Do not batch either stage.
- Route every newly created Experiment explicitly to `pydata2026`.
- Run a one-case observation isolation before the canonical observation Experiment.
- Run a two-development-row, 18-call jury smoke before the 450-call jury Experiment.
- Preserve complete jury records containing mechanical judge failures so the annotation producer
  can put those rows in `jury_errors.json`. Mechanical failures are operational evidence, never
  annotation priority.
- Use the clean `feature/decision-support-evaluation` worktree because the primary `main` checkout
  contains unrelated user edits. Every artifact records the exact committed revision used.
- Port 8765 is the annotation-view port. The pre-existing listener was explicitly terminated at
  the user's request and the port must be checked again before serving.

The user accepts the remaining single-run trade-off: a process-level interruption can require
rerunning a whole Experiment. The runs are expected to complete within minutes, so resumable
batches and a multi-Experiment manifest are deliberately excluded.

## Preflight

Before any model call:

1. require the primary checkout's ignored `.env` to contain `ORQ_API_KEY` without copying or
   printing it;
2. require a clean committed feature worktree;
3. verify the hosted `analytics-chatbot` has a no-op agent-only reconciliation against the reviewed
   Sphere YAML;
4. verify the database manifest is `sphere-orders-v1`, the database is readable, and the v4 corpus
   has its reviewed SHA-256, exactly 50 unique IDs, and the frozen 30-development/20-test split;
5. require all requested output and report paths not to exist; and
6. print the selected row count, model configuration, Experiment path, and fixed jury call budget
   before execution.

No tool or evaluator resource is applied. The local evaluatorq jury calls the three configured
judge models directly through the existing gateway credential.

## Observation execution

`scripts/run_simulation.py` keeps its existing behavior but gains fail-closed execution controls:

- an explicit `--experiment-path` defaulting to `pydata2026`, forwarded as
  `orq_results_path` to evaluatorq;
- preflight refusal when either `--output` or `--report` already exists or aliases the other path;
- exact selection reporting for `--case-id` or `--limit`; and
- no creation of final JSONL/report paths until evaluatorq owns the run.

First run one development case through the full target in isolation. Validate that it produces one
structurally usable replay row with the Sphere decision context and recorded output. The pilot is
diagnostic and does not enter the canonical corpus.

Then run all 50 rows once with a unique name, output path, and report path. Accept the observations
only when `load_simulation_replay` returns exactly 50 samples, no rejected or duplicate rows, the
30/20 split, and complete `(case_id, transcript_fingerprint)` identities. Goal failure remains an
observed agent outcome rather than a structural rejection.

## Jury execution

`scripts/run_decision_support_jury.py` gains repeatable `--case-id` selection. Selection occurs only
after the complete observation corpus passes the existing v4 structural validation. Unknown,
duplicate, or non-development smoke IDs fail before evaluator construction.

The smoke selects two explicit development identities and prints exactly 18 approved calls. It
must return two score envelopes with the exact ordered three-model panel and three repetition
records per vote. Any top-level evaluatorq/scorer error, missing raw jury, identity mismatch, or
incomplete released payload stops the full run.

For a structurally complete `JuryResult`, failed judges, failed repetitions, replacements, or too
few successful judges no longer invalidate the whole artifact. They remain losslessly serialized;
the downstream producer classifies them as mechanical errors and excludes them from annotation
priority. Ties, clean abstentions, and genuine inconclusive outcomes remain valid high-signal jury
evidence.

The canonical run consumes all 50 accepted observations in one evaluatorq Experiment: 50 rows ×
3 judges × 3 repetitions = 450 calls. It writes one new no-clobber JSONL artifact and reports the
Experiment URL returned by evaluatorq. No automatic whole-run retry is authorized.

## Annotation handoff

After the 50-row jury file validates, run the repository-local `orq-jury-to-alignment` skill. The
offline producer requires exact 50-row identity coverage, seals test outcomes, ranks development
ties/abstentions/inconclusive outcomes before disagreement and wobble, selects up to five stable
controls, and writes mechanical failures to `jury_errors.json`.

Launch only the installed jury-aware annotation view on 127.0.0.1:8765 after verifying the port is
free. Stop after the user labels or defers the presented rows. Prompt rewriting, evaluator creation,
test evaluation, CI gating, and agent self-learning remain later stages.

## Acceptance evidence

- Focused tests fail before and pass after the simulation path/no-clobber and jury selector/error
  changes.
- The full non-live suite, Ruff, diff check, and package build pass before live execution.
- Agent-only reconciliation is a no-op immediately before the pilot.
- Pilot: one accepted replay row.
- Canonical observations: 50 accepted, zero rejected/duplicates, 30/20 split.
- Jury smoke: two complete 3-by-3 records and 18 attempted calls.
- Canonical jury: 50 identity-bound records and 450 attempted calls; mechanical rows, if any, are
  counted separately rather than interpreted as disagreement.
- Annotation bundle: ready manifest, dev-only queue, identities-only test manifest, and explicit
  error count.
