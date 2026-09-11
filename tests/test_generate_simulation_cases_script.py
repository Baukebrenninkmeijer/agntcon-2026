import json
import os
import subprocess
import sys
from pathlib import Path

from analytics_chatbot.data import seed_database

ROOT = Path(__file__).resolve().parents[1]


def test_cli_defaults_to_the_tracked_v4_output_path(tmp_path: Path) -> None:
    database = tmp_path / "sphere.duckdb"
    seed_database(database)
    environment = os.environ.copy()
    environment["ANALYTICS_CHATBOT_DATABASE_PATH"] = str(database)

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_simulation_cases.py")],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    output = tmp_path / "orq/resources/datasets/simulation-cases-v4.jsonl"
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 50
    assert {record["corpus_version"] for record in records} == {"simulation-v4"}
