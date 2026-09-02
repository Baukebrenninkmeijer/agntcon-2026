"""Run-scoped insight state with verifiable snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel, Field

from analytics_chatbot.models import ToolResult


class SaveInsightArgs(BaseModel):
    title: str
    summary: str
    supporting_sql: str
    tags: list[str] = Field(default_factory=list)


class InsightStore:
    """Append structured insights beneath one run directory."""

    def __init__(self, run_directory: Path) -> None:
        self.run_directory = Path(run_directory)
        self.path = self.run_directory / "insights.jsonl"

    def snapshot(self) -> dict[str, str | int]:
        if not self.path.exists():
            payload = b""
            count = 0
        else:
            payload = self.path.read_bytes()
            count = sum(1 for line in payload.splitlines() if line.strip())
        return {"count": count, "sha256": hashlib.sha256(payload).hexdigest()}

    def save(self, arguments: SaveInsightArgs) -> ToolResult:
        started = perf_counter()
        if not all(
            value.strip()
            for value in (arguments.title, arguments.summary, arguments.supporting_sql)
        ):
            return ToolResult.failure(
                "invalid_insight",
                "title, summary, and supporting_sql must be non-empty",
                execution_ms=(perf_counter() - started) * 1_000,
            )

        self.run_directory.mkdir(parents=True, exist_ok=True)
        insight = {
            "id": f"insight-{uuid4().hex}",
            "created_at": datetime.now(UTC).isoformat(),
            **arguments.model_dump(),
        }
        with self.path.open("a", encoding="utf-8") as destination:
            destination.write(json.dumps(insight, sort_keys=True) + "\n")
            destination.flush()
        return ToolResult.success(
            {"insight": insight},
            execution_ms=(perf_counter() - started) * 1_000,
        )
