---
name: orq-jury-to-alignment
description: "Prepare a completed evaluatorq decision-support jury for human annotation. Use when v4 case definitions, recorded observations, and decision-support-jury-v1 JSONL already exist and the user wants disagreement, wobble, ties, or abstentions to prioritize review without any new model calls."
---

# Jury to Human Annotation

This skill is an offline bridge into the annotation view of
`orq-evaluator-alignment`. It does not run the agent or jury and it does not use
the existing single-judge rewrite or retest stages.

## Hard boundaries

- Require all three inputs: canonical v4 cases, one accepted observation per
  case, and one complete `decision-support-jury-v1` record per observation.
- Do not treat case definitions as observations or jury verdicts as human labels.
- Do not run any model, evaluator, target, hosted-resource, or network operation.
- Do not expose or summarize test outcomes during development annotation.
- Stop after `annotations.json` is saved. `grey_zone.py`, `recommend.py`,
  `aggregate.py`, `rewrite_eval.py`, `create_eval.py`, and `retest.py` belong to
  the single-judge workflow and are out of scope for this jury.

## Workflow

1. Resolve the three user-supplied JSONL paths. If any is missing, report which
   prerequisite is absent and stop. Never substitute v1-v3 artifacts.
2. Select a new output directory under `runs/`. The producer refuses an existing
   path; do not delete or overwrite one to make a rerun fit.
3. Run:

   ```bash
   uv run scripts/prepare_jury_annotations.py \
     --cases <simulation-cases-v4.jsonl> \
     --results <simulation-v4-observations.jsonl> \
     --jury <decision-support-jury-v1.jsonl> \
     --output-dir <new-run-directory>
   ```

4. Read `manifest.json`, `queue.json`, and `jury_errors.json`. Report the number
   of high-signal rows, stable controls, and excluded mechanical errors. Do not
   read or aggregate test verdicts; `test_manifest.json` contains identities only.
5. Locate the installed `orq-evaluator-alignment` skill. Prefer a project-local
   install, then the harness's normal global skill directory. From that skill's
   directory, launch only:

   ```bash
   uv run scripts/serve_annotation.py --run_dir <absolute-new-run-directory>
   ```

6. Tell the user the jury panel is collapsed by default to reduce anchoring.
   They can expand it to inspect every model and repetition after reading the
   decision evidence.
7. After the UI closes, verify `annotations.json` exists and report labeled,
   deferred, and remaining counts. Stop. Further annotation is the user's next
   step; jury-native prompt comparison is separate future work.

## Signal interpretation

- Ties, clean abstentions, and genuine inconclusive outcomes are the first review
  tier because the evaluator could not settle on a usable boundary.
- Cross-judge disagreement and within-judge wobble remain separate signals.
- Provider, transport, replacement, and repetition failures are operational
  errors. They appear in `jury_errors.json` and never become annotation priority.
- Stable controls are a deterministic sample of at most five dev rows, using
  seed 42, and are marked explicitly in the UI.
