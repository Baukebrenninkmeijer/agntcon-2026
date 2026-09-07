# Jury Annotation Producer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert a complete v4 evaluatorq jury artifact into a deterministic, reviewer-safe development annotation queue without additional model calls.

**Architecture:** A pure `jury_annotation` module reuses the canonical simulation loader and typed jury validator, derives jury-native signals, and publishes a dev-only run directory atomically. A thin CLI exposes it, while a project-local skill orchestrates preparation and the separately installed annotation view.

**Tech Stack:** Python 3.11+, Pydantic, evaluatorq 1.35.0, pytest, Ruff, Agent Skills.

## Global Constraints

- Join only by exact `(case_id, transcript_fingerprint)` and require the canonical 50-case 30/20 corpus.
- Never expose oracle/reference-family fields in annotation artifacts.
- Treat ties, abstentions, and genuine inconclusive results as high signal; exclude mechanical failures from ranking.
- Publish no test outcomes or evidence in the development run directory.
- Make no network, target, evaluator, hosted-resource, or credential call.
- Never overwrite an existing output path.

---

### Task 1: Pure jury signal and queue contracts

**Files:**
- Create: `src/analytics_chatbot/evaluation_ops/jury_annotation.py`
- Create: `tests/test_jury_annotation.py`

**Interfaces:**
- Produces: `annotation_id(case_id: str, transcript_fingerprint: str) -> str`
- Produces: `analyze_jury(jury: Mapping[str, Any]) -> JurySignals`
- Produces: `build_annotation_bundle(corpus: SimulationReplayCorpus, jury_rows: Sequence[Mapping[str, Any]], *, seed: int = 42, control_count: int = 5) -> AnnotationBundle`

- [ ] **Step 1: Write failing unit tests** for stable annotation IDs; independent three-label entropy per successful judge; tie/abstention/inconclusive priority; disagreement+wobble separation; mechanical-error exclusion; exact case-set and one-row-per-case enforcement; and oracle-family absence from serialized queue items.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `uv run pytest tests/test_jury_annotation.py -q`

Expected: collection fails because `jury_annotation` does not exist.

- [ ] **Step 3: Implement the typed contracts and pure builder**

Use frozen dataclasses for `JudgeWobble`, `JurySignals`, and `AnnotationBundle`. Reuse `lib.instability.categorical` semantics locally through a small stdlib calculation rather than importing an installed skill. Validate each jury row through `validate_jury_record`, compute the exact five priority tiers from the design, sample controls from the annotation-ID-sorted stable pool with `random.Random(seed)`, and serialize only the evidence allowlist.

- [ ] **Step 4: Run focused tests and Ruff**

Run: `uv run pytest tests/test_jury_annotation.py -q`

Expected: all tests pass.

Run: `uv run ruff check src/analytics_chatbot/evaluation_ops/jury_annotation.py tests/test_jury_annotation.py`

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add src/analytics_chatbot/evaluation_ops/jury_annotation.py tests/test_jury_annotation.py
git commit -m "feat: derive jury annotation priorities"
```

### Task 2: Atomic offline producer CLI

**Files:**
- Create: `scripts/prepare_jury_annotations.py`
- Modify: `tests/test_jury_annotation.py`

**Interfaces:**
- Consumes: `build_annotation_bundle(...)`
- Produces: `prepare(cases_path: Path, results_path: Path, jury_path: Path, output_dir: Path, *, seed: int = 42, control_count: int = 5) -> Path`
- Produces: `queue.json`, `test_manifest.json`, `jury_errors.json`, and ready `manifest.json`

- [ ] **Step 1: Add failing publication tests** covering malformed JSONL, missing/duplicate identities, an existing destination, injected mid-write failure, concurrent destination creation, ready-manifest-last behavior, and byte-identical output from identical inputs.

- [ ] **Step 2: Run the publication slice and verify RED**

Run: `uv run pytest tests/test_jury_annotation.py -q -k 'publish or prepare or deterministic'`

Expected: failures because the CLI and publisher do not exist.

- [ ] **Step 3: Implement preparation and staged-directory publication**

Load observations through `load_simulation_replay`, load jury JSONL as mappings, build the bundle, write canonical JSON with sorted keys into a unique sibling staging directory, fsync each file and directory, write `manifest.json` last, and publish with an exclusive destination operation. Convert JSON, Pydantic, filesystem, and jury-validation exceptions into one concise nonzero CLI error without a traceback.

- [ ] **Step 4: Run focused and full offline checks**

Run: `uv run pytest tests/test_jury_annotation.py tests/test_run_decision_support_jury.py tests/test_simulation_artifacts.py -q`

Expected: all pass.

Run: `uv run ruff check scripts/prepare_jury_annotations.py src/analytics_chatbot/evaluation_ops/jury_annotation.py tests/test_jury_annotation.py`

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add scripts/prepare_jury_annotations.py src/analytics_chatbot/evaluation_ops/jury_annotation.py tests/test_jury_annotation.py
git commit -m "feat: publish offline jury annotation queues"
```

### Task 3: Repository-local orchestration skill

**Files:**
- Create: `.agents/skills/orq-jury-to-alignment/SKILL.md`
- Create: `.agents/skills/orq-jury-to-alignment/agents/openai.yaml`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

**Interfaces:**
- Consumes: `scripts/prepare_jury_annotations.py`
- Hands off to: installed `orq-evaluator-alignment/scripts/serve_annotation.py`

- [ ] **Step 1: Scaffold the skill** with the system skill initializer, then replace generated instructions with a short workflow that verifies all three artifacts, runs the offline producer, reports queue/error/control counts, launches only the annotation server, and stops after annotations are saved.

- [ ] **Step 2: Add explicit gates** stating that absent v4 observations or jury JSONL is a blocker, machine verdicts are not labels, test outcomes stay sealed, and single-judge rewrite/retest commands are out of scope.

- [ ] **Step 3: Validate the skill and documentation**

Run: `python /Users/baukebrenninkmeijer/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/orq-jury-to-alignment`

Expected: validation succeeds.

Run: `git diff --check`

Expected: clean.

- [ ] **Step 4: Run the complete offline gate and record fresh evidence in the living plan**

Run: `uv run pytest -q -m 'not live'`

Expected: all non-live tests pass.

Run: `uv run ruff check .`

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/orq-jury-to-alignment README.md docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat: add jury annotation orchestration skill"
```
