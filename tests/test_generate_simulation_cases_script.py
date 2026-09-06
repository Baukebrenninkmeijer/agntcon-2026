import json
import os
import subprocess
import sys
from pathlib import Path

from analytics_chatbot.data import seed_database

ROOT = Path(__file__).resolve().parents[1]


def test_cli_generates_edge_v2_corpus_at_requested_output(tmp_path: Path) -> None:
    output = tmp_path / "edge-v2.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_simulation_cases.py",
            "--variant",
            "edge-v2",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 50
    assert {record["corpus_version"] for record in records} == {"simulation-edge-v2"}
    assert f"to {output}" in result.stdout


def test_cli_defaults_to_standard_corpus_and_original_output_path(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["ANALYTICS_CHATBOT_DATABASE_PATH"] = str(ROOT / "data/analytics.duckdb")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_simulation_cases.py")],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    output = tmp_path / "orq/resources/datasets/simulation-cases.jsonl"
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 50
    assert {record["corpus_version"] for record in records} == {"simulation-v1"}


def test_edge_v2_variant_defaults_to_separate_output_path(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["ANALYTICS_CHATBOT_DATABASE_PATH"] = str(ROOT / "data/analytics.duckdb")

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/generate_simulation_cases.py"),
            "--variant",
            "edge-v2",
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    output = tmp_path / "orq/resources/datasets/simulation-cases-v2.jsonl"
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 50
    assert not (tmp_path / "orq/resources/datasets/simulation-cases.jsonl").exists()


def test_v4_variant_defaults_to_separate_output_path(tmp_path: Path) -> None:
    database = tmp_path / "sphere.duckdb"
    seed_database(database)
    environment = os.environ.copy()
    environment["ANALYTICS_CHATBOT_DATABASE_PATH"] = str(database)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/generate_simulation_cases.py"),
            "--variant",
            "v4",
        ],
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
    assert not (tmp_path / "orq/resources/datasets/simulation-cases.jsonl").exists()
