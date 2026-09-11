# Jury with human boundary rules, version 1

Diagnostic rerun after the evaluator prompt incorporated the first three human boundary decisions: evidence validity, conversational completion when a benchmark is missing, and conversation-level context retention.

- Prompt snapshot: `evaluator-prompt.txt`
- Results: `jury-results.jsonl`
- Experiment: <https://my.orq.ai/<workspace>/experiments/<orq-id>?runId=<run-id>>
- Structure: 50 rows, three judges, three repetitions, zero mechanical errors.
- Development signal: 30 aggregate passes, eight panel-disagreement rows, eight within-judge-wobble rows, 19 review items including five stable controls.
- Baseline comparison: zero development aggregate-verdict flips; disagreement increased from four to eight rows and wobble from six to eight.

This is a diagnostic after version, not a validated evaluator result: no human labels existed when it ran, and test verdicts remain sealed from analysis.
