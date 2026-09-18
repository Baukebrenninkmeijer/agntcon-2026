# Conclusion verbs implementation plan

> **For agentic workers:** Use executing-plans for inline execution. Track steps below.

**Goal:** Implement approved conclusion option B in the existing deck.

**Architecture:** Keep the Python HTML generator and existing embedded fonts. Replace only conclusion markup and scoped styles; rebuild the single-file HTML.

**Tech Stack:** Python, HTML, CSS.

## Constraints

Use FIND., DECIDE., GUARD. in orange, deep teal, and ink respectively. Pair each with the exact existing takeaway. Show all rows immediately. Preserve 30 slides and the one-minute conclusion. Specification: `docs/superpowers/specs/2026-09-18-conclusion-verbs-design.md`.

## Task 1: Conclusion layout

- [x] Replace the indented paragraphs in `slides/build_deck.py` with three semantic rows: a strong verb and a paragraph containing a lead span plus a line break and the existing completion.
- [x] Scope layout to `.conclusion-slide`. Use top alignment, 84px heading, three 248px rows, 45% verb column, 176px verbs and 46px supporting text; thin neutral top borders separate the rows.
- [x] Update `outline.md` to describe the approved composition and mark the spec approved for build.

## Task 2: Integrate and verify

- [x] Complete the previously requested slide-27 image swap using the already generated `divine-hand-takes-the-wheel-renaissance-ai-founders.png`; record it in the outline and delivery log.
- [x] Run `uv run python slides/build_deck.py`, `uv run ruff check slides/build_deck.py`, and `git diff --check`.
- [x] Inspect generated slide count, conclusion text, and selected embedded image. Check layout in a browser when available; explicitly record any visual verification limitation.
- [x] Record fresh evidence in the living delivery plan and commit only the intended slide, asset, and documentation changes.

Execution evidence: deck build, Ruff, generated content/image inspection, and diff check passed. Fresh browser capture remains unavailable following the earlier access restriction; inspect slides 27–28 in the presentation preview. Changes remain on the delivery branch.
