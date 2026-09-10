# Speaker Slide Expert Loop Design

**Date:** 2026-09-10  
**Status:** Approved in conversation; awaiting written-spec review

## Contract

This change serves the abstract's judge-alignment promise. The previous slide shows that an agent
cannot safely learn from an untrusted judge. The speaker slide will extend that picture to show the
missing control: an expert must also align the judge.

The change adds no slide and no speaking-time allocation. It does not change the running example,
evaluation criterion, or evidence.

## Current State

Slide 3 shows a vertical Agent–Judge optimization loop with a broken signal path. Slide 4 introduces
the speaker with three short biography lines.

## Approved Interaction

Slide 4 has one click step.

- Before the click, the speaker introduction keeps its current composition.
- On click, the biography group moves upward into the upper portion of the slide.
- A horizontal diagram rises from below while fading in.
- The movement must feel like the arriving diagram pushes the existing content upward, rather than
  covering it.

The existing rule remains unchanged: clicks advance steps only in fullscreen mode. Keyboard
navigation continues to reveal the step in either mode.

## Approved Diagram

The diagram contains three outlined circular entities in one horizontal row:

`Agent` — `Judge` — `Expert`

Two opposing curved arrows connect Agent and Judge. A second pair of opposing curved arrows connects
Judge and Expert. Together they form two adjacent feedback loops with the judge as the shared entity.

The diagram has no arrow labels. Its line weight, circle treatment, arrowheads, type, teal colour, and
spacing follow the loop on slide 3. The expert loop is visually equal to the agent loop; hierarchy
comes from the left-to-right sequence, not from a new colour or larger shape.

## Layout and Motion

- Keep the speaker eyebrow, name, and biography unchanged.
- Group the speaker content so one transform moves it as a unit.
- Place the hidden diagram below the visible canvas position with zero opacity.
- At step one, translate the speaker group upward and translate the diagram into the lower half while
  fading it in.
- Use the deck's existing easing and approximately half-second transition duration.
- Disable transforms under `prefers-reduced-motion`, while still switching the diagram's visibility.

## Acceptance Criteria

- Slide 4 initially matches the current speaker slide.
- One forward step reveals Agent ↔ Judge ↔ Expert as two distinct horizontal loops.
- The diagram does not overlap the speaker copy or slide counter.
- The reveal does not alter the order or behavior of adjacent slides.
- Fullscreen mouse clicks and keyboard navigation retain their existing behavior.
- The source builds, passes Ruff and Python compilation, and produces no diff whitespace errors.
- Fresh renders of slide 4 before and after the reveal show no clipping or overlap at 2048×1152.

