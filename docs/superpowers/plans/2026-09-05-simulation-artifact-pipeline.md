# Simulation Artifact Pipeline Implementation Plan

> **Status:** `COMPLETE`. The adapter is integrated on local `main`. A bounded
> 50-case live simulation was subsequently approved and run, so the "no live
> runs" scope note below applied only to this plan's own implementation work,
> not to the project as a whole. No remote resource was written by this plan.

**Goal:** Prove evaluatorq's raw simulation artifact contains everything needed
for native downstream evaluation, with only light deduplication and quality
checks.

**Design:** [Simulation Artifact Pipeline Design](../specs/2026-09-05-simulation-artifact-pipeline-design.md)

## Task 1: Permit self-contained simulation rows

**Files:** `src/analytics_chatbot/evaluation_ops/__init__.py`,
`tests/test_evaluation_ops.py`

1. Add a failing round-trip test for an evaluation row with no Orq trace source.
2. Make trace source optional while preserving existing trace-backed behavior.
3. Run the focused test.

## Task 2: Normalize and validate raw simulation results

**Files:** `src/analytics_chatbot/evaluation_ops/simulation_artifacts.py`,
`tests/test_simulation_artifacts.py`

1. Add fixtures matching evaluatorq 1.33 `SimulationResult` JSON output.
2. Test case/oracle joining, tool pairing, parsed arguments, and final-assistant
   ordering.
3. Test expected-tool failures, malformed calls, unsuccessful runs, missing
   cases, and exact duplicate removal while retaining distinct attempts.
4. Implement pure normalization and validation functions with a structured
   rejection report.
5. Verify each accepted row round-trips to evaluatorq `DataPoint`.

## Task 3: Record evidence and verify

**Files:** `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

1. Validate the local raw pilot artifacts through the adapter without modifying
   or committing them. Originally three pilot artifacts; the approved 50-case
   run has since replaced them with 50 raw results in the ignored run
   directory. The edge-v2 follow-up run also has 50 raw results; all 50 are
   structurally valid and behavioral failures remain replayable.
2. Record field sufficiency, accepted/rejected counts, and any limitations in
   the living plan.
3. Run Ruff, the full non-live test suite, and package build.
4. Commit the implementation, tests, design, plan, and living-plan update as one
   coherent change.
