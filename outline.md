# Evaluating Agents at Scale — talk outline

30 minutes: 25 speaking + 5 Q&A. PyData audience, technically literate, industry-heavy.
No hand-holding, no listicle. All slides static for the first delivery.

Design constraints settled during planning:

- The talk presents **our method and our findings**, not a to-do list for the attendee.
- We present the alignment **protocol**, not measured agreement — we have no human labels yet,
  so no numeric threshold appears on a slide. The honesty about that gap is load-bearing, not an
  apology.
- The simulation harness' own scorer numbers stay off the slides. They are a second unvalidated
  instrument and putting them on screen invites the audience to read them as agent quality.
- The infrastructure war stories (jury vote discarding, empty SDK response, experiment
  misplacement) are cut. One argument per talk.

---

## 1. Why evaluation, and why now (5 min)

Four beats, in this order.

**1a. Origin: we came for optimization and got stuck on the signal.**
We set out to automate agent improvement — feed evaluation critiques back as an optimization
signal and let the system improve its own prompt. We could not do it, because we could not trust
the signal. An unaligned judge optimizes the agent toward the judge's own errors. That ordering
constraint is the reason this talk is about alignment and not about optimization:

> You cannot use evals to improve an agent before the eval is aligned.

Told from the historical angle: this is what made us look closely at evaluation as its own
object of study, with its own lifecycle, rather than as a test suite bolted onto the agent.

**1b. The lineage: hard metrics to judgement metrics.**
Information retrieval and NLP already went through this. Retrieval had crisp, countable targets
and then had to move to human relevance judgements — and the moment humans were the target,
assessors disagreed with each other. Generation went the same way: n-gram overlap metrics gave a
number that stopped correlating with quality. The field's answer, repeatedly, was to bring in
human judgement and then measure how much the humans agreed.

We do not need to name specific test collections. The point is the shape of the move: as the task
got more open-ended, the metric got softer, and the *agreement* between judges became the thing
that had to be measured.

**1c. Agents break it again, in several ways at once.**
Non-deterministic across multiple calls. Trajectories branch — many valid paths to one answer.
State mutates in external systems, so "did it do the thing" must be checked rather than inferred.
And correctness is judged along several axes simultaneously.

**1d. The double loop.**
Two lifecycles, not one. The application loop: build, ship, observe failures, change the agent.
The evaluation loop: define criteria, annotate, align the judge, discover the criteria were wrong,
redefine. They are coupled but they are not in lockstep — it is not true that each agent change
implies an eval change. What is true is that the evaluation loop has to reach a certain maturity
before the application loop can use it at all.

Land the framing line here: **an evaluation system is another system with a prompt, a dataset,
versions, and a human reviewer.** Same object, moustache and hat. Payoff comes at the end.

## 2. The grey zone (2 min)

Stay high level and generic here. The audience has no context on our agent yet, so use a familiar
classic — sentiment on movie reviews, or similar.

Start with a classifier picture everyone recognises: two classes, points in a space, a clean
decision boundary. Then pan to evaluation and the boundary dissolves into a gradient band.

Animate **several different, all defensible, boundary placements** over the same points. Not
multiple agent trajectories — that is a different idea and it belongs in section 7. The point
here is that the criterion itself is what is under dispute.

Name it: **the grey zone.** Every evaluation has one. Every evaluation also has a set of
sub-dimensions it is implicitly grading, and you only discover what they are by iterating on
actual data. Deliberately do not label the axes — the axes are whatever you turn out to be
measuring, and you do not know that yet.

Close the section on the open question, and leave it open: *who decides where the boundary goes?*

## 3. The agent and the corpus (3 min)

Introduce the running example properly, with context. A small analytics agent over a business
dataset, answering questions like "month-over-month EMEA revenue growth in Q3". It writes SQL,
runs it against DuckDB, and can save an insight.

Failure modes we care about: right query with the wrong aggregation, hallucinated numbers with no
query behind them, correct answer via an invalid path, multi-turn context loss.

The corpus (v3): **one user, fifty situations.** A single business-analyst persona asks fifty
different questions — different metric, period, filter, grouping, and conversational shape (26
one-turn, 18 two-turn, 6 three-turn). Every answerable case carries an executable DuckDB oracle
computed from the data, not written by a model; three cases are deliberately unanswerable (a
column that does not exist, a period outside the data, a region that does not exist). Frozen
30-dev / 20-test split, decided before looking at any results.

Why one persona: the previous corpus crossed five personas with ten scenarios. When we measured
the judge's consistency on it (section 6), three of the four cases it kept changing its mind on
were the *same scenario* worn by different personas. The grid had bought us fifty rows and ten
situations. Persona variation is cheap; situation variation is what finds the grey zone.

The important design choice: **we deliberately keep the failures.** Conversations where the agent
misbehaves are retained rather than regenerated. A corpus of successes teaches you nothing, and —
as section 6 shows — those retained failures are the thing that catches the judge out.

## 4. Cheap graders first (2 min)

Before any judge. Deterministic checks over the run record: did the SQL parse, did it execute,
did the insight actually get written. Stdlib only, AST-checked, no credentials, no network.

Rule: if code can grade it, never pay a model to. This is the highest-return hour in the whole
process and it is the section most evaluation talks skip entirely.

*Compress to 60 seconds if running long.*

## 5. Decomposing the judge (3 min)

"Is this correct?" is not alignable — annotators disagree with themselves on it, because it is
several questions wearing one coat. This is the grey zone from section 2, restated concretely.

We cut it into atomic rubrics: answer correctness, query semantics, evidence faithfulness,
multi-turn consistency. Each one has a narrower grey zone than the union did.

**We align one metric: answer correctness.** The other rubrics are deferred — multi-turn
consistency included — because aligning one rubric properly beats aligning four thinly. Then we
decompose *that one* further, because "is the final answer correct" is still several questions:
right metric definition (gross vs net, rate vs amount), right period boundary, right entity or
grouping, figures that follow from the evidence, and nothing material omitted. Each of these is a
place the judge can disagree with itself, and the stability run in section 6 tells us which ones
actually do.

The slide worth stopping on: **the judge is reference-free and sees everything.** It gets the full
ordered conversation — user turns, tool calls, tool results, intermediate assistant messages — and
no expected answer. It has to derive the correct result from the recorded evidence and compare the
final response against that. Show the line from the actual prompt:

> You have no reference answer. Derive the correct result yourself from the user's request and the
> tool calls and tool results recorded in the conversation.

Two reasons. First, in production there is no oracle; a judge that needs one is a test fixture,
not an evaluator. Second, keeping the oracle *out* of the judge is what lets the oracle serve as
ground truth *for* the judge: if the judge had seen it, agreement with it would be circular.

This is the start-small lesson from the closing, applied to ourselves before we recommend it to
anyone.

## 6. Alignment (6 min) — the centre of the talk

**6a. The protocol.** Treat the judge exactly as you would treat an outsourced annotator. Binary
pass/fail plus a written critique — the critique is the asset, the label is just an index into it.
Dev/test split applied to the evaluation itself. Iterate on *disagreement patterns*, never on
individual rows.

**6b. The bar is human agreement.** The judge is held to the same standard as a second human
annotator: it must agree with the human reviewer about as often as two careful humans agree with
each other on the same rows. That inter-annotator agreement is measured first and becomes the
ceiling; the judge's agreement with the humans is then read against it. Say why the false pass is
the error to watch: it is asymmetric, because a false pass ships. Do not put specific numeric
thresholds on the slide — we have not measured human agreement yet, and any number would be
invented.

**6c. Audience places the boundary.** This is where the grey zone becomes concrete and where the
room participates. Take real responses from the corpus that sit in the band, put the question to
the audience, collect the split, then show our own reading and where it was contested. Use the
real judge explanations verbatim — they are short and specific enough to read from a slide.
Example of a clean catch:

> The tool result for the region × year aggregation clearly shows that for 2025, EMEA leads with
> 10,369,167.91. The assistant, however, refused to commit: it claimed the year was masked by
> placeholder tokens and asked the user to confirm the concrete year even though the user had
> already specified 2025 unambiguously.

Note that the judge reconstructed the right answer from the tool result on its own — no oracle in
sight — and then graded the refusal as a fail. Whether a well-meant refusal to answer a clear
question is a *correctness* failure is exactly the kind of boundary the room should argue about.

**6d. The finding.** Two things, both made without a single human label.

First, the pass rate. One pinned experiment over all 50 rows of the previous corpus: the
reference-free judge passed 48 and failed 2, while the corpus contained ten conversations we
deliberately retained as behavioural failures. An unaligned judge produces a number that looks
like a result and is not one.

Second, consistency. Ask the judge the same question eight times over, on the 30 dev rows, at
temperature 1. It gave the same answer every time on 26 rows and changed its mind on 4 — and
three of the four were one scenario ("compare gross with net for Software, then correct the
request") under different personas. Two of those four flipped from a single-shot pass to a
majority fail. That is the grey zone, located by the judge itself: it does not know whether a
corrected request that the agent half-applied is a pass. It is also what sent us back to the
corpus (section 3) — consistency measurement found a corpus design flaw before it found a judge
flaw. Do not over-work this; it is one example among the section's material, not a reveal to
build to.

**6e. Where we actually are.** Zero human labels so far, and therefore no measured human
agreement to hold the judge against. What we have is the judge's self-consistency map over the
corpus and the executable oracles as a mechanical ground truth. The protocol above is what we run
next. Say it plainly — the gap is the reason the talk exists.

## 7. Trajectory and state (2 min)

The dimensions that only appear once the system is an agent.

Replay recorded responses without re-invoking the agent. You judge the recorded artifact rather
than a fresh non-deterministic run, which is what makes agent evaluation reproducible at all.

State: assert the insight file exists. Never ask a model whether the agent did something you can
check directly.

Non-determinism at scale: pass@k for capability, pass^k for reliability. One slide, keep moving.

*Compress to one slide if running long.*

## 8. Where this goes, and the closing (2 min)

Return to the origin from section 1a. Once the judge is aligned, its critiques become an
optimization signal — every failure produces an English critique, and the critiques drive
targeted changes rather than prompt-tinkering. That is what we wanted at the start, and the
ordering constraint is the price of admission.

The close, and the only thing they need to keep:

**The grey zone does not go away. Your job is to locate it deliberately instead of pretending it
is not there — and alignment is how you locate it.**

Then the practical lesson underneath it: **start small, validate small components, then increase
scope.** One rubric aligned properly is worth more than four rubrics guessed at. The same holds
as scope grows — to multi-agent systems, to software factories, to anything where the output is
judged rather than checked. The open questions live at that level, not in our toy dataset.

---

## Cut list, if running long

1. Section 4 down to 60 seconds.
2. Section 7 down to one slide.
3. Never cut section 6.

## Deliberately not in this talk

Decision trees for choosing metrics; annotation-era history tables; the Mechanical Turk framing;
prompt-learning mechanics and benchmark results; vendor bug stories; a live demo.
