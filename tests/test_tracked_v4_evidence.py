from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from analytics_chatbot.evaluation_ops.jury_annotation import build_annotation_bundle
from analytics_chatbot.evaluation_ops.simulation_artifacts import load_simulation_replay

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "orq/resources/datasets/simulation-cases-v4.jsonl"
BUNDLE = ROOT / "orq/resources/datasets/decision-support-v4"
HUMAN_LABELS = BUNDLE / "human-labels-dev-v1.jsonl"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_tracked_v4_evidence_is_complete_sanitized_and_identity_bound() -> None:
    observations = BUNDLE / "observations.jsonl"

    assert _sha256(observations) == (
        "bf560f5cd94aa916110a03fc46cf006bbbe5e006e839680427aed481c67740ab"
    )
    observation_text = observations.read_text()
    for runtime_identifier in (
        r'"id":"call_[^"]+"',
        r'"item_id":"fc_[^"]+"',
        r'insight-[0-9a-f]{32}',
        r'"thread_id":"[0-9a-f]{32}:',
    ):
        assert re.search(runtime_identifier, observation_text) is None

    corpus = load_simulation_replay(cases_path=CASES, results_path=observations)
    assert len(corpus.samples) == 50
    assert not corpus.rejected
    assert not corpus.duplicates
    assert len(corpus.warnings) == 2

    versions = {
        "jury-baseline": {
            "jury_hash": "1c1a900fcbf33f84c1db9e9076a409c654e32614d6dfc0538762183dc81e1f69",
            "prompt_hash": "ae60365a11a5745b5bd38ef484e2503b7ac189a49fde604eb63f1a05d6e44579",
            "queue_items": 14,
        },
        "jury-human-rules-v1": {
            "jury_hash": "bbbddb22d3fbcc9fa71ff22ba39a76247bfd59170a3cbb5ae0a92569ef2a4a9f",
            "prompt_hash": "a2c3568d3efc4de644d40d986c9e88a46eda2af3e52ecf21790ce59527c55e3d",
            "queue_items": 19,
        },
    }
    for version, expected in versions.items():
        version_dir = BUNDLE / version
        jury = version_dir / "jury-results.jsonl"
        annotation = version_dir / "annotation"
        assert _sha256(jury) == expected["jury_hash"]
        assert _sha256(version_dir / "evaluator-prompt.txt") == expected["prompt_hash"]

        jury_rows = [json.loads(line) for line in jury.read_text().splitlines() if line]
        assert len(jury_rows) == 50
        regenerated = build_annotation_bundle(corpus, jury_rows)
        stored_queue = json.loads((annotation / "queue.json").read_text())
        stored_test = json.loads((annotation / "test_manifest.json").read_text())
        stored_errors = json.loads((annotation / "jury_errors.json").read_text())
        assert stored_queue["meta"]["n_items"] == expected["queue_items"]
        assert regenerated.queue == stored_queue
        assert regenerated.test_manifest == stored_test
        assert regenerated.jury_errors == stored_errors

        manifest = json.loads((annotation / "manifest.json").read_text())
        assert manifest["status"] == "ready"
        for filename, expected_hash in manifest["files"].items():
            assert _sha256(annotation / filename) == expected_hash


def test_confirmed_development_labels_cover_the_full_dev_split() -> None:
    corpus = load_simulation_replay(
        cases_path=CASES,
        results_path=BUNDLE / "observations.jsonl",
    )
    rows = [
        json.loads(line)
        for line in HUMAN_LABELS.read_text().splitlines()
        if line.strip()
    ]

    expected_identities = {
        sample.identity
        for sample in corpus.samples
        if sample.row.evaluation_split == "dev"
    }
    actual_identities = {
        (row["case_id"], row["transcript_fingerprint"]) for row in rows
    }
    assert len(rows) == 30
    assert actual_identities == expected_identities
    assert all(row["evaluation_split"] == "dev" for row in rows)
    assert all(row["evaluator_key"] == "analytics-decision-support-quality" for row in rows)
    assert all(row["reviewed_by"] == "human" for row in rows)
    assert all(row["explanation"].strip() for row in rows)
    assert {row["label"] for row in rows} == {"pass", "fail"}
    assert sum(row["label"] == "pass" for row in rows) == 27
    assert {
        row["case_id"].removeprefix("sphere-stakeholder--v4-")
        for row in rows
        if row["label"] == "fail"
    } == {
        "best-month-net",
        "save-staged-emea",
        "segment-then-2024-check",
    }

    jury_rows = {
        (row["case_id"], row["transcript_fingerprint"]): row
        for line in (
            BUNDLE / "jury-human-rules-v1/jury-results.jsonl"
        ).read_text().splitlines()
        if line.strip()
        for row in [json.loads(line)]
        if row["evaluation_split"] == "dev"
    }
    assert set(jury_rows) == actual_identities
    assert all(row["value"] == "pass" for row in jury_rows.values())
    assert {
        identity
        for identity, row in jury_rows.items()
        if row["value"]
        != next(
            label["label"]
            for label in rows
            if (label["case_id"], label["transcript_fingerprint"]) == identity
        )
    } == {
        identity
        for identity in actual_identities
        if identity[0].removeprefix("sphere-stakeholder--v4-")
        in {
            "best-month-net",
            "save-staged-emea",
            "segment-then-2024-check",
        }
    }
