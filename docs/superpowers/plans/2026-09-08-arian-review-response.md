# Response to Arian's deck review — proposal

**Date:** 2026-09-08 · **Talk:** Thursday 2026-09-10 · **Deck:** 23 slides, 30 minutes fixed
**Source:** Arian Pasquali, PyData talk review, 2026-09-08

This is a proposal, not applied work. Nothing below has been changed in `slides/build_deck.py` yet.

## Current deck, for reference

| # | Slide | Outline section |
|---|---|---|
| 1 | Title | — |
| 2 | Two correct answers. One useful decision. | 1. Evaluation gap |
| 3 | Who is saying this (bio) | 1 |
| 4 | Three questions | 1 |
| 5 | Sphere.com | 1 |
| 6 | A fifty-case review pool *(eyebrow: Question 01)* | 2. Start with humans |
| 7 | Pass or fail *(eyebrow: How do you create an eval?)* | 2 |
| 8 | The grey zone | 2 |
| 9 | Does the answer help the decision? | 2 |
| 10 | The historical method *(eyebrow: Question 02)* | 3. Align an LLM judge |
| 11 | LLM judges determine priority (+ Wobbly on click) | 3 |
| 12 | We are lazy (priority queue) | 3 |
| 13 | Develop on 30. Measure on 20. | 3 |
| 14 | One answer exposed another ambiguity | 3 |
| 15 | The grey-zone loop (v1 → v2 → v3) | 3 |
| 16 | v3 keeps the agreement and stops flipping (Orq experiment grid) | 3 |
| 17 | What changes with agents? *(divider)* | 4. Agent evaluation |
| 18 | The answer is only the endpoint (trajectories) | 4 |
| 19 | Offline, online, continuous (lifecycle axis) | 5. Scaling |
| 20 | Build the eval once. Then it guards every commit. | 5 |
| 21 | What a failed eval teaches the agent and the rubric | 6. Software factory |
| 22 | Automate the preparation. Keep the decision human. | 6 |
| 23 | Trust the slice tested against humans | 7. Close |

Known drift: `outline.md` still lists a **"Replay, do not regenerate"** slide in section 4 that is
not in the deck. Either build it or cut it from the outline — see item 12.

## Proposal, grouped by cost

### A. Free — wording only, no layout work, no time cost

| # | Feedback | Change |
|---|---|---|
| A1 | "Historical method" is ambiguous | Slide 10 heading → **"The pre-LLM method"**. Same everywhere in `outline.md`. |
| A2 | Discovery vs. regression distinction missing | Slide 20 stage leads: `FIRST` → **`DISCOVERY`**, `THEN` → **`REGRESSION`**. Body copy already says the right thing ("a low pass rate at the start is the point" / "everything passes, or the commit stops"); only the vocabulary is missing. |
| A3 | Test-coverage analogy for the software factory | Slide 22 eyebrow → **"With software we write tests. With a software factory we build evals."** Replaces the current "Evals in the software factory". Exactly the sentence Arian predicts the PyData room will respond to. |
| A4 | Jury mechanics unclear | Slide 11: add **"three repetitions per judge"** to the model-wobbling bullet. The number is what makes self-flip mean anything. |
| A5 | Non-wobbly ≠ correct | Slide 12: one line under the queue — **"Stable cases are not assumed correct. They get random-sampled as a second layer."** Arian's point, and it closes an honesty hole in the lazy-queue argument. |
| A6 | Priority queue tiers | Slide 12: make the three tiers explicit — **both signals → top, disagreement only → middle, self-flip only → bottom.** Check whether the current visual already implies this; if it does, label it rather than adding copy. |
| A7 | Double feedback loop | Slide 21 already *is* the double loop (Sphere skill update + evaluator update from one finding). It is not labelled as two loops. Label the two right-hand stages **"agent loop"** and **"evaluator loop"**. No new slide. |

### B. Cheap — rewrite an existing slide, no net slide added

**B1 — The intern analogy becomes slide 10 (the biggest single win).**

Arian's framing and the pre-LLM method are the same story, so they should be the same slide rather
than two. Rewrite slide 10 as:

> A domain expert writes the guidelines. Interns — students, Mechanical Turk annotators — apply
> them. Inter-annotator agreement is how you decide whether to trust the labels.
> **Nothing about that changed. The interns are now models.**

This does three jobs at once: it renames the slide (A1), it gives the audience a familiar mental
model they already trust, and it makes "alignment" concrete before any judge appears. It also sets
up `aligned_with_human` on slide 16 for free.

**B2 — Trim slide 19 (offline / online / continuous).**

Arian: too much text. The axis rebuild already cut the three cards; the three `meta` lines are what
is left. Cut each to four words or fewer:

- Offline — *the curated 50, on demand*
- Online — *sampled production traces*
- Continuous — *every change, then on a schedule*

Keep the honesty footnote ("the criterion moves between modes only while production stays inside
the slice validated by humans") — it is load-bearing for the close.

**B3 — Wobble stays, and earns it with motion.**

Arian's verdict: keep "wobble" if the animation lands; flag that it is industry vocabulary, not
academic. Today the Wobbly definition fades in on click with no motion. Add a small CSS wobble to
the word itself on reveal (a 2-3 degree rotate oscillation, ~600ms, one shot, with a
`prefers-reduced-motion` fallback to the current fade). Speaker note, not slide text: *"industry
term, not academic — the academic word is instability."*

### C. Structural — costs slides, needs displacement

**C1 — Fix the three-questions spine (this is the "storyline not flowing" fix).**

Questions 01 and 02 arrive as small eyebrows on content slides; question 03 gets a full divider.
The spine only works if the audience notices it three times, the same way each time.

- Proposal: **dividers for all three.** Slide 6 and slide 10 each get a divider in front of them,
  matching slide 17. Cost: **+2 slides, ~20 seconds.**
- Cheaper alternative: **drop the slide-17 divider** and put question 03 back to an eyebrow. Cost:
  −1 slide. Weaker — a section break the audience can see is worth the 20 seconds.

Recommend the dividers. Displacement to pay for them is in C3.

**C2 — "Why align at all", before the binary-evals slide.**

Arian's missing-intro point. With B1 in place, most of this is already covered — the intern
analogy explains why agreement matters. What is still missing is the lazy framing *as a question*:
*we need human agreement, but human review does not scale, so what do we review first?* That
question is what slides 11 and 12 answer, and right now nobody asks it out loud.

- Proposal: **no new slide.** Put the question on the slide-10 divider (from C1) as its subtitle:
  **"We need humans to agree. Humans do not scale."** Zero slide cost, and the divider stops being
  decoration.

**C3 — Displacement: merge slides 8 and 9.**

To pay for C1's two dividers inside the fixed 30 minutes: slide 8 (the grey zone) and slide 9
(*does the answer help the decision?*) are the same beat — the criterion exists because the middle
is grey. Merge into one slide: the grey-zone visual with the criterion as its heading.
**Cost: −1 slide, ~40 seconds recovered.** Net after C1: **+1 slide, roughly time-neutral.**

**C4 — The agent transition (open question, needs Bauke's call).**

Arian says the jump to agent evals is abrupt and wants a bridging slide. Slide 17 is that bridge,
and it was added after this deck version — Arian may not have seen it. Its subtitle was
deliberately dropped last week. Options:

1. Leave it as the bare question, bridge in narration ("everything so far assumed one answer; an
   agent produces a path"). **Free.**
2. Restore one subtitle line to make the bridge visible. Reverses a deliberate decision.

Recommend 1 unless the run-through shows the transition still landing hard.

## Sequence for today and tomorrow

1. **A1-A7** — one pass, one commit, ~30 minutes. All wording, all low risk.
2. **B1** — the intern-analogy rewrite. Do this before anything structural; it may make C2 moot in
   full.
3. **B2, B3** — trim and motion.
4. **C3 then C1** — merge first, then add the dividers, so the deck never goes over budget.
5. Full run-through with a timer. Then settle **C4** and the outline's phantom replay slide (item 12
   below) from what the run-through shows.
6. Send to Arian.

## Not accepted as-is

- **"Wobbly" → "unstable".** Arian himself leaves this open and prefers wobble if the motion lands.
  Keeping wobble; B3 makes it earn the name.

## Open items

- `outline.md` section 4 lists a "Replay, do not regenerate" slide that does not exist in the deck.
  Build it or cut it — it is currently a promise to a reader that the deck does not keep.
- Every change above must be reflected in `abstract.md` / `outline.md` in the same commit, per the
  repository's contract rule.
