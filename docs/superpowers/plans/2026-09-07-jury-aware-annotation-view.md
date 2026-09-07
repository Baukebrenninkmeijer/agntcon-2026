# Jury-Aware Annotation View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend assistant-plugins' evaluator-alignment annotation view to display and save jury-native review items without breaking legacy queues.

**Architecture:** The server selects a stable annotation key per item and validates jury queue identities before serving. The existing standalone HTML view gains a collapsed jury panel rendered from inline queue evidence; legacy single-judge rendering and annotation files remain unchanged.

**Tech Stack:** Python 3.11+, stdlib HTTP server, standalone HTML/CSS/JavaScript, pytest.

## Global Constraints

- Work only in `/private/tmp/assistant-plugins-jury-aware-annotation` on `feature/jury-aware-annotation`, based on current `origin/main`.
- Preserve every legacy `source_index` contract and the existing 549-test baseline.
- Do not dereference paths from queue data or serve external evidence files.
- Keep jury reasoning collapsed until the reviewer explicitly expands it.
- Bump all four root plugin manifests consistently and update `CHANGELOG.md`.

---

### Task 1: Backward-compatible jury annotation identity

**Files:**
- Modify: `skills/orq-evaluator-alignment/scripts/serve_annotation.py`
- Modify: `skills/orq-evaluator-alignment/tests/test_serve_annotation.py`

**Interfaces:**
- Produces: `annotation_key(item: Mapping[str, Any], mode: str | None) -> str`
- Produces: `validate_queue_identities(queue: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]`
- Extends: `build_annotation_record(..., case_id: str | None = None, transcript_fingerprint: str | None = None)`

- [ ] **Step 1: Add failing tests** proving legacy rows still key by stringified `source_index`; jury rows require nonblank unique `annotation_id`, `case_id`, and 64-character fingerprint; duplicate jury identities fail before the server binds; and saved jury annotations retain case/fingerprint provenance.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `uv run --no-project --with-requirements tests/requirements.txt python -m pytest tests/test_serve_annotation.py -q`

Expected: new identity tests fail.

- [ ] **Step 3: Implement identity selection and fail-closed validation** while retaining legacy function defaults and on-disk shapes for non-jury queues.

- [ ] **Step 4: Run focused tests**

Run: `uv run --no-project --with-requirements tests/requirements.txt python -m pytest tests/test_serve_annotation.py -q`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add skills/orq-evaluator-alignment/scripts/serve_annotation.py skills/orq-evaluator-alignment/tests/test_serve_annotation.py
git commit -m "feat(evaluator-alignment): accept jury annotation identities"
```

### Task 2: Jury evidence view

**Files:**
- Modify: `skills/orq-evaluator-alignment/annotation/annotate.html`
- Modify: `skills/orq-evaluator-alignment/tests/test_serve_annotation.py`

**Interfaces:**
- Consumes: queue items with `evidence`, `jury`, `signals`, `priority_reasons`, and `control_sample`

- [ ] **Step 1: Add failing HTML-contract tests** requiring decision evidence to appear before jury markup, a closed `<details>` jury section, model/repetition rendering functions, and explicit tie/abstention/inconclusive/disagreement/wobble/control badge labels.

- [ ] **Step 2: Run the HTML-contract slice and verify RED**

Run: `uv run --no-project --with-requirements tests/requirements.txt python -m pytest tests/test_serve_annotation.py -q -k jury`

Expected: failures because jury rendering is absent.

- [ ] **Step 3: Implement safe jury rendering** using the existing `esc()` function for every model, verdict, and explanation; render decision context, conversation/tool evidence, and final response first; then render the collapsed panel with one judge card and three repetition rows per vote.

- [ ] **Step 4: Run focused and full skill tests**

Run: `uv run --no-project --with-requirements tests/requirements.txt python -m pytest tests/ -q`

Expected: at least 549 tests pass with zero failures.

- [ ] **Step 5: Commit**

```bash
git add skills/orq-evaluator-alignment/annotation/annotate.html skills/orq-evaluator-alignment/tests/test_serve_annotation.py
git commit -m "feat(evaluator-alignment): render detailed jury evidence"
```

### Task 3: Package, version, and local install

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.cursor-plugin/plugin.json`
- Modify: `plugin.json`
- Modify: `CHANGELOG.md`
- Modify: `skills-lock.json`

- [ ] **Step 1: Bump version 3.1.1 to 3.2.0** in all four manifests because jury-aware annotation is a backward-compatible capability, add the dated changelog entry, stage the skill changes, and regenerate `skills-lock.json` with `node tests/scripts/validate-skills.mjs --fix`.

- [ ] **Step 2: Run repository validation**

Run: `tests/scripts/validate-plugin-manifests.sh`

Expected: `Plugin manifest validation passed.`

Run: `uv run --no-project --with-requirements skills/orq-evaluator-alignment/tests/requirements.txt python -m pytest skills/orq-evaluator-alignment/tests/ -q`

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add plugin.json .claude-plugin/plugin.json .codex-plugin/plugin.json .cursor-plugin/plugin.json CHANGELOG.md skills-lock.json
git commit -m "chore: bump version to 3.2.0"
```

- [ ] **Step 4: Install the verified skill locally** by copying only `skills/orq-evaluator-alignment/` from the worktree into the user's global Codex skills directory, without touching other installed skills, then rerun `test_serve_annotation.py` against the installed copy.

- [ ] **Step 5: Record the installed source commit and test evidence** in the PyData living plan. Do not push or open a pull request unless separately requested.
