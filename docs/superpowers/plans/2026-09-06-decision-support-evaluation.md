# Decision-Support Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recast the analytics-agent example as Sphere.com's decision-support analyst, generate a context-enriched fifty-case v4 corpus, and replace the active reference-oriented LLM judges with one subjective evaluatorq jury: `decision_support_quality`.

**Architecture:** Preserve every tracked v1/edge-v2/v3 corpus and run artifact. Change the deterministic data generator to Sphere.com's appliance taxonomy, derive v4 case definitions from the fifty v3 analytical situations with hand-authored decision contexts and recalculated oracles, carry that context into the replay row, and project reference-free evidence into one local `llm_jury` evaluator. Repository YAML mirrors that subjective contract without applying remote changes; a dedicated offline replay script on evaluatorq 1.35.0 persists the complete jury record exposed for `assignment="all"`.

**Tech Stack:** Python 3.11+, Polars, DuckDB, Pydantic, evaluatorq 1.35.0, Orq resource YAML, pytest, Ruff, Markdown.

## Global Constraints

- Use only the analytics agent in the talk; do not introduce podcast examples.
- Do not modify tracked v1, edge-v2, or v3 dataset JSONL or any existing run artifact.
- Do not add a knowledge base, retrieval corpus, hidden target, or ideal response.
- Keep data fabrication, read-only SQL, evidence, and save-authorization safeguards intact.
- Keep the baseline free of decision-support coaching; it only answers, reports results, and includes SQL.
- The agent recommends action only when the user explicitly requests a recommendation.
- The `decision_support_quality` jury receives no oracle, reference SQL, expected output, or ideal answer.
- Do not implement, configure, or run the three alternative subjective rubrics in this stage.
- Use three distinct judges, `assignment="all"`, `aggregator="majority"`, `min_successful_judges=2`, structured categorical output, and three repetitions for the alignment run.
- Do not run the 450-call jury job, generate live v4 responses, apply hosted resources, alter CI, or automate prompt promotion.
- Keep evaluatorq pinned exactly to the user-confirmed 1.35.0 release whose public `assignment="all"` scorer returns complete jury data. The package gate is satisfied; v4 observation generation, the two-row jury smoke, and the 450-call full jury remain separately approved live operations.
- Update `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md` in the same implementation commit that changes operational reality.

---

## File Map

- `src/analytics_chatbot/data.py`: Sphere.com catalog, customer segments, economics, and `sphere-orders-v1` manifest.
- `src/analytics_chatbot/config.py`: runtime dataset/agent version defaults.
- `src/analytics_chatbot/prompts.py`: rudimentary local baseline prompt.
- `orq/resources/agents/analytics-chatbot.yaml`: matching hosted baseline and Sphere identity.
- `src/analytics_chatbot/evaluation_ops/cases_v4.py`: v3-to-v4 taxonomy migration, fifty decision contexts, v4 builder, preserved split assignment.
- `scripts/generate_simulation_cases.py`: `v4` variant and default v4 output path.
- `orq/resources/datasets/simulation-cases-v4.jsonl`: generated, reviewable v4 definitions; not observed responses.
- `src/analytics_chatbot/evaluation_ops/__init__.py`: decision-context replay contract and the `decision_support_quality` jury specification.
- `src/analytics_chatbot/evaluation_ops/simulation_artifacts.py`: preserve case decision context in normalized replay rows.
- `orq/resources/evaluators/jury/decision-support-quality.yaml`: the single subjective hosted definition; old four LLM YAML files are replaced, while two Python files remain historical and unchanged.
- `src/analytics_chatbot/orq_resources.py`: generic subjective-evaluator evidence guards.
- `scripts/run_decision_support_jury.py`: local no-inference jury replay, call-count gate, and detailed JSONL persistence.
- `pyproject.toml`, `uv.lock`: evaluatorq pinned exactly to the user-confirmed 1.35.0 release.
- `story-outline.md`, `outline.md`: analytics-only talk story aligned with the submitted abstract.
- `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`: living delivery state, evidence, blockers, and handoff.

---

### Task 1: Rebrand the Deterministic Dataset as Sphere.com

**Files:**
- Modify: `src/analytics_chatbot/data.py`
- Modify: `src/analytics_chatbot/config.py`
- Modify: `tests/test_data.py`
- Modify: `tests/test_config.py`

**Interfaces:**
- Produces: `PRODUCTS`, `SEGMENTS`, and `CATEGORY_COST_BASIS_POINTS` for Sphere.com; `seed_database(...) -> DatasetManifest` with `schema_version="sphere-orders-v1"`.
- Consumes: existing deterministic RNG, financial formulas, geography, dates, statuses, and storage schema.

- [ ] **Step 1: Write failing Sphere taxonomy tests**

Add assertions that generated data exposes this exact catalog and segmentation:

```python
EXPECTED_PRODUCTS = {
    "Small Appliances": {"Espresso Machine", "Air Purifier"},
    "Cleaning": {"Robot Vacuum", "Dishwasher"},
    "Laundry": {"Washing Machine", "Tumble Dryer"},
    "Major Appliances": {"Refrigerator", "Heat Pump"},
}
EXPECTED_SEGMENTS = {"Independent Retailers", "Regional Chains", "National Retailers"}


def test_seeded_orders_use_sphere_catalog(tmp_path: Path) -> None:
    path = tmp_path / "sphere.duckdb"
    manifest = seed_database(path)
    with duckdb.connect(str(path), read_only=True) as connection:
        products = connection.execute(
            "SELECT product_category, product FROM orders GROUP BY ALL"
        ).fetchall()
        segments = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT customer_segment FROM orders"
            ).fetchall()
        }
    by_category: dict[str, set[str]] = {}
    for category, product in products:
        by_category.setdefault(category, set()).add(product)
    assert by_category == EXPECTED_PRODUCTS
    assert segments == EXPECTED_SEGMENTS
    assert manifest.schema_version == "sphere-orders-v1"
```

Update the settings test to require:

```python
assert Settings().dataset_version == "sphere-orders-v1"
assert Settings().agent_version == "sphere-baseline-v1"
```

- [ ] **Step 2: Run the focused tests and confirm the old taxonomy fails**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_data.py tests/test_config.py -v`

Expected: FAIL because current data contains `Software`, `Hardware`, `Services`, `Data`, and the version defaults are `revenue-v1` / `v1`.

- [ ] **Step 3: Replace the generator constants without changing its deterministic mechanics**

Use these exact constants in `data.py`:

```python
PRODUCTS: dict[str, tuple[tuple[str, int], ...]] = {
    "Small Appliances": (("Espresso Machine", 29_900), ("Air Purifier", 39_900)),
    "Cleaning": (("Robot Vacuum", 49_900), ("Dishwasher", 69_900)),
    "Laundry": (("Washing Machine", 84_900), ("Tumble Dryer", 74_900)),
    "Major Appliances": (("Refrigerator", 149_900), ("Heat Pump", 249_900)),
}

SEGMENTS = ("Independent Retailers", "Regional Chains", "National Retailers")

CATEGORY_COST_BASIS_POINTS = {
    "Small Appliances": 5_000,
    "Cleaning": 5_800,
    "Laundry": 6_200,
    "Major Appliances": 6_800,
}
```

Replace the `segment == "Enterprise"` quantity branch with `segment == "National Retailers"`, use `CATEGORY_COST_BASIS_POINTS[category]`, and emit `schema_version="sphere-orders-v1"`. Change `Settings.dataset_version` to `sphere-orders-v1` and `Settings.agent_version` to `sphere-baseline-v1`.

- [ ] **Step 4: Verify deterministic generation and financial invariants**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_data.py tests/test_config.py -v`

Expected: all focused tests PASS; two databases seeded with seed 2026 have identical hashes; revenue semantics still have zero violations.

- [ ] **Step 5: Commit the Sphere data model and update the living plan**

Record that the source generator now models Sphere.com, that tracked historic corpus/run artifacts were not regenerated, and that v4 is the only corpus intended for the new baseline.

```bash
git add src/analytics_chatbot/data.py src/analytics_chatbot/config.py tests/test_data.py tests/test_config.py docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat: model Sphere appliance orders"
```

---

### Task 2: Generate the Context-Enriched v4 Corpus

**Files:**
- Create: `src/analytics_chatbot/evaluation_ops/cases_v4.py`
- Modify: `scripts/generate_simulation_cases.py`
- Create: `orq/resources/datasets/simulation-cases-v4.jsonl`
- Modify: `tests/test_simulation_cases.py`
- Modify: `tests/test_generate_simulation_cases_script.py`

**Interfaces:**
- Consumes: `cases_v3.SCENARIOS`, `_expected(Path, str)`, the Sphere DuckDB database, and v3 case IDs for split preservation.
- Produces: `DecisionContext`, `V4_CONTEXTS`, `build_v4_cases(database_path: Path) -> list[dict[str, Any]]`, corpus version `simulation-v4`.

- [ ] **Step 1: Write failing v4 structure and preservation tests**

Add tests with these assertions:

```python
def test_v4_enriches_all_fifty_distinct_v3_situations(tmp_path: Path) -> None:
    database = tmp_path / "sphere.duckdb"
    seed_database(database)
    records = build_v4_cases(database)
    assert len(records) == 50
    assert len({record["id"] for record in records}) == 50
    assert {record["corpus_version"] for record in records} == {"simulation-v4"}
    assert sum(record["split"] == "dev" for record in records) == 30
    assert sum(record["split"] == "test" for record in records) == 20
    assert all(record["id"].startswith("sphere-stakeholder--v4-") for record in records)
    assert all(set(record["decision_context"]) == {
        "stakeholder", "decision", "delivery_setting", "communication_need"
    } for record in records)
    assert all(
        all(value.strip() for value in record["decision_context"].values())
        for record in records
    )
    assert all("Sphere.com" in record["first_message"] for record in records)
    assert not any(
        old in json.dumps(records)
        for old in ("Software", "Hardware", "Services", "Data", "SMB", "Mid-Market", "Enterprise")
    )
```

Snapshot the current tracked v1/v2/v3 JSONL hashes before generation and assert they are identical afterward:

```bash
shasum -a 256 orq/resources/datasets/simulation-cases.jsonl orq/resources/datasets/simulation-cases-v2.jsonl orq/resources/datasets/simulation-cases-v3.jsonl
```

- [ ] **Step 2: Run tests and confirm v4 is absent**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_simulation_cases.py tests/test_generate_simulation_cases_script.py -v`

Expected: FAIL because `cases_v4`, `build_v4_cases`, and CLI variant `v4` do not exist.

- [ ] **Step 3: Implement taxonomy migration and the decision-context contract**

Define:

```python
@dataclass(frozen=True)
class DecisionContext:
    stakeholder: str
    decision: str
    delivery_setting: str
    communication_need: str

    def render(self) -> str:
        return (
            f"I work at Sphere.com as {self.stakeholder}. {self.decision} "
            f"This is for {self.delivery_setting}. {self.communication_need}"
        )


TERM_REPLACEMENTS = {
    "Analytics Pro": "Robot Vacuum",
    "Automation Suite": "Dishwasher",
    "Edge Appliance": "Washing Machine",
    "Sensor Kit": "Tumble Dryer",
    "Implementation": "Refrigerator",
    "Training": "Heat Pump",
    "Market Feed": "Espresso Machine",
    "Risk Dataset": "Air Purifier",
    "Software": "Cleaning",
    "Hardware": "Laundry",
    "Services": "Major Appliances",
    "Data": "Small Appliances",
    "Enterprise": "National Retailers",
    "Mid-Market": "Regional Chains",
    "SMB": "Independent Retailers",
}


def sphere_text(value: str) -> str:
    for old, new in TERM_REPLACEMENTS.items():
        value = value.replace(old, new)
    return value
```

The v4 split is the split of the corresponding v3 case ID, not a new hash over the v4 ID:

```python
ranked_v3_ids = sorted(
    (f"business-analyst--v3-{scenario.key}" for scenario in SCENARIOS),
    key=lambda case_id: hashlib.sha256(case_id.encode()).hexdigest(),
)
dev_keys = {case_id.removeprefix("business-analyst--v3-") for case_id in ranked_v3_ids[:30]}
```

- [ ] **Step 4: Hand-author all fifty decision contexts**

Use this matrix. Turn each row into one `DecisionContext`; write natural sentences rather than concatenating column labels.

| Scenario key | Stakeholder | Decision | Setting | Communication need |
|---|---|---|---|---|
| total-net-2024 | CFO | establish the prior-year revenue baseline for annual planning | board-prep note | lead with the total and scope |
| total-gross-2025 | commercial director | compare booked demand with realized revenue | leadership Slack update | distinguish gross from realized performance |
| net-by-region-2025 | regional lead | choose which region needs the first performance review | operating-review brief | foreground the weakest region, then the ranking |
| top-country-net | CFO | choose the country to feature in the board narrative | one-sentence board brief | name the leader and essential scope first |
| net-by-category-2024 | category director | decide which category needs deeper review | category-review note | show the mix and identify the largest contributor |
| refund-share-apac | finance controller | assess whether APAC refunds need investigation | audit note | make the denominator and definitions explicit |
| avg-order-net-enterprise | national-accounts lead | calibrate account coverage for national retailers | planning memo | state the segment and what the average represents |
| cancelled-count-2025 | operations director | size the operational impact of cancellations | weekly review | pair volume with gross value without calling it realized revenue |
| units-hardware | laundry category manager | assess total unit movement in the laundry category | category Slack thread | lead with units and avoid revenue commentary |
| margin-services | major-appliances director | decide whether the category economics deserve escalation | margin-review note | distinguish reported margin from margin rate |
| avg-discount-smb | independent-retail channel lead | review whether discounting is becoming habitual | commercial review | state the population and avoid causal claims |
| q3-2025-emea-net | EMEA lead | prepare a quarterly performance update | executive email | give the quarter, region, and realized metric immediately |
| best-month-net | CFO | select the month to examine as the revenue high point | board-prep workbook note | identify the month and define the comparison window |
| yoy-net-growth | CEO | frame the quality-of-growth discussion | board briefing | lead with direction and magnitude, then absolute and percentage change |
| pending-exposure | operations director | decide whether pending orders need intervention | risk huddle | separate pipeline exposure from realized revenue |
| germany-vs-france | EMEA lead | decide which country review comes first | regional meeting note | make the comparison and gap easy to scan |
| software-share | cleaning category manager | judge how dependent revenue is on cleaning appliances | category plan | give the share and its denominator clearly |
| cost-ratio-data | small-appliances director | assess category cost intensity | planning note | define cost and denominator without prescribing action |
| top-product-2025 | merchandising director | choose a product for deeper assortment analysis | category briefing | identify the product and avoid equating revenue with profitability |
| refunded-status-net | finance controller | reconcile value retained on refunded orders | audit note | explain what the status and net value mean together |
| distinct-customers-2025 | commercial director | establish the active-customer baseline | planning deck note | report the definition and period concisely |
| missing-column | operations manager | prepare for a meeting requiring shipping-cost evidence | urgent Slack reply | state the data limitation and safest next step |
| future-period | CFO | respond to a request for a period outside the dataset | executive reply | say what is unavailable without substituting another period |
| unknown-region | commercial analyst | validate a Nordics request against available geography | analyst handoff | state the scope mismatch and useful clarification |
| save-top-region | commercial director | preserve the leading-region finding for annual planning | analyst request | calculate first and confirm only an actual successful save |
| no-save-category-2025 | category director | review category performance without persisting a conclusion | working session | summarize the mix and respect the no-save instruction |
| region-then-gap | CFO | understand whether the leading region is meaningfully ahead | multi-turn board prep | retain the original year and metric in the follow-up |
| category-then-yoy | category director | compare category growth before choosing review priorities | multi-turn planning | preserve category scope and make both years explicit |
| gross-then-net-correction | laundry category manager | correct the metric before using it in a category review | multi-turn Slack thread | acknowledge the correction and report only the revised metric |
| refunds-then-share-na | finance controller | judge North American refund exposure relative to sales | multi-turn audit | retain geography and use the requested denominator |
| top3-countries-then-segment | commercial director | see which customer segment leads inside the top-revenue country | multi-turn review | retain the top-country scope and name the leading segment |
| clarify-japan-revenue | APAC lead | prepare a country result where revenue definition matters | executive note | clarify gross versus net before calculating |
| q4-months-then-mom | CFO | identify the Q4 month-to-month change worth discussing | multi-turn board prep | preserve Q4 scope and make comparison direction clear |
| avg-then-median-midmarket | regional-chain lead | choose a representative order-value measure | multi-turn analysis | explain why the changed statistic answers a different question |
| discount-then-cost-of-discount | commercial director | estimate how discounting affects reported gross value | multi-turn planning | retain segment scope and label the counterfactual assumption |
| cancelled-then-realized | operations director | prevent cancelled demand from being presented as realized revenue | multi-turn review | explicitly separate gross cancelled value from realized value |
| save-after-confirm | major-appliances director | review a result before deciding whether it belongs in saved insights | staged request | do not save until the later explicit instruction |
| no-save-then-top | category director | move from category detail to category leadership without persistence | multi-turn working session | keep the no-save constraint active and name the leading category |
| mutation-then-counterfactual | operations director | understand a hypothetical completion scenario without changing source data | risk exercise | refuse mutation and distinguish counterfactual analysis from actual state |
| units-then-price-hardware | laundry category manager | assess whether unit movement and price tell a consistent story | multi-turn category review | preserve product scope and distinguish units from price |
| cost-then-margin-data | small-appliances director | move from category cost to margin interpretation | multi-turn planning | retain year and category while defining margin |
| segment-then-2024-check | commercial director | test whether the leading customer segment was also ahead in 2024 | multi-turn review | retain the winning segment and change only the period |
| singapore-then-apac-share | APAC lead | understand Singapore's contribution to regional revenue | multi-turn regional review | use APAC as denominator and avoid causal explanation |
| ambiguous-best-product | merchandising director | choose a product for management attention | urgent planning request | clarify what best means when the choice could materially change |
| region-gap-yearcheck | CFO | test whether the regional leader changed by year | multi-turn board prep | keep net revenue as the metric and compare both years |
| canada-quarters | North America lead | locate the quarter that deserves a Canadian performance review | regional brief | foreground the weakest or strongest quarter only if the data supports that emphasis |
| category-region-drill | category director | understand how the global leading category's revenue is distributed across regions | multi-turn assortment review | retain the selected category and make the regional split and top-region share explicit |
| refund-rate-drill | finance controller | determine where the company-wide refund rate is concentrated | multi-turn audit | preserve the original denominator through the drill-down |
| save-staged-emea | EMEA lead | verify a regional result before authorizing it as a saved insight | staged request | separate calculation from the later save decision |
| product-drill | merchandising director | understand the leading product's unit movement and discounting | multi-turn category brief | retain the product and distinguish units from average discount rate |

- [ ] **Step 5: Build v4 records and expose the CLI variant**

For each v3 scenario, transform its question, goal, reference SQL, follow-up criterion, and coverage text through `sphere_text`; compute its oracle against the Sphere database; render the decision context into `first_message`; store the structured `decision_context`; and retain state expectations and minimum-turn requirements. Add:

```python
V4_OUTPUT = Path("orq/resources/datasets/simulation-cases-v4.jsonl")
BUILDERS["v4"] = (build_v4_cases, V4_OUTPUT)
```

- [ ] **Step 6: Seed ignored Sphere data, generate the tracked v4 definition, and verify old hashes**

Run:

```bash
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run analytics-chatbot seed-data
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run python scripts/generate_simulation_cases.py --variant v4
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_simulation_cases.py tests/test_generate_simulation_cases_script.py -v
git diff --exit-code -- orq/resources/datasets/simulation-cases.jsonl orq/resources/datasets/simulation-cases-v2.jsonl orq/resources/datasets/simulation-cases-v3.jsonl
```

Expected: 50 v4 records, 30 dev / 20 test, all tests PASS, and no diff in tracked historic datasets.

- [ ] **Step 7: Commit v4 definitions and update the living plan**

```bash
git add src/analytics_chatbot/evaluation_ops/cases_v4.py scripts/generate_simulation_cases.py orq/resources/datasets/simulation-cases-v4.jsonl tests/test_simulation_cases.py tests/test_generate_simulation_cases_script.py docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat: add Sphere decision-context corpus"
```

---

### Task 3: Replace the Active Atomic Judges with Decision-Support Quality

**Files:**
- Modify: `src/analytics_chatbot/evaluation_ops/__init__.py`
- Modify: `src/analytics_chatbot/evaluation_ops/simulation_artifacts.py`
- Modify: `tests/test_evaluation_ops.py`
- Modify: `tests/test_simulation_artifacts.py`

**Interfaces:**
- Produces: `DecisionContextEvidence`, the single `AtomicJudge.DECISION_SUPPORT_QUALITY` value, reference-free evidence projection, and `build_atomic_evaluator(..., repetitions: int = 3)`.
- Consumes: v4 case `decision_context`, recorded conversation/tool events, and final assistant response.

- [ ] **Step 1: Write failing replay-contract tests**

Add `decision_context` to the test row and require round-trip preservation:

```python
"decision_context": {
    "stakeholder": "CFO preparing the board narrative",
    "decision": "decide which region needs review",
    "delivery_setting": "one-paragraph board-prep note",
    "communication_need": "lead with the decision-relevant comparison",
},
```

Assert normalized simulation results copy this field from the case definition rather than target metadata.

- [ ] **Step 2: Write failing subjective-jury configuration tests**

Require these enum values and default order:

```python
assert [judge.value for judge in AtomicJudge] == [
    "decision_support_quality",
]
```

For every captured jury configuration assert `repetitions == 3`, `assignment == "all"`, `aggregator == "majority"`, `min_successful_judges == 2`, and the three categorical labels. Serialize every projected datapoint and assert none of these keys or strings occurs: `expected_output`, `expected_answer`, `reference_sql`, `query_requirements`.

- [ ] **Step 3: Run focused tests and confirm they fail on the old contract**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_evaluation_ops.py tests/test_simulation_artifacts.py -v`

Expected: FAIL on the absent decision context and old correctness/semantics/faithfulness/consistency enum.

- [ ] **Step 4: Add the decision-context replay field**

Define in `evaluation_ops/__init__.py`:

```python
class DecisionContextEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stakeholder: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    delivery_setting: str = Field(min_length=1)
    communication_need: str = Field(min_length=1)
```

Add `decision_context: DecisionContextEvidence | None = None` to `TraceBackedEvaluationRow`. In `normalize_simulation_results`, validate `case["decision_context"]` when present and pass it into the row. Historic traces without the field remain valid and route to `not_applicable`.

- [ ] **Step 5: Implement the decision-support specification**

Replace `AtomicJudge` and `_SPECS`. All specifications apply only when `row.decision_context is not None` and project this exact evidence shape:

```python
def _subjective_evidence(row: TraceBackedEvaluationRow) -> dict[str, Any]:
    assert row.decision_context is not None
    return {
        "decision_context": row.decision_context.model_dump(mode="json"),
        "conversation": _conversation(row),
        "tool_events": [event.model_dump(mode="json") for event in row.tool_events],
        "final_response": row.assistant_response,
    }
```

Use the `decision_support_quality` criterion verbatim from the approved design spec. The common prompt must explicitly state:

```text
You have no reference answer or ideal response. Do not recompute the analysis or grade SQL.
Judge only the named criterion from the stated stakeholder, decision, delivery setting,
conversation, visible execution evidence, and final response. Return pass or fail.
Return not_applicable only when the required decision context is absent or the criterion itself
does not apply to the request.
```

Make `build_atomic_evaluator` and `build_atomic_evaluators` accept `repetitions: int = 3` and pass it through to `llm_jury`. Default `run_trace_evaluation` to `AtomicJudge.DECISION_SUPPORT_QUALITY`.

- [ ] **Step 6: Verify reference-free projections and routing**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_evaluation_ops.py tests/test_simulation_artifacts.py -v`

Expected: all focused tests PASS, historic rows without decision context skip the jury, and v4 rows expose no oracle evidence to any subjective judge.

- [ ] **Step 7: Commit the subjective runtime contract and update the living plan**

```bash
git add src/analytics_chatbot/evaluation_ops/__init__.py src/analytics_chatbot/evaluation_ops/simulation_artifacts.py tests/test_evaluation_ops.py tests/test_simulation_artifacts.py docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat: add subjective decision-support juries"
```

---

### Task 4: Mirror the Rubric in Repository Resources and Simplify the Baseline

**Files:**
- Modify: `src/analytics_chatbot/prompts.py`
- Modify: `orq/resources/agents/analytics-chatbot.yaml`
- Delete: `orq/resources/evaluators/jury/answer-correctness.yaml`
- Delete: `orq/resources/evaluators/jury/query-semantics.yaml`
- Delete: `orq/resources/evaluators/jury/evidence-faithfulness.yaml`
- Delete: `orq/resources/evaluators/jury/multi-turn-consistency.yaml`
- Create: `orq/resources/evaluators/jury/decision-support-quality.yaml`
- Modify: `src/analytics_chatbot/orq_resources.py`
- Modify: `tests/test_orq_resources.py`
- Modify: `tests/test_agent.py`

**Interfaces:**
- Produces: one rudimentary baseline prompt shared semantically by local and hosted execution; one shadow hosted evaluator payload matching Task 3.
- Consumes: the existing YAML loader, three approved model slugs, and categorical output resource schema.

- [ ] **Step 1: Write failing baseline and resource tests**

Assert the agent identifies Sphere.com and retains the hard safeguards, while none of these phrases appears in either prompt: `foreground`, `decision impact`, `adapt detail`, `recommend next steps`, `board narrative`.

Require the LLM evaluator keys:

```python
assert llm_keys == {
    "analytics-decision-support-quality",
}
```

Require every LLM resource to be jury mode, use three judges, `repetitions: 3`, have `validation.status: pending_human_labels`, and omit all reference-family template variables.

- [ ] **Step 2: Run tests and confirm the old resources fail**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_orq_resources.py tests/test_agent.py -v`

Expected: FAIL because the old analytics identity and reference-oriented resource keys remain.

- [ ] **Step 3: Reduce both agent prompts to the rudimentary baseline**

Use this communication contract after the unchanged safety/tool constraints:

```text
Answer the analytical question from successful query results. Report the requested metric,
scope, period, and units, and include the supporting SQL. If a required definition is materially
ambiguous, ask one focused clarification question. Do not recommend an action unless the user
explicitly asks for one.
```

Describe the agent as Sphere.com's analytics chatbot over wholesale home-appliance orders. Do not
add instructions for stakeholder adaptation, decision emphasis, business interpretation, or
proactive next steps.

- [ ] **Step 4: Replace the four old LLM YAML definitions with one decision-support definition**

The file uses the approved three-model panel, `mode: jury`, `min_successful_judges: 2`,
`repetitions: 3`, categorical labels `pass` / `fail` / `not_applicable`, and mappings for:

```yaml
input.all_messages: full ordered conversation including tool calls and results
output.response: final assistant response
```

The stakeholder, decision, setting, and communication need are read from the agent-visible user
message inside `input.all_messages`; do not invent a custom hosted trace variable. Copy the
criterion exactly from Task 3. Mark it `pending_human_labels` with zero labels. Do not touch
`orq/resources/evaluators/python/*.yaml`; they remain historical, are not featured, and receive no
further development.

- [ ] **Step 5: Replace key-specific reference guards with a subjective evidence guard**

In `LlmEvaluatorResource.validate_prompt_contract`, for the new stable key, require
`input.all_messages` and `output.response`; forbid `input.decision_context`,
`input.expected_output`, `reference_sql`, `query_requirements`, and any prompt phrase claiming a
reference or ideal answer exists.

- [ ] **Step 6: Verify resource compilation without applying it**

Run:

```bash
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_orq_resources.py tests/test_agent.py -v
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run python scripts/sync_orq_resources.py --resources orq/resources
```

Expected: focused tests PASS; dry-run loads one agent, two tools, two unchanged Python evaluators,
and one pending subjective LLM evaluator; no remote apply occurs.

- [ ] **Step 7: Commit prompts/resources and update the living plan**

```bash
git add src/analytics_chatbot/prompts.py orq/resources/agents/analytics-chatbot.yaml orq/resources/evaluators/jury src/analytics_chatbot/orq_resources.py tests/test_orq_resources.py tests/test_agent.py docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat: define Sphere subjective evaluator resources"
```

---

### Task 5: Require and Persist the Detailed evaluatorq Jury Record

**Files:**
- Modify after dependency gate: `pyproject.toml`
- Modify after dependency gate: `uv.lock`
- Create: `scripts/run_decision_support_jury.py`
- Create: `tests/test_run_decision_support_jury.py`
- Modify: `tests/test_evaluation_ops.py`

**Interfaces:**
- Consumes: the exact evaluatorq release supplied by the user, v4 case JSONL, a v4 observed-results JSONL, `load_simulation_replay`, and `build_atomic_evaluator(AtomicJudge.DECISION_SUPPORT_QUALITY, repetitions=3)`.
- Produces: one joined local JSONL record per corpus row with `raw_output.jury` preserved byte-for-byte from evaluatorq's typed result.

- [x] **Step 1: Stop at the release gate**

Gate satisfied on 2026-09-06: the user explicitly confirmed evaluatorq 1.35.0, published on PyPI at 2026-09-06 14:24 UTC, for the `assignment="all"` result-flow change. The pin remains exact; no unreleased checkout is used.

- [x] **Step 2: Write the failing detailed-result contract test before upgrading**

Monkeypatch `evaluatorq.llm_jury._run_single_judge` to return controlled `Prediction` values across
three models and three repetitions. Invoke the public `llm_jury` scorer with `assignment="all"` and
assert:

```python
jury = result.raw_output["jury"]
assert jury["judges_configured"] == 3
assert jury["judges_succeeded"] == 3
assert jury["raw_agreement"] == pytest.approx(2 / 3)
assert [vote["model"] for vote in jury["votes"]] == [
    "openai/model-a", "anthropic/model-b", "google/model-c"
]
assert all(len(vote["repetitions"]) == 3 for vote in jury["votes"])
assert all("explanation" in vote for vote in jury["votes"])
```

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_evaluation_ops.py::test_llm_jury_returns_detailed_all_assignment_record -v`

Expected on 1.33.0: FAIL because `result.raw_output` is `None`.

- [x] **Step 3: Pin the exact supplied release and lock it**

Replace `evaluatorq==1.33.0` with the exact version supplied at Step 1, then run:

```bash
UV_CACHE_DIR=/tmp/pydata-uv-cache uv lock --upgrade-package evaluatorq
UV_CACHE_DIR=/tmp/pydata-uv-cache uv sync
```

Expected: the lock contains exactly the supplied evaluatorq version and no unrelated direct
dependency changes.

- [x] **Step 4: Verify the public jury contract passes**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_evaluation_ops.py::test_llm_jury_returns_detailed_all_assignment_record -v`

Expected: PASS with three model votes and nine raw repetition verdict slots present.

- [x] **Step 5: Write failing offline-runner tests**

Test parser validation, the exact call count (`rows * judges * repetitions`), refusal without
`--approve-calls`, selection of only `decision_support_quality`, no-inference replay, and complete
serialization of `score.raw_output["jury"]`. The script must reject a score whose jury record is
missing or whose vote/repetition counts differ from 3/3.

- [x] **Step 6: Implement the guarded offline runner**

Expose:

```python
EXPECTED_JUDGES = 3
EXPECTED_REPETITIONS = 3


def expected_calls(row_count: int) -> int:
    return row_count * EXPECTED_JUDGES * EXPECTED_REPETITIONS


def validate_jury_record(raw_output: object) -> dict[str, Any]:
    if not isinstance(raw_output, dict) or not isinstance(raw_output.get("jury"), dict):
        raise JuryReplayError("decision-support score is missing raw_output.jury")
    jury = raw_output["jury"]
    votes = jury.get("votes")
    if not isinstance(votes, list) or len(votes) != EXPECTED_JUDGES:
        raise JuryReplayError("decision-support jury must retain exactly three votes")
    if any(len(vote.get("repetitions", [])) != EXPECTED_REPETITIONS for vote in votes):
        raise JuryReplayError("each decision-support vote must retain three repetitions")
    return jury
```

The CLI takes `--cases`, `--results`, `--output`, and `--approve-calls`. It prints the row/judge/
repetition multiplication and exits successfully without model calls when approval is absent. With
approval, it calls `run_trace_evaluation(..., inference=False)` through the existing native path and
writes case ID, split, transcript fingerprint, decision context, recorded output, aggregate value,
explanation, pass value, and the complete jury record.

- [x] **Step 7: Verify the runner offline with fakes only**

Run: `UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest tests/test_run_decision_support_jury.py tests/test_evaluation_ops.py -v`

Expected: all tests PASS; no API key or network call is required.

- [x] **Step 8: Commit the dependency and detailed-result runner, then update the living plan**

Record the exact evaluatorq version and contract evidence. Keep the full live run `NOT STARTED` and
name its 450-call approval gate.

```bash
git add pyproject.toml uv.lock scripts/run_decision_support_jury.py tests/test_run_decision_support_jury.py tests/test_evaluation_ops.py docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "feat: preserve detailed decision-support jury votes"
```

---

### Task 6: Align the Talk Documents and Verify the Repository

**Files:**
- Modify: `story-outline.md`
- Modify: `outline.md`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-09-03-project-status-and-handoff.md`

**Interfaces:**
- Consumes: implemented Sphere corpus/evaluator contracts and fresh verification evidence.
- Produces: one analytics-only story, accurate operator documentation, and an auditable handoff.

- [ ] **Step 1: Rewrite the story outline around the submitted abstract**

Use this exact narrative spine:

1. A technically plausible analytics answer is not necessarily useful for a business decision.
2. Sphere.com and its quality-of-growth board question provide the running example.
3. Fifty context-enriched cases replace generic spot checks with stakeholder decisions.
4. The rudimentary baseline answers questions but does not reliably support decisions.
5. `decision_support_quality` makes the subjective boundary explicit.
6. Three repeated jury judges expose self-wobble and cross-model disagreement.
7. Disagreement orders the human annotation queue; unanimous samples check confident consensus.
8. Human rules drive the alignment rewrite; measured claims cover only annotated rows.
9. Once aligned, the evaluator becomes a CI regression check.
10. Separate analysis, improvement, and validation agents can use critiques under human promotion
    authority.
11. Close with the trust rule: trust automation only inside the slice tested against humans; stop
    when disagreement, drift, or false passes leave that slice.

Delete every podcast reference, deterministic-grader beat, claim of completed v4 measurement, and
claim that all fifty examples are hand-reviewed before that evidence exists.

- [ ] **Step 2: Reconcile the timed outline**

Map the story to 25 speaking minutes plus 5 Q&A:

- evaluation gap and Sphere cold open: 3 minutes;
- corpus and rudimentary baseline: 4 minutes;
- subjective rubric and jury: 6 minutes;
- disagreement-led human alignment: 7 minutes;
- CI/self-improvement steps and limitations: 3 minutes;
- takeaways: 2 minutes;
- Q&A: 5 minutes.

Keep final response, trajectory, and state changes as concepts promised by the abstract, but do not
invent new deterministic evaluators or give them implementation time. The live technical walkthrough
uses the recorded analytics trace and the local jury artifact only after those artifacts exist.

- [ ] **Step 3: Update README commands and status language**

Document Sphere data seeding, `--variant v4`, the single shadow evaluator name, and the guarded jury
runner. State plainly that v4 observed responses and human alignment evidence do not exist until run
artifacts are accepted.

- [ ] **Step 4: Run full fresh verification**

Run:

```bash
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run ruff check .
UV_CACHE_DIR=/tmp/pydata-uv-cache uv run pytest -m "not live"
UV_CACHE_DIR=/tmp/pydata-uv-cache uv build
git diff --check
git diff --exit-code -- orq/resources/datasets/simulation-cases.jsonl orq/resources/datasets/simulation-cases-v2.jsonl orq/resources/datasets/simulation-cases-v3.jsonl
```

Expected: Ruff clean, all offline tests PASS, sdist and wheel build successfully, no whitespace
errors, and every tracked historic corpus is unchanged.

- [ ] **Step 5: Update the living handoff with exact evidence**

Set the status date to the execution date. Record Sphere dataset/corpus status, subjective evaluator
status, exact test/lint/build output, evaluatorq version, and the unpublished operations gates:
generating fifty v4 observations, running the 450-call jury, prioritizing annotation, and entering
the evaluator-alignment workflow. Mark only implemented and freshly verified code `VERIFIED`.

- [ ] **Step 6: Commit the talk and handoff reconciliation**

```bash
git add story-outline.md outline.md README.md docs/superpowers/plans/2026-09-03-project-status-and-handoff.md
git commit -m "docs: align PyData story with decision-support evaluation"
```

---

## Execution Boundary

Completing this plan produces code, definitions, and documentation only. The first live v4
simulation remains a separate one-run operation. The first full jury invocation remains a separate
450-call paid operation. Hosted resource application, human annotation, evaluator rewriting, CI
gating, and multi-agent prompt optimization each require their own evidence and approval.
