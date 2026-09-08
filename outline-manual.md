# Manual outline

The structure the deck is built to. Every slide belongs to one block, and every
block after the opening answers one of the three questions named on slide 4.
Total 30 minutes including 5 for Q&A; the budget is fixed, so new material has
to displace old material.

Slide numbers refer to `slides/build_deck.py` and the generated
`slides/pydata-2026.html` (`#s4` deep-links to slide 4).

## Opening — 3 min · slides 1-4

- **1 Title.** Evaluating agents at scale.
- **2 The evaluation gap.** Two correct answers to the same question. Same
  number, only one of them supports the decision. This is the whole talk in one
  slide.
- **3 Who is saying this.** Three lines of bio. Orq is introduced out loud, not
  on the slide.
- **4 Three questions.** The spine. Each question opens a block below, and the
  block's first slide carries it in the eyebrow.

## Question 01 — how do you get a first signal with no labels? — 5 min · slides 5-9

- **5 The case.** Sphere.com, a B2B wholesaler; the board wants the quality of
  growth. Four things the agent has to get right.
- **6 A fifty-case review pool.** Start with humans, not infrastructure.
- **7 Pass or fail.** Binary verdict plus a written critique. Why this beats a
  scored rubric.
- **8 The grey zone.** The cases where reviewers disagree are the product of
  this step, not a defect in it.
- **9 One criterion for this talk.** Does the answer help the decision?

## Question 02 — when can you trust a judge instead of a human? — 7 min · slides 10-14

- **10 The historical method.** Random sampling and manual review, repeated on
  every change. Clean, and expensive.
- **11 We are lazy.** Three judges, one rubric.
- **12 Develop on 30. Measure on 20.** Treat the judge like a model you
  validate: dev/test split, agreement, kappa.
- **13 One answer exposed another ambiguity.** The alignment work surfaces
  questions about the rubric, not just about the agent.
- **14 The grey-zone loop.** How a disagreement becomes a rule.

## Question 03 — what do you evaluate in an agent that is not the final answer? — 5 min · slides 15-16

- **15 The answer is only the endpoint.** Trajectory and state, not just the
  final response.
- **16 Offline, online, continuous.** The three operating modes and what each
  one can be trusted to decide.

## Then: what it costs to run this forever — 3.5 min · slides 17-19

- **17 Build the eval once, then it guards every commit.** Capability evals
  climb toward a target; regression evals hold at it, and a dip is caught.
- **18 What a failed eval teaches the agent and the rubric.** Error analysis
  produces two updates, not one.
- **19 Automate the preparation, keep the decision human.** Automated prompt
  optimization is named here and shown once, not walked through.

## Close and Q&A — 6 min · slide 20

- **20 Trust the slice tested against humans.** The rule for when to trust the
  judge and when to stop.
