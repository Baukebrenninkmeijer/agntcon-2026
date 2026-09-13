# Slides Social Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the hosted slide deck a deliberate LinkedIn card using the Grey-zone loop slide.

**Architecture:** Keep `slides/build_deck.py` as the source of the generated page head. Publish the existing final-state Grey-zone loop PNG beside the deck and reference it through absolute GitHub Pages URLs in Open Graph and Twitter metadata.

**Tech Stack:** Static HTML metadata, Python deck generator, PNG asset, GitHub Pages

## Global Constraints

- Use `slides/screenshots/20-grey-zone-loop.png` unchanged as the social image.
- Keep the image at 1920 by 1080.
- Do not change slide content, order, animation, or timing.
- Use absolute GitHub Pages URLs for the page and image.

---

### Task 1: Publish explicit social-card metadata

**Files:**
- Modify: `slides/build_deck.py`
- Regenerate: `slides/pydata-2026.html`
- Publish: `slides/screenshots/20-grey-zone-loop.png`
- Modify: `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

**Interfaces:**
- Consumes: the final-state Grey-zone loop PNG and the public GitHub Pages path.
- Produces: one HTML document with Open Graph and Twitter large-card metadata.

- [x] **Step 1: Verify the asset and the missing metadata**

Run:

```bash
sips -g pixelWidth -g pixelHeight slides/screenshots/20-grey-zone-loop.png
rg -n 'og:|twitter:|name="description"' slides/pydata-2026.html
```

Expected: the image is 1920 by 1080 and the metadata search returns no matches.

- [x] **Step 2: Add metadata to the generator**

Add these fields in `<head>` immediately after `<title>`:

```html
<meta name="description" content="How human judgement becomes an evaluator you can run on every change.">
<meta property="og:type" content="website">
<meta property="og:title" content="Building the evaluation flywheel">
<meta property="og:description" content="How human judgement becomes an evaluator you can run on every change.">
<meta property="og:url" content="https://baukebrenninkmeijer.github.io/building-the-evaluation-flywheel-pydata-2026/slides/pydata-2026.html">
<meta property="og:image" content="https://baukebrenninkmeijer.github.io/building-the-evaluation-flywheel-pydata-2026/slides/screenshots/20-grey-zone-loop.png">
<meta property="og:image:width" content="1920">
<meta property="og:image:height" content="1080">
<meta property="og:image:alt" content="The grey-zone evaluation loop, from judge disagreement through a human boundary decision to an updated evaluator.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Building the evaluation flywheel">
<meta name="twitter:description" content="How human judgement becomes an evaluator you can run on every change.">
<meta name="twitter:image" content="https://baukebrenninkmeijer.github.io/building-the-evaluation-flywheel-pydata-2026/slides/screenshots/20-grey-zone-loop.png">
```

- [x] **Step 3: Regenerate and verify**

Run:

```bash
uv run --no-sync python slides/build_deck.py
uv run --no-sync python -m py_compile slides/build_deck.py
uv run --no-sync ruff check slides/build_deck.py
git diff --check
```

Expected: generation succeeds, Ruff reports `All checks passed!`, and the diff check emits no output.

- [x] **Step 4: Inspect the generated contract**

Run:

```bash
test "$(rg -c '<meta property="og:' slides/pydata-2026.html)" -eq 8
test "$(rg -c '<meta name="twitter:' slides/pydata-2026.html)" -eq 4
test "$(rg -c '<meta name="description"' slides/pydata-2026.html)" -eq 1
rg -n 'https://baukebrenninkmeijer.github.io/building-the-evaluation-flywheel-pydata-2026/slides/(pydata-2026.html|screenshots/20-grey-zone-loop.png)' slides/pydata-2026.html
sips -g pixelWidth -g pixelHeight slides/screenshots/20-grey-zone-loop.png
```

Expected: all three `test` commands succeed; the absolute page and image URLs appear in the
metadata; the image remains 1920 by 1080.

- [x] **Step 5: Record and commit the verified change**

Update the living delivery plan with the fresh evidence, then commit the metadata, generated HTML, published image, this plan, and the plan log without pushing.
