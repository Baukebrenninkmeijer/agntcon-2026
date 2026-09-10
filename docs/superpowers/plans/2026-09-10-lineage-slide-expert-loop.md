# Lineage Slide Expert Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one on-click reveal to slide 4 that extends the evaluation lineage with a large horizontal Agent–Judge–Expert feedback diagram.

**Architecture:** Keep the self-contained HTML deck generator as the single source. Wrap slide 4's existing content in one transformable group, add one inline SVG for the new diagram, and drive both through the deck's existing `data-steps` / `data-step` state mechanism.

**Tech Stack:** Python-generated HTML, CSS transitions, inline SVG, headless Chrome rendering

## Global Constraints

- Preserve the initial appearance of slide 4.
- Preserve the existing content's full horizontal width and type scale.
- Keep the diagram unlabeled except for the three entity names.
- Keep non-fullscreen mouse clicks inert and retain keyboard navigation.
- Add no slide and no new dependency.

---

### Task 1: Add and verify the lineage reveal

**Files:**
- Modify: `slides/build_deck.py`
- Regenerate: `slides/pydata-2026.html`
- Modify: `outline.md`
- Modify: `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

**Interfaces:**
- Consumes: the deck's existing `data-steps="1"` and `.slide[data-step="1"]` convention
- Produces: slide 4 with a stable initial state and one expert-loop reveal state

- [x] **Step 1: Add the slide state and content groups**

Change slide 4 to `section class="slide lineage-slide" data-steps="1"`. Wrap its existing heading and
lineage SVG in `<div class="lineage-content">...</div>`. Add a sibling inline SVG with class
`lineage-loops`, three circles named Agent, Judge, and Expert, and two pairs of opposing curved teal
arrows.

- [x] **Step 2: Add the transitions**

Add CSS that leaves `.lineage-content` unchanged at step zero, translates it upward at step one, and
brings `.lineage-loops` from below the canvas to a final centerline about 30% above the bottom. Keep
the diagram nearly full width. Add a `prefers-reduced-motion` rule that removes transition travel.

- [x] **Step 3: Regenerate and run static checks**

Run:

```bash
uv run ruff check slides/build_deck.py
uv run python -m py_compile slides/build_deck.py
uv run python slides/build_deck.py
git diff --check
```

Expected: Ruff reports `All checks passed!`, Python compilation exits zero, the generator writes
`slides/pydata-2026.html`, and the diff check exits zero.

- [x] **Step 4: Render both states**

Open slide 4 in an isolated headless-Chrome profile at 2048×1152. Capture step zero, send one forward
keyboard event, and capture step one. Inspect both images for full-width lineage content, correct
vertical movement, a large low-positioned two-loop diagram, and no clipping or overlap.

- [x] **Step 5: Synchronize narrative and delivery status**

Update `outline.md` to describe the click reveal after the lineage explanation. Add fresh validation
evidence and the next handoff to the living delivery plan. Mark the implementation verified only
after reviewing both renders.

- [x] **Step 6: Commit the implementation**

```bash
git add slides/build_deck.py slides/pydata-2026.html outline.md \
  docs/superpowers/specs/2026-09-10-lineage-slide-expert-loop-design.md \
  docs/superpowers/plans/2026-09-10-lineage-slide-expert-loop.md \
  docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "slides: reveal expert alignment loop"
```

Expected: one commit containing the reviewed design correction, implementation, generated deck,
outline, and delivery evidence.

## Completion Evidence

Implemented on 2026-09-10. Ruff, Python compilation, deck regeneration, and `git diff --check`
passed. Fresh 2048×1152 headless-Chrome renders verified slide 4 before and after one forward step.
The initial state retains the prior composition. The reveal keeps the lineage full-width, clears the
closing sentence, and places the large two-loop diagram in the lower portion without clipping or
overlap.
