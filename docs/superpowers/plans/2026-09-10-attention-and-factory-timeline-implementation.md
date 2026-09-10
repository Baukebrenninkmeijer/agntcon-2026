# Attention and Software Factory Timeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sharpen the human-attention, disagreement, grey-zone, and software-factory beats without adding a new argument or extending the talk.

**Architecture:** `slides/build_deck.py` remains the source of truth and regenerates `slides/pydata-2026.html`. The narrative mirror in `outline.md` and the living delivery plan change in the same commit as the deck.

**Tech Stack:** Python-generated HTML, CSS, inline SVG, vanilla JavaScript.

## Global Constraints

- Preserve the existing visual system, animation semantics, keyboard controls, and fullscreen-only mouse navigation.
- Keep slide 13 and the operating-modes slide unchanged.
- Add no factual claims, intermediate dates, or invented software-factory milestones.
- Keep the 30-minute contract time-neutral by replacing the old software-factory explanation with the new visual transition.

---

### Task 1: Refine human attention and the grey-zone loop

**Files:**
- Modify: `slides/build_deck.py`

**Interfaces:**
- Consumes: the existing `.statement`, `.grey-loop-stage`, and click-revealed `.case-proof` components.
- Produces: a two-level human-attention conclusion and a five-stage loop with larger titles and no stage descriptions.

- [x] **Step 1: Update the attention conclusion**

Replace the single `.price` line with a two-level block whose setup reads `The most valuable thing is` and whose orange emphasis reads `human attention.`.

- [x] **Step 2: Simplify the grey-zone stages**

Remove each stage `<p>` and increase `.grey-loop-stage h3` from `32px` to `38px`. Keep the numbers, return loop, held-out note, and case proof unchanged.

- [x] **Step 3: Regenerate and check copy**

Run `python3 slides/build_deck.py`. Expect the generated HTML to contain `human attention.` and no longer contain `Same frozen development cases`.

### Task 2: Increase the disagreement visual

**Files:**
- Modify: `slides/build_deck.py`

**Interfaces:**
- Consumes: `.gridwrap`, `.deck3d`, `.layer`, axis labels, and the existing click-state rotation.
- Produces: a larger initial 3-by-3 grid and a materially larger rotated 50-case stack.

- [x] **Step 1: Scale and reposition the grid**

Increase the layer square from `390px` to `460px`, center it with `left/top: -230px`, align the axis and repetitions labels to the new footprint, and increase the click-state scale from `.64` to `.76`.

- [x] **Step 2: Render both states**

Render the slide at 1600 by 900 before and after the click state. Adjust only position or scale if labels clip or the stack collides with the caption.

### Task 3: Add the software-factory transition

**Files:**
- Modify: `slides/build_deck.py`
- Modify: `outline.md`

**Interfaces:**
- Consumes: the deck's muted line, teal text, orange terminal marker, and mono-label vocabulary.
- Produces: a quiet timeline slide immediately before the inverted software-factory statement.

- [x] **Step 1: Add the timeline**

Add a full-slide `factory-era` composition with a horizontal line beginning beyond the left edge, a subtle fade over its earlier portion, and one orange terminal marker labelled `2026` and `Software Factory`. Do not add intermediate events or dates.

- [x] **Step 2: Remove the old explanation**

Delete `You cannot scale review. You can scale the thing that decides what is worth reviewing.` from the following slide while preserving its title, section label, and bar reveal.

- [x] **Step 3: Mirror the narrative**

Update `outline.md` so the new timeline is a visual transition inside the existing two-minute section and the removed explanatory sentence no longer appears.

### Task 4: Verify, document, and commit

**Files:**
- Modify: `slides/pydata-2026.html`
- Modify: `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

**Interfaces:**
- Consumes: the regenerated deck and fresh validation evidence.
- Produces: a reproducible deck artifact and accurate delivery handoff.

- [x] **Step 1: Run static checks**

Run `python3 -m py_compile slides/build_deck.py`, `ruff check slides/build_deck.py`, and `git diff --check`. Expect all commands to exit zero.

- [x] **Step 2: Verify the changed slides**

Render the attention, disagreement, grey-zone, timeline, and inverted statement slides at 1600 by 900. Inspect both click states for the disagreement and grey-zone slides. Confirm the deck contains 28 slides, windowed clicks do not navigate, keyboard navigation still works, and the CSS retains reduced-motion rules.

- [x] **Step 3: Record evidence**

Add the newest changelog entry and update any affected talk-delivery handoff text in `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`.

- [x] **Step 4: Commit the scoped files**

Stage only the implementation plan, `slides/build_deck.py`, `slides/pydata-2026.html`, `outline.md`, and the living delivery plan. Commit with a message describing the deck refinement.
