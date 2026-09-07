# The story

*Previous version preserved at [`story-outline-pre.md`](story-outline-pre.md) for comparison.*

## The claim

An evaluation is a set of judgement calls someone made. Until you check that those calls are the
ones you actually meant, every number the evaluation produces is measuring somebody's unexamined
afternoon. **Aligning the evaluator is the work.** Nothing downstream — improving the agent, closing
the loop, comparing two versions — is worth anything before it.

You end up needing alignment from three directions, and the talk hits all three:

- **You are writing an evaluator for the first time.** "Is this a good episode?" is four questions
  in a coat, and nobody has decided what passing means.
- **You are moving off a deterministic check.** Regex and word lists were never the rubric; they
  were the part of the rubric that happened to be expressible in code.
- **Your evaluator was aligned once and the world moved.** A judge aligned in 2024 is misaligned in
  2026 without anyone touching it.

Working title: *Who Decides What Passes?*

## The arc

**1. Cold open — the sentence that shipped.** On screen, from a real episode delivered last week:
*"seventy-two point six percent on OSWorld two point zero is a complete paradigm shift."* A
production filter checked that script and passed it. Did the check fail? Hold the question.

One line of standing, then move: I build evaluation infrastructure at Orq and watch this fail across
a lot of customers. No product, no UI, all night.

**2. The running example.** A weekly job turns ten AI newsletters — 310,647 characters — into four
minutes of audio delivered over Telegram. My pipeline, in production for months. Nobody reads
anything. Play four seconds of it. Two facts drive everything after:

- **The target is unstable by design.** Format, hosts, voices, length and temperature are drawn from
  a seeded engine. There is no correct episode to match against — only defensible ones.
- **Almost nothing is checked**, and what is checked is checked by a word list.

**3. Why the judge exists at all.** Labels got cheap to start with — thousands, then hundreds, then
a few. The need to evaluate never moved. One slide, one breath, keep going.

**4. The grey zone.** Every evaluation has a band where reasonable people disagree, and several
defensible lines run through it. Alignment is what turns them into one line. So: who decides where
the line goes?

**5. The cheap grader, and where it stops.** Production already has a deterministic filter: banned
words, banned phrases, structural tells, a refine loop that regenerates on failure. It fires on the
captured run, and all six episodes ship with zero residual issues. Never pay a model to check what
code can check.

But "the filter passes" is not "the episode is good", and the gap has three separate causes, which
is the argument of the talk in one slide:

- **It was never the rubric.** The list encodes the part of the judgement that could be written as
  string matching. The questions that matter — did the right topics survive, may a host invent a
  figure to make a point — were never expressible, so they were never checked.
- **The check is not independent of the instruction.** The banned list is injected into the
  generation prompt *and* used as the grader. The writer holds the answer key, so a pass is evidence
  about compliance, not about the writing.
- **It was cut once and never re-cut.** It catches the 2023-24 vocabulary, has no rule for the em
  dash, and knows nothing about the 2026 tells people now call **claudish**. Show the three eras and
  ask the room which era their own filters are from.

Moving to an LLM judge does not solve any of these by itself. It just moves the judgement calls
somewhere you can argue with them — which is the point, and the reason alignment comes next.

**6. The reveal — the rubric lives in a code comment.** Back to the opening sentence. Put the vote
to the room: violation, or fine? State both defensible readings out loud first, count hands aloud.

Then the reveal: `paradigm` was removed from the banned list by hand, in a code comment, with a
justification — *"legitimate in a senior-engineering podcast"*. That comment **is** the rubric. It
was written on one afternoon by one person and nobody has revisited it since. Everything that
shipped after was measured against a judgement call nobody remembers making.

(If the room votes lopsided: *"one person disagreed — and that person is the one who shipped it."*)

**7. So you need a judge you can hold to account.** Binary pass/fail plus a written critique; the
critique is the asset, the label is an index into it. A scale lets the annotator sit at 3. Treat the
judge like an annotator you hired: low agreement means the guideline is unclear, not that the
annotator is stupid. Iterate on disagreement patterns, never single rows. The guideline you converge
on becomes the judge prompt. Dev/test split on the evaluation itself — that part needs real human
annotations, and it is the ideal-world version.

**8. Consistency is not correctness.** A judge wrong the same way every time scores perfectly on
stability. The digest carried eight topics; the episode covers four and the rest vanish without a
word. A judge can pass that every time, and be right every time about what it did look at, because
nothing in the rubric says silent coverage collapse is a fault. Repeatability finds what a judge is
unsure about. It structurally cannot find what it is confidently wrong about.

What finds it is reading what the judge says it believes, recognising the belief as wrong, and
correcting every row that shares it. Say plainly: in a reference-free setting we have not yet
demonstrated this catch on the podcast judge — the case we have came from an agent with an oracle to
sweep against.

**9. What "aligned" is measured against.** Not a number borrowed from someone else's benchmark. Hold
the judge to an adjudicated human consensus, not to any single annotator, and report the **false
pass rate separately** — the error is asymmetric, because a false pass ships. Published
human-agreement rates describe the *shape* of the problem on a different task; they are not our
ceiling and they do not go on a slide as one.

**10. Where the judges disagree.** Same episodes, same rubric, three different models — one of which
wrote the episodes, which is the self-preference check. The disagreements are the work; everything
they agree on needs no attention. Show the shape of the disagreement, not invented numbers.

**11. Agent-only dimensions.** One sentence: replay the recorded run rather than re-invoking the
agent, assert state with code rather than with a model, and separate capability (pass@k) from
reliability (pass^k). Pointer to the repo, not a slide each.

**12. Close.** The grey zone does not go away — locate it on purpose, start small, validate small
components, then widen. And the last thing on screen is the code comment, with the date it was
written. Somebody's unrevisited afternoon is still deciding what ships.

## What the audience should leave with

1. Aligning the evaluator is the work. Validate it before you trust a single number it produces.
2. Your rubric is wherever the last judgement call was written down — often a code comment nobody
   has revisited.
3. Cheap deterministic checks first, and know what they are not checking. A word list is the
   expressible fraction of a rubric, never the rubric. Never let the grader share a list with the
   generator.
4. Alignment is needed at three moments: writing an evaluator, replacing a deterministic one, and
   whenever the world moves under one you already had.
5. Consistency is a ceiling, not proof. Read the critiques.

## Honesty constraints on stage

The pipeline, the run and every artifact shown are real. The judge and its alignment session for
this example are illustrative and are labelled as such. No published benchmark number is presented
as our measurement, and no invented number is ever read as one. Where a claim is unevidenced in the
reference-free setting, say so at the mic. Ship a repo link carrying the judge prompt, the corpus
spec and the replay invocation.

## Open before the deck freezes

- The multi-judge run is still labelled real with no artifact in the repo. Ship the agreement data
  or drop the label.
- All measured numbers to date come from a different agent than the running example. Either run one
  real alignment iteration on the podcast judge, or say openly which half of the talk the evidence
  belongs to.
- The critique-reading method is O(n) human attention. State the sampling strategy at scale, or
  scope the claim to small-corpus alignment.
