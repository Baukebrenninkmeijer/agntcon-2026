# Running example for the talk: the newsletter podcast

This file holds the worked example the talk uses on stage.

The pipeline is real and it runs weekly in production on my home server. The run captured
here is execution 9308 from 6 September 2026. Its artifacts are in
[`examples/podcast-run-2026-09-06/`](examples/podcast-run-2026-09-06/): the source messages, the
intermediate digest, the narration draft, the delivered dialogue script, and both prompts that
produce it.

**What is real and what is not.** The pipeline, the run, and every artifact on the slides are real.
The judge and the alignment session for this task are illustrative unless a slide says otherwise;
the multi-judge agreement run is real and is described where it appears. The structural findings the
talk reports about consistency and blind spots come from a real alignment run on a different agent,
recorded in [the session log](alignment-session-log.md). Keep that line clean on stage.

## A boundary, or a gap?

Not every disagreement needs an alignment session, and the captured run carries one of each.

Alex opens on "seventy-two point six percent on OSWorld two point zero". Two reviewers can disagree
about whether that is right, and the disagreement dies the moment either of them opens the digest,
where the figure is written down. That is a knowledge gap. Someone has to go and read.

Nadia says an agent "spends five hundred dollars attempting to click a missing button". There is
nothing to open. The number is in no source, the debate format asked for concrete jabs, and whether
audio may carry an invented figure to make a point is a product decision two careful people land on
differently. That is a boundary. Someone has to go and decide.

Only the second kind is what alignment is for. Sorting them first is the cheapest step in the whole
process.

## The pipeline

A weekly job reads the AI newsletters that accumulated in an inbox, condenses them, rewrites the
result as spoken text, turns that into a two-host episode, and delivers the audio over Telegram. The
listener plays it on a walk. Nobody reads anything.

In the captured run it ingested ten newsletters totalling 310,647 characters, produced a 2,522
character digest carrying eight topics, and delivered a 2,514 character two-host script in which
four of those topics survive.

**Two prompts write the episode, and the first one's output is never heard.** The first prompt
produces a single-voice narration draft. That draft is thrown away as soon as it is written: a
second prompt treats it as source material and rewrites it as a conversation between two hosts. The
artifact that gets evaluated is the output of a prompt nobody thinks of as the writer.

## The show is different every week, on purpose

The pipeline picks the format, the two personas, their voices, the opener, the sign-off, the
target length and the sampling temperature from a seeded configuration engine. The seed is derived
from the content and the current date, so a retry on the same day is reproducible and a new day
rolls the variety forward.

The captured run drew `debate`, Alex and Nadia, four minutes, temperature 0.9. The run seven minutes
earlier drew `critique` at five minutes. **The target output is deliberately unstable**, which makes
"is this the correct episode?" a question with no fixed answer, and forces every rubric to be about
defensibility rather than about matching.

## What the medium decides, and what it does not

The medium settles a set of questions outright: one pass with no scroll-back, so the consequential
item goes first; no URLs or unspoken version strings, because the listener cannot write anything
down; a linear form, because structure a reader skims is structure a listener has to hold; and a
fixed budget, four minutes against 310,000 characters of input.

What the medium does not settle is everything interesting.

## The grey zones, visible in the real script

**Coverage collapse.** The digest carries eight topics across four sections. The delivered script
covers four of them and drops the rest entirely: Meta's Muse Spark, the Z.ai model identification,
World Labs Atlas, the NYC schools ban, and every item under "worth exploring". Nobody decided that.
The debate format did, and the format was chosen by a seeded random number.

**The cleared cliché.** The script says "a complete paradigm shift" about a benchmark score. The
production slop filter would have caught that vocabulary, except `paradigm` sits on a hand-written
exclusion list with the justification "legitimate in a senior-engineering podcast". The boundary is
a comment in source control, and nobody has revisited it.

**Invented specifics.** "Spends five hundred dollars attempting to click a missing button" and "step
forty-two of a three-day job" appear nowhere in the digest or the sources. They are rhetorical
illustration, and the debate format explicitly asks for concrete jabs. The defensible rule: an
invented figure must be marked as hypothetical, because audio has no citation channel and the
listener cannot tell reporting from illustration.

**Contradicting prompts.** The first prompt says to add a greeting at the beginning and a
sign-off at the end. The second prompt's structural rules ban template sign-offs outright. The
delivered script opens mid-sentence on an ellipsis and ends on a host saying what she is watching
next. Two prompts in one pipeline, in direct conflict, and the second one won.

**A pass worth showing.** "Seventy-five percent discount on cache reads" and "net execution costs
jumped twenty percent" both survive correctly from the digest. Show a pass next to the failures.

## The filter that already exists

`slop_filter.validate` is a real deterministic grader in production. It checks a script against
about 150 banned words and 40 banned phrases, two structural regexes, four sign-off tells, a minimum
length, the presence of both speakers, and a "too clean" rule that fires when a format demanding
interruptions produces no ellipses or dashes. It is wired into a refine loop: on failure the issues
are fed back as revision notes and the script is regenerated, up to two retries, shipping the
cleanest draft either way and logging a Sentry warning if issues remain. It fired on the captured
run — `Refine pass 0: 2 issues; regenerating`.

Two things about it drive the talk. The banned lists are injected into the generation prompt **and**
used as the grader, so the check is not independent of the instruction. And the lexicon was vendored
once from a skill file and has no re-cut schedule, so it encodes one moment in a moving target: it
covers the 2023-24 vocabulary, has no rule for the em dash, and knows nothing about the 2026
"claudish" tells. A judge aligned in 2024 is misaligned in 2026 without anyone touching it.

## Decomposing the judge

"Is this a good episode?" is several questions wearing one coat: content selection, faithfulness,
listenability, and actionability. The talk aligns one of them and says why. Listenability is the
cheap-grader half — a regular expression finds URLs and unspoken version strings, a word count
checks the budget — and is exactly where the deterministic filter already lives.

## The reference-free judge

Nobody can write the correct episode; writing it would mean settling every question above first, and
the show format changes weekly anyway. So the judge gets the source newsletters, the digest and the
delivered script, and decides whether the result is defensible on that evidence. In production there
is never a reference. A judge that needs one is a test fixture, not an evaluator.

## The stable-and-wrong case

A judge can be perfectly consistent and perfectly wrong. Consistency measurement finds what a judge
is unsure about; it structurally cannot find what a judge is confidently wrong about. What finds it
is reading what the judge says it believes, recognising the belief as wrong, and correcting every
row that shares it. No reference answer is involved, which matters, because here there is none.

## The corpus

One listener, many weeks. Vary the situation, not the person: a week with one enormous story, a week
with nothing, a week where two newsletters contradict each other, a week where the same launch is
covered five times, a week where an item is already stale by the time the audio plays.

And keep the failures. A corpus of weeks the pipeline handled well teaches nothing.
