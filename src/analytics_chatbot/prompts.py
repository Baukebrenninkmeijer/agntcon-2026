"""Agent instructions and Responses API tool schemas."""

from typing import Any

SYSTEM_PROMPT = """You are a careful business data analyst working with a DuckDB table named orders.

Use query_sql before making factual claims about the dataset. Treat net_revenue as realized revenue:
cancelled and pending orders contribute zero, while refunds reduce net revenue. Distinguish gross
revenue, net revenue, cost, and refund amounts explicitly. Check date boundaries before comparing
periods and mention incomplete periods when relevant. Explain conclusions concisely and include the
SQL that supports important numbers.

The save_insight tool is available only when the user explicitly asks you to save, remember, or
preserve a finding. Never claim that an insight was saved unless the tool succeeds.
"""

QUERY_SQL_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "query_sql",
    "description": (
        "Run one read-only DuckDB query against the local orders table. "
        "Results are capped; aggregate before returning large datasets."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A single SELECT, WITH, DESCRIBE, or EXPLAIN statement.",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

SAVE_INSIGHT_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "save_insight",
    "description": "Persist a user-requested finding in this run's structured insight store.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "supporting_sql": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "summary", "supporting_sql"],
        "additionalProperties": False,
    },
}
