# Evaluating Agents at Scale — talk outline

30 minutes: 25 speaking + 5 Q&A. PyData audience, technically literate and industry-heavy.

The submitted abstract is the spine. Sphere.com and `decision_support_quality` are the running
example, not the structure of the talk.

The story follows two related lifecycles:

- the evaluator lifecycle: human judgment → aligned judge → regression signal;
- the application lifecycle: observed failure → structural analysis → reviewed improvement.

The central claim:

> An LLM judge is another model. It earns trust only by demonstrating alignment with human
> judgment on the boundary we actually care about.

Honesty constraints:

- The fifty v4 cases are a review pool until humans have actually annotated them.
- Jury consensus and consistency are annotation signals, not ground truth.
- No measured human alignment is claimed before labels exist.
- CI, online evaluation, and the software factory are next stages, not completed work.
- The talk uses only the analytics agent. There are no podcast examples.

---

## Spine: the three questions

Slide 4 names three questions, and every block after the opening answers one of them. The block's
first slide carries its question in the eyebrow, so the promise on slide 4 is visibly kept.

| Question | Answered in | Deck slides | Block eyebrow |
|---|---|---|---|
| 01 · How do you get a first signal with no labels? | section 2 | 5-9 | `Question 01 · Start with humans` (slide 6) |
| 02 · When can you trust a judge instead of a human? | section 3 | 10-15 | `Question 02 · Trust the judge` (slide 10) |
| 03 · What do you evaluate in an agent that is not the final answer? | section 4 | 16-18 | `Question 03 · What changes with agents` (slide 17) |

Sections 5 and 6 are the payoff rather than a fourth question: what it costs to run this forever.

Moving or renaming a block means updating slide 4, that block's eyebrow, and this table together.

---

## 1. The evaluation gap (3 min)

### Slide: Two correct answers, one useful answer

Introduce Sphere.com, an Amsterdam-based B2B wholesaler of physical home appliances.

The board is asking about quality of growth: discounts, refunds, cancellations, and regional and
category mix. The analytics agent can query order data and explain the result.

Put two plausible answers to the same CFO question on screen. Both can contain the right number.
Only one makes the relevant comparison clear enough to support the stated decision.

That is the evaluation gap. Reference matching can verify a number, but it cannot determine whether
the response used sound judgment about emphasis, explanation, caveats, and scope.

### Slide: Who is saying this

Three lines of bio. Orq is introduced out loud, not on the slide.

### Slide: Three questions

Name the three questions the talk answers, then hand each one to a block below.

### Slide: Agents widen the gap

An agent is not a single model call. Its path can branch, its tool usage can differ, earlier context
can disappear, and its actions can change external state.

The final answer is therefore only the visible endpoint. We need a way to evaluate open-ended
behavior without pretending that one ideal response exists.

---

## 2. Start with humans, not infrastructure (5 min)

### Slide: Begin with a small human-reviewed corpus

Build roughly fifty diverse cases around real decisions. Each Sphere.com case includes the
stakeholder, decision, delivery setting, communication need, and analytical question.

The cases vary the situation rather than multiplying cosmetic personas. Include easy cases,
ambiguous requests, multi-turn corrections, missing data, and answers that look plausible but are
not useful for the decision.

Until review is complete, call this the **fifty-case review pool**. It becomes “roughly fifty
hand-reviewed examples” only after those judgments exist.

### Slide: How do you create an eval?

For every applicable case, the reviewer must choose `pass` or `fail` and explain why. The critique
contains the nuance; the label makes the boundary operational.

The practical benefits highlighted in the ECIR material are:

- a binary decision is clear and actionable;
- it avoids false precision from inconsistently interpreted 1–5 scales;
- it lowers cognitive load and increases annotation throughput;
- agreement, precision, recall, and false-pass rate become directly measurable.

The important cost is also the point: binary grading offers no “maybe” bucket. Forcing the judge to
go either way does not eliminate ambiguity. It forces every ambiguous case onto one side of the
boundary.

That makes alignment harder and more important. Instability and disagreement reveal where the
judge does not know how humans place the boundary.

`not_applicable` is reserved for cases where the criterion genuinely does not apply. It is not an
escape hatch for uncertainty.

The consistency and throughput benefits are also summarized in O’Reilly’s
[What We Learned from a Year of Building with LLMs](https://www.oreilly.com/radar/what-we-learned-from-a-year-of-building-with-llms-part-i/).

### Slide: One criterion at a time

For this talk we align only `decision_support_quality`:

> Does the response turn the analysis into clear, appropriately scoped input to the stakeholder’s
> stated decision, using sound judgment about emphasis, explanation, caveats, and next steps?

The evaluator does not recompute the analysis or compare the response with an ideal answer. It
judges the conversation, visible tool evidence, and final response against the stated decision.

---

## 3. Align an LLM-as-a-judge (7 min)

### Slide: The historical method

Show the conventional workflow first:

1. Randomly sample cases.
2. Ask humans to review all of them and record pass/fail labels with critiques.
3. Rewrite the judge on the gaps this exposes.

The development and test split belongs to this method too, but it is introduced once, on the
`Align the evaluator like any other model` slide, rather than named here and again there.

This is methodologically clean and expensive in expert attention.

### Slide: LLM judges determine priority

The concept before the picture, stated as plainly as it will go: two signals decide what a human
reads first.

- model disagreement
- model wobbling

On the click, the definition of the second one appears on the same slide: **Wobbly**, adjective,
LLM-as-a-judge flips sides on repeated evaluations of the same case. The term recurs for the rest
of the talk, so define it here and do not re-explain it later.

### Slide: We are lazy—make the queue smarter

We still need human judgment, but we do not have to review cases in random order.

Run the unaligned evaluator as a three-model jury, with three repetitions per model. This yields two
signals before annotation:

- **self-wobble:** one model changes its verdict across repetitions;
- **jury disagreement:** different models place the same case on different sides.

Prioritize those cases for human review, then add a sample of unanimous cases to catch confidently
wrong consensus. Continue until the reviewed set is broad enough to support alignment claims.

The slide carries this in three beats: fifty plain case dots, then the rings for the two signals,
then the flagged cases rising into the review lane in priority order. Positions come from the
canonical v4 jury run: six cases with jury disagreement, eight with self-wobble, twelve flagged in
total.

The jury accelerates annotation; it does not annotate for us. Humans still decide where the
boundary belongs.

### Slide: Wobbly

Give the term a compact dictionary definition before showing the measured queue:

> **wobbly**, adjective — of an LLM judge: returning different verdicts when asked to grade the
> same case with the same rubric.

For this walkthrough, one pass/fail change across a model's three repetitions is enough to flag the
case for review. This definition takes the detailed explanation off the preceding queue slide; it
does not add time to the seven-minute section.

### Slide: Align the evaluator like any other model

Use the 30-case development split to study disagreement patterns and revise the evaluator. Do not
patch individual rows or expose the held-out cases during iteration.

Use the 20-case test split only to measure agreement, precision, recall, and especially false-pass
behavior. A false pass matters most because it allows a bad answer to ship.

A panel reduces dependence on one model’s preferences. Consensus still does not prove correctness;
it only tells us the models agree.

For the live walkthrough, open the single dev-only Orq Experiment that places prompt v1, v2, and
v3 side by side. Its boolean cells separate human alignment, panel consensus, and within-judge
stability: v3 is visibly less wobbly while human agreement remains unchanged.

### Slide: One answer exposed another ambiguity

Use the first human boundary answer as the walkthrough: visible analytical claims should always be
valid and correct. Show how encoding that rule exposed a second interpretation gap. Some judges
treated a claim as incorrect when the visible evidence did not prove it; others reserved failure
for a visible contradiction.

The development-only rerun made the boundary more visible: panel disagreement increased from four
to eight cases, within-judge wobble increased from six to eight, and no aggregate verdict flipped.
This does not show that the rule made the evaluator worse. It shows that the principle was clearer
than the threshold for “unsupported,” giving humans a better next question to answer.

---

## 4. What makes agent evaluation different (4 min)

### Slide: What changes with agents?

A divider carrying only the question. Question 03 was named on slide 4 and then not heard from
again until its block opened, so it gets stated once in full before the block starts: the heading asks
what changes with agents, and nothing else is on screen.

### Slide: The answer is only the endpoint

Keep this high level. Do not introduce a hierarchy of evaluation levels.

Agent evaluation can inspect:

- the full trajectory rather than only the final text;
- which tools were selected and how their outputs were used;
- assumptions or unsupported claims introduced between steps;
- context, definitions, or constraints lost across turns;
- state changes such as saving an insight or performing a write.

Trajectory evidence can explain why an answer failed. Tool calls reveal whether the response rests
on observed data. Multi-turn replay exposes context drift that a final-answer judge cannot see.

For Sphere.com, `decision_support_quality` remains one focused subjective verdict. The conversation
and tool events provide context for that verdict; they are not turned into additional evaluators in
this stage.

### Slide: Replay, do not regenerate

Evaluate recorded runs without invoking the target agent again. The object under review must stay
fixed while the judge changes.

This separates target non-determinism from evaluator non-determinism and lets humans and jury
members inspect the same behavior.

---

## 5. Scaling: offline, online, continuous (3 min)

### Slide: Three operating modes

Keep this slide about where and when evaluation runs:

- **Offline:** curated cases used during development, alignment, and model or prompt comparison.
- **Online:** sampled production traces used to find real failures, new situations, and drift.
- **Continuous:** automated checks triggered by changes and repeated over time.

These are operating modes, not three different definitions of quality. The same aligned criterion
can move between them, provided the production slice still resembles the slice validated by humans.

CI becomes appropriate only after the evaluator has earned that trust. A failed check should name
the affected cases and preserve the evidence needed for review.

Do not put structural error analysis or automated improvement on this slide. That is the software
factory’s job.

---

## 6. Evals in the software factory (2 min)

### Slide: A finding is not yet knowledge

An evaluator produces a finding: a failed case plus a critique. The finding becomes reusable only
after repeated failures are analyzed into a structural rule.

Show the relationship explicitly:

| Artifact | Role |
|---|---|
| Finding | Evidence that a specific behavior failed |
| Structural analysis | Explanation of the recurring cause |
| Evaluator | Defines how success and failure are recognized |
| Skill | Teaches the agent domain knowledge, criteria, and task-specific behavior |
| System prompt | Holds the small set of global identity, safety, and behavioral invariants |

The evaluator says what failed. The skill teaches the agent what to know or do differently. Do not
blindly paste evaluator prose into the system prompt.

Domain-specific knowledge belongs primarily in skills because it can be scoped, versioned, tested,
and loaded for the relevant task. Only genuinely global rules should move into the system prompt.

If the finding shows that the evaluator misunderstood the boundary, update the evaluator instead of
teaching the agent to satisfy a broken judge.

### Slide: Automate preparation, preserve human authority

The software-factory loop is:

1. The evaluator identifies failures or changed behavior.
2. An analysis agent clusters cases and proposes a structural cause.
3. The analysis is presented to a human with the underlying evidence.
4. An improvement agent prepares a skill, prompt, tool, or code change and opens a PR.
5. A separate validation agent runs the regression set and reviews the proposed change.
6. A human decides whether the diagnosis is valid and whether the PR should merge.

Example: several failures show that the agent does not understand a company-specific revenue
definition.

The factory proposes a tested skill update containing that domain rule and examples. It opens a PR
and attaches the affected cases and validation results for review.

CI asks whether a change can ship. The software factory investigates what went wrong and prepares a
reviewable response.

This closes the application lifecycle without collapsing it into the evaluator lifecycle.

Agent knowledge can improve while the definition of quality stays fixed. The evaluator changes only
when human review shows that its boundary is wrong.

---

## 7. Takeaways and Q&A (6 min)

### Takeaways (1 min)

1. Humans define the boundary; the judge does not invent it.
2. Binary verdicts make the boundary actionable and make ambiguity visible as disagreement.
3. Repeated juries can route human attention, but consensus is not ground truth.
4. Agent evaluation can inspect trajectories, tool use, context drift, and state—not only answers.
5. Aligned findings can drive reviewed improvements through skills, PRs, and regression checks.

Close with:

> Trust automation only inside the slice tested against humans. Stop when disagreement, drift, or
> false passes show that you have left it.

### Q&A (5 min)
