# Evaluation Flywheel Visual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one accurate, reusable evaluation-flywheel visual that renders on GitHub and exports cleanly for PyData slides.

**Architecture:** The Mermaid block embedded near the README overview is the maintainable source of truth. A generated SVG under `docs/assets/` is the slide-ready derivative; its accessible title and description restate the diagram's flow and status semantics.

**Tech Stack:** GitHub-flavored Markdown, portable Mermaid flowchart syntax, Mermaid CLI, SVG.

## Global Constraints

- Preserve useful README content and do not modify implementation modules or remote Orq state.
- Show Orq platform execution separately from local/evaluatorq processing.
- Label verified, active, and planned elements explicitly; do not rely on color alone.
- Quote every Mermaid node, subgraph, and edge label and use `<br/>` for line breaks.
- Keep the README Mermaid block as the source of truth and the SVG as a generated export.
- Use only local assets and commit the coherent documentation change without pushing or merging.

---

### Task 1: Integrate the evaluation flywheel into the README

**Files:**

- Modify: `README.md`

**Interfaces:**

- Consumes: the architecture and status claims in the evaluator-native design, simulation plan, and living project plan.
- Produces: one portable Mermaid source block plus a caption, status key, text alternative, and link to the slide export.

- [x] **Step 1: Add the source-of-truth Mermaid diagram near the project overview**

  Use a compact two-band flow with labeled Orq, local-tool, and evaluatorq boundaries, central agent/tools, forked deterministic/LLM evaluation, human review, and an explicit manual loop back to the agent.

- [x] **Step 2: Add accessible status and text descriptions**

  State that `VERIFIED`, `ACTIVE`, and `PLANNED` describe repository delivery status, then describe the full loop in prose for readers who cannot use the visual.

- [x] **Step 3: Validate Markdown and strict Mermaid portability**

  Run the skill hardener in check-by-diff mode, verify fenced-code balance, and render the extracted Mermaid block with Mermaid CLI.

### Task 2: Produce and inspect the slide-ready SVG

**Files:**

- Create: `docs/assets/evaluation-flywheel.svg`

**Interfaces:**

- Consumes: the exact Mermaid source block from `README.md`.
- Produces: a local, scalable 16:9-compatible visual linked from the README.

- [x] **Step 1: Extract and render the README Mermaid block**

  Render with Mermaid CLI at a slide-scale width and a transparent or neutral background without maintaining a second hand-edited diagram definition.

- [x] **Step 2: Add SVG accessibility metadata**

  Ensure the SVG contains a concise `<title>` and `<desc>` that identify the flywheel, the Orq/local boundary, status semantics, and feedback loop.

- [x] **Step 3: Inspect at README and slide scales**

  Rasterize locally at representative widths, visually inspect both versions, and revise the Mermaid source if labels or edges are unclear.

- [x] **Step 4: Run repository checks and commit**

  Run Ruff, the offline pytest selection, asset/link checks, and a secret-pattern scan of staged content. Commit only the plan, README, and generated SVG.
