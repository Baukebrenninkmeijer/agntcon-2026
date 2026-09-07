# Three-judge claudish run, 6 September 2026

The same rubric — [`podcast-claudish.yaml`](../../../orq/resources/evaluators/jury/podcast-claudish.yaml),
unchanged — scored by three models on the six real episodes in
[`../podcast-corpus-2026-09-06/`](../podcast-corpus-2026-09-06/) and
[`../podcast-run-2026-09-06/`](../podcast-run-2026-09-06/). Temperature 0, one pass each, 18 calls.

This is a **pre-alignment** measurement. There are no human labels yet, so nothing here says which
judge is right.

## Verdicts

| Episode | Gemini 3.6 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash | |
|---|---|---|---|---|
| `972faadcbe03` | fail | fail | fail | unanimous |
| `78e67d066fa6` | fail | fail | fail | unanimous |
| `bfbab87e0c6c` | fail | pass | fail | split |
| `dd292f0743b7` | fail | pass | fail | split |
| `4aeb4ec5c6ad` | fail | pass | fail | split |
| `f9245734c6fa` | fail | pass | fail | split |

Four of six episodes get a split verdict. Every deterministic-filter check passed on all six.

## Pairwise agreement

| | agreement |
|---|---|
| Gemini vs Qwen | 6/6 |
| Gemini vs DeepSeek | 2/6 |
| DeepSeek vs Qwen | 2/6 |

## What the disagreement is actually about

It is not about the evidence. On the production episode `f9245734c6fa`, Gemini and DeepSeek quote
**the same passages** — the ask-and-answer move in *"Why else would NVIDIA buy Hugging Face?"*, the
verbatim phrase echo across the interruption — and DeepSeek's explanation opens by saying a careful
listener *would* catch them. It returns `pass` anyway.

The rubric never says how many tells make a failure, or whether recognising a tell on the page is
the same as a listener noticing it on a walk. Two judges applied the same list to the same lines and
placed the threshold in different places. That is the grey zone, located by disagreement rather than
guessed at, and it is the thing a human has to decide before any of these numbers mean anything.

## Two operational notes

- **No self-preference here.** Gemini wrote all six episodes and failed all six. The model that
  generated the scripts is the harshest judge of them, which is the opposite of the effect the run
  was designed to check for.
- **Qwen leaks its reasoning into the answer**, opening with *"We need answer user's request..."*
  before reaching a verdict. The label had to be recovered by parsing. A judge whose output format
  is unreliable is an alignment problem before it is a quality one.
