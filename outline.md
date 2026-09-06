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
- The running example on the slides is **illustrative**. The method and the structural findings come
  from a real alignment run on a different agent; the inbox transcripts and judge explanations are
  written to teach. One real morning appears on screen in section 3, redacted. No invented number is
  ever read as a measurement.
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

Introduce the running example properly, with context. An agent reads the morning's email and
produces a five-minute audio brief. The listener plays it while commuting or making coffee. They
are not at a laptop, and they will act on it later.

It has tools: search the inbox over a window, expand a thread to its full history, check the
calendar to know whether the meeting an email argues about has already happened, resolve who a
sender is, and write the finished script to a file. It decides what to fetch and how deep to go.
Those decisions happen before a word of the script is written, and they are the interesting part.

Show one real morning on screen: the source messages on the left, the produced script on the right.
One slide, real data, redacted. Everything after this point is easier once the room has seen the
artifact.

Failure modes we care about: an item that should have led buried in the middle, a claim the mail
does not support, a thread summarised as settled when it was not, and a script that is unusable in
audio because it reads out a list or a URL.

The corpus: **one listener, many mornings.** Vary the situation, not the person. A quiet inbox, a
crisis, a day that is all newsletters, a thread that resolves itself between its first and last
message, a meeting that has already happened by the time the brief plays.

Why one listener: an earlier corpus of ours crossed five personas with ten scenarios. When we
measured the judge's consistency on it, three of the four cases it kept changing its mind about
were the *same scenario* worn by different personas. The grid had bought fifty rows and ten
situations. Persona variation is cheap; situation variation is what finds the grey zone.

The important design choice: **we deliberately keep the failures.** Mornings the agent handled
badly are retained rather than regenerated. A corpus of successes teaches you nothing, and those
retained failures are what catches the judge out.

## 4. Cheap graders first (2 min)

Before any judge. Half of what makes a brief listenable is decidable by code: a regular expression
finds URLs, ticket numbers, and order identifiers, none of which survive being spoken aloud; a word
count checks the five-minute budget; a parser finds nested structure a listener cannot hold in
memory. And the state change is checkable directly, because either the script file exists or it does
not.

Rule: if code can grade it, never pay a model to. This is the highest-return hour in the whole
process and it is the section most evaluation talks skip entirely.

*Compress to 60 seconds if running long.*

## 5. Decomposing the judge (3 min)

"Is this a good brief?" is not alignable. It is several questions wearing one coat, and annotators
disagree with themselves on it. This is the grey zone from section 2, restated concretely.

We cut it into atomic rubrics: content selection, faithfulness, listenability, actionability. Each
has a narrower grey zone than the union did.

**We align one: content selection.** It has the widest grey zone and it is where the product
decisions live. The others are deferred, because aligning one rubric properly beats aligning four
thinly. Then we decompose *that one* further, because selection is still several judgements: is this
item newsworthy at all, is this thread ripe enough to mention, is a thread the listener is only
copied on their business, does automated mail count, and does the ordering put the most consequential
item first.

**The downstream medium writes half the rubric, and that is the slide to stop on.** Ask the room what
audio does to the output and they derive the rules with you. One pass and no scroll-back, so the ask
goes first. Eyes and hands busy, so no URLs and no identifiers. A linear medium, so no nesting and no
six-item list. A fixed budget, so coverage and depth are in direct conflict and the rubric has to say
which wins. None of those are facts about email. They are consequences of how the output is consumed,
and that is where evaluation criteria actually come from.

**The judge is reference-free, and here it has no choice.** There is no correct brief, and nobody can
write one, because writing it would mean settling every open question in the next section first. So
the judge gets the source messages, the tool calls the agent made, and the produced script, and it
decides whether the selection was defensible on that evidence. Show the line from the prompt:

> You have no reference brief, and none exists. Decide from the source messages and the agent's
> recorded tool calls whether the selection is defensible, and whether anything material to the
> listener was dropped.

In production there is never a reference. A judge that needs one is a test fixture, not an evaluator.

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

**6c. Audience places the boundary.** This is where the grey zone becomes concrete and the room
participates. Two cases, both content-selection calls, both of which split a room, and neither
settled by looking anything up.

*The thread you are only copied on.* Four messages arguing about a vendor renewal. No decision was
reached and no question is aimed at the listener. The brief includes one line: the vendor renewal is
still unresolved. Pass or fail? For pass: they want to know a decision they care about is stuck, and
one line is cheap. For fail: nothing is asked of them, nothing changed, and twenty seconds of a
five-minute budget went to something they cannot act on. Which reading is right depends on whether
the product is a news service or a to-do list. Somebody has to decide that on purpose.

*The inferred noun.* An email says "can you look at this before Thursday?" with a file attached
called `Q3-review-deck.pdf`. The brief says Priya needs the deck reviewed by Thursday. Faithful,
because the attachment name is evidence sitting right there? Or fabricated, because the sender never
said the word and the agent guessed what "this" meant? Move one detail and the room changes its mind.

Collect the split, then show our reading and where it was contested. This is the answer to the
question section 2 left open.

**6d. What the protocol finds, before any human label.** Two things.

First, an unaligned judge produces a number that looks like a result and is not one. Run it over a
corpus that contains conversations you deliberately kept because the agent handled them badly, and
watch how many of them it passes. The pass rate is a measurement of the judge, not of the agent, and
until it is aligned you cannot tell those apart.

Second, consistency. Ask the judge the same question eight times over at temperature 1 and see where
it changes its mind. Two things fall out. The rows it wavers on are the grey zone, located by the
judge itself rather than guessed at. And when the wavering rows cluster — when three of the four are
the same situation wearing different costumes — the measurement has found a corpus design flaw before
it found a judge flaw. That is what sent us back to section 3.

Then the limit, and say it plainly because it is the honest half. **Consistency is a ceiling, not
proof.** A judge can be wrong the same way every time and score perfectly here. Imagine it passes,
every time, a brief that reads out six items in a row, and every explanation says the same thing:
all the material items were covered. It is right about that. Nothing in the rubric says six items in
a row is unusable in audio, so it has no reason to object, and asking eight more times will never
reveal it. Consistency measurement finds what a judge is unsure about. It structurally cannot find
what it is confidently wrong about.

What does find it: reading what the judge says it believes. The explanations name the judgement it
keeps blessing, someone who has actually listened to a brief in a car recognises it as wrong, and one
correction covers every row that shares it. No reference answer is involved, which matters, because
here there is none to be had.

**6e. Where we actually are.** Zero human labels so far, and therefore no measured human agreement to
hold the judge against. What we have is the protocol and the judge's self-consistency map. Say it
plainly — the gap is the reason the talk exists.

## 7. Trajectory and state (2 min)

The dimensions that only appear once the system is an agent.

Replay recorded runs without re-invoking the agent. You judge the recorded artifact rather than a
fresh non-deterministic run, which is what makes agent evaluation reproducible at all.

State: assert the script file exists and holds what the agent claimed it wrote. Never ask a model
whether the agent did something you can check directly.

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
