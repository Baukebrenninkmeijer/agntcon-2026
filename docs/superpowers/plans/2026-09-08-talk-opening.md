# Plan: the opening of the PyData Amsterdam 2026 talk

Status date: 2026-09-08. Status: `VERIFIED` — both slides are built in `slides/build_deck.py` and
`abstract.md` / `outline-manual.md` carry the matching contract change. Evidence: Ruff clean, Python
compilation, 20-slide regeneration (18 before), `git diff --check` clean, and headless-Chrome renders
of slides 3 and 4 at 1280x720 with no clipping or overlap.

## What this serves in the contract

`abstract.md` allocates **3 minutes to "The evaluation gap"** and states the talk **is not a product
demo**. `outline-manual.md` opens on "How to evaluate an agentic system". The deck currently jumps
from the title slide straight into the two-answers comparison: there is no speaker introduction, no
Orq framing, and no roadmap. This plan adds those three things inside the existing 3-minute budget
and names what is displaced to pay for them.

## Research: how Bauke has opened talks before

Read from the earlier decks in `~/Developer` and from blog.baukebrenninkmeijer.nl/talks.

**Context is King — PyData Amsterdam 2025** (`pydata-2025-context-is-king/presentation.qmd`) uses
this order:

1. Title slide, image only, no bullets.
2. A single provocative claim on an otherwise empty slide: *"Your RAG Pipeline is Probably Overkill"*.
3. **The Problem That Started It All** — a real, named work problem (ESG emissions extraction from
   annual reports at a bank), three reasons the obvious approach failed, then the research question.
4. **Why This Matters to You** — three fragments, audience-facing, no speaker content.
5. **Who am I** — only now. A bio card with four checkmarks (Research Engineer @ orq.ai; CS @ Radboud;
   6 years data science @ ABN AMRO & ING; Organiser @ MLOps Community Amsterdam), a headshot, and
   then two joke portraits flown in as fragments.
6. **The Questions We Will Answer** — three numbered questions, revealed one at a time.

**A Developer's Guide to GenAI** (`developers-guide-to-genai/developers-guide-to-genai.qmd`) opens
the same shape at lower resolution: a "Start with why?" chapter slide, then one large claim
("GenAI will change everything"), then imagery — the outline slide is present but commented out.

Three properties are consistent across both, and are worth keeping:

- **The hook precedes the speaker.** The audience gets a claim and a real problem before they get a
  bio. The bio is slide 5, not slide 2.
- **Credibility is delivered as a list of places, not as a pitch.** Four lines, no paragraph. Orq.ai
  appears only as the employer line — neither deck has a company slide, a product screenshot, or a
  "what we do" beat.
- **The opening ends by naming the questions the talk answers**, so the audience knows the shape.

The blog reinforces the self-description to use verbatim: *AI Research Engineer at orq.ai, working on
AI agent infrastructure, LLM evaluation, and production AI systems*; prior years in Dutch banking
(ABN AMRO, ING); MSc CS/DS at Radboud with a GAN synthetic-data thesis that became `table-evaluator`;
co-organiser of MLOps Community Amsterdam.

## The plan

Four slides before the current slide 4 (the fifty-case review pool). Slides 1 and 2 already exist.

**1 · Title** — unchanged.

**2 · The hook.** Reuse the existing two-answers comparison as the provocation, which is what it
already is. Nothing to build. Spoken framing: both answers are correct; only one of them is useful;
nothing in a normal test suite separates them. Budget 45 s.

**3 · Who am I (new).** Port the bio-card layout from the 2025 deck into the current deck's visual
language: name, three lines, headshot. Radboud and `table-evaluator` are deliberately off the slide —
they do not buy credibility for an evaluation talk and they cost reading time.

- Research Engineer @ Orq.ai — agent infrastructure and LLM evaluation
- 6 years data science @ ABN AMRO & ING
- Organiser @ MLOps Community Amsterdam

Alongside the card, one short line explaining what Orq is, so the employer line is not a mystery:

> **Orq.ai** — a platform for building, shipping and evaluating LLM apps and agents. One gateway to
> every model, plus tracing, evaluators and experiments on top.

Spoken, that is two sentences and then the disclaimer that keeps the talk on the right side of the
abstract's "not a product demo": *"Orq is where teams build and run their LLM apps and agents — one
gateway to every model, with tracing and evaluation on top. That is where these numbers come from,
but everything in this talk works with any SDK and any test runner. I am showing you the method, not
the product."* No separate company slide, no product screenshot. Budget 30 s.

**4 · The questions we will answer (new).** Three, revealed one at a time, matched to the deck that
follows:

1. How do you get a first signal with no labels?
2. When can you trust an LLM judge instead of a human?
3. What do you evaluate in an agent that is not the final answer?

Budget 20 s.

Total added: ~50 s of new material across two new slides.

## What this displaces

The 30-minute budget is fixed, so the ~50 s is taken from section 5 ("Scaling: offline, online,
continuous", 4 min), specifically the automated-prompt-optimization beat that the abstract already
describes as "a brief look". Cut it to the single "What the agent learns from a failed eval" slide
and drop the spoken elaboration. `abstract.md` needs no edit — "a brief look" still holds. If the
prompt-optimization beat is instead kept in full, the roadmap slide (4) is the one to drop, and the
three questions become spoken over the who-am-I slide.

## As built

Slide 3 places the three bio lines and the Orq block in the left column and the headshot
(`slides/assets/headshot.jpg`, downscaled to 620 px and base64-embedded) on the right. Slide 4 reuses
the existing `.spine` component for the three questions. The prompt-optimization beat is the
displacement recorded in `abstract.md`; the "What the agent learns from a failed eval" slide stays.

## Open decisions for the speaker

1. Keep the 2025 deck's joke-portrait fragments on the bio slide, or drop them? They cost ~15 s and
   read as an in-joke to the MLOps Amsterdam crowd; PyData Amsterdam overlaps but is not the same room.
2. Is the Orq one-liner set on the bio slide, or spoken only over a card that just says "Orq.ai"?
3. Displace the prompt-optimization beat (recommended) or the roadmap slide?

## Acceptance evidence required before marking this `VERIFIED`

Regenerate the deck, confirm the new slide count, run Ruff and the Python compile check, run
`git diff --check`, and render the two new slides at 1280×720 in headless Chrome to confirm no
clipping or overlap — the same evidence every prior deck change in this repo recorded.
