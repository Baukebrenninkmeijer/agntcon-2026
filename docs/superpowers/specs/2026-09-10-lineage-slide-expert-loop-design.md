# Lineage Slide Expert Loop Design

**Date:** 2026-09-10  
**Status:** Approved through the brainstorming scratchpad

## Contract

This change serves the abstract's judge-alignment promise. Slide 3 shows that an agent cannot safely
learn from an untrusted judge. Slide 4 extends that picture to show the missing control: an expert
must also align the judge.

The change adds no slide and no speaking-time allocation. It does not change the running example,
evaluation criterion, or evidence.

## Current State

Slide 4 shows the progression from known-answer evaluation to human judgement and then to an LLM
judge. It closes with `The evaluator now needs its own evaluation.`

## Approved Interaction

Slide 4 has one click step.

- Before the click, the slide keeps its current composition.
- On click, the title, full-width lineage, and closing sentence move upward without becoming narrower.
- A large horizontal diagram rises from below while fading in.
- The movement reads as vertical reflow: the arriving diagram pushes the existing content upward.

The existing rule remains unchanged: clicks advance steps only in fullscreen mode. Keyboard
navigation continues to reveal the step in either mode.

## Approved Diagram

The diagram contains three outlined circular entities in one horizontal row:

`Agent` — `Judge` — `Expert`

Two opposing curved arrows connect Agent and Judge. A second pair connects Judge and Expert. The two
adjacent feedback loops share the judge. The arrows have no labels.

The diagram reuses slide 3's line weight, circle treatment, arrowheads, type, and teal colour. It
occupies most of the slide width. Its centerline sits about 30% above the bottom edge rather than in
the vertical middle.

## Layout and Motion

- Group the existing title, lineage, and closing sentence so one vertical transform moves them.
- Preserve their original horizontal size and spacing in both states.
- Place the hidden diagram below its final position with zero opacity.
- At step one, translate the existing group upward only far enough to clear the diagram.
- Translate the diagram into the lower portion of the slide and fade it in.
- Use the deck's existing easing and approximately half-second transition duration.
- Under `prefers-reduced-motion`, remove the travel while still changing the final positions and
  diagram visibility.

## Acceptance Criteria

- Slide 4 initially matches the current lineage slide.
- One forward step reveals Agent ↔ Judge ↔ Expert as two distinct horizontal loops.
- The existing title and lineage retain their full width and type scale.
- The loop diagram occupies most of the width and sits in the lower portion of the slide.
- The diagram does not overlap the lineage copy or slide counter.
- The reveal does not alter adjacent slides or navigation behavior.
- The source builds, passes Ruff and Python compilation, and produces no diff whitespace errors.
- Fresh renders of slide 4 before and after the reveal show no clipping or overlap at 2048×1152.

