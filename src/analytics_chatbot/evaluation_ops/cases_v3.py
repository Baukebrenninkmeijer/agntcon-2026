"""Simulation corpus v3: one persona, fifty distinct situations.

v2 crossed five personas with ten scenarios, so a single hard scenario family showed up five
times and dominated the judge-instability list. v3 keeps one persona and varies the situation
instead: every row is a different question, period, filter, or conversational shape.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluatorq.simulation import Criterion, Persona, Scenario, SimulationDatapoint

from analytics_chatbot.evaluation_ops.cases import _expected

CORPUS_VERSION = "simulation-v3"

PERSONA = Persona(
    name="business-analyst",
    patience=0.8,
    assertiveness=0.7,
    politeness=0.7,
    technical_level=0.7,
    communication_style="casual",
    background=(
        "A business analyst preparing a revenue review. Asks concrete questions, expects exact "
        "figures with the SQL behind them, and follows up when the first answer is incomplete."
    ),
)

Y24 = "order_date >= DATE '2024-01-01' AND order_date < DATE '2025-01-01'"
Y25 = "order_date >= DATE '2025-01-01' AND order_date < DATE '2026-01-01'"
FABRICATION = Criterion(
    description="The agent fabricates a number or claims a tool/state outcome that did not occur.",
    type="must_not_happen",
)
EVIDENCE = Criterion(
    description="A successful query_sql result supports every material numeric claim.",
    type="must_happen",
)


@dataclass(frozen=True)
class V3Scenario:
    key: str
    first_message: str
    goal: str
    reference_sql: str | None
    coverage: tuple[str, ...]
    strategy: str = "cooperative"
    must_save: bool | None = None
    edge: bool = False
    min_user_turns: int = 1
    followup_criterion: str | None = None


def _s(*args: Any, **kwargs: Any) -> V3Scenario:
    return V3Scenario(*args, **kwargs)


SCENARIOS: tuple[V3Scenario, ...] = (
    # --- single-turn aggregates -------------------------------------------------------------
    _s(
        "total-net-2024",
        "What was our total net revenue in 2024?",
        "Obtain the exact 2024 total net revenue with supporting SQL.",
        f"SELECT SUM(net_revenue) AS value FROM orders WHERE {Y24}",
        ("period-boundary", "aggregation"),
    ),
    _s(
        "total-gross-2025",
        "Give me total gross revenue for 2025.",
        "Obtain the exact 2025 gross revenue, not net, with supporting SQL.",
        f"SELECT SUM(gross_revenue) AS value FROM orders WHERE {Y25}",
        ("period-boundary", "net-vs-gross"),
    ),
    _s(
        "net-by-region-2025",
        "Break down 2025 net revenue by region.",
        "Obtain net revenue for each of the four regions in 2025.",
        f"SELECT region, SUM(net_revenue) AS value FROM orders WHERE {Y25} "
        "GROUP BY region ORDER BY region",
        ("aggregation", "period-boundary"),
    ),
    _s(
        "top-country-net",
        "Which country brought in the most net revenue over the whole dataset?",
        "Identify the single top country by total net revenue and its figure.",
        "SELECT country, SUM(net_revenue) AS value FROM orders GROUP BY country "
        "ORDER BY value DESC, country LIMIT 1",
        ("ranking", "aggregation"),
    ),
    _s(
        "net-by-category-2024",
        "How did 2024 net revenue split across product categories?",
        "Obtain 2024 net revenue per product category.",
        f"SELECT product_category, SUM(net_revenue) AS value FROM orders WHERE {Y24} "
        "GROUP BY product_category ORDER BY product_category",
        ("aggregation", "period-boundary"),
    ),
    _s(
        "refund-share-apac",
        "How much did we refund in APAC, and what share of APAC gross revenue is that?",
        "Compute APAC refunds and the share against APAC gross revenue as the denominator.",
        "SELECT SUM(refund_amount) AS refunds, SUM(gross_revenue) AS gross, "
        "SUM(refund_amount) / NULLIF(SUM(gross_revenue), 0) AS share FROM orders "
        "WHERE region = 'APAC'",
        ("refunds", "denominator"),
    ),
    _s(
        "avg-order-net-enterprise",
        "What is the average net revenue per order for Enterprise customers?",
        "Compute the mean net revenue per Enterprise order across the full dataset.",
        "SELECT AVG(net_revenue) AS value FROM orders WHERE customer_segment = 'Enterprise'",
        ("average", "aggregation"),
    ),
    _s(
        "cancelled-count-2025",
        "How many orders were cancelled in 2025, and what gross value did they carry?",
        "Report the 2025 cancelled order count and their summed gross revenue.",
        f"SELECT COUNT(*) AS orders, SUM(gross_revenue) AS gross FROM orders WHERE {Y25} "
        "AND order_status = 'cancelled'",
        ("cancellations", "counting"),
    ),
    _s(
        "units-hardware",
        "How many Hardware units did we sell in total?",
        "Sum quantity for the Hardware category across the full dataset.",
        "SELECT SUM(quantity) AS value FROM orders WHERE product_category = 'Hardware'",
        ("units", "aggregation"),
    ),
    _s(
        "margin-services",
        "What margin did Services make, defining margin as net revenue minus cost?",
        "Compute net revenue minus cost for the Services category, using the stated definition.",
        "SELECT SUM(net_revenue) - SUM(cost) AS value FROM orders "
        "WHERE product_category = 'Services'",
        ("margin", "definition-given"),
    ),
    _s(
        "avg-discount-smb",
        "What is the average discount rate on SMB orders?",
        "Report the mean discount_rate for SMB orders as a rate, not an amount.",
        "SELECT AVG(discount_rate) AS value FROM orders WHERE customer_segment = 'SMB'",
        ("average", "rate-vs-amount"),
    ),
    _s(
        "q3-2025-emea-net",
        "What was EMEA net revenue in Q3 2025?",
        "Obtain EMEA net revenue for July through September 2025 with correct boundaries.",
        "SELECT SUM(net_revenue) AS value FROM orders WHERE region = 'EMEA' "
        "AND order_date >= DATE '2025-07-01' AND order_date < DATE '2025-10-01'",
        ("period-boundary", "quarter"),
    ),
    _s(
        "best-month-net",
        "Which calendar month had the highest net revenue?",
        "Identify the single best month across both years and its net revenue.",
        "SELECT STRFTIME(order_month, '%Y-%m') AS month, SUM(net_revenue) AS value FROM orders "
        "GROUP BY month ORDER BY value DESC, month LIMIT 1",
        ("ranking", "period-boundary"),
    ),
    _s(
        "yoy-net-growth",
        "How much did net revenue grow from 2024 to 2025, in absolute terms and as a percentage?",
        "Report both yearly totals, the absolute difference, and the percentage growth.",
        f"SELECT SUM(CASE WHEN {Y24} THEN net_revenue END) AS net_2024, "
        f"SUM(CASE WHEN {Y25} THEN net_revenue END) AS net_2025, "
        f"SUM(CASE WHEN {Y25} THEN net_revenue END) - "
        f"SUM(CASE WHEN {Y24} THEN net_revenue END) AS delta, "
        f"(SUM(CASE WHEN {Y25} THEN net_revenue END) / "
        f"NULLIF(SUM(CASE WHEN {Y24} THEN net_revenue END), 0)) - 1 AS growth FROM orders",
        ("growth", "period-boundary"),
    ),
    _s(
        "pending-exposure",
        "What gross value is sitting in pending orders, and how much of it counts as net revenue?",
        "Report pending gross revenue and state that pending net revenue is zero.",
        "SELECT SUM(gross_revenue) AS gross, SUM(net_revenue) AS net FROM orders "
        "WHERE order_status = 'pending'",
        ("pending", "net-vs-gross"),
    ),
    _s(
        "germany-vs-france",
        "Compare Germany and France on total net revenue.",
        "Report both countries' net revenue and which is larger.",
        "SELECT country, SUM(net_revenue) AS value FROM orders "
        "WHERE country IN ('Germany', 'France') GROUP BY country ORDER BY country",
        ("comparison", "aggregation"),
    ),
    _s(
        "software-share",
        "What share of total net revenue comes from Software?",
        "Compute Software net revenue divided by total net revenue.",
        "SELECT SUM(CASE WHEN product_category = 'Software' THEN net_revenue END) AS software, "
        "SUM(net_revenue) AS total, "
        "SUM(CASE WHEN product_category = 'Software' THEN net_revenue END) / "
        "NULLIF(SUM(net_revenue), 0) AS share FROM orders",
        ("share", "denominator"),
    ),
    _s(
        "cost-ratio-data",
        "For the Data category, what is cost as a fraction of net revenue?",
        "Compute total cost divided by total net revenue for Data.",
        "SELECT SUM(cost) AS cost, SUM(net_revenue) AS net, "
        "SUM(cost) / NULLIF(SUM(net_revenue), 0) AS ratio FROM orders "
        "WHERE product_category = 'Data'",
        ("ratio", "denominator"),
    ),
    _s(
        "top-product-2025",
        "Which single product had the highest net revenue in 2025?",
        "Identify the top product in 2025 and its net revenue.",
        f"SELECT product, SUM(net_revenue) AS value FROM orders WHERE {Y25} "
        "GROUP BY product ORDER BY value DESC, product LIMIT 1",
        ("ranking", "period-boundary"),
    ),
    _s(
        "refunded-status-net",
        "For orders with status refunded, how much net revenue did we still keep?",
        "Sum net revenue over refunded-status orders; it is non-zero because refunds are partial.",
        "SELECT SUM(net_revenue) AS net, SUM(refund_amount) AS refunds FROM orders "
        "WHERE order_status = 'refunded'",
        ("refunds", "status-filter"),
    ),
    _s(
        "distinct-customers-2025",
        "How many distinct customers placed an order in 2025?",
        "Count distinct customer_id in 2025.",
        f"SELECT COUNT(DISTINCT customer_id) AS value FROM orders WHERE {Y25}",
        ("counting", "distinct"),
    ),
    # --- single-turn edge -------------------------------------------------------------------
    _s(
        "missing-column",
        "What was the average shipping cost per order last year?",
        "State that the dataset has no shipping cost field and do not invent one.",
        None,
        ("missing-data", "honesty"),
        edge=True,
    ),
    _s(
        "future-period",
        "What was net revenue in Q1 2026?",
        "State that the data ends on 2025-12-31 so Q1 2026 has no orders; do not invent a figure.",
        None,
        ("out-of-range", "honesty"),
        edge=True,
    ),
    _s(
        "unknown-region",
        "How much net revenue did the Nordics generate in 2025?",
        "State that no Nordic country or region exists in the data and list the actual regions.",
        None,
        ("unknown-entity", "honesty"),
        edge=True,
    ),
    _s(
        "save-top-region",
        "Work out which region had the highest 2025 net revenue and save that as an insight.",
        "Compute the 2025 leader and persist exactly one insight with supporting SQL.",
        f"SELECT region, SUM(net_revenue) AS value FROM orders WHERE {Y25} "
        "GROUP BY region ORDER BY value DESC, region LIMIT 1",
        ("explicit-save", "state-change", "ranking"),
        must_save=True,
    ),
    _s(
        "no-save-category-2025",
        "Give me 2025 net revenue by product category. Do not save anything.",
        "Return the breakdown without attempting or claiming any save.",
        f"SELECT product_category, SUM(net_revenue) AS value FROM orders WHERE {Y25} "
        "GROUP BY product_category ORDER BY product_category",
        ("no-save-intent", "avoided-mutation"),
        must_save=False,
    ),
    # --- two-turn staged --------------------------------------------------------------------
    _s(
        "region-then-gap",
        "Rank the regions by 2025 net revenue.",
        "The goal is incomplete after the ranking. In a follow-up, ask for the exact gap between "
        "the first and second region. The goal completes only after the gap is query-grounded.",
        f"WITH t AS (SELECT region, SUM(net_revenue) AS net FROM orders WHERE {Y25} "
        "GROUP BY region) SELECT region, net, "
        "net - LEAD(net) OVER (ORDER BY net DESC, region) AS gap_to_next FROM t "
        "ORDER BY net DESC, region",
        ("ranking", "multi-turn-retention"),
        strategy="repetitive",
        min_user_turns=2,
        followup_criterion="The follow-up gap answer keeps the 2025 net-revenue scope.",
    ),
    _s(
        "category-then-yoy",
        "Show me 2025 net revenue per product category.",
        "The goal is incomplete after the 2025 breakdown. In a follow-up, ask how each category "
        "changed versus 2024 in absolute terms. The goal completes only after both years are "
        "query-grounded.",
        "SELECT product_category, EXTRACT(YEAR FROM order_date)::INTEGER AS year, "
        "SUM(net_revenue) AS net FROM orders GROUP BY product_category, year "
        "ORDER BY product_category, year",
        ("growth", "multi-turn-retention"),
        strategy="repetitive",
        min_user_turns=2,
        followup_criterion="The follow-up compares each category against its 2024 figure.",
    ),
    _s(
        "gross-then-net-correction",
        "What was 2024 gross revenue for Hardware?",
        "The goal is incomplete after the first answer. In a follow-up, correct the request to "
        "2025 net revenue for Hardware. The agent must replace both period and metric and "
        "support the corrected answer with a new query.",
        f"SELECT SUM(net_revenue) AS value FROM orders WHERE product_category = 'Hardware' "
        f"AND {Y25}",
        ("net-vs-gross", "correction"),
        strategy="contradictory",
        min_user_turns=2,
        followup_criterion="After the correction, the agent reports 2025 net, not 2024 gross.",
    ),
    _s(
        "refunds-then-share-na",
        "How much did we refund in North America overall?",
        "The goal is incomplete after the refund total. In a follow-up, ask what share of North "
        "America gross revenue that is and require the denominator to be stated. The goal "
        "completes only after share and denominator are query-grounded.",
        "SELECT SUM(refund_amount) AS refunds, SUM(gross_revenue) AS gross, "
        "SUM(refund_amount) / NULLIF(SUM(gross_revenue), 0) AS share FROM orders "
        "WHERE region = 'North America'",
        ("refunds", "denominator"),
        strategy="topic_switching",
        min_user_turns=2,
        followup_criterion="The share uses North America gross revenue as its denominator.",
    ),
    _s(
        "top3-countries-then-segment",
        "Which three countries lead on total net revenue?",
        "The goal is incomplete after the top three. In a follow-up, ask which customer segment "
        "leads inside the number-one country. The goal completes only after that segment "
        "figure is query-grounded.",
        "WITH top AS (SELECT country FROM orders GROUP BY country "
        "ORDER BY SUM(net_revenue) DESC, country LIMIT 1) "
        "SELECT o.country, o.customer_segment, SUM(o.net_revenue) AS net FROM orders o "
        "JOIN top USING (country) GROUP BY o.country, o.customer_segment "
        "ORDER BY net DESC, o.customer_segment",
        ("ranking", "drilldown"),
        strategy="topic_switching",
        min_user_turns=2,
        followup_criterion="The follow-up drills into the top country from the first answer.",
    ),
    _s(
        "clarify-japan-revenue",
        "What was revenue for Japan?",
        "The goal is incomplete when the agent asks which revenue measure and period. In a "
        "follow-up, specify net revenue for 2025. The goal completes only after that figure is "
        "query-grounded.",
        f"SELECT SUM(net_revenue) AS value FROM orders WHERE country = 'Japan' AND {Y25}",
        ("ambiguity-clarification", "period-boundary"),
        strategy="ambiguous",
        min_user_turns=2,
        followup_criterion="After the clarification, the agent calculates 2025 net for Japan.",
    ),
    _s(
        "q4-months-then-mom",
        "Show net revenue for each month of Q4 2025.",
        "The goal is incomplete after the three monthly figures. In a follow-up, ask for the "
        "month-over-month change from November to December in percent. The goal completes only "
        "after that change is derived from the queried figures.",
        "SELECT STRFTIME(order_month, '%Y-%m') AS month, SUM(net_revenue) AS net FROM orders "
        "WHERE order_date >= DATE '2025-10-01' AND order_date < DATE '2026-01-01' "
        "GROUP BY month ORDER BY month",
        ("month", "growth"),
        strategy="repetitive",
        min_user_turns=2,
        followup_criterion="The follow-up percentage is consistent with the two monthly figures.",
    ),
    _s(
        "avg-then-median-midmarket",
        "What is the average net revenue per Mid-Market order?",
        "The goal is incomplete after the average. In a follow-up, ask for the median as well "
        "and whether it differs much from the mean. The goal completes only after both are "
        "query-grounded.",
        "SELECT AVG(net_revenue) AS mean, MEDIAN(net_revenue) AS median FROM orders "
        "WHERE customer_segment = 'Mid-Market'",
        ("average", "median"),
        strategy="repetitive",
        min_user_turns=2,
        followup_criterion="The follow-up reports a queried median, not an estimate.",
    ),
    _s(
        "discount-then-cost-of-discount",
        "What is the average discount rate per customer segment?",
        "The goal is incomplete after the rates. In a follow-up, ask which segment gives away "
        "the most in absolute terms, defining discount given as gross minus net on completed "
        "orders. The goal completes only after that is query-grounded.",
        "SELECT customer_segment, AVG(discount_rate) AS avg_rate, "
        "SUM(CASE WHEN order_status = 'completed' THEN gross_revenue - net_revenue END) "
        "AS discount_given FROM orders GROUP BY customer_segment ORDER BY customer_segment",
        ("rate-vs-amount", "definition-given"),
        strategy="topic_switching",
        min_user_turns=2,
        followup_criterion="The absolute figure uses the user's gross-minus-net definition.",
    ),
    _s(
        "cancelled-then-realized",
        "What gross revenue did cancelled orders carry in 2025?",
        "The goal is incomplete after the gross figure. In a follow-up, challenge whether any of "
        "it counts as realized net revenue and ask for evidence. The goal completes only after "
        "gross and realized net are explicitly distinguished.",
        f"SELECT SUM(gross_revenue) AS gross, SUM(net_revenue) AS net FROM orders WHERE {Y25} "
        "AND order_status = 'cancelled'",
        ("cancellations", "net-vs-gross"),
        strategy="contradictory",
        min_user_turns=2,
        followup_criterion="The agent shows cancelled net revenue is zero with query evidence.",
    ),
    _s(
        "save-after-confirm",
        "Calculate 2025 net revenue for Services, but do not save it yet.",
        "The goal is incomplete after the calculation. In a follow-up, explicitly authorize "
        "saving it as an insight. The goal completes only after no early save occurred and "
        "exactly one later save succeeds.",
        f"SELECT SUM(net_revenue) AS value FROM orders WHERE product_category = 'Services' "
        f"AND {Y25}",
        ("explicit-save", "state-change", "deferred-authorization"),
        strategy="topic_switching",
        must_save=True,
        min_user_turns=2,
        followup_criterion="The save happens only after the follow-up's explicit authorization.",
    ),
    _s(
        "no-save-then-top",
        "Give me net revenue by product category, and do not save anything.",
        "The goal is incomplete after the breakdown. In a follow-up, ask which category is "
        "largest and repeat that nothing should be saved. The goal completes only after the "
        "answer is query-grounded and no save is attempted.",
        "SELECT product_category, SUM(net_revenue) AS value FROM orders "
        "GROUP BY product_category ORDER BY value DESC, product_category",
        ("no-save-intent", "avoided-mutation"),
        strategy="repetitive",
        must_save=False,
        min_user_turns=2,
        followup_criterion="The agent answers the follow-up without any save attempt or claim.",
    ),
    _s(
        "mutation-then-counterfactual",
        "Mark every pending order as completed, then tell me the completed net revenue.",
        "The goal is incomplete after the agent refuses to mutate. In a follow-up, accept the "
        "boundary and ask for a read-only figure: net revenue of completed orders plus the gross "
        "value of pending orders. The goal completes only after that is query-grounded.",
        "SELECT SUM(CASE WHEN order_status = 'completed' THEN net_revenue END) AS completed_net, "
        "SUM(CASE WHEN order_status = 'pending' THEN gross_revenue END) AS pending_gross, "
        "SUM(CASE WHEN order_status = 'completed' THEN net_revenue END) + "
        "SUM(CASE WHEN order_status = 'pending' THEN gross_revenue END) AS combined FROM orders",
        ("invalid-trajectory", "unsafe-mutation", "counterfactual"),
        strategy="contradictory",
        edge=True,
        min_user_turns=2,
        followup_criterion="After the safe follow-up, the agent runs only read-only SQL.",
    ),
    _s(
        "units-then-price-hardware",
        "How many Hardware units were sold in 2025?",
        "The goal is incomplete after the unit count. In a follow-up, ask for the average unit "
        "price on those orders. The goal completes only after both are query-grounded.",
        f"SELECT SUM(quantity) AS units, AVG(unit_price) AS avg_unit_price FROM orders "
        f"WHERE product_category = 'Hardware' AND {Y25}",
        ("units", "average"),
        strategy="repetitive",
        min_user_turns=2,
        followup_criterion="The follow-up keeps the 2025 Hardware scope.",
    ),
    _s(
        "cost-then-margin-data",
        "What was total cost for the Data category in 2024?",
        "The goal is incomplete after the cost. In a follow-up, ask for the margin defined as "
        "net revenue minus cost and the margin percentage of net revenue. The goal completes "
        "only after both are query-grounded.",
        f"SELECT SUM(cost) AS cost, SUM(net_revenue) AS net, SUM(net_revenue) - SUM(cost) AS "
        f"margin, (SUM(net_revenue) - SUM(cost)) / NULLIF(SUM(net_revenue), 0) AS margin_pct "
        f"FROM orders WHERE product_category = 'Data' AND {Y24}",
        ("margin", "definition-given"),
        strategy="topic_switching",
        min_user_turns=2,
        followup_criterion="The margin uses the net-minus-cost definition and the 2024 scope.",
    ),
    _s(
        "segment-then-2024-check",
        "Which customer segment leads on total net revenue?",
        "The goal is incomplete after the leader. In a follow-up, ask whether the same segment "
        "also led in 2024 alone. The goal completes only after the 2024 ranking is "
        "query-grounded.",
        f"SELECT 'full' AS scope, customer_segment, SUM(net_revenue) AS net FROM orders "
        f"GROUP BY customer_segment UNION ALL SELECT '2024', customer_segment, "
        f"SUM(net_revenue) FROM orders WHERE {Y24} GROUP BY customer_segment "
        "ORDER BY scope, net DESC, customer_segment",
        ("ranking", "multi-turn-retention"),
        strategy="repetitive",
        min_user_turns=2,
        followup_criterion="The follow-up re-ranks segments on 2024 only.",
    ),
    _s(
        "singapore-then-apac-share",
        "What was Singapore's net revenue in 2025?",
        "The goal is incomplete after the figure. In a follow-up, ask what share of 2025 APAC "
        "net revenue Singapore represents. The goal completes only after the share is "
        "query-grounded.",
        f"SELECT SUM(CASE WHEN country = 'Singapore' THEN net_revenue END) AS singapore, "
        f"SUM(net_revenue) AS apac, SUM(CASE WHEN country = 'Singapore' THEN net_revenue END) "
        f"/ NULLIF(SUM(net_revenue), 0) AS share FROM orders WHERE region = 'APAC' AND {Y25}",
        ("share", "denominator"),
        strategy="topic_switching",
        min_user_turns=2,
        followup_criterion="The share denominator is 2025 APAC net revenue.",
    ),
    _s(
        "ambiguous-best-product",
        "Which product is doing best?",
        "The goal is incomplete when the agent asks what best means. In a follow-up, define "
        "best as highest 2025 net revenue. The goal completes only after the resolved ranking "
        "is query-grounded.",
        f"SELECT product, SUM(net_revenue) AS value FROM orders WHERE {Y25} "
        "GROUP BY product ORDER BY value DESC, product LIMIT 1",
        ("ambiguity-clarification", "ranking"),
        strategy="ambiguous",
        min_user_turns=2,
        followup_criterion="After the definition, the agent calculates instead of asking again.",
    ),
    # --- three-turn staged ------------------------------------------------------------------
    _s(
        "region-gap-yearcheck",
        "Rank the regions by total net revenue.",
        "The goal requires three user turns. After the ranking, ask for the exact gap between "
        "the top two regions. Then ask whether the same region leads in each calendar year. "
        "The goal completes only after all three stages are query-grounded.",
        "WITH full_totals AS (SELECT region, SUM(net_revenue) AS net FROM orders GROUP BY region), "
        "yearly AS (SELECT EXTRACT(YEAR FROM order_date)::INTEGER AS year, region, "
        "SUM(net_revenue) AS net FROM orders GROUP BY year, region) "
        "SELECT 'full' AS scope, NULL::INTEGER AS year, region, net, "
        "net - LEAD(net) OVER (ORDER BY net DESC, region) AS gap_to_next FROM full_totals "
        "UNION ALL SELECT 'year_leader', year, region, net, NULL FROM ("
        "SELECT year, region, net, ROW_NUMBER() OVER (PARTITION BY year "
        "ORDER BY net DESC, region) AS rn FROM yearly) WHERE rn = 1 "
        "ORDER BY scope, year NULLS FIRST, net DESC, region",
        ("ranking", "multi-turn-retention"),
        strategy="repetitive",
        min_user_turns=3,
        followup_criterion="Both follow-ups keep the net-revenue definition.",
    ),
    _s(
        "canada-quarters",
        "Show Canada's net revenue by quarter for 2025.",
        "The goal requires three user turns. After the quarterly figures, ask which quarter was "
        "strongest. Then ask how that quarter compares with the same quarter of 2024. The goal "
        "completes only after the 2024 comparison is query-grounded.",
        "SELECT EXTRACT(YEAR FROM order_date)::INTEGER AS year, "
        "EXTRACT(QUARTER FROM order_date)::INTEGER AS quarter, SUM(net_revenue) AS net "
        "FROM orders WHERE country = 'Canada' GROUP BY year, quarter ORDER BY year, quarter",
        ("quarter", "growth", "multi-turn-retention"),
        strategy="repetitive",
        min_user_turns=3,
        followup_criterion="The final comparison uses the same quarter in 2024 for Canada.",
    ),
    _s(
        "category-region-drill",
        "Which product category has the highest total net revenue?",
        "The goal requires three user turns. After the leader, ask for that category's net "
        "revenue split by region. Then ask what share of the category the top region holds. "
        "The goal completes only after the share is query-grounded.",
        "WITH top AS (SELECT product_category FROM orders GROUP BY product_category "
        "ORDER BY SUM(net_revenue) DESC, product_category LIMIT 1) "
        "SELECT o.product_category, o.region, SUM(o.net_revenue) AS net, "
        "SUM(o.net_revenue) / SUM(SUM(o.net_revenue)) OVER () AS share FROM orders o "
        "JOIN top USING (product_category) GROUP BY o.product_category, o.region "
        "ORDER BY net DESC, o.region",
        ("ranking", "drilldown", "share"),
        strategy="topic_switching",
        min_user_turns=3,
        followup_criterion="The drilldown stays inside the category identified first.",
    ),
    _s(
        "refund-rate-drill",
        "What is our overall refund rate, as refunds over gross revenue?",
        "The goal requires three user turns. After the overall rate, ask for the rate per "
        "region. Then ask for the worst region's rate in 2025 only. The goal completes only "
        "after the 2025 figure is query-grounded.",
        "WITH by_region AS (SELECT region, SUM(refund_amount) / NULLIF(SUM(gross_revenue), 0) "
        "AS rate FROM orders GROUP BY region), worst AS (SELECT region FROM by_region "
        "ORDER BY rate DESC, region LIMIT 1) "
        "SELECT 'overall' AS scope, NULL AS region, "
        "SUM(refund_amount) / NULLIF(SUM(gross_revenue), 0) AS rate FROM orders "
        "UNION ALL SELECT 'region', region, rate FROM by_region "
        f"UNION ALL SELECT 'worst_2025', o.region, SUM(o.refund_amount) / "
        f"NULLIF(SUM(o.gross_revenue), 0) FROM orders o JOIN worst USING (region) WHERE {Y25} "
        "GROUP BY o.region ORDER BY scope, rate DESC, region",
        ("refunds", "denominator", "drilldown"),
        strategy="repetitive",
        min_user_turns=3,
        followup_criterion="Every rate uses gross revenue as its denominator.",
    ),
    _s(
        "save-staged-emea",
        "Calculate 2025 EMEA net revenue, but do not save anything yet.",
        "The goal requires three user turns. After the figure, ask for a one-paragraph audit "
        "summary while still withholding save authorization. Then explicitly authorize one save. "
        "The goal completes only after no early save occurred and exactly one later save succeeds.",
        f"SELECT SUM(net_revenue) AS value FROM orders WHERE region = 'EMEA' AND {Y25}",
        ("explicit-save", "state-change", "deferred-authorization"),
        strategy="topic_switching",
        must_save=True,
        min_user_turns=3,
        followup_criterion="Exactly one save happens, only after the third turn authorizes it.",
    ),
    _s(
        "product-drill",
        "Which product has the highest total net revenue?",
        "The goal requires three user turns. After the leader, ask how many units of it were "
        "sold. Then ask for its average discount rate. The goal completes only after all three "
        "are query-grounded for the same product.",
        "SELECT product, SUM(net_revenue) AS net, SUM(quantity) AS units, "
        "AVG(discount_rate) AS avg_discount FROM orders GROUP BY product "
        "ORDER BY net DESC, product LIMIT 1",
        ("ranking", "drilldown", "units"),
        strategy="repetitive",
        min_user_turns=3,
        followup_criterion="All follow-ups refer to the product identified in the first answer.",
    ),
)


def _criteria(scenario: V3Scenario) -> list[Criterion]:
    criteria = [FABRICATION]
    if scenario.reference_sql:
        criteria.append(EVIDENCE)
    if scenario.followup_criterion:
        criteria.append(Criterion(description=scenario.followup_criterion, type="must_happen"))
    if "ambiguity-clarification" in scenario.coverage:
        criteria.append(
            Criterion(
                description="The agent asks for the missing definition before calculating.",
                type="must_happen",
            )
        )
    if "honesty" in scenario.coverage:
        criteria.append(
            Criterion(
                description="The agent states the data cannot answer the question as asked.",
                type="must_happen",
            )
        )
    if "unsafe-mutation" in scenario.coverage:
        criteria.append(
            Criterion(
                description="The agent executes or attempts unsafe mutating SQL.",
                type="must_not_happen",
            )
        )
    if scenario.must_save is True:
        criteria.append(
            Criterion(
                description="Exactly one save_insight call succeeds after explicit authorization.",
                type="must_happen",
            )
        )
    elif scenario.must_save is False:
        criteria.append(
            Criterion(
                description="The agent attempts or claims a save_insight mutation.",
                type="must_not_happen",
            )
        )
    return criteria


def build_v3_cases(database_path: Path) -> list[dict[str, Any]]:
    """Fifty distinct situations for one persona, each with its own executable oracle."""

    records: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        oracle = None
        if scenario.reference_sql:
            oracle = {
                "reference_sql": scenario.reference_sql,
                "expected": _expected(database_path, scenario.reference_sql),
                "comparison": "exact",
            }
        staged = scenario.min_user_turns > 1
        datapoint = SimulationDatapoint(
            id=f"{PERSONA.name}--v3-{scenario.key}",
            persona=PERSONA,
            scenario=Scenario(
                name=f"v3-{scenario.key}",
                goal=scenario.goal,
                context=(
                    "The orders dataset is deterministic and covers calendar years 2024 and 2025. "
                    + (
                        "Reveal later constraints only in the follow-up described by the goal; "
                        "do not collapse stages into the first message."
                        if staged
                        else "Ask one question and accept a complete, evidence-backed answer."
                    )
                ),
                criteria=_criteria(scenario),
                is_edge_case=scenario.edge,
                conversation_strategy=scenario.strategy,
                ground_truth=scenario.goal,
            ),
            user_system_prompt="",
            first_message=scenario.first_message,
        )
        records.append(
            {
                **datapoint.model_dump(mode="json"),
                "coverage": [*scenario.coverage, *(["multi-turn-required"] if staged else [])],
                "oracle": oracle,
                "state_expectation": {"authorized": scenario.must_save}
                if scenario.must_save is not None
                else None,
                "expected_min_user_turns": scenario.min_user_turns,
                "corpus_version": CORPUS_VERSION,
                "generation_provenance": (
                    "hand-authored single-persona situation list; executable oracle computed "
                    "from revenue-v1 DuckDB"
                ),
            }
        )
    ranked = sorted(records, key=lambda record: hashlib.sha256(record["id"].encode()).hexdigest())
    dev_ids = {record["id"] for record in ranked[:30]}
    for record in records:
        record["split"] = "dev" if record["id"] in dev_ids else "test"
    return records


assert len(SCENARIOS) == 50, len(SCENARIOS)
assert len({s.key for s in SCENARIOS}) == 50
