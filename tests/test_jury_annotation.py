from __future__ import annotations

import copy
import json
import os
from types import SimpleNamespace

import pytest

from analytics_chatbot.evaluation_ops import (
    DEFAULT_JUDGES,
    ConversationMessage,
    DecisionContextEvidence,
    OracleEvidence,
    ToolEvent,
    TraceBackedEvaluationRow,
)
from analytics_chatbot.evaluation_ops.jury_annotation import (
    analyze_jury,
    annotation_id,
    build_annotation_bundle,
    publish_annotation_bundle,
)
from analytics_chatbot.evaluation_ops.simulation_artifacts import (
    SimulationReplayCorpus,
    SimulationReplaySample,
)


def _jury(values: tuple[str | None, str | None, str | None] = ("pass", "pass", "pass")) -> dict:
    votes = []
    for index, (model, value) in enumerate(zip(DEFAULT_JUDGES, values, strict=True)):
        votes.append(
            {
                "model": model,
                "replacement": False,
                "success": True,
                "abstained": value is None,
                "value": value,
                "explanation": f"aggregate {index}",
                "error": None,
                "repetitions": [
                    {"value": value, "explanation": f"repeat {index}-{repeat}"}
                    for repeat in range(3)
                ],
                "repetitions_failed": 0,
            }
        )
    non_null = [value for value in values if value is not None]
    return {
        "judges_configured": 3,
        "judges_succeeded": len(non_null),
        "judges_failed": 0,
        "replacements_used": 0,
        "tie": len(set(non_null)) == 3,
        "inconclusive": not non_null,
        "votes": votes,
        "stats": None,
        "raw_agreement": max((non_null.count(value) for value in set(non_null)), default=0)
        / len(non_null)
        if non_null
        else None,
    }


def _corpus() -> SimulationReplayCorpus:
    samples = []
    for index in range(50):
        case_id = f"sphere-stakeholder--v4-{index:02d}"
        fingerprint = f"{index:064x}"
        split = "dev" if index < 30 else "test"
        row = TraceBackedEvaluationRow(
            case_id=case_id,
            evaluation_split=split,
            conversation=[
                ConversationMessage(role="user", content=f"question {index}"),
                ConversationMessage(role="assistant", content=f"answer {index}"),
            ],
            assistant_response=f"answer {index}",
            decision_context=DecisionContextEvidence(
                stakeholder="CFO",
                decision="choose a product allocation",
                delivery_setting="weekly review",
                communication_need="lead with the decision-relevant result",
            ),
            oracle=OracleEvidence(expected_answer=index, reference_sql="select secret"),
            tool_events=[
                ToolEvent(name="query_sql", arguments={"sql": "select 1"}, result={"x": 1})
            ],
            metadata={"transcript_fingerprint": fingerprint},
        )
        samples.append(
            SimulationReplaySample(
                case_id=case_id,
                transcript_fingerprint=fingerprint,
                row=row,
            )
        )
    return SimulationReplayCorpus(samples=samples, rejected=[], duplicates=[], warnings=[])


def _jury_rows(corpus: SimulationReplayCorpus) -> list[dict]:
    return [
        {
            "schema_version": "decision-support-jury-v1",
            "case_id": sample.case_id,
            "evaluation_split": sample.row.evaluation_split,
            "transcript_fingerprint": sample.transcript_fingerprint,
            "decision_context": sample.row.decision_context.model_dump(mode="json"),
            "recorded_output": sample.row.assistant_response,
            "value": "pass",
            "explanation": "panel aggregate",
            "pass": True,
            "jury": _jury(),
        }
        for sample in corpus.samples
    ]


def test_annotation_id_is_stable_and_uses_both_identity_parts():
    base = annotation_id("case", "a" * 64)
    assert base == annotation_id("case", "a" * 64)
    assert base != annotation_id("other", "a" * 64)
    assert base != annotation_id("case", "b" * 64)
    assert len(base) == 64


def test_analyze_jury_keeps_abstention_tie_disagreement_and_wobble_distinct():
    jury = _jury(("pass", "fail", "not_applicable"))
    jury["votes"][0]["repetitions"][2]["value"] = "fail"
    signals = analyze_jury(jury)
    assert signals.tie is True
    assert signals.panel_disagreement is True
    assert signals.within_judge_wobble is True
    assert signals.abstention is False
    assert signals.priority_tier == 1
    assert signals.per_judge[0].instability > 0

    abstaining = analyze_jury(_jury(("pass", "pass", None)))
    assert abstaining.abstention is True
    assert abstaining.priority_tier == 1


def test_analyze_jury_marks_mechanical_errors_unrankable():
    jury = _jury()
    jury["judges_failed"] = 1
    jury["judges_succeeded"] = 2
    jury["votes"][2].update(
        success=False,
        abstained=False,
        value=None,
        explanation="",
        error="provider timeout",
        repetitions=[],
        repetitions_failed=3,
    )
    signals = analyze_jury(jury)
    assert signals.mechanical_errors
    assert signals.priority_tier is None


def test_analyze_jury_treats_clean_repetition_abstention_as_high_signal():
    jury = _jury()
    jury["votes"][0]["repetitions"][1]["value"] = None
    signals = analyze_jury(jury)
    assert signals.abstention is True
    assert signals.mechanical_errors == ()
    assert signals.priority_tier == 1


def test_analyze_jury_requires_the_exact_ordered_three_by_three_panel():
    wrong_model = _jury()
    wrong_model["votes"][0]["model"] = "other/model"
    with pytest.raises(ValueError, match="ordered models"):
        analyze_jury(wrong_model)

    missing_repeat = _jury()
    missing_repeat["votes"][0]["repetitions"].pop()
    with pytest.raises(ValueError, match="three repetitions"):
        analyze_jury(missing_repeat)


def test_bundle_is_dev_only_oracle_free_and_has_seeded_controls():
    corpus = _corpus()
    rows = _jury_rows(corpus)
    rows[0]["jury"] = _jury(("pass", "fail", "pass"))
    bundle = build_annotation_bundle(corpus, rows, seed=42, control_count=5)

    assert bundle.queue["meta"]["mode"] == "jury"
    assert len(bundle.test_manifest["items"]) == 20
    assert len(bundle.queue["items"]) == 6
    assert bundle.queue["items"][0]["case_id"] == corpus.samples[0].case_id
    assert sum(item["control_sample"] for item in bundle.queue["items"]) == 5
    serialized = repr(bundle.queue).lower()
    assert "reference_sql" not in serialized
    assert "expected_answer" not in serialized
    assert all(item["evaluation_split"] == "dev" for item in bundle.queue["items"])
    assert set(bundle.test_manifest["items"][0]) == {
        "annotation_id",
        "case_id",
        "evaluation_split",
        "transcript_fingerprint",
    }


def test_bundle_rejects_missing_or_duplicate_case_coverage():
    corpus = _corpus()
    rows = _jury_rows(corpus)
    with pytest.raises(ValueError, match="exactly 50"):
        build_annotation_bundle(
            SimpleNamespace(samples=corpus.samples[:-1], rejected=[], duplicates=[], warnings=[]),
            rows[:-1],
        )

    duplicate = copy.deepcopy(rows)
    duplicate[-1].update(
        case_id=duplicate[0]["case_id"],
        transcript_fingerprint=duplicate[0]["transcript_fingerprint"],
    )
    with pytest.raises(ValueError, match="duplicate jury identity"):
        build_annotation_bundle(corpus, duplicate)


def test_bundle_validates_test_jury_without_exposing_its_outcome():
    corpus = _corpus()
    rows = _jury_rows(corpus)
    rows[-1]["jury"] = {"malformed": True}
    bundle = build_annotation_bundle(corpus, rows)
    assert bundle.queue["meta"]["n_errors"] == 1
    assert bundle.jury_errors["items"][0]["case_id"] == corpus.samples[-1].case_id
    assert all(
        forbidden not in bundle.test_manifest["items"][0]
        for forbidden in ("jury", "value", "explanation", "recorded_output")
    )


def test_publish_annotation_bundle_writes_ready_manifest_last(tmp_path):
    bundle = build_annotation_bundle(_corpus(), _jury_rows(_corpus()))
    destination = tmp_path / "alignment-run"
    assert publish_annotation_bundle(bundle, destination) == destination
    assert json.loads((destination / "manifest.json").read_text())["status"] == "ready"
    assert json.loads((destination / "queue.json").read_text()) == bundle.queue
    assert sorted(path.name for path in destination.iterdir()) == [
        "jury_errors.json",
        "manifest.json",
        "queue.json",
        "test_manifest.json",
    ]


def test_publish_annotation_bundle_refuses_existing_destination(tmp_path):
    destination = tmp_path / "alignment-run"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        publish_annotation_bundle(
            build_annotation_bundle(_corpus(), _jury_rows(_corpus())), destination
        )


def test_publish_annotation_bundle_cleans_failed_staging_and_lock(tmp_path, monkeypatch):
    destination = tmp_path / "alignment-run"

    def fail_rename(_source, _destination):
        raise OSError("injected publish failure")

    monkeypatch.setattr(os, "rename", fail_rename)
    with pytest.raises(OSError, match="injected"):
        publish_annotation_bundle(
            build_annotation_bundle(_corpus(), _jury_rows(_corpus())), destination
        )
    assert not destination.exists()
    assert not list(tmp_path.iterdir())
