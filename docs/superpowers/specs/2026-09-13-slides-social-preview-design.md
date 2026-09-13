# Slides social preview design

## Purpose

Give the hosted slide deck a deliberate LinkedIn and social preview instead of letting crawlers
assemble a card from visible slide text.

## Card

Use the final-state Grey-zone loop slide export as the social image. The diagram is the talk's core
process: jury disagreement focuses attention, a collaborator helps formulate the boundary question,
the human answers it, and the evaluator is updated before the frozen development cases run again.

Keep the existing 1920 by 1080 image intact. Do not crop it or add a second title treatment. The
Open Graph title and description provide the page identity beside the process visual.

## Page metadata

The generated slide HTML will include:

- `description`;
- `og:type`, `og:title`, `og:description`, `og:url`, and `og:image`;
- `og:image:width`, `og:image:height`, and an accessible `og:image:alt`;
- `twitter:card`, `twitter:title`, `twitter:description`, and `twitter:image`.

The canonical page and image use absolute GitHub Pages URLs so LinkedIn can fetch them without
resolving repository-relative paths.

## Files

- `slides/screenshots/20-grey-zone-loop.png`: the published card image.
- `slides/build_deck.py`: metadata source for the generated `slides/pydata-2026.html`.

No slide content, order, animation, or timing changes.

## Verification

- Confirm the PNG is exactly 1920 by 1080.
- Inspect the card at full size and a compact preview size for legibility and cropping.
- Regenerate the deck and confirm every metadata field appears once with the expected absolute URL.
- Run Python compilation, Ruff, and `git diff --check`.
- After deployment, refresh LinkedIn's cached card through Post Inspector if the old preview remains.
