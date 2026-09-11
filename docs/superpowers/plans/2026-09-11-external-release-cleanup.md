# External Release Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the private working repository into a public companion repo for the talk that contains only the v4 decision-support path, the agent, the deck, and the evidence the talk shows, with no internal history, names, identifiers, or dead experiments.

**Architecture:** Delete in layers, running the offline gate after each: side projects first (podcast, ECIR), then the superseded v1-v3 correctness pipeline, then process documents, then portability and metadata fixes. Collapse `cases.py`/`cases_v3.py`/`cases_v4.py` into one module and prove the v4 corpus still regenerates byte-for-byte. Publish as a fresh single-commit history in a new public repository under the current name, keeping the old repository as a private archive.

**Tech Stack:** Python 3.11+, uv, pytest, Ruff, evaluatorq 1.35.0, DuckDB, git, gh.

**Spec:** this document. The contract files (`abstract.md`, `outline-manual.md`) are unchanged by this plan; it only removes material the talk no longer uses (`outline.md` already states "The talk uses only the analytics agent. There are no podcast examples.").

## Global Constraints

- Offline gate after every task: `uv run --no-sync ruff check .` clean and `uv run --no-sync pytest -m "not live and not simulation_live and not alignment_live" -q` green. Baseline on 2026-09-11: `223 passed, 1 deselected`, Ruff clean.
- Never call Orq, a model, or the network. No hosted resource changes; `orq_sync` never deletes, so removing YAML does not touch the workspace.
- Never edit tracked v4 evidence under `orq/resources/datasets/decision-support-v4/` or `simulation-cases-v4.jsonl`.
- Never force-push or delete the remote without explicit approval at Task 9.
- `outline-manual.md` is never rewritten. Removing it from the public tree is decision D4 and needs Bauke's explicit yes.

## Decisions (defaults used unless Bauke says otherwise)

| # | Question | Default |
|---|---|---|
| D1 | History | Fresh single-commit history. Rename current repo to `building-the-evaluation-flywheel-archive` (stays private), create a new public repo with the original name so the deck QR (`REPO_URL`) stays valid, push the squashed tree. Old history contains the workspace slug, project ids, the third-party ECIR PDF, reviewer names, and ~60 copies of the 1.3 MB deck. |
| D2 | Commercial font (ES Klarheit Kurrent) embedded in `slides/pydata-2026.html` and read from `/Users/baukebrenninkmeijer/.claude/...` | `build_deck.py` embeds the font only when `DECK_FONT_DIR` is set, else falls back to a system font stack. The public HTML is built without the font. Bauke keeps presenting from a local build with the font. |
| D3 | Unfinished trace importer (`trace_import.py`, status `ACTIVE`, no script uses it) | Drop. Online evaluation is "next stage, not completed work" per `outline.md`. |
| D3b | Python trajectory evaluators (`state-change-policy`, `tool-execution-integrity`) | Keep. They are the code-based trajectory checks behind abstract section 4. |
| D4 | Talk-authoring files: `outline-manual.md`, `outline.md`, `story-outline*.md`, `CLAUDE.md` | Keep `abstract.md` and `outline.md` (useful talk notes). Drop `story-outline.md`, `story-outline-pre.md`, and, only with Bauke's yes, `outline-manual.md`. Replace `CLAUDE.md` with a short public `AGENTS.md`. |
| D5 | License | MIT for code, CC BY 4.0 for slides, docs, and data. |

## Keep / drop map

Keep (the v4 path and the talk):

- `src/analytics_chatbot/` agent, CLI, SQL tool, insights, run store, gateway, config, models, prompts, `orq_resources.py`, `orq_sync.py`
- `src/analytics_chatbot/evaluation_ops/`: `__init__.py` (minus trace import and `orq_evaluator`), `simulation_artifacts.py`, `jury_annotation.py`, `target.py`, and one merged `cases.py`
- Scripts: `generate_simulation_cases.py`, `run_simulation.py`, `run_decision_support_jury.py`, `prepare_jury_annotations.py`, `upload_decision_support_jury_comparison.py`, `sync_orq_resources.py`
- `orq/resources/` agent, tools, project, `decision-support-quality.yaml`, both Python evaluators, `simulation-cases-v4.jsonl`, all of `decision-support-v4/` (three jury versions are the prompt lineage the talk shows)
- `slides/` (`build_deck.py`, generated HTML, `case-signals-v4.json`, `judge-grid-v3.json`, `trajectories-v4.json`, `cartoon-bauke.jpg`, `experiment-grid.jpg`)
- `docs/assets/`, `docs/examples/decision-support-contrast-2026-09-07/`, `docs/examples/jury-signals-2026-09-07/README.md`
- `.agents/skills/orq-jury-to-alignment/`, `.github/workflows/offline-ci.yml`, `Makefile`, `pyproject.toml`, `uv.lock`, `.env.example`, `abstract.md`, `outline.md`, `README.md`

Drop (alternative directions, old runs, process residue):

| Path | Why |
|---|---|
| `ECIR2026-text2story-keynote-slides (1).pdf`, `docs/reference/ecir-2026-keynote-slide-deck-plan.md` | Third-party deck and a different talk |
| `docs/examples/podcast-*`, `docs/examples/claudish-jury-2026-09-06/`, `docs/talk-example-podcast.md`, `orq/resources/evaluators/jury/podcast-claudish.yaml` | Podcast running example, abandoned |
| `docs/alignment-session-log.md`, `scripts/prepare_alignment_datapoints.py`, `scripts/run_evaluatorq_replay.py`, `evaluation_ops/hosted_evaluators.py`, `tests/test_hosted_evaluators.py`, `tests/test_run_evaluatorq_replay_script.py` | v1-v3 single-judge answer-correctness path |
| `scripts/run_agent_smoke.py` | Covered by `analytics-chatbot ask` |
| `orq/resources/datasets/simulation-cases.jsonl`, `-v2.jsonl`, `-v3.jsonl`, `simulation-pilot-review.json` | Superseded corpora |
| `evaluation_ops/trace_import.py`, `tests/test_trace_import.py`, `tests/fixtures/traces/` | D3 |
| `docs/superpowers/` (all 28 specs and plans, including this file) | Agent process logs with reviewer names and internal Linear links; archived in D1 |
| `outputs/html/pydata-2026-evaluation-status.html` | Internal status report |
| `slides/assets/headshot.jpg`, `slides/replay-trace.json` | Not read by `build_deck.py`, not in the deck |
| `docs/examples/jury-signals-2026-09-07/*.json` | Byte-identical copies of `slides/*.json` |
| `story-outline.md`, `story-outline-pre.md` | D4 |
| Untracked: `setup.sh` (an unrelated exo-harness installer), `review-arian.md`, `review-arian-transcript.md` | Not this project; move the review notes out of the repo, do not commit |
| Local only: `runs/` (380 run dirs, 12 MB), `.evaluatorq/`, `dist/`, `.superpowers/`, `.conductor/`, `.ropeproject/`, stale worktree `/private/tmp/pydata-2026-decision-support.0wFNsV`, merged branches `Baukebrenninkmeijer/ecir2026-text2story`, `codex/evaluation-flywheel-visual`, `codex/project-status-plan`, `feature/decision-support-evaluation` | Old runs; all accepted v4 evidence already has tracked copies |

---

### Task 0: Preflight and safety net

**Files:** none tracked beyond the pending WIP.

- [ ] **Step 1:** Commit the pending slide-14 edit (`slides/build_deck.py`, `slides/pydata-2026.html`, `outline.md`, living-plan entry 117) so cleanup starts from a clean tree.

```bash
git add slides/build_deck.py slides/pydata-2026.html outline.md docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat(slides): state the annotation constraint on the lazy slide"
```

- [ ] **Step 2:** Tag the pre-cleanup state locally: `git tag pre-public-cleanup`.
- [ ] **Step 3:** Move untracked personal files out: `mkdir -p ~/Documents/pydata-2026-private && mv review-arian.md review-arian-transcript.md ~/Documents/pydata-2026-private/`. Delete `setup.sh` after confirming with Bauke it is not wanted here.
- [ ] **Step 4:** Work on a branch: `git switch -c cleanup/public-release`.
- [ ] **Step 5:** Run the offline gate; record the count.

### Task 1: Remove side projects (podcast, ECIR)

**Files:**
- Delete: paths in rows 1-2 of the drop table
- Modify: `tests/test_orq_resources.py:59`, `tests/test_orq_sync.py:47`

- [ ] **Step 1:** `git rm -r "ECIR2026-text2story-keynote-slides (1).pdf" docs/reference docs/examples/podcast-run-2026-09-04 docs/examples/podcast-run-2026-09-06 docs/examples/podcast-corpus-2026-09-06 docs/examples/claudish-jury-2026-09-06 docs/talk-example-podcast.md orq/resources/evaluators/jury/podcast-claudish.yaml`
- [ ] **Step 2:** Run the gate. Expected failures: the two asserts that name `podcast-claudish`.
- [ ] **Step 3:** In `tests/test_orq_resources.py:59` change the set to `{"analytics-decision-support-quality"}`; delete the `("create", "evaluator", "podcast-claudish")` tuple in `tests/test_orq_sync.py:47`. Fix any count asserts nearby that assumed two LLM evaluators.
- [ ] **Step 4:** Gate green. `git grep -in 'podcast\|claudish\|ecir'` returns only `outline.md` lines that explicitly say there are no podcast examples and the ECIR attribution of the three benefits; reword that attribution if Bauke prefers.
- [ ] **Step 5:** Commit `chore: drop podcast and ECIR side projects`.

### Task 2: Remove the v1-v3 correctness pipeline and the trace importer

**Files:**
- Delete: rows 3-6 of the drop table
- Modify: `src/analytics_chatbot/evaluation_ops/__init__.py:19-24,369-373`, `tests/test_simulation_cases.py`, `tests/test_generate_simulation_cases_script.py`, `scripts/generate_simulation_cases.py`, `scripts/run_simulation.py:18-21`

- [ ] **Step 1:** `git rm scripts/run_evaluatorq_replay.py scripts/prepare_alignment_datapoints.py scripts/run_agent_smoke.py src/analytics_chatbot/evaluation_ops/hosted_evaluators.py src/analytics_chatbot/evaluation_ops/trace_import.py tests/test_hosted_evaluators.py tests/test_run_evaluatorq_replay_script.py tests/test_trace_import.py docs/alignment-session-log.md orq/resources/datasets/simulation-cases.jsonl orq/resources/datasets/simulation-cases-v2.jsonl orq/resources/datasets/simulation-cases-v3.jsonl orq/resources/datasets/simulation-pilot-review.json && git rm -r tests/fixtures/traces`
- [ ] **Step 2:** In `evaluation_ops/__init__.py` delete the `hosted_evaluators` and `trace_import` imports and remove `TraceImportError`, `import_orq_trace`, `import_run_audit`, `orq_evaluator` from `__all__`. Update the module docstring to "Evaluatorq-native jury evaluation of stored, trace-backed conversations."
- [ ] **Step 3:** In `tests/test_simulation_cases.py` delete `test_builds_fifty_stable_oracle_backed_cases`, `test_builds_fifty_harder_multi_turn_edge_cases`, `test_edge_v2_oracles_cover_the_staged_final_request`, `test_pilot_review_preserves_every_attempt_transcript`. Keep `test_v3_is_one_persona_fifty_distinct_situations` only if it asserts on `SCENARIOS` (still used by v4); otherwise delete. In `tests/test_generate_simulation_cases_script.py` delete the two edge-v2 tests and the standard-corpus default test.
- [ ] **Step 4:** Run the gate; fix remaining imports until green. Commit `chore: drop the superseded v1-v3 correctness pipeline`.

### Task 3: Collapse the three case modules into one

**Files:**
- Create: `src/analytics_chatbot/evaluation_ops/cases.py` (new content)
- Delete: `cases_v3.py`, `cases_v4.py`
- Modify: `scripts/generate_simulation_cases.py`, `scripts/run_simulation.py`, tests importing `cases_v3`/`cases_v4`

**Interfaces:**
- Produces: `analytics_chatbot.evaluation_ops.cases.build_v4_cases(database_path: Path) -> list[dict[str, Any]]`, `write_cases(records, path) -> None`, `CORPUS_VERSION = "simulation-v4"`

- [ ] **Step 1: Write the guard test first** in `tests/test_simulation_cases.py`:

```python
def test_v4_regenerates_the_tracked_corpus_byte_for_byte(tmp_path: Path) -> None:
    from analytics_chatbot.data import seed_database
    from analytics_chatbot.evaluation_ops.cases import build_v4_cases, write_cases

    database = tmp_path / "analytics.duckdb"
    seed_database(database)
    output = tmp_path / "cases.jsonl"
    write_cases(build_v4_cases(database), output)
    tracked = ROOT / "orq/resources/datasets/simulation-cases-v4.jsonl"
    assert output.read_bytes() == tracked.read_bytes()
```

Check `seed_database`'s real signature in `src/analytics_chatbot/data.py` and pass defaults exactly as `analytics-chatbot seed-data` does.

- [ ] **Step 2:** Run it against the current modules (import from `cases_v4`/`cases`) and confirm it PASSES before refactoring. If it fails, stop: the tracked corpus is not reproducible and the refactor has no safety net; report to Bauke.
- [ ] **Step 3:** Build the new `cases.py`: `_expected` and `write_cases` from old `cases.py`; `V3Scenario` (renamed `CaseScenario`), `_s`, `SCENARIOS`, `FABRICATION`, `EVIDENCE`, `_criteria` from `cases_v3.py`; everything from `cases_v4.py`. Drop `ScenarioTemplate`, `EdgeScenarioTemplate`, `PERSONAS`, `TEMPLATES`, `EDGE_TEMPLATES`, `EDGE_REFERENCE_SQL`, `build_cases`, `build_edge_cases`, `build_v3_cases`, and the v3 `PERSONA`/`CORPUS_VERSION`. Do not change any string, id, or ordering that reaches the output.
- [ ] **Step 4:** `git rm` `cases_v3.py`, `cases_v4.py`. Point the guard test and any other test at `evaluation_ops.cases`.
- [ ] **Step 5:** `scripts/generate_simulation_cases.py`: remove `--variant` and `BUILDERS`; always build v4, default output `orq/resources/datasets/simulation-cases-v4.jsonl`. `scripts/run_simulation.py:18-21`: default `--cases` to the v4 file. Update `tests/test_generate_simulation_cases_script.py::test_v4_variant_defaults_to_separate_output_path` to call without `--variant`.
- [ ] **Step 6:** Gate green including the guard test. Commit `refactor: fold the case corpora into one v4 module`.

### Task 4: Deduplicate and prune slide material; make the deck buildable anywhere

**Files:**
- Delete: `slides/assets/headshot.jpg`, `slides/replay-trace.json`, `docs/examples/jury-signals-2026-09-07/{case-signals-v4,trajectories-v4,replay-trace}.json`, `outputs/`
- Modify: `slides/build_deck.py:11-23`, `docs/examples/jury-signals-2026-09-07/README.md`

- [ ] **Step 1:** Delete the files above. In the jury-signals README, point to `slides/case-signals-v4.json` and `slides/trajectories-v4.json`, drop the `replay-trace.json` sections, and replace `runs/v4-jury-20260907.jsonl` with the tracked `orq/resources/datasets/decision-support-v4/jury-baseline/jury-results.jsonl` if that is the same run (check the SHA or README; if not, say "the canonical v4 jury run, not tracked").
- [ ] **Step 2:** Replace the hard-coded font path (D2):

```python
FONT_DIR = pathlib.Path(os.environ["DECK_FONT_DIR"]) if "DECK_FONT_DIR" in os.environ else None
FONT_FILES = {
    "RG": "ESKlarheitKurrent-Rg.woff2",
    "MD": "ESKlarheitKurrent-Md.woff2",
    "SB": "ESKlarheitKurrent-Smbd.woff2",
    "MONO": "ESKlarheitKurrentMono-Md.ttf",
}
# ponytail: commercial font is embedded only when the presenter points at a licensed copy
fonts = {k: base64.b64encode((FONT_DIR / f).read_bytes()).decode() for k, f in FONT_FILES.items()} if FONT_DIR else {}
```

Then emit the `@font-face` block only when `fonts` is non-empty, and make every `font-family` declaration end in a system fallback (`system-ui, -apple-system, "Segoe UI", sans-serif` and `ui-monospace, "SF Mono", Menlo, monospace`). Find the `@font-face` block with `grep -n 'font-face\|fonts\[' slides/build_deck.py`.
- [ ] **Step 3:** Build without the font: `env -u DECK_FONT_DIR uv run python slides/build_deck.py`; `grep -c 'font/woff2;base64' slides/pydata-2026.html` must be `0`. Render slides 1, 14, and 28 in headless Chrome at 1600x900 and check for overflow caused by the metric change; adjust only if a slide clips.
- [ ] **Step 4:** Gate green. Commit `feat(slides): build the deck without the licensed font by default`.

### Task 5: Remove process documents and rewrite repo guidance

**Files:**
- Delete: `docs/superpowers/`, `story-outline.md`, `story-outline-pre.md`, `outline-manual.md` (only with D4 yes), `CLAUDE.md`, `AGENTS.md` symlink
- Create: `AGENTS.md`
- Modify: `.agents/skills/orq-jury-to-alignment/SKILL.md:25-28`

- [ ] **Step 1:** Before deleting, lift the one paragraph of component boundaries and trace semantics from `docs/superpowers/specs/2026-09-02-analytics-chatbot-design.md` into the README's "Observability and safety" section if anything there is not already covered.
- [ ] **Step 2:** `git rm -r docs/superpowers story-outline.md story-outline-pre.md CLAUDE.md AGENTS.md` (plus `outline-manual.md` if approved).
- [ ] **Step 3:** Write `AGENTS.md` (plain file, about 20 lines): what the repo is, the offline gate commands, "never run live or paid commands without the operator's say-so", "`orq/resources/datasets/decision-support-v4/` is frozen evidence; never edit it", "the 20-case test split stays sealed". Add `CLAUDE.md` as a symlink to it if Claude Code support is wanted.
- [ ] **Step 4:** In `SKILL.md` replace step 1 with "From the repository root, read `orq/resources/datasets/decision-support-v4/README.md`." and change the `runs/` wording in step 3 to "a new directory outside the tracked tree".
- [ ] **Step 5:** `git grep -n 'docs/superpowers\|story-outline\|outline-manual\|CLAUDE.md'` returns nothing (except the new symlink). Gate green. Commit `docs: replace internal process docs with public agent guidance`.

### Task 6: Metadata, license, README

**Files:**
- Create: `LICENSE` (MIT), `LICENSE-content` (CC BY 4.0 notice covering `slides/`, `docs/`, `orq/resources/datasets/`)
- Modify: `README.md`, `pyproject.toml`, `.gitignore`

- [ ] **Step 1:** `.gitignore`: add `dist/`, `.conductor/`, `.ropeproject/`.
- [ ] **Step 2:** `pyproject.toml`: add `license = "MIT"`, register the two unregistered markers: `markers = ["live: ...", "simulation_live: opt-in live simulation runs", "alignment_live: opt-in live alignment runs"]`. Run `grep -rn 'simulation_live\|alignment_live' tests` first; if no test uses them, remove them from the CI command and README instead.
- [ ] **Step 3:** README rewrite. Remove: "Historical v1-v3 evidence" section, the BOPS-1180 Linear link, the `podcast` pending-evaluator sentence under "Hosted resources", the "living delivery plan" row, the design-spec link. Fix the stale "Current v4 review pool" section: the tracked pool has 50 observations, three immutable jury versions, and 30 confirmed development labels; the 20-case test split is sealed. Change the `prepare_jury_annotations.py` example to use tracked paths (`orq/resources/datasets/decision-support-v4/observations.jsonl`, `.../jury-prompt-v3/jury-results.jsonl`). Add a "Reproduce the pipeline" section listing the five v4 scripts in order: generate cases, run simulation, run jury, prepare annotations, upload comparison, each marked offline or paid. Add a License section. Run the prose through the humanizer skill.
- [ ] **Step 4:** Check every relative link in the README resolves: `grep -o '](\([^)#]*\)' README.md | sed 's/](//' | grep -v '^http' | xargs -I{} test -e {} || echo broken`.
- [ ] **Step 5:** Gate green, `uv build` succeeds. Commit `docs: license and README for the public release`.

### Task 7: Scrub pass

- [ ] **Step 1:** Each of these must return nothing (or only a justified hit):

```bash
git grep -nI '/Users/'
git grep -nIi 'linear\.app\|@orq\.ai\|arian\b\|pasquali'
git grep -nI 'my\.orq\.ai' -- ':!tests'
git grep -nIE '[0-9A-HJKMNP-TV-Z]{26}'   # raw ULIDs such as project or experiment ids
git grep -nIi 'workspace' -- '*.md' '*.json'
```

- [ ] **Step 2:** If `gitleaks` or `trufflehog` is installed, run `gitleaks detect --no-git -s .`; otherwise note it was skipped.
- [ ] **Step 3:** Spot-read `observations.jsonl` and one `jury-results.jsonl` for anything that is not synthetic Sphere.com data.
- [ ] **Step 4:** Commit any fixes `chore: scrub remaining internal references`.

### Task 8: Fresh-clone verification

- [ ] **Step 1:** In the scratchpad: `git clone --branch cleanup/public-release <repo> fresh && cd fresh`.
- [ ] **Step 2:** Run with no `.env` and no `DECK_FONT_DIR`:

```bash
uv sync --locked --dev
uv run --no-sync ruff check .
uv run --no-sync pytest -m "not live and not simulation_live and not alignment_live" -q
uv run --no-sync python -c 'from pathlib import Path; from analytics_chatbot.orq_resources import load_resource_bundle; load_resource_bundle(Path("orq/resources"))'
uv run analytics-chatbot seed-data
uv run python scripts/generate_simulation_cases.py --output /tmp/v4.jsonl && cmp /tmp/v4.jsonl orq/resources/datasets/simulation-cases-v4.jsonl
uv run python slides/build_deck.py && git diff --exit-code slides/pydata-2026.html
uv build
```

The resource bundle load needs `ORQ_PROJECT_ID`; if it fails loudly without it, run that one line with `ORQ_PROJECT_ID=example` and confirm the README says so.
- [ ] **Step 3:** Record the file count (`git ls-files | wc -l`, baseline 189) and repo size.

### Task 9: Publish (needs Bauke's explicit go)

- [ ] **Step 1:** Merge `cleanup/public-release` into local `main`.
- [ ] **Step 2 (D1):** Rename the GitHub repo: `gh repo rename building-the-evaluation-flywheel-archive -R Baukebrenninkmeijer/building-the-evaluation-flywheel`. Confirm it is still private.
- [ ] **Step 3:** Build the single commit: `git checkout --orphan public main && git commit -m "Building the evaluation flywheel: companion repository for the PyData 2026 talk"`.
- [ ] **Step 4:** `gh repo create Baukebrenninkmeijer/building-the-evaluation-flywheel --public --description "<current description>"`, then `git push <new-remote> public:main`. Re-point local `origin`; keep the archive as a second remote.
- [ ] **Step 5:** Confirm Offline CI passes on the new repo and the deck QR resolves.

## Out of scope

- Hosted Orq state. The `pydata2026` project keeps the old `analytics-answer-correctness` evaluator and experiments; the sync never deletes. Clean up in the Orq UI separately if wanted.
- Any change to the talk's content or timing.
