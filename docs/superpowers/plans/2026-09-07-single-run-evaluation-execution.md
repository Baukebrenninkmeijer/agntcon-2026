# Single-Run Evaluation Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden and execute one canonical Sphere v4 observation Experiment and one canonical
50-row `decision_support_quality` jury Experiment without batching or accidental artifact loss.

**Architecture:** Add only the missing fail-closed controls to the two existing runners, keeping
evaluatorq responsible for execution. A one-case observation isolation and two-development-row
jury smoke gate the two full single-Experiment runs; the existing offline producer then creates the
human annotation queue.

**Tech Stack:** Python 3.11+, evaluatorq 1.35.0, Pydantic, pytest, Ruff, Orq AI Gateway.

## Global Constraints

- Create one canonical observation Experiment and one canonical jury Experiment; do not batch.
- Route every new Experiment explicitly to `pydata2026`.
- Never overwrite an existing output or report path.
- Preserve mechanically failed but structurally complete jury records for `jury_errors.json`.
- Reject missing/incomplete jury payloads and all source/result identity mismatches.
- Make no tool or evaluator resource mutation.
- Use the primary checkout's ignored `.env` without printing or relocating its credential.
- Update the living delivery plan and commit every implementation or operational state change.

---

### Task 1: Harden the single observation runner

**Files:**
- Modify: `tests/test_run_simulation_script.py`
- Modify: `scripts/run_simulation.py`

**Interfaces:**
- Produces: `_resolve_output_paths(output: Path, report: Path | None) -> tuple[Path, Path | None]`
- Produces: `--experiment-path` with default `pydata2026`
- Consumes: evaluatorq `simulate(..., orq_results_path=...)`

- [ ] **Step 1: Write failing tests** that import the script, require default project path
  `pydata2026`, reject existing output/report paths and aliases before invoking simulation, and
  assert the selected Experiment path is forwarded.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_run_simulation_script.py -q`

Expected: failures because the path resolver and Experiment-path forwarding do not exist.

- [ ] **Step 3: Implement the minimal controls** by resolving both paths, requiring an existing
  parent directory, refusing existing/symlinked/aliased paths, adding `--experiment-path`, and
  passing it as `orq_results_path`. Keep `--case-id` and `--limit` behavior unchanged.

- [ ] **Step 4: Verify GREEN and lint**

Run: `uv run pytest tests/test_run_simulation_script.py -q`

Run: `uv run ruff check scripts/run_simulation.py tests/test_run_simulation_script.py`

Expected: both commands pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/run_simulation.py tests/test_run_simulation_script.py
git commit -m "fix: harden canonical simulation outputs"
```

### Task 2: Add a strict jury smoke selector and preserve mechanical records

**Files:**
- Modify: `tests/test_run_decision_support_jury.py`
- Modify: `scripts/run_decision_support_jury.py`

**Interfaces:**
- Produces: repeatable `--case-id <id>` selection
- Preserves: `validate_jury_record(raw_output) -> dict[str, Any]` for every structurally complete
  exact-panel/exact-repetition `JuryResult`

- [ ] **Step 1: Write failing tests** requiring two explicit development IDs to select exactly two
  validated samples and print an 18-call budget; duplicate, missing, or test IDs must fail before
  evaluator construction. Change the mechanical-failure expectation so a complete typed jury with
  a failed judge is serialized, while `raw_output.evaluation_error`, absent jury data, incomplete
  repetitions, and wrong model order still fail.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_run_decision_support_jury.py -q`

Expected: failures because `--case-id` does not exist and mechanical jury rows are rejected.

- [ ] **Step 3: Implement selection and structural validation** after full-corpus validation but
  before call budgeting. Require unique requested IDs, exact coverage, and development-only IDs.
  Remove only the mechanical-state rejection from `validate_jury_record`; retain complete strict
  Pydantic validation and every identity/output/top-level error gate.

- [ ] **Step 4: Verify GREEN and lint**

Run: `uv run pytest tests/test_run_decision_support_jury.py tests/test_jury_annotation.py -q`

Run: `uv run ruff check scripts/run_decision_support_jury.py tests/test_run_decision_support_jury.py`

Expected: both commands pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/run_decision_support_jury.py tests/test_run_decision_support_jury.py
git commit -m "fix: gate and preserve jury execution evidence"
```

### Task 3: Verify and execute the approved single-run sequence

**Files:**
- Modify: `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`
- Runtime only: ignored `runs/` and `.evaluatorq/`

**Interfaces:**
- Produces: one pilot JSONL/report, one canonical 50-row observation JSONL/report, one two-row jury
  smoke JSONL, one canonical 50-row jury JSONL, and one annotation run directory

- [ ] **Step 1: Run the complete offline gate**

Run: `uv run pytest -q -m 'not live'`

Run: `uv run ruff check .`

Run: `uv build`

Run: `git diff --check`

Expected: all pass before any model call.

- [ ] **Step 2: Re-run the authenticated agent-only plan** and require `analytics-chatbot: noop`.

- [ ] **Step 3: Run one explicit development case** with unique output/report names and
  `--experiment-path pydata2026`; require one accepted replay row.

- [ ] **Step 4: Run all 50 v4 cases once** in a tracked terminal session with unique output/report
  names and `--experiment-path pydata2026`. Require exactly 50 accepted replay rows, zero rejected
  or duplicates, and the frozen 30/20 split.

- [ ] **Step 5: Run the two-row jury smoke** with two explicit development IDs and
  `--approve-calls`. Require two complete exact 3-by-3 jury records and no top-level errors.

- [ ] **Step 6: Run the canonical 50-row jury** once with `--approve-calls`. Require 50 exact
  identities and complete raw jury objects; count mechanical rows separately.

- [ ] **Step 7: Run `orq-jury-to-alignment`** to publish the annotation bundle, verify port 8765 is
  free, and launch the installed view. Stop after human annotation.

- [ ] **Step 8: Update and commit the living plan** with exact artifact hashes, Experiment URLs,
  counts, failures, tests, and remaining handoffs. Do not commit ignored runtime artifacts or
  credentials.
