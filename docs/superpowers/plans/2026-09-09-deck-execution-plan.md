# Deck execution plan — Arian review, decisions applied

**Date:** 2026-09-09 · **Talk:** Thursday 2026-09-10 · **Deck:** 25 slides
**Source of decisions:** Bauke's inline answers in `2026-09-08-arian-review-response.md`, plus the
2026-09-09 review conversation.

Slide count is not the budget. Bauke's ruling: a fast slide costs no meaningful time, so the
30-minute contract is managed by what is *said*, not by how many screens it is said on. Items below
that add a slide say so, and none of them add material that has to be narrated at length.

## Deck as it stands (re-validated 2026-09-09)

| # | Slide | Touched by |
|---|---|---|
| 1 | Title | — |
| 2 | Two correct answers. One useful decision. | — |
| 3 | Bauke Brenninkmeijer (bio, no portrait) | — |
| 4 | Three questions | **W4** inserts after this |
| 5 | The case — Sphere.com | — |
| 6 | A fifty-case review pool *(Question 01)* | — |
| 7 | Pass or fail | — |
| 8 | The grey zone | — |
| 9 | Does the answer help the decision? | — |
| 10 | Every failure has two suspects *(Question 02)* | kept |
| 11 | Two lifecycles, not one | kept |
| 12 | The historical method | **W3** full rebuild |
| 13 | LLM judges determine priority (+ definition on click) | **W1**, **W5** full rebuild |
| 14 | We are lazy (priority queue, 12 of 50) | **W1**, **W6**, **W7** |
| 15 | Develop on 30. Measure on 20. | — |
| 16 | One answer exposed another ambiguity | **W1** |
| 17 | The grey-zone loop | **W1** |
| 18 | Stability came from constant passes (Orq grid) | — |
| 19 | What changes with agents? *(Question 03)* | kept as-is (C4) |
| 20 | The answer is only the endpoint | — |
| 21 | Offline, online, continuous | not touched (B2 rejected) |
| 22 | Build the eval once. Then it guards every commit. | not touched (A2 rejected) |
| 23 | What a failed eval teaches the agent and the rubric | **W2** |
| 24 | Automate the preparation. Keep the decision human. | **W2** |
| 25 | Trust the slice tested against humans | — |

## Decisions locked

| Item | Decision |
|---|---|
| A1 / B1 / D4 | Fold the intern analogy into slide 12. There is no separate "with and without LLMs" slide to merge with — slide 12 *becomes* it, as two visual flows. |
| A2 | Rejected. Discovery/regression is already covered by slide 22's copy. |
| A3 | Accepted. Test-coverage line becomes slide 24's eyebrow. |
| A4 | Accepted, expanded: 3×3 grid of judges × repetitions, then rotate to a 50-deep stack. See W5. |
| A5 / D2 / Q2 | Accepted, changed: the review queue is **4 prioritised + 4 randomly sampled**, drawn as two bars. Framed as the recommendation, not as a measurement. |
| A6 / D3 | Already covered by the ranked queue. No change. |
| A7 | Label slide 23's two branches as the agent loop and the evaluator loop. |
| B2 | Rejected. The lifecycle axis is already trimmed; leave it. |
| B3 / D6 | "Wobbly" becomes **unstable** everywhere. Instability is shown by cells flipping red/green, not by shaking. Keep the rings. |
| C1 | Deferred. Leave the eyebrow/divider asymmetry alone for now. |
| C2 / Q4 | Restore the lost **ordering constraint** slide after slide 4. |
| C3 | Rejected. Slide 9 is fast and costs nothing; do not merge 8 and 9. |
| C4 | Keep slide 19 as the bare question; bridge in narration. |
| D1 / Q3 | Keep both slide 10 and slide 11. The decision comes first, then the cycles. |
| D5 | Noted, left alone: slides 21 and 22 both answer "when do evals run". |

## Work items, in execution order

### W1 — Rename wobbly to unstable *(free, do first)*

Every later item writes new copy, so the vocabulary has to settle before they do. Six places:

- slide 13: the `Model wobbling` bullet and the whole `Wobbly` definition block
- slide 14: the `one model wobbles` legend and the "disagreement between models, wobble within one" bullet
- slide 16: the `self-wobbles` metric label
- slide 17: the `Surface wobble` stage, and the `more wobble` / `less wobble` version chips
- `outline.md`: the "Slide: Wobbly" heading, the definition, and every prose use
- CSS class names and the Python `wobble` field stay as they are — internal, not audience-facing

The definition is rewritten, not word-swapped:

> **unstable** — of an LLM judge: returning different verdicts on repeated evaluations of the same
> case.

### W2 — Free wording *(A3, A7)*

- Slide 24 eyebrow → "With software we write tests. With a software factory we build evals."
- Slide 23: label the two right-hand stages `agent loop` and `evaluator loop`.

### W3 — Rebuild slide 12 as two flows *(A1 + B1 + C2 + D4)*

Replaces "The historical method". Two horizontal flows stacked, same shape both times so the
substitution is the only thing that changes:

- **Before:** domain expert writes guidelines → interns apply them → inter-annotator agreement
  decides whether to trust the labels
- **Now:** domain expert writes guidelines → LLM judges apply them → agreement with the expert
  decides whether to trust the judge

Heading names the substitution; the interns row is teal, the judges row orange, and the last column
is identical in both rows because that is the point. The current spine (`random sample`, `human
label + written critique`, `identify gaps with judge`) and the "every change" cost panel are cut —
the analogy carries the same argument in a shape people already trust.

### W4 — Restore the two lost intro slides *(C2, and Bauke's 2026-09-09 call)*

Reinstate the slide dropped in `c280a25`, immediately after slide 4:

> eyebrow **The ordering constraint** · heading **You cannot use evals to improve an agent before
> the eval is aligned.**

Verbatim from history, including the `.hl` on "aligned". This is the fast why-align beat: good agent
needs a good judge, and a good judge needs human alignment.

Also restore, from the same commit, the metric-lineage slide that went with it:

> eyebrow **We have been here before** · heading **Hard metrics gave way to judgement. Judgement had
> to be measured.**

with its timeline SVG (countable target → human relevance → …). It earns its place by making the
ordering constraint feel inevitable rather than asserted: this field has already done this once.
**+2 slides.**

### W5 — Rebuild slide 13 as the judge grid *(A4)*

The two bullets and the definition block are replaced by a stepped 3D grid. Three steps:

1. **A 3×3 grid, one real case.** Rows are the three judges by name (`gpt-5.6-luna`,
   `qwen3.8-27b`, `gemini-3.5-flash-lite`), columns are the three repetitions, each cell a real
   pass/fail. The front case is `sphere-stakeholder--v4-best-month-net`: Luna votes fail, pass,
   fail; the other two never move. Heading states the two signals read off it.
2. **Rotate to the dataset.** The container rotates about 27 degrees, scaling to 0.64, and 49
   further case-layers stand behind the front one at 58px spacing, so one case becomes fifty.
   Reduced motion: crossfade straight to the rotated end state.

**Each cell is one decision, so it holds one colour.** No flipping on this slide — the red/green
flip belongs to the fifty datapoints on slide 14 (W7). Decided against the mocked alternatives: a
static isometric stack (safe but hands over the picture instead of turning it) and fifty small
multiples (readable, but a chart rather than a move). Companion mock: `variantA.html`.

Data: real, from `runs/decision-support-jury-prompt-v3-20260908.jsonl`, which carries per-judge,
per-repetition verdicts for all 50 cases — 450 cells, nothing invented. Extract to a
`slides/judge-grid-v3.json` alongside the existing `case-signals-v4.json`.

Risk: the rotation is a CSS 3D transform. Both end states can be verified headlessly with
transitions disabled; the motion itself cannot, and must be checked on the presenting machine.

### W6 — Queue becomes 4 + 4 *(A5, D2, Q2)*

Slide 14's lane currently promotes all twelve flagged cases and mentions the control sample only in
a closing sentence. Replace with two bars:

- **Review first — 4:** the top four by priority (both signals, then disagreement, then instability)
- **Sampled — 4:** four drawn at random from the cases nothing flagged

The fifty dots still show all twelve flags, so the slide does not claim only four were flagged. The
second bar is the honesty point Arian raised: stable cases are not assumed correct, they are
sampled. Copy says this is the recommended split, not a measurement of what this project ran.

### W7 — Instability motion on the dots *(B3)*

The `wobble-hard` shake on slide 14 is replaced by the red/green flip used in W5, so both slides
show instability the same way. Keep the rings.

### W8 — Contract and plan

`outline.md` updated for W1–W7 in the same commits. `abstract.md` checked: section 3's minute
budget is unchanged, since W3 and W5 replace material rather than adding it, and W4 is one
sentence. Plan changelog entry per commit. `outline-manual.md` untouched.

## Left open

- **C1**, the question 01/02 eyebrow versus question 03 divider asymmetry. Deferred by decision.
- **The phantom slide.** `outline.md` section 4 still promises "Replay, do not regenerate", which
  the deck does not contain. Build it or cut it after the run-through.
- **Whether the 3D rotation earns its place.** Build it, look at it, and cut back to a static tilted
  grid if it does not land.

## Sequence

W1 → W2 → W3 → W4 → W6 → W7 → W5 → W8, then a timed run-through, then send to Arian. W5 is last
because it is the only item that can fail on the night; everything before it is finished work if
the grid has to be abandoned.

---

## Second review pass — 2026-09-09, after the four-agent audit

Four agents audited the current 27-slide deck against `review-arian.md` and
`review-arian-transcript.md`. Bauke's decisions on their findings, recorded verbatim in intent:

| # | Finding | Decision |
|---|---|---|
| 1 | The three-tier priority queue (both signals, disagreement only, instability only) is computed but not visible on slide 16 | **Not building it.** Covered verbally on stage |
| 2 | `discovery` and `regression` are never named; slide 24 has the shapes under generic `FIRST` / `THEN` leads | **Do it** (W9) |
| 3 | The trajectory slide carries no framing: slide 21 is a bare title card and slide 22 has no argument text | **Do it, expanded** (W10): x-axis marker `Nr. of tokens →`, new subtitle *Agents require evaluating behaviour, rather than final answers*, the present chart-description subtitle demoted to a caption under the chart, and example agentic evals down the right side (tool-call efficiency, error recovery, and one more) |
| 4 | Nothing bridges slide 22 into slide 23; this, not the question 02 to 03 pivot, is the abrupt transition Arian meant | **Swap instead** (W11): operating modes and `Build the eval once` change places, so the lifecycle argument lands before the modes it is run in. No bridge slide |
| 5 | The phrase `human alignment` appears nowhere in the deck | **Do it** (W12) |
| 6 | No persistent then/now signposting across the method slides; Arian said he got lost | **Omit** |
| 7 | No intro explaining why alignment is needed and how to do it well before the binary-evals slide | **Do it** (W13), proposal first |
| 8 | `outline.md` section 4 promises a `Replay, do not regenerate` slide the deck does not have | **Omit.** Remove the promise from the outline instead |

Not a gap, recorded to stop it being re-raised: the apparent contradiction that you cannot improve
what you have no eval for is not unaddressed. It is the talk's subject. The whole middle section is
the answer to it: how to align a judge efficiently enough that the eval exists before the agent work
begins.

Confirmed done by the audit and not to be redone: the `unstable` rename, stable-is-not-correct via
the control lane, the double-loop slide, the test-coverage line, the three-repetitions mechanics, and
workstreams W1 and W3 through W7. Dropped as non-gaps: literal red/green flicker, which the rotating
gradient carries, and the text density of the operating-modes slide, which is already a compact SVG.

### W9 — Name the two phases

Slide 24's two leads become `DISCOVERY` and `REGRESSION`. Add Arian's rule in one line: during
discovery a high failure rate is the eval working, and an eval that never fails is too easy; once a
behaviour is a regression, a failure means something broke. No new slide.

### W10 — Give the trajectory slide its argument

Slide 22 gains, in this order: the subtitle `Agents require evaluating behaviour, rather than final
answers`; the existing bar-chart description moved below the chart as a caption; a mono
`Nr. of tokens →` marker on the x-axis; and a short right-hand column of example agentic evals —
tool-call efficiency, error recovery, and one more drawn from the observation run rather than
invented. Slide 21 stays a bare divider.

### W11 — Swap the lifecycle and operating-modes slides

`Build the eval once. Then it guards every commit.` moves before `Offline, online, continuous`. The
lifecycle argument then hands off to the modes that lifecycle runs in, which removes the jump Arian
flagged without spending a slide on a bridge. Update the outline section order to match.

### W12 — Say `human alignment` out loud

The term goes on slide 17, whose whole subject it is, either as the eyebrow or in the sub-line.

### W13 — The why-and-how-to-align intro

Needs a proposal before it is built. It sits after the ordering constraint (slide 6) and before the
case, and it must not restate slide 12 (two suspects), slide 14 (the interns analogy) or slide 17
(develop on 30, measure on 20). Its job is to say what aligning a judge actually consists of, so the
rest of the section reads as the efficient way to do a thing the audience already understands the
shape of.
