# Running example for the talk: the inbox brief

This file holds the worked example the talk uses on stage. It replaces the analytics agent as the
running example in the slides.

**Status: illustrative.** Nothing here is backed by a run. The transcripts, judge explanations, and
counts below were written to teach the method, not measured. The method itself, and the structural
findings the talk reports, come from the real alignment work on the analytics agent recorded in
[the session log](alignment-session-log.md). Keep that line clean on stage: describe the protocol
and the shape of what it finds, and never read an invented number as though it were measured. Where
a slide needs a count, say "in a run like this you typically see" or drop the number.

## Why this example and not the analytics agent

The analytics agent produced a real grey zone, and it turned out to be the wrong kind. The question
it raised was whether refunds are already subtracted inside the revenue column. That has one right
answer, written down in a data dictionary, and anyone who reads it agrees. Alignment was not needed
to settle it. Someone had to go look it up.

That is a knowledge gap, not a boundary. It undercuts the talk in two places. Section 2 closes on
"who decides where the boundary goes?", and the honest answer for the analytics case is that nobody
decides. Section 6 holds the judge to human agreement, and if two annotators disagree about refunds
one of them is simply wrong, so the agreement number measures schema literacy rather than a
contested boundary.

The inbox brief has the property the talk needs. Its hard rules are not facts about the world; they
are consequences of how the output gets consumed. Its open questions are genuine product decisions
where two careful people land differently and both can defend it.

## The task

An agent reads the morning's email and produces a five-minute audio brief. The listener plays it
while commuting or making coffee. They are not at a laptop, and they will act on it later.

## The agent

It has tools, so the trajectory material in the talk still applies:

- search and list the inbox over a time window
- expand a thread to its full message history
- look up the calendar, to know whether the meeting an email argues about has already happened
- look up a contact, to resolve who someone is
- write the script to a file, which is the state change worth asserting

It decides what to fetch, how deep to expand a thread, and what to leave out. The decisions are the
interesting part, and they happen before a single word of the script is written.

## The downstream requirements write the rubric

This is the beat the analytics example could not give. Ask the room what audio does to the output
and they will derive the rules with you:

- **One pass, no scroll-back.** The ask goes first. A brief that builds to the point has already
  lost the listener, because they cannot go back.
- **Eyes and hands busy.** No URLs, no order numbers, no ticket identifiers, no code. A string of
  characters is unusable in audio and the listener cannot write it down.
- **Linear medium.** No nesting, no "as shown above", no six-item list. Structure that a reader
  skims, a listener has to hold in memory.
- **Fixed budget.** Five minutes is roughly 750 words. Coverage and depth are in direct conflict,
  and the rubric has to say which wins.
- **Action happens later.** Anything needing a reply must be recoverable from memory: who, what,
  and by when, in a form the listener can act on an hour later.

Every one of those is a hard requirement derived from the medium, not a preference. They are the
part a rubric can state plainly. What follows is the part it cannot.

## The grey zones

These are the questions where two competent people disagree and the organisation has to choose.
They are the reason the alignment session exists.

1. **Report or interpret.** An email reads "let's circle back once the numbers land." Does the brief
   say that, or does it say the sender is stalling? Interpretation is more useful and less faithful.
2. **Threads with no decision.** Four people argued about a vendor renewal and reached nothing. Is
   an unresolved thread worth twenty seconds of a five-minute budget?
3. **Mail the listener is only cc'd on.** Context they would want, or someone else's business?
4. **Automated mail.** Newsletters, receipts, build notifications. One sentence, or silence?
5. **Advice.** Does the brief say what happened, or what the listener should do about it?
6. **Conflicting mail.** Two people state incompatible facts. Flag the conflict, or pick the one
   that looks right?

None of these has a lookup answer. Each is a product decision that changes what the thing is for.

## Decomposing the judge

"Is this a good brief?" is several questions wearing one coat, exactly as "is this correct?" was:

- **Content selection.** Did the right items make it in, and was anything material dropped?
- **Faithfulness.** Is every claim supported by the mail it came from?
- **Listenability.** Does it obey the constraints the medium imposes?
- **Actionability.** Can the listener act an hour later without opening a laptop?

Align one: content selection. It has the widest grey zone, it is where the product decisions live,
and the other three are narrower once it is settled. Then decompose that one further, because
selection is still several judgements: is this item newsworthy at all, is this thread ripe enough to
mention, is a cc-only thread the listener's business, does automated mail count as an item, and does
the ordering put the most consequential item first.

Listenability is worth naming as the cheap-grader section's example too. Half of it is deterministic:
a regular expression finds URLs and identifiers, a word count checks the budget, and a parser finds
nested structure. Never pay a model to check what code can check.

## The reference-free judge

Same principle as the analytics judge, and easier to justify here. There is no correct brief. Nobody
can write the reference, because writing it would require settling every question in the grey-zone
list first. So the judge gets the source emails, the tool calls the agent made, and the produced
script, and it has to decide whether the selection was defensible on the evidence it can see.

Prompt line to show on the slide:

> You have no reference brief, and none exists. Decide from the source messages and the agent's
> recorded tool calls whether the selection is defensible, and whether anything material to the
> listener was dropped.

## The audience moment

Two cases to put on screen for the room to vote on. Both are content-selection calls, both split a
room, and neither is settled by looking something up.

**Case one, the cc-only thread.** The listener is copied on a four-message argument about a vendor
renewal. No decision was reached and no question is aimed at them. The brief includes one line: "the
vendor renewal is still unresolved." Pass or fail?

The case for pass: the listener wants to know a decision they care about is stuck, and one line is a
cheap way to say so. The case for fail: nothing is being asked of them, no state changed, and twenty
seconds of a five-minute budget went to an item they can do nothing about. Both readings are
defensible. Which one is right depends on whether the product is a news service or a to-do list, and
that is a decision somebody has to make on purpose.

**Case two, the inferred noun.** An email says "can you look at this before Thursday?" with a file
attached named `Q3-review-deck.pdf`. The brief says "Priya needs the deck reviewed by Thursday."
Faithful, because the attachment name is evidence sitting right there? Or fabricated, because the
sender never said the word and the agent guessed at what "this" meant? Move one detail and the room
changes its mind, which is the point.

## The stable-and-wrong case

Worth keeping, because it is the real lesson from the analytics run and it transfers cleanly.

A judge can be perfectly consistent and perfectly wrong. Imagine it passes, every single time, briefs
that read out a list of six items in a row. Every explanation says the same thing: all the material
items were covered. And it is right about that, because coverage is what the rubric asked about.
Nothing in the rubric says that six items in a row is unusable in audio, so the judge has no reason
to object, and asking it eight times will never reveal the problem. Consistency measurement finds
what a judge is unsure about. It structurally cannot find what a judge is confidently wrong about.

What finds it: reading what the judge says it believes. The explanations name the derivation the
judge keeps blessing, someone who has actually listened to a brief in a car recognises it as wrong,
and one correction covers every row that shares it. That is the discovery move, and it needs no
reference answer, which matters because there is none to be had here.

## Grading the corpus

The corpus shape carries over unchanged: one listener, many situations. Vary the morning, not the
person. A quiet inbox, a crisis, a day that is all newsletters, a thread that resolves itself between
the first and last message, a sender who writes one line and a sender who writes nine paragraphs, a
meeting that already happened by the time the brief plays.

And keep the failures. A corpus of mornings the agent handled well teaches nothing.
