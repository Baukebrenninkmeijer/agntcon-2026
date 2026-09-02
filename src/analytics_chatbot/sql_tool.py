"""Guarded, read-only SQL execution against the analytics database."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from threading import Timer
from time import perf_counter
from typing import Any

import duckdb
import sqlglot
from sqlglot import exp

from analytics_chatbot.models import ToolResult

_DENIED_WORDS = re.compile(
    r"\b(attach|copy|create|delete|detach|drop|export|import|insert|install|load|"
    r"merge|pragma|replace|truncate|update|vacuum)\b",
    re.IGNORECASE,
)
_EXTERNAL_FUNCTIONS = re.compile(
    r"\b(read_csv|read_csv_auto|read_json|read_ndjson|read_parquet|sqlite_scan|"
    r"postgres_scan|httpfs)\s*\(",
    re.IGNORECASE,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    return value


class SqlTool:
    """Validate and execute one bounded read-only DuckDB query."""

    def __init__(
        self,
        database_path: Path,
        max_rows: int = 200,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.database_path = Path(database_path)
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds

    def _validate(self, query: str) -> str | None:
        if not query.strip():
            return "Query cannot be empty"
        if _DENIED_WORDS.search(query) or _EXTERNAL_FUNCTIONS.search(query):
            return "Only read-only queries against the local orders table are allowed"
        try:
            statements = sqlglot.parse(query, read="duckdb")
        except sqlglot.errors.ParseError as error:
            return f"SQL could not be parsed: {error}"
        if len(statements) != 1:
            return "Exactly one SQL statement is allowed"

        statement = statements[0]
        normalized = query.lstrip().lower()
        if isinstance(statement, exp.Query):
            return None
        if normalized.startswith(("describe ", "desc ", "explain ")):
            return None
        return "Only SELECT, WITH, DESCRIBE, or EXPLAIN statements are allowed"

    def execute(self, query: str) -> ToolResult:
        started = perf_counter()
        validation_error = self._validate(query)
        if validation_error:
            return ToolResult.failure(
                "unsafe_sql",
                validation_error,
                execution_ms=(perf_counter() - started) * 1_000,
            )

        connection = duckdb.connect(str(self.database_path), read_only=True)
        timer = Timer(self.timeout_seconds, connection.interrupt)
        try:
            timer.start()
            cursor = connection.execute(query)
            columns = [description[0] for description in cursor.description]
            fetched = cursor.fetchmany(self.max_rows + 1)
            rows = [list(map(_json_value, row)) for row in fetched[: self.max_rows]]
            return ToolResult.success(
                {
                    "query": query,
                    "columns": columns,
                    "rows": rows,
                    "truncated": len(fetched) > self.max_rows,
                },
                execution_ms=(perf_counter() - started) * 1_000,
            )
        except duckdb.Error as error:
            return ToolResult.failure(
                "query_error",
                str(error)[:1_000],
                execution_ms=(perf_counter() - started) * 1_000,
            )
        finally:
            timer.cancel()
            connection.close()
