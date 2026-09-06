# Running example for the talk: the newsletter podcast

This file holds the worked example the talk uses on stage. It replaces the analytics agent as the
running example in the slides.

The pipeline is real and it runs weekly in production, in n8n on the home server. The run captured
here is execution 9267 from 4 September 2026. Its artifacts are in
[`examples/podcast-run-2026-09-04/`](examples/podcast-run-2026-09-04/): the source messages, the
intermediate digest, the delivered script, and the production prompt that produces it.

**What is real and what is not.** The pipeline, the run, and every artifact on the slides are real.
The judge, the rubrics, and the alignment session for this task are not: they are written to teach.
The structural findings the talk reports come from a real alignment run on a different agent,
recorded in [the session log](alignment-session-log.md). Keep that line clean on stage. Show the
real artifacts, describe the protocol, and never read an invented number as a measurement.

## Why this example and not the analytics agent

The analytics agent produced a real grey zone, and it turned out to be the wrong kind. The question
it raised was whether refunds are already subtracted inside the revenue column. That has one right
answer, written down in a data dictionary, and anyone who reads it agrees. Alignment was not needed
to settle it. Someone had to go look it up.

That is a knowledge gap, not a boundary, and it undercuts the talk in two places. Section 2 closes
on "who decides where the boundary goes?", and for the analytics case the honest answer is that
nobody decides. Section 6 holds the judge to human agreement, and if two annotators disagree about
refunds one of them is simply wrong, so the agreement number measures schema literacy rather than a
contested boundary.

The podcast has the property the talk needs. Its hard rules are consequences of how the output is
consumed, not facts about the world. Its open questions are product decisions where two careful
people land differently and both can defend it.

## The pipeline

A weekly job reads the AI newsletters that accumulated in an inbox, condenses them, rewrites the
result as spoken text, sends that to a text-to-speech service, and delivers the audio over Telegram.
The listener plays it on a walk. Nobody reads anything.

In the captured run it ingested ten newsletters totalling 310,647 characters, produced a 2,600
character digest, and turned that into a 535 word script, about three and a half minutes of audio.
That compression ratio is the whole problem in one number: 99.8 percent of the input does not
survive, and every rubric question is a question about what should have been in the surviving 0.2
percent.

## The production prompt is the argument

Show [the Podcastify prompt](examples/podcast-run-2026-09-04/podcastify-prompt.md) on a slide as it
runs, and let the room read it. It says to convert dates into spoken form, replace bullet points
with transitions, emit one continuous text with no paragraph breaks, and include no markdown, no
speaker names, no timestamps, and no stage directions like `[pause]`.

Every one of those rules exists because the output is spoken. None of them is a fact about email.
And nothing in the pipeline checks any of them. That is the honest picture of how most LLM features
ship, it is on screen in the speaker's own production code, and it sets up both the cheap-grader
section and the judge.

The delivered script shows the rules being followed. It says "G P T six Astra", "Claude Fable five
point one", "twenty-five cents per million tokens", and "Friday, September fourth, twenty
twenty-six". A reader would find that text bizarre. A listener needs every bit of it.

## What the medium decides, and what it does not

The medium settles a set of questions outright, and these are the rules a rubric can state plainly:

- **One pass, no scroll-back.** The consequential item goes first. A script that builds to its point
  has lost the listener, who cannot go back.
- **Eyes and hands busy.** No URLs, no identifiers, no model version strings left unspoken. The
  listener cannot write anything down.
- **A linear form.** No nesting, no "as listed above", no long enumerations, because structure a
  reader skims is structure a listener has to hold in memory.
- **A fixed budget.** Three and a half minutes against 310,000 characters of input. Coverage and
  depth are in direct conflict and something has to say which one wins.

What the medium does not settle is everything interesting.

## The grey zones, visible in the real script

Each of these is a real property of the captured run, so the slide can quote the artifact rather
than a hypothetical.

**Coverage against budget.** The script carries almost the entire digest: four model launches,
three action items, three projects to explore, and the hardware section. Nothing was cut. Is total
coverage the goal for a three minute brief, or should the thing have picked two stories and dropped
the rest? Both are defensible products and they need different rubrics.

**Editorial colour.** The digest is neutral. The script calls it an "UNBELIEVABLE week", describes
the cybersecurity threshold as "a major milestone for agent capability", calls safety interventions
"frustrating", and reassures the listener with "do not worry". None of that came from the source.
It is also exactly what the production prompt asked for, because the prompt demands an engaging
conversational tone. So the pipeline is compliant with its spec and unfaithful to its input at the
same time. Two rubrics in direct conflict, and the room has to pick.

**Lost attribution.** The digest carries numbered citations, and the script drops them, correctly,
because reading footnote markers aloud is absurd. But now no claim is attributable. Does
faithfulness in audio require saying "according to AINews", at a cost of several seconds per claim,
or is dropping attribution the right call for a personal brief?

**The list the medium forbids.** Near the end the script says there are three standout projects, and
then reads three in a row. The prompt banned bullet points and got prose that is still a list. A
rubric that only bans the formatting misses this entirely.

**A pass worth showing.** The dollar figure survives correctly as "twenty-five cents per million
tokens". Show it next to the failures, because a rubric that only ever fires on problems teaches the
room nothing about where the boundary is.

## Decomposing the judge

"Is this a good episode?" is several questions wearing one coat:

- **Content selection.** Did the right items survive the cut, and was anything material dropped?
- **Faithfulness.** Is every claim supported by the newsletters it came from?
- **Listenability.** Does it obey the constraints the medium imposes?
- **Actionability.** Can the listener act on it later without a laptop?

Align one: content selection. It has the widest grey zone, it is where the product decisions live,
and the others are narrower once it is settled. Then decompose that one further, because selection is
still several judgements: is an item newsworthy at all, does an action item belong in a news brief,
do three "worth exploring" links earn their forty seconds, and does the ordering put the most
consequential story first.

Listenability is the cheap-grader example. Half of it is decidable by code: a regular expression
finds URLs and unspoken version strings, a word count checks the budget, and a scan finds the
markdown the prompt forbade. Never pay a model to check what code can check.

## The reference-free judge

Nobody can write the correct episode. Writing it would mean settling every question above first. So
the judge gets the source newsletters, the intermediate digest, and the delivered script, and it
decides whether the selection was defensible on that evidence.

Prompt line for the slide:

> You have no reference episode, and none exists. Decide from the source messages and the
> intermediate digest whether the selection is defensible, and whether anything material to the
> listener was dropped.

In production there is never a reference. A judge that needs one is a test fixture, not an evaluator.

## The stable-and-wrong case

This is the real lesson from the analytics run and it transfers cleanly, so keep it.

A judge can be perfectly consistent and perfectly wrong. Suppose it passes, every single time, the
three-projects-in-a-row passage, and every explanation says the same thing: all the material items
were covered. It is right about that. Nothing in the rubric says three items in a row is unusable in
audio, so it has no reason to object, and asking it eight more times will never reveal the problem.
Consistency measurement finds what a judge is unsure about. It structurally cannot find what a judge
is confidently wrong about.

What finds it: reading what the judge says it believes. The explanations name the judgement it keeps
blessing, someone who has actually listened to the episode on a walk recognises it as wrong, and one
correction covers every row that shares it. No reference answer is involved, which matters, because
here there is none to be had.

## The corpus

One listener, many weeks. Vary the situation, not the person. A week with one enormous story, a week
with nothing, a week where two newsletters contradict each other, a week where the same launch is
covered five times, a week where an item is already stale by the time the audio plays.

And keep the failures. A corpus of weeks the pipeline handled well teaches nothing.
