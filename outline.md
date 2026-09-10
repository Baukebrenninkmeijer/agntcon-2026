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

The three questions are no longer given their own slide; they are spoken over the opening. Each
block still carries its question in the first slide's eyebrow, so the structure stays visible even
though nothing enumerates it up front.

| Question | Answered in | Deck slides | Block eyebrow |
|---|---|---|---|
| 01 · How do you get a first signal with no labels? | section 2 | 9-11 | no eyebrow; the question is the heading (slide 9) |
| 02 · When can you trust a judge instead of a human? | section 3 | 12-20 | `Question 02 · Trust the judge` (slide 12) |
| 03 · What do you evaluate in an agent that is not the final answer? | section 4 | 21-22 | `Question 03` over the question itself (slide 21) |

Sections 5 and 6 are the payoff rather than a fourth question: what it costs to run this forever.

Moving or renaming a block means updating that block's eyebrow, the spoken opening, and this table
together.

---

## 1. The evaluation gap (3 min)

### Slide: Two correct answers, only one you want

Introduce Sphere.com, an Amsterdam-based B2B wholesaler of physical home appliances.

The board is asking about quality of growth: discounts, refunds, cancellations, and regional and
category mix. The analytics agent can query order data and explain the result.

Put two answers to one question on screen: where is the station? One gives the coordinates, the
other says two streets left, five minutes on foot. Both are true and the precise one is useless.
Nothing here needs a criterion, a dataset, or a definition, which is the point: the room agrees on
which answer is better before the talk has defined anything, and that agreement is the thing the
rest of the talk has to teach a judge.

Sphere.com and the quality-of-growth framing are introduced on the case slide, not here.

That is the evaluation gap. Reference matching can verify a number, but it cannot determine whether
the response used sound judgment about emphasis, explanation, caveats, and scope.

### Slide: We came for optimization. We got stuck on the signal.

Where the project actually started, and why this talk is about evaluation at all. The plan was to
feed the judge's critiques back into the agent and let it improve itself. That works only if the
judge can be trusted: an unaligned judge optimizes the agent toward its own mistakes. The diagram is
that loop with the signal arm crossed out.

On screen this is two lines, "Self-improvement runs on the judge's critiques. A wrong judge, wrong
improvements." The loop and its consequence are spoken over the diagram rather than written out.

This slide is the motivation the deck was missing; it was cut in `c280a25` and restored on
2026-09-09.

### Slide: Evaluation moved from correctness to alignment

A three-stage evolution at the level needed for the talk. Known-answer evaluation compares an
output with ground truth. Human-judgement evaluation compares an annotation with an expert.
LLM-judge evaluation compares judge labels with expert labels. The slide drops the earlier n-gram
detour and closes on the consequence: the evaluator now needs its own evaluation.

On click, the full-width lineage moves upward without shrinking. A large horizontal diagram rises
into the lower portion: Agent and Judge form one feedback loop, while Judge and Expert form the
second. The shared judge makes the control visible: the agent can learn from the judge only while
the judge learns from expert decisions.

### Slide: The ordering constraint

You cannot use evals to improve an agent before the eval is aligned. This is why the alignment work
in section 3 comes before the agent work in section 4, and it is stated once, plainly.

### Slide: Who is saying this

A full-bleed slide on the deep teal, ported from the ADC red-teaming deck: the cartoon avatar in a
ring, the name, "Applied AI Researcher, orq.ai", and two mono lines: the three work areas (red
teaming, evaluation, agent simulation) and the Agentic AI Foundation Amsterdam role. It is the only
dark slide in the deck, which is what makes the break work. This sits last in section 1, so
the whole problem lands before the speaker introduction: the two answers, the origin story, the
lineage, and the ordering constraint all come first, and the bio arrives as a credential for what
was just argued rather than as a preamble to it.

### Slide: What is orq.ai?

Ported from the same ADC deck. A dark teal band gives the one-line platform description, then three
cards name the parts: Agents (build), Router (ship), Observability (optimize), each with the
comparable tools underneath so the audience can place the product without a pitch. Roughly 25
seconds, spoken over, and it exists so the rest of the talk can refer to the platform the evaluation
work runs on without explaining it mid-argument. The case slide follows immediately.

---

## 2. Start with humans, not infrastructure (5 min)

### Slide: Does the answer support the decision?

The criterion is the heading, because it is what the next twelve slides argue about. Under it, one
line says it is a subjective criterion agreed by humans before any judge sees it, and a footer strip
carries the only other number the slide needs: fifty distinct business situations. "Start with
humans" is spoken, not printed, and the two labels (`pass` or `fail`, with a written critique) belong
to the slide after this one, which is where they are explained.

The fifty cases vary the situation rather than multiplying cosmetic personas. Each Sphere.com case
includes the stakeholder, decision, delivery setting, communication need, and analytical question.
Include easy cases, ambiguous requests, multi-turn corrections, missing data, and answers that look
plausible but are not useful for the decision.

Until review is complete, call this the **fifty-case review pool**. It becomes “roughly fifty
hand-reviewed examples” only after those judgments exist. Do not show the 30/20 development/test
split here; introduce it later when it becomes part of validating the judge.

### Slide: How do you create an eval?

For every applicable case, the reviewer must choose `pass` or `fail` and explain why. The critique
contains the nuance; the label makes the boundary operational.

Three benefits on the slide, taken from the ECIR material:

- a binary decision is clear enough to act on;
- no false precision from a 1–5 scale;
- agreement and false passes become measurable.

The cost gets stated once, at the bottom, and only once: binary grading offers no “maybe” bucket, so
an unaligned boolean judge is worse than an unaligned 1–5 judge, because every mistake becomes a hard
boundary decision instead of an imperfect position on a scale.

Forcing the judge to choose does not remove ambiguity. It pushes every ambiguous case onto one side of
the boundary, which is what makes alignment both harder and more important. The throughput and
cognitive-load argument is narration, not a bullet.

`not_applicable` is reserved for cases where the criterion genuinely does not apply. It is not an
escape hatch for uncertainty.

The consistency and throughput benefits are also summarized in O’Reilly’s
[What We Learned from a Year of Building with LLMs](https://www.oreilly.com/radar/what-we-learned-from-a-year-of-building-with-llms-part-i/).

### Slide: The grey zone

The consequence of the binary, shown rather than argued. The clear passes and clear fails sit at
either end; between them is the band of cases where reasonable reviewers disagree. That band is
where all the alignment work happens, and it is the slide the later grey-zone loop refers back to.

### The criterion, on the `Start with humans` slide

The criterion is not its own slide. It sits below the three setup numbers, under an orange rule,
in the lower third of that slide, so the room reads the setup and the question it is a setup for in
one place. For this talk we align only `decision_support_quality`:

> Does the response turn the analysis into clear, appropriately scoped input to the stakeholder’s
> stated decision, using sound judgment about emphasis, explanation, caveats, and next steps?

The evaluator does not recompute the analysis or compare the response with an ideal answer. It
judges the conversation, visible tool evidence, and final response against the stated decision.

---

## 3. Align an LLM-as-a-judge (7 min)

### Slide: Every failure has two suspects

Opens the question 02 block, before the pre-LLM method. One failing evaluation starts one of two
loops: either the answer really was wrong and the agent gets updated (system loop), or the judge
was wrong and the evaluator gets updated (evaluator loop). The point of the slide is the closing
line: aligning the judge to humans is how you tell the two apart. This is the motivation for
everything in section 3 — without alignment you cannot know which loop a failure belongs to, so
you risk fixing the agent to satisfy a judge that is itself wrong.

The concrete instance of both loops appears in section 6 ("A finding is not yet knowledge"), where
one Sphere finding produces a skill update and an evaluator update from the same case.

### Slide: Two lifecycles, not one

Follows the two-suspects slide and gives the same idea a picture, revived from the earlier version
of this deck. Two three-stage cycles turn side by side: application (build, ship, observe) and
evaluation (criteria, label, align). Two dashed links between them carry the coupling — evaluation
gates every release, and failures found in production become new cases — over a line naming what
both loops act on: the same cases, the same prompt versions, the same human labels. The line to say
out loud is the subtitle: the application loop only moves as fast as the evaluation loop it trusts.

### Slide: The quality-control process has not changed

Show the conventional quality-control workflow as two parallel tracks. In both, an expert annotates
reference cases, a delegate independently annotates the same cases, and their annotations are
compared. The grey track delegates to a student or Mechanical Turk worker. The orange track delegates
to an LLM judge.

Expert–delegate agreement answers the alignment question: can we trust this delegate's labels?
Agreement among students or among repeated LLM judges remains a useful stability measure, but it is
not the base flow taught on this slide. The unchanged comparison with expert annotations establishes
version one of the process. The later grey-zone loop proposes a faster way to sharpen the criteria
before applying them across the dataset.

### Slide: But we are lazy

A statement slide, and the motive for the two that follow. The heading, one line under it, and then,
set apart below in mono teal, what this whole block is spending: the most valuable thing.
The line is let the LLM judges find the ambiguous cases and spend human time only there. How the judges
find them is the next slide; what the queue looks like is the one after.

### Slide: Two ways of disagreement

Both signals in one picture, on real verdicts. A three-by-three grid: rows are the three judges by
name, columns are the three repetitions of the same case, each cell coloured by its verdict. Read
across a row and you see one judge disagreeing with itself; read down a column and you see the
judges disagreeing with each other. Every cell is one measured decision, so it holds one colour.

This is also where the term is defined, by picture rather than by dictionary: a judge is *unstable*
when it returns different verdicts on repeated evaluations of the same case, and one pass/fail
change across a model's three repetitions is enough to flag the case for review. The term recurs
for the rest of the talk and is not re-explained.

On the click, the grid rotates back into depth and forty-nine further layers appear behind it, one
per case in the pool: the same two signals exist for all fifty. Verdicts come from the v3
decision-support jury run of 2026-09-08; the front layer is the case discussed out loud.

### Slide: The judge sorts the queue

We still need human judgment, but we do not have to review cases in random order.

Run the unaligned evaluator as a three-model jury, with three repetitions per model. This yields two
signals before annotation:

- **instability:** one judge changes its verdict across repetitions;
- **jury disagreement:** different models place the same case on different sides.

Prioritize those cases for human review, then add a sample of unanimous cases to catch confidently
wrong consensus. Continue until the reviewed set is broad enough to support alignment claims.

The slide carries this in three beats: fifty plain case dots, then the rings for the two signals
with the unstable cases carrying a slowly rotating red-to-green gradient, then a review batch rising
out of the grid: four flagged cases into the review lane and four unflagged cases into a control
lane beside it. That
half-and-half batch is the recommendation. Positions come from the canonical v4 jury run: six cases
with jury disagreement, eight unstable, twelve flagged in total.

The jury accelerates annotation; it does not annotate for us. Humans still decide where the
boundary belongs.

### Slide: Disagreement gives us a question

The bridge out of the queue and into the grey-zone work. A funnel: the cases the panel split on, drawn
as dashed orange dots, converge on one dark teal circle carrying a question mark, labelled one boundary
question. Under it, the line that says what happened: the flagged cases produced no labels, they produced
the question the criterion never answered.

The slide is deliberately general. The premise of this whole section is that scattered disagreement
collapses into a small number of answerable questions, so naming any single case here would argue the
opposite. The cases stay anonymous; the next slide shows what answering one of them did.

### Slide: One answer exposed another ambiguity

Use the first human boundary answer as the walkthrough: visible analytical claims should always be
valid and correct. Show how encoding that rule exposed a second interpretation gap. Some judges
treated a claim as incorrect when the visible evidence did not prove it; others reserved failure
for a visible contradiction.

The development-only rerun made the boundary more visible: panel disagreement increased from four
to eight cases, within-judge instability increased from six to eight, and no aggregate verdict flipped.
This does not show that the rule made the evaluator worse. It shows that the principle was clearer
than the threshold for “unsupported,” giving humans a better next question to answer.

On screen this is the slide-12 grey zone drawn twice: the same fifty reviewed cases against the
boundary band, before the rule and, on click, after it. The band widens rather than narrows, and the
count of split cases goes from four to eight. The dot positions are the slide-12 illustration reused;
only the counts are measured. The instability and no-flip numbers are spoken, not printed.

### Slide: The grey-zone loop

Present the proposed version-two process as an acceleration layer before full annotation. Run the
jury on the same frozen development cases, use disagreement and self-flips only as signals, and let
the collaborator read the reasons to identify competing interpretations. The collaborator formulates
one boundary question; the human answers it; the accepted rule is encoded in the evaluator; then the
same cases run again. Repeat until the important boundary questions have been answered.

Only after those iterations do the human decisions get applied across cases to create reference
labels. The click-revealed lower strip makes this exit explicit with three real development cases:
clarifying the metric first passes, the visibly contradictory net-revenue definition fails, and
context established earlier in the conversation still counts. Orange remains reserved for the human
step in the loop; the failed case uses red.

### Slide: Human labels reveal the judge limits

Keep the real Orq experiment grid as evidence rather than presenting a detailed experiment report.
The jury signals helped locate unresolved questions. The collaborator turned those signals into
boundary questions, the human supplied the decisions, and those decisions became reference labels.
Comparing the judge labels with the expert labels then exposed which judges could reproduce the
human boundary.

The detailed development result remains supporting evidence for questions: prompt v3 is more stable,
but its aggregate still misses all three human failures. That is the stopping point for this talk:
preserve v3 as evidence of a judge capability limit, keep it in shadow, and do not imply that another
prompt iteration or more repetitions would supply the missing judgment.

---

## 4. What makes agent evaluation different (4 min)

### Slide: What changes with agents?

A divider carrying only the question. This is where question 03 is stated in full, since nothing
enumerated it earlier: the heading asks what changes with agents, and nothing else is on screen.

### Slide: The answer is only the endpoint

Keep this high level. Do not introduce a hierarchy of evaluation levels.

On screen: the sub-line says agents require evaluating behavior rather than final answers. The
fifty-run trajectory chart fills the left column with a `NR. OF TOKENS` axis marker under it and
its description below that. The right column names three example behavioral evals - tool-call
efficiency, error recovery, instruction adherence - so the abstract point lands as concrete evals.

Agent evaluation can inspect:

- the full trajectory rather than only the final text;
- which tools were selected and how their outputs were used;
- assumptions or unsupported claims introduced between steps;
- context, definitions, or constraints lost across turns;
- state changes such as saving an insight or performing a write.

Replay rather than regenerate: the runs under review are recorded, so the object stays fixed while
the judge changes. That is spoken, not given a slide.

Trajectory evidence can explain why an answer failed. Tool calls reveal whether the response rests
on observed data. Multi-turn replay exposes context drift that a final-answer judge cannot see.

For Sphere.com, `decision_support_quality` remains one focused subjective verdict. The conversation
and tool events provide context for that verdict; they are not turned into additional evaluators in
this stage.

---

## 5. Scaling: offline, online, continuous (3 min)

### Slide: Build the eval once. Then it guards every commit.

Opens section 5, before the operating modes, because the payoff has to land before the taxonomy.
The aligned eval is written once and then runs on every change: a DISCOVERY phase over hard and
edge cases, where a low pass rate means the eval is working, and a REGRESSION phase over known
behavior and core paths, where anything failing stops the commit.

### Slide: Three operating modes

A single time axis with a release marker rather than three equal cards. Offline sits before the
marker, online after it, and continuous is a row of separated dark-grey blocks spanning both, one
per repeated run, so the modes read as positions in the lifecycle rather than three competing
definitions of quality.

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

### Slide: Most software will ship without a human reading it

A full-bleed statement, the same treatment as "But we are lazy" in section 3, so the deck already
has the grammar for it. The claim is the premise the next slide needs: pull requests increasingly
merge without anyone opening them.

The line under it is the argument: you cannot scale review, you can scale the thing that decides
what is worth reviewing. That is the same move as "the judge sorts the queue" in section 3, one
level up, and it is worth naming the callback out loud.

### Slide: Same throughput. Different factory.

Two identical cards, side by side. Same unlabelled gauge, same sentence: most pull requests merge
untouched. Below a dashed rule they diverge. One is holding, its criterion still passes. The other
is rotting, the same criterion started failing.

The point is that the throughput number is identical in both. A factory reports how much moved; it
cannot tell these two apart. Only an eval can.

No numbers on the slide. The gauges are unlabelled, and the argument is borrowed from Warp's own
write-up on evals and scorers, without their marketing figures.

CI asks whether a change can ship. The software factory investigates what went wrong and prepares a
reviewable response.

Narration, not slides: the loop behind this is an evaluator finding, a structural analysis, a
proposed skill or evaluator change that arrives as a pull request, and a human who decides. Nothing
writes back to configuration on its own. If the finding shows the evaluator misread the boundary,
the evaluator changes rather than the agent.

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
