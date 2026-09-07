# Ambiguity Increased Wobbliness Slide Design

## Purpose

Replace the existing short-walkthrough placeholder with one evidence-backed slide that demonstrates
an important evaluator-alignment result: answering a human grey-zone question can clarify the
intended principle while exposing a second ambiguity in how judges apply it.

This serves the submitted abstract's seven-minute **Align an LLM-as-a-judge** section and the
outline's recorded-case walkthrough. It does not add time or introduce a new narrative branch.

## Approved framing

The slide follows one sequence:

1. Human question: **Should visible analytical claims always be valid and correct?**
2. Human answer: **Yes.**
3. Evaluator rule: visible analytical claims must be valid against the supplied evidence.
4. Newly exposed ambiguity: does **unsupported** mean factually wrong, or merely not proven by the
   visible evidence?
5. Measured development result: panel disagreement increased from 4 to 8 cases, within-judge
   wobble increased from 6 to 8 cases, and aggregate verdicts did not flip.

The slide's conclusion is:

> We aligned the principle, but not what counts as unsupported.

## Slide design

- Title: **One answer exposed another ambiguity**
- Replace the current slide titled **One case through the full loop**. The deck remains at 20
  slides and the talk remains within its fixed 30-minute budget.
- Use a single left-to-right composition rather than cards or a dashboard:
  - the human question and answer on the left;
  - the unresolved interpretation in the center;
  - the three measured before-and-after results on the right.
- Give the human answer and the increased counts the existing orange accent. Use teal for the
  evaluator rule and neutral text for the unresolved interpretation.
- Keep the slide readable without speaker narration, but leave case-level explanation to the
  talk. Do not expose held-out test verdicts.

## Evidence and wording constraints

- Source the counts only from the tracked development comparison between `jury-baseline` and
  `jury-human-rules-v1`.
- Label the counts as development signals, not human alignment metrics.
- Do not imply that increased wobbliness is automatically bad. It is evidence that the new rule
  activated a contested threshold.
- Do not claim a causal mechanism beyond the inspected judge explanations. Present the
  fact-versus-proof distinction as the observed interpretation gap.
- Preserve the existing claim that aggregate verdicts stayed unchanged.

## Validation

- Regenerate the HTML deck and confirm it contains exactly 20 slides.
- Run Ruff and Python compilation for `slides/build_deck.py`.
- Run `git diff --check`.
- Render and inspect the new slide and both adjacent slides at 1280×720 for overlap, clipping,
  hierarchy, and legibility.
- Confirm windowed mouse clicks still do not advance the deck.

