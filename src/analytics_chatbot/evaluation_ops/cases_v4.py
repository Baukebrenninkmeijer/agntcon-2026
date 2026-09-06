"""Sphere.com simulation corpus v4 with explicit decision-support context."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evaluatorq.simulation import Criterion, Persona, Scenario, SimulationDatapoint

from analytics_chatbot.evaluation_ops.cases import _expected
from analytics_chatbot.evaluation_ops.cases_v3 import SCENARIOS, V3Scenario, _criteria

CORPUS_VERSION = "simulation-v4"

PERSONA = Persona(
    name="sphere-stakeholder",
    patience=0.7,
    assertiveness=0.7,
    politeness=0.7,
    technical_level=0.5,
    communication_style="casual",
    background=(
        "A Sphere.com stakeholder using analysis of appliance orders to make a business "
        "decision. Expects evidence, appropriate scope, and communication suited to the stated "
        "setting."
    ),
)


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
    """Translate the historic demo taxonomy into Sphere.com's appliance taxonomy."""

    for old, new in TERM_REPLACEMENTS.items():
        value = value.replace(old, new)
    return value


def _context(
    stakeholder: str,
    decision: str,
    delivery_setting: str,
    communication_need: str,
) -> DecisionContext:
    article = "an" if delivery_setting[0].lower() in "aeiou" else "a"
    return DecisionContext(
        stakeholder=stakeholder,
        decision=f"I need to {decision}.",
        delivery_setting=f"{article} {delivery_setting}",
        communication_need=f"Please {communication_need}.",
    )


V4_CONTEXTS: dict[str, DecisionContext] = {
    "total-net-2024": _context(
        "CFO",
        "establish the prior-year revenue baseline for annual planning",
        "board-prep note",
        "lead with the total and scope",
    ),
    "total-gross-2025": _context(
        "commercial director",
        "compare booked demand with realized revenue",
        "leadership Slack update",
        "distinguish gross from realized performance",
    ),
    "net-by-region-2025": _context(
        "regional lead",
        "choose which region needs the first performance review",
        "operating-review brief",
        "foreground the weakest region, then the ranking",
    ),
    "top-country-net": _context(
        "CFO",
        "choose the country to feature in the board narrative",
        "one-sentence board brief",
        "name the leader and essential scope first",
    ),
    "net-by-category-2024": _context(
        "category director",
        "decide which category needs deeper review",
        "category-review note",
        "show the mix and identify the largest contributor",
    ),
    "refund-share-apac": _context(
        "finance controller",
        "assess whether APAC refunds need investigation",
        "audit note",
        "make the denominator and definitions explicit",
    ),
    "avg-order-net-enterprise": _context(
        "national-accounts lead",
        "calibrate account coverage for national retailers",
        "planning memo",
        "state the segment and what the average represents",
    ),
    "cancelled-count-2025": _context(
        "operations director",
        "size the operational impact of cancellations",
        "weekly review",
        "pair volume with gross value without calling it realized revenue",
    ),
    "units-hardware": _context(
        "laundry category manager",
        "assess total unit movement in the laundry category",
        "category Slack thread",
        "lead with units and avoid revenue commentary",
    ),
    "margin-services": _context(
        "major-appliances director",
        "decide whether the category economics deserve escalation",
        "margin-review note",
        "distinguish reported margin from margin rate",
    ),
    "avg-discount-smb": _context(
        "independent-retail channel lead",
        "review whether discounting is becoming habitual",
        "commercial review",
        "state the population and avoid causal claims",
    ),
    "q3-2025-emea-net": _context(
        "EMEA lead",
        "prepare a quarterly performance update",
        "executive email",
        "give the quarter, region, and realized metric immediately",
    ),
    "best-month-net": _context(
        "CFO",
        "select the month to examine as the revenue high point",
        "board-prep workbook note",
        "identify the month and define the comparison window",
    ),
    "yoy-net-growth": _context(
        "CEO",
        "frame the quality-of-growth discussion",
        "board briefing",
        "lead with direction and magnitude, then absolute and percentage change",
    ),
    "pending-exposure": _context(
        "operations director",
        "decide whether pending orders need intervention",
        "risk huddle",
        "separate pipeline exposure from realized revenue",
    ),
    "germany-vs-france": _context(
        "EMEA lead",
        "decide which country review comes first",
        "regional meeting note",
        "make the comparison and gap easy to scan",
    ),
    "software-share": _context(
        "cleaning category manager",
        "judge how dependent revenue is on cleaning appliances",
        "category plan",
        "give the share and its denominator clearly",
    ),
    "cost-ratio-data": _context(
        "small-appliances director",
        "assess category cost intensity",
        "planning note",
        "define cost and denominator without prescribing action",
    ),
    "top-product-2025": _context(
        "merchandising director",
        "choose a product for deeper assortment analysis",
        "category briefing",
        "identify the product and avoid equating revenue with profitability",
    ),
    "refunded-status-net": _context(
        "finance controller",
        "reconcile value retained on refunded orders",
        "audit note",
        "explain what the status and net value mean together",
    ),
    "distinct-customers-2025": _context(
        "commercial director",
        "establish the active-customer baseline",
        "planning deck note",
        "report the definition and period concisely",
    ),
    "missing-column": _context(
        "operations manager",
        "prepare for a meeting requiring shipping-cost evidence",
        "urgent Slack reply",
        "state the data limitation and safest next step",
    ),
    "future-period": _context(
        "CFO",
        "respond to a request for a period outside the dataset",
        "executive reply",
        "say what is unavailable without substituting another period",
    ),
    "unknown-region": _context(
        "commercial analyst",
        "validate a Nordics request against available geography",
        "analyst handoff",
        "state the scope mismatch and useful clarification",
    ),
    "save-top-region": _context(
        "commercial director",
        "preserve the leading-region finding for annual planning",
        "analyst request",
        "calculate first and confirm only an actual successful save",
    ),
    "no-save-category-2025": _context(
        "category director",
        "review category performance without persisting a conclusion",
        "working session",
        "summarize the mix and respect the no-save instruction",
    ),
    "region-then-gap": _context(
        "CFO",
        "understand whether the leading region is meaningfully ahead",
        "multi-turn board prep",
        "retain the original year and metric in the follow-up",
    ),
    "category-then-yoy": _context(
        "category director",
        "compare category growth before choosing review priorities",
        "multi-turn planning",
        "preserve category scope and make both years explicit",
    ),
    "gross-then-net-correction": _context(
        "laundry category manager",
        "correct the metric before using it in a category review",
        "multi-turn Slack thread",
        "acknowledge the correction and report only the revised metric",
    ),
    "refunds-then-share-na": _context(
        "finance controller",
        "judge North American refund exposure relative to sales",
        "multi-turn audit",
        "retain geography and use the requested denominator",
    ),
    "top3-countries-then-segment": _context(
        "commercial director",
        "see whether country leadership changes within a customer segment",
        "multi-turn review",
        "retain ranking scope and name the segment",
    ),
    "clarify-japan-revenue": _context(
        "APAC lead",
        "prepare a country result where revenue definition matters",
        "executive note",
        "clarify gross versus net before calculating",
    ),
    "q4-months-then-mom": _context(
        "CFO",
        "identify the Q4 month-to-month change worth discussing",
        "multi-turn board prep",
        "preserve Q4 scope and make comparison direction clear",
    ),
    "avg-then-median-midmarket": _context(
        "regional-chain lead",
        "choose a representative order-value measure",
        "multi-turn analysis",
        "explain why the changed statistic answers a different question",
    ),
    "discount-then-cost-of-discount": _context(
        "commercial director",
        "estimate how discounting affects reported gross value",
        "multi-turn planning",
        "retain segment scope and label the counterfactual assumption",
    ),
    "cancelled-then-realized": _context(
        "operations director",
        "prevent cancelled demand from being presented as realized revenue",
        "multi-turn review",
        "explicitly separate gross cancelled value from realized value",
    ),
    "save-after-confirm": _context(
        "major-appliances director",
        "review a result before deciding whether it belongs in saved insights",
        "staged request",
        "do not save until the later explicit instruction",
    ),
    "no-save-then-top": _context(
        "category director",
        "move from category detail to product leadership without persistence",
        "multi-turn working session",
        "keep the no-save constraint active and answer the follow-up",
    ),
    "mutation-then-counterfactual": _context(
        "operations director",
        "understand a hypothetical completion scenario without changing source data",
        "risk exercise",
        "refuse mutation and distinguish counterfactual analysis from actual state",
    ),
    "units-then-price-hardware": _context(
        "laundry category manager",
        "assess whether unit movement and price tell a consistent story",
        "multi-turn category review",
        "preserve product scope and distinguish units from price",
    ),
    "cost-then-margin-data": _context(
        "small-appliances director",
        "move from category cost to margin interpretation",
        "multi-turn planning",
        "retain year and category while defining margin",
    ),
    "segment-then-2024-check": _context(
        "commercial director",
        "test whether the leading customer segment was also ahead in 2024",
        "multi-turn review",
        "retain the winning segment and change only the period",
    ),
    "singapore-then-apac-share": _context(
        "APAC lead",
        "understand Singapore's contribution to regional revenue",
        "multi-turn regional review",
        "use APAC as denominator and avoid causal explanation",
    ),
    "ambiguous-best-product": _context(
        "merchandising director",
        "choose a product for management attention",
        "urgent planning request",
        "clarify what best means when the choice could materially change",
    ),
    "region-gap-yearcheck": _context(
        "CFO",
        "test whether the regional leader changed by year",
        "multi-turn board prep",
        "keep net revenue as the metric and compare both years",
    ),
    "canada-quarters": _context(
        "North America lead",
        "locate the quarter that deserves a Canadian performance review",
        "regional brief",
        "foreground the weakest or strongest quarter only if the data supports that emphasis",
    ),
    "category-region-drill": _context(
        "category director",
        "see whether the global category leader also leads in a chosen region",
        "multi-turn assortment review",
        "retain the selected category and make regional scope explicit",
    ),
    "refund-rate-drill": _context(
        "finance controller",
        "determine where the company-wide refund rate is concentrated",
        "multi-turn audit",
        "preserve the original denominator through the drill-down",
    ),
    "save-staged-emea": _context(
        "EMEA lead",
        "verify a regional result before authorizing it as a saved insight",
        "staged request",
        "separate calculation from the later save decision",
    ),
    "product-drill": _context(
        "merchandising director",
        "identify where the leading product's revenue is concentrated",
        "multi-turn category brief",
        "retain the product and rank the requested breakdown",
    ),
}


def _sphere_criteria(scenario: V3Scenario) -> list[Criterion]:
    return [
        Criterion(description=sphere_text(item.description), type=item.type)
        for item in _criteria(scenario)
    ]


def build_v4_cases(database_path: Path) -> list[dict[str, Any]]:
    """Enrich all fifty v3 situations with Sphere.com decision context and fresh oracles."""

    ranked_v3_ids = sorted(
        (f"business-analyst--v3-{scenario.key}" for scenario in SCENARIOS),
        key=lambda case_id: hashlib.sha256(case_id.encode()).hexdigest(),
    )
    dev_keys = {
        case_id.removeprefix("business-analyst--v3-") for case_id in ranked_v3_ids[:30]
    }

    records: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        decision_context = V4_CONTEXTS[scenario.key]
        reference_sql = sphere_text(scenario.reference_sql) if scenario.reference_sql else None
        oracle = None
        if reference_sql:
            oracle = {
                "reference_sql": reference_sql,
                "expected": _expected(database_path, reference_sql),
                "comparison": "exact",
            }

        staged = scenario.min_user_turns > 1
        question = sphere_text(scenario.first_message)
        goal = sphere_text(scenario.goal)
        datapoint = SimulationDatapoint(
            id=f"{PERSONA.name}--v4-{scenario.key}",
            persona=PERSONA,
            scenario=Scenario(
                name=f"v4-{scenario.key}",
                goal=goal,
                context=(
                    "Sphere.com's orders dataset is deterministic and covers calendar years "
                    "2024 and 2025. "
                    + (
                        "Reveal later constraints only in the follow-up described by the goal; "
                        "do not collapse stages into the first message."
                        if staged
                        else "Ask one question and accept a complete, evidence-backed answer."
                    )
                ),
                criteria=_sphere_criteria(scenario),
                is_edge_case=scenario.edge,
                conversation_strategy=scenario.strategy,
                ground_truth=goal,
            ),
            user_system_prompt="",
            first_message=f"{decision_context.render()}\n\n{question}",
        )
        records.append(
            {
                **datapoint.model_dump(mode="json"),
                "decision_context": asdict(decision_context),
                "coverage": [
                    *(sphere_text(label) for label in scenario.coverage),
                    *(["multi-turn-required"] if staged else []),
                ],
                "oracle": oracle,
                "state_expectation": {"authorized": scenario.must_save}
                if scenario.must_save is not None
                else None,
                "expected_min_user_turns": scenario.min_user_turns,
                "corpus_version": CORPUS_VERSION,
                "generation_provenance": (
                    "hand-authored Sphere.com decision contexts over the fifty v3 analytical "
                    "situations; executable oracle computed from sphere-orders-v1 DuckDB"
                ),
                "split": "dev" if scenario.key in dev_keys else "test",
            }
        )
    return records


assert len(V4_CONTEXTS) == len(SCENARIOS) == 50
assert set(V4_CONTEXTS) == {scenario.key for scenario in SCENARIOS}
