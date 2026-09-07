# The story

## The claim

You cannot use evaluations to improve an agent until the evaluation itself is aligned. An unaligned
judge optimises the agent toward the judge's own mistakes.

## The arc

**1. Where this started.** We wanted to close the loop: feed judge critiques back into the agent's
prompt and let it improve itself. It works, but only if the judge can be trusted. We got stuck on
the signal, not the optimisation.

**2. We have been here before.** Supervised learning needed thousands of labels, transfer learning
needed hundreds, language models need a few or none. The cost of *getting started* collapsed. The
need to *evaluate* never moved. Agents make it worse: there are now two lifecycles, and the
evaluation loop has to mature first.

**3. The grey zone.** Every evaluation has one — a band of cases where reasonable people disagree.
You can draw several defensible boundaries through it. Alignment is the process that turns them into
one line. So: who decides where the line goes?

**4. Not every disagreement is a grey zone.** An analytics agent subtracted refunds twice, and two
reviewers disagreed about whether that was wrong. It was not a boundary — the answer was in the data
dictionary, and one reviewer had read it. A gap closes when someone looks it up. A boundary has to be
decided. Only one of them needs alignment. *(This is why the running example changed.)*

**5. The running example.** A weekly job turns ten AI newsletters (310,000 characters) into four
minutes of audio delivered over Telegram. Nobody reads anything. Three facts about it drive
everything after:

- **Two prompts write the episode, and only one is visible in the workflow.** The visible one
  produces a narration draft nobody ever hears; a downstream service rewrites it as a two-host
  conversation.
- **The target is unstable by design.** Format, hosts, voices, length and temperature are drawn from
  a seeded engine. There is no "correct episode" to match against — only defensible ones.
- **Almost nothing is checked**, and what is checked is checked by a word list.

**6. The cheap grader, and where it stops.** Production already has a deterministic filter: banned
words, banned phrases, structural tells, a refine loop that regenerates on failure. It fires. Never
pay a model to check what code can check. But two things break it. The banned lists are injected
into the generation prompt *and* used as the grader, so the check is not independent of the
instruction. And the list was cut once and never re-cut: it catches the 2023-24 vocabulary, has no
rule for the em dash, and knows nothing about the 2026 tells people now call "claudish". **A judge
aligned in 2024 is misaligned in 2026 without anyone touching it.** Alignment is maintenance, not a
milestone.

**7. Your turn.** The delivered episode calls a benchmark score "a complete paradigm shift". The
filter cleared it — because someone removed `paradigm` from the banned list by hand, in a code
comment, with a justification. That comment *is* the boundary. Nobody has revisited it. Ask the room
to vote before revealing it.

**8. So you need a judge.** Binary pass/fail plus a written critique; the critique is the asset. A
scale lets the annotator sit at 3. Treat the judge like an annotator you hired: low agreement means
the guideline is unclear, not that the annotator is stupid. Iterate on disagreement patterns, never
single rows. The guideline you converge on becomes the judge prompt.

**9. Agreement is the ceiling, not the target.** Ground truth is one annotator's opinion. Humans
agree with each other about 81% of the time; GPT-4 agreed with humans 85% of the time on the same
comparison. A judge at the human agreement rate is *at* the ceiling. Chasing the last 15% is chasing
label noise.

**10. What the judge cannot tell you.** Consistency is not correctness. A judge that is wrong the
same way every time scores perfectly on stability. Measuring repeatability finds what a judge is
unsure about; it structurally cannot find what a judge is confidently wrong about. What finds it is
reading what the judge says it believes.

**11. Where the judges disagree.** Same episodes, same rubric, three different models — one of which
wrote the episodes. The disagreements are the work. Everything the models agree on needs no
attention.

**12. Agent-only dimensions.** Replay the recorded run; never re-invoke the agent to judge it. Assert
state with code, not with a model. pass@k for capability, pass^k for reliability.

**13. Close.** The grey zone does not go away. Locate it on purpose. Start small, validate small
components, then increase scope.

## What the audience should leave with

1. Validate the evaluator before you trust anything it says about the agent.
2. Most "disagreements" are knowledge gaps. Find out which kind you have before you run an alignment.
3. Human agreement is the ceiling. Stop optimising past it.
4. Cheap deterministic checks first; a model only for what code cannot decide.
5. Alignment decays. Re-cut it, or it silently stops measuring what you meant.

## Honesty constraints on stage

The pipeline, the run and every artifact shown are real. The judge and its alignment session for
this example are illustrative, except the multi-judge agreement run, which is real and labelled as
such. Findings about consistency and blind spots come from a real alignment run on a different
agent. No invented number is ever read as a measurement.
