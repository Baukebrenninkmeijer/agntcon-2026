"""Exact local trajectory persistence with atomic successful finalization."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunStore:
    def __init__(self, runs_path: Path, run_id: str) -> None:
        self.run_id = run_id
        self.directory = Path(runs_path) / run_id
        self.directory.mkdir(parents=True, exist_ok=True)
        self.partial_path = self.directory / "events.partial.jsonl"
        self.final_path = self.directory / "events.jsonl"

    def append(self, event: dict[str, Any]) -> None:
        record = {"recorded_at": datetime.now(UTC).isoformat(), **event}
        with self.partial_path.open("a", encoding="utf-8") as destination:
            destination.write(json.dumps(record, sort_keys=True, default=str) + "\n")
            destination.flush()

    def finalize(self, summary: dict[str, Any]) -> Path:
        self.append({"type": "run_finished", **summary})
        self.partial_path.replace(self.final_path)
        return self.final_path

    def abort(self, error: str) -> Path:
        self.append({"type": "run_failed", "status": "failed", "error": error})
        return self.partial_path
