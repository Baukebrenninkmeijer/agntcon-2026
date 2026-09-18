# Conclusion slide: FIND. DECIDE. GUARD.

## Selected design

Bauke selected option B in the brainstorming scratchpad: three oversized verbs paired with the existing conclusion. This replaces the progressively indented lines on slide 28, “The evaluation flywheel.”

## Composition

Keep the CONCLUSION eyebrow and “The evaluation flywheel” heading. Below them, use three equal horizontal rows with fine neutral dividing rules. Each row has a large verb on the left and two lines of supporting text on the right:

| Verb | Supporting text | Verb colour |
|---|---|---|
| FIND. | Judge disagreement / directs attention. | Orange, `--orange-dark` |
| DECIDE. | Human judgement / sets the boundary. | Deep teal, `--teal-deep` |
| GUARD. | The resulting eval / guards every change. | Dark ink, `--ink` |

Use the deck's embedded Kurrent typography. Give the verbs roughly 45% of the content width and align all supporting text to the same left edge. Keep generous separation between DECIDE. and its supporting text. The first supporting line uses dark ink; the second uses secondary ink. All three rows are visible immediately, as in the selected static mockup.

Reference: option B in `.superpowers/brainstorm/53420-1789720954/content/conclusion-options.html`.

## Talk contract and scope

This serves abstract section 7's takeaway and the manual outline's two evaluation/application cycles. The original three claims and their order remain the conclusion; the verbs improve recall and readability. It occupies the existing one-minute conclusion slot within the 30-minute talk, with 30 slides total.

The change consists of scoped conclusion styles and markup in `slides/build_deck.py`, regeneration of `slides/pydata-2026.html`, and matching updates to `outline.md` and the delivery log. Existing navigation and slide numbering continue to apply. The separate, unfinished slide-27 angel-image edit is not part of this design.

## Acceptance

- The slide contains the three verbs and the exact supporting text above.
- All content fits the existing 1920 × 1080 stage with comfortable margins and no overlap.
- The deck builds successfully and remains at 30 slides.
- Inspect the rendered slide at presentation size when browser capture is available; retain a clear pending note if capture remains unavailable.

## Review state

Visual option B selected. Spec self-review completed: no placeholders, conflicting requirements, or unresolved design choices. Written-spec review pending before implementation planning, as required by the invoked brainstorming skill.
