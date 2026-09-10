# Attention, Grey-Zone, and Software-Factory Slide Refinement

**Date:** 2026-09-10

## Scope

Refine four existing slides and add one transition slide. Leave the quality-control and operating-modes layouts unchanged.

## Approved design

### Human attention

Keep `But we are lazy` and its existing explanatory sentence. Replace the orphaned label with a two-level conclusion: `The most valuable thing is` as the smaller setup and `human attention.` as the large orange emphasis.

### Grey-zone loop

Remove the small explanatory text beneath all five stages. Increase the five stage titles by 20 percent. Preserve the stage numbers, return loop, held-out note, and click-revealed case strip.

### Disagreement visual

Increase the initial three-by-three judge grid. On the click state, enlarge the rotated fifty-case stack further while preserving its existing rotation, depth, measured colors, and reduced-motion behavior.

### Software-factory transition

Insert a quiet transition slide immediately before `Most software will ship without a human reading it.` A horizontal timeline enters from beyond the left edge so only its final portion is visible. Its terminal orange marker is labelled `2026` and `Software Factory`. Do not invent intermediate events or dates.

### Existing software-factory statement

Remove `You cannot scale review. You can scale the thing that decides what is worth reviewing.` Preserve the title and section label.

## Verification

- Regenerate the HTML from `slides/build_deck.py`.
- Render the changed slides at 1600 by 900 in their initial states.
- Render the disagreement and grey-zone slides after their click states.
- Confirm fullscreen click behavior, keyboard navigation, reduced-motion fallbacks, slide order, and absence of clipping.
- Run Python compilation, Ruff, and `git diff --check`.

## Scope check

The timeline introduces one new slide and no new factual claim. It visually establishes the software-factory endpoint already covered by the following slides. The other edits reduce text or increase the prominence of existing evidence.
