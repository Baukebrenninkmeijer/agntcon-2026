from __future__ import annotations

import importlib.util
import json
import os
from argparse import Namespace
from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from evaluatorq import DataPoint, EvaluationResult, llm_jury
from evaluatorq.common.jury import Prediction

from analytics_chatbot.evaluation_ops import DEFAULT_JUDGES, TraceBackedEvaluationRow

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_decision_support_jury.py"


def _load_script() -> ModuleType:
    assert SCRIPT_PATH.exists(), "the guarded decision-support jury runner must exist"
    spec = importlib.util.spec_from_file_location("run_decision_support_jury", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(index: int = 0, **overrides: Any) -> TraceBackedEvaluationRow:
    response = f"recorded response {index}"
    data: dict[str, Any] = {
        "case_id": f"sphere-stakeholder--v4-case-{index}",
        "evaluation_split": "dev" if index == 0 else "test",
        "source": None,
        "conversation": [
            {"role": "user", "content": f"Sphere.com question {index}"},
            {"role": "assistant", "content": response},
        ],
        "assistant_response": response,
        "decision_context": {
            "stakeholder": "CFO",
            "decision": "choose a region",
            "delivery_setting": "board note",
            "communication_need": "lead with the comparison",
        },
        "metadata": {"transcript_fingerprint": f"{index:064x}"},
    }
    data.update(overrides)
    return TraceBackedEvaluationRow.model_validate(data)


def _corpus(row_count: int = 2) -> SimpleNamespace:
    rows = [_row(index) for index in range(row_count)]
    samples = [
        SimpleNamespace(
            case_id=row.case_id,
            transcript_fingerprint=str(row.metadata["transcript_fingerprint"]),
            row=row,
        )
        for row in rows
    ]
    return SimpleNamespace(samples=samples, rejected=[], duplicates=[], warnings=[])


def _dev_corpus(row_count: int = 2) -> SimpleNamespace:
    corpus = _corpus(row_count)
    for sample in corpus.samples:
        sample.row = sample.row.model_copy(update={"evaluation_split": "dev"})
    return corpus


def _jury() -> dict[str, Any]:
    return {
        "judges_configured": 3,
        "judges_succeeded": 3,
        "judges_failed": 0,
        "replacements_used": 0,
        "tie": False,
        "inconclusive": False,
        "votes": [
            {
                "model": model,
                "replacement": False,
                "success": True,
                "abstained": False,
                "value": value,
                "explanation": f"aggregate explanation {index}",
                "error": None,
                "repetitions": [
                    {"value": value, "explanation": f"raw explanation {index}-{repetition}"}
                    for repetition in range(3)
                ],
                "repetitions_failed": 0,
            }
            for index, (model, value) in enumerate(
                zip(DEFAULT_JUDGES, ["pass", "pass", "fail"], strict=True)
            )
        ],
        "stats": None,
        "raw_agreement": 2 / 3,
    }


def _results(corpus: SimpleNamespace | None = None, *, row_count: int = 2) -> list[SimpleNamespace]:
    corpus = corpus or _corpus(row_count)
    return [
        SimpleNamespace(
            data_point=sample.row.to_datapoint(),
            error=None,
            job_results=[
                SimpleNamespace(
                    job_name="trace-backed-response",
                    output=sample.row.assistant_response,
                    error=None,
                    evaluator_scores=[
                        SimpleNamespace(
                            evaluator_name="decision_support_quality",
                            error=None,
                            score=EvaluationResult(
                                value="pass",
                                explanation=f"aggregate {sample.case_id}",
                                pass_=True,
                                raw_output={"jury": _jury()},
                            ),
                        )
                    ],
                )
            ],
        )
        for sample in corpus.samples
    ]


def _args(tmp_path: Path, *, approve_calls: bool) -> Namespace:
    args = Namespace(
        cases=tmp_path / "cases.jsonl",
        results=tmp_path / "observed.jsonl",
        output=tmp_path / "jury.jsonl",
        approve_calls=approve_calls,
        case_id=None,
    )
    args.cases.write_text("{}\n", encoding="utf-8")
    args.results.write_text("{}\n", encoding="utf-8")
    return args


def test_parser_requires_all_input_and_output_paths() -> None:
    runner = _load_script()

    with pytest.raises(SystemExit):
        runner.build_parser().parse_args([])

    args = runner.build_parser().parse_args(
        [
            "--cases",
            "cases.jsonl",
            "--results",
            "results.jsonl",
            "--output",
            "jury.jsonl",
        ]
    )
    assert args.approve_calls is False


def test_parser_collects_repeatable_case_ids() -> None:
    runner = _load_script()

    args = runner.build_parser().parse_args(
        [
            "--cases",
            "cases.jsonl",
            "--results",
            "results.jsonl",
            "--output",
            "jury.jsonl",
            "--case-id",
            "sphere-stakeholder--v4-case-0",
            "--case-id",
            "sphere-stakeholder--v4-case-1",
        ]
    )

    assert args.case_id == [
        "sphere-stakeholder--v4-case-0",
        "sphere-stakeholder--v4-case-1",
    ]


def test_expected_calls_multiplies_rows_judges_and_repetitions() -> None:
    runner = _load_script()

    assert runner.EXPECTED_JUDGES == 3
    assert runner.EXPECTED_REPETITIONS == 3
    assert runner.expected_calls(50) == 450


@pytest.mark.asyncio
@pytest.mark.parametrize("input_name", ["cases", "results"])
async def test_output_collision_is_rejected_before_loading_or_paid_calls(
    tmp_path: Path,
    input_name: str,
) -> None:
    runner = _load_script()
    args = _args(tmp_path, approve_calls=True)
    args.output = getattr(args, input_name)

    with pytest.raises(runner.JuryReplayError, match="output.*alias"):
        await runner.run(
            args,
            replay_loader=lambda **_kwargs: pytest.fail("replay must not load"),
            evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
            evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        )


@pytest.mark.asyncio
async def test_symlinked_output_alias_is_rejected_before_loading(tmp_path: Path) -> None:
    runner = _load_script()
    args = _args(tmp_path, approve_calls=True)
    alias = tmp_path / "alias.jsonl"
    alias.symlink_to(args.cases)
    args.output = alias

    with pytest.raises(runner.JuryReplayError, match="output.*alias"):
        await runner.run(
            args,
            replay_loader=lambda **_kwargs: pytest.fail("replay must not load"),
            evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
            evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        )


@pytest.mark.asyncio
async def test_samefile_output_alias_is_rejected_before_loading(tmp_path: Path) -> None:
    runner = _load_script()
    args = _args(tmp_path, approve_calls=True)
    alias = tmp_path / "hardlink.jsonl"
    os.link(args.results, alias)
    args.output = alias

    with pytest.raises(runner.JuryReplayError, match="output.*alias"):
        await runner.run(
            args,
            replay_loader=lambda **_kwargs: pytest.fail("replay must not load"),
            evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
            evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        )


@pytest.mark.asyncio
async def test_existing_output_fails_closed_before_loading(tmp_path: Path) -> None:
    runner = _load_script()
    args = _args(tmp_path, approve_calls=True)
    args.output.write_text("keep me\n", encoding="utf-8")

    with pytest.raises(runner.JuryReplayError, match="output already exists"):
        await runner.run(
            args,
            replay_loader=lambda **_kwargs: pytest.fail("replay must not load"),
            evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
            evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        )

    assert args.output.read_text(encoding="utf-8") == "keep me\n"


@pytest.mark.asyncio
async def test_unapproved_run_prints_budget_without_building_or_calling_jury(
    tmp_path: Path,
) -> None:
    runner = _load_script()
    printed: list[str] = []

    exit_code = await runner.run(
        _args(tmp_path, approve_calls=False),
        replay_loader=lambda **_kwargs: _corpus(),
        evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not be built"),
        evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        printer=printed.append,
    )

    assert exit_code == 0
    assert printed == [
        "2 rows × 3 judges × 3 repetitions = 18 model calls; "
        "rerun with --approve-calls to execute."
    ]
    assert not (tmp_path / "jury.jsonl").exists()


@pytest.mark.asyncio
async def test_explicit_dev_case_ids_select_two_rows_and_report_18_calls(
    tmp_path: Path,
) -> None:
    runner = _load_script()
    corpus = _dev_corpus()
    args = _args(tmp_path, approve_calls=False)
    args.case_id = [sample.case_id for sample in corpus.samples]
    printed: list[str] = []

    await runner.run(
        args,
        replay_loader=lambda **_kwargs: corpus,
        evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
        evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        printer=printed.append,
    )

    assert printed == [
        "2 rows × 3 judges × 3 repetitions = 18 model calls; "
        "rerun with --approve-calls to execute."
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case_ids", "message"),
    [
        (
            [
                "sphere-stakeholder--v4-case-0",
                "sphere-stakeholder--v4-case-0",
            ],
            "unique",
        ),
        (["sphere-stakeholder--v4-missing"], "unknown"),
        (["sphere-stakeholder--v4-case-1"], "development"),
    ],
)
async def test_case_id_selection_rejects_duplicate_unknown_or_test_rows(
    tmp_path: Path,
    case_ids: list[str],
    message: str,
) -> None:
    runner = _load_script()
    args = _args(tmp_path, approve_calls=False)
    args.case_id = case_ids

    with pytest.raises(runner.JuryReplayError, match=message):
        await runner.run(
            args,
            replay_loader=lambda **_kwargs: _corpus(),
            evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
            evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("row", "sample_overrides", "message"),
    [
        (_row(case_id="legacy-case"), {}, "v4 Sphere case ID"),
        (_row(decision_context=None), {}, "decision_context"),
        (_row(metadata={}), {}, "transcript fingerprint"),
        (_row().model_copy(update={"evaluation_split": "holdout"}), {}, "dev/test split"),
        (_row().model_copy(update={"assistant_response": ""}), {}, "recorded output"),
        (_row(), {"case_id": "sphere-stakeholder--v4-other"}, "case identity"),
        (_row(), {"transcript_fingerprint": "f" * 64}, "fingerprint"),
    ],
)
async def test_invalid_v4_rows_are_rejected_before_evaluator_construction(
    tmp_path: Path,
    row: TraceBackedEvaluationRow,
    sample_overrides: dict[str, str],
    message: str,
) -> None:
    runner = _load_script()
    sample = SimpleNamespace(
        case_id=row.case_id,
        transcript_fingerprint=(row.metadata or {}).get("transcript_fingerprint", ""),
        row=row,
    )
    for name, value in sample_overrides.items():
        setattr(sample, name, value)
    corpus = SimpleNamespace(samples=[sample], rejected=[], duplicates=[], warnings=[])

    with pytest.raises(runner.JuryReplayError, match=message):
        await runner.run(
            _args(tmp_path, approve_calls=True),
            replay_loader=lambda **_kwargs: corpus,
            evaluator_builder=lambda *_args, **_kwargs: pytest.fail("jury must not build"),
            evaluation_runner=lambda *_args, **_kwargs: pytest.fail("jury must not run"),
        )


@pytest.mark.asyncio
async def test_approved_run_uses_only_decision_support_jury_and_no_inference(
    tmp_path: Path,
) -> None:
    runner = _load_script()
    build_calls: list[tuple[Any, dict[str, Any]]] = []
    run_calls: list[tuple[list[TraceBackedEvaluationRow], dict[str, Any]]] = []
    printed: list[str] = []

    def fake_builder(judge: Any, **kwargs: Any) -> dict[str, Any]:
        build_calls.append((judge, kwargs))
        return {"name": "decision_support_quality", "scorer": object()}

    async def fake_evaluation_runner(
        rows: list[TraceBackedEvaluationRow], **kwargs: Any
    ) -> list[SimpleNamespace]:
        run_calls.append((rows, kwargs))
        kwargs["experiment_url_out"].append("https://example.test/experiment/jury")
        return _results()

    await runner.run(
        _args(tmp_path, approve_calls=True),
        replay_loader=lambda **_kwargs: _corpus(),
        evaluator_builder=fake_builder,
        evaluation_runner=fake_evaluation_runner,
        printer=printed.append,
    )

    assert build_calls == [
        (runner.AtomicJudge.DECISION_SUPPORT_QUALITY, {"repetitions": 3})
    ]
    rows, kwargs = run_calls[0]
    assert len(rows) == 2
    assert [evaluator["name"] for evaluator in kwargs["evaluators"]] == [
        "decision_support_quality"
    ]
    assert kwargs["inference"] is False
    assert kwargs["experiment_path"] == "pydata2026"
    assert kwargs["experiment_url_out"] == [
        "https://example.test/experiment/jury"
    ]
    assert printed[-1] == "Experiment: https://example.test/experiment/jury"


@pytest.mark.asyncio
async def test_approved_run_serializes_the_complete_jury_record(tmp_path: Path) -> None:
    runner = _load_script()
    expected_jury = _jury()
    results = _results(row_count=1)
    results[0].job_results[0].evaluator_scores[0].score.raw_output = {
        "jury": expected_jury
    }

    await runner.run(
        _args(tmp_path, approve_calls=True),
        replay_loader=lambda **_kwargs: _corpus(row_count=1),
        evaluator_builder=lambda *_args, **_kwargs: {
            "name": "decision_support_quality",
            "scorer": object(),
        },
        evaluation_runner=lambda *_args, **_kwargs: _async_result(results),
        printer=lambda _message: None,
    )

    saved = json.loads((tmp_path / "jury.jsonl").read_text())
    assert saved == {
        "schema_version": "decision-support-jury-v1",
        "case_id": "sphere-stakeholder--v4-case-0",
        "evaluation_split": "dev",
        "transcript_fingerprint": "0" * 64,
        "decision_context": {
            "stakeholder": "CFO",
            "decision": "choose a region",
            "delivery_setting": "board note",
            "communication_need": "lead with the comparison",
        },
        "recorded_output": "recorded response 0",
        "value": "pass",
        "explanation": "aggregate sphere-stakeholder--v4-case-0",
        "pass": True,
        "jury": expected_jury,
    }


@pytest.mark.asyncio
async def test_results_are_joined_by_identity_when_native_results_are_reordered(
    tmp_path: Path,
) -> None:
    runner = _load_script()
    corpus = _corpus()
    results = list(reversed(_results(corpus)))

    await runner.run(
        _args(tmp_path, approve_calls=True),
        replay_loader=lambda **_kwargs: corpus,
        evaluator_builder=lambda *_args, **_kwargs: {
            "name": "decision_support_quality",
            "scorer": object(),
        },
        evaluation_runner=lambda *_args, **_kwargs: _async_result(results),
        printer=lambda _message: None,
    )

    saved = [json.loads(line) for line in (tmp_path / "jury.jsonl").read_text().splitlines()]
    assert [record["case_id"] for record in saved] == [
        "sphere-stakeholder--v4-case-0",
        "sphere-stakeholder--v4-case-1",
    ]
    assert [record["explanation"] for record in saved] == [
        "aggregate sphere-stakeholder--v4-case-0",
        "aggregate sphere-stakeholder--v4-case-1",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("corrupt", "message"),
    [
        ("context", "returned data point.*source row"),
        ("output", "recorded output"),
        ("duplicate", "duplicate returned result identity"),
    ],
)
async def test_result_identity_or_recorded_output_mismatch_is_rejected(
    tmp_path: Path,
    corrupt: str,
    message: str,
) -> None:
    runner = _load_script()
    corpus = _corpus()
    results = _results(corpus)
    if corrupt == "context":
        wrong_context = _row(
            0,
            decision_context={
                "stakeholder": "COO",
                "decision": "choose a category",
                "delivery_setting": "review",
                "communication_need": "show risk",
            },
        )
        results[0].data_point = wrong_context.to_datapoint()
    elif corrupt == "output":
        results[0].job_results[0].output = "a regenerated response"
    else:
        results[1].data_point = results[0].data_point
        results[1].job_results[0].output = results[0].job_results[0].output

    with pytest.raises(runner.JuryReplayError, match=message):
        await runner.run(
            _args(tmp_path, approve_calls=True),
            replay_loader=lambda **_kwargs: corpus,
            evaluator_builder=lambda *_args, **_kwargs: {
                "name": "decision_support_quality",
                "scorer": object(),
            },
            evaluation_runner=lambda *_args, **_kwargs: _async_result(results),
            printer=lambda _message: None,
        )

    assert not (tmp_path / "jury.jsonl").exists()


@pytest.mark.asyncio
async def test_atomic_writer_uses_unique_temp_fsync_and_preserves_old_temp_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_script()
    deterministic_temp = tmp_path / "jury.jsonl.tmp"
    deterministic_temp.write_text("unrelated prior file\n", encoding="utf-8")
    fsync_calls: list[int] = []
    real_fsync = os.fsync

    def recording_fsync(file_descriptor: int) -> None:
        fsync_calls.append(file_descriptor)
        real_fsync(file_descriptor)

    monkeypatch.setattr(runner.os, "fsync", recording_fsync)
    await runner.run(
        _args(tmp_path, approve_calls=True),
        replay_loader=lambda **_kwargs: _corpus(row_count=1),
        evaluator_builder=lambda *_args, **_kwargs: {
            "name": "decision_support_quality",
            "scorer": object(),
        },
        evaluation_runner=lambda *_args, **_kwargs: _async_result(_results(row_count=1)),
        printer=lambda _message: None,
    )

    assert (tmp_path / "jury.jsonl").exists()
    assert deterministic_temp.read_text(encoding="utf-8") == "unrelated prior file\n"
    assert fsync_calls
    assert not list(tmp_path.glob(".jury.jsonl.*.tmp"))


@pytest.mark.asyncio
async def test_atomic_writer_cleans_unique_temp_when_publication_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_script()

    def fail_link(_source: object, _destination: object) -> None:
        raise OSError("link failed")

    monkeypatch.setattr(runner.os, "link", fail_link)
    with pytest.raises(OSError, match="link failed"):
        await runner.run(
            _args(tmp_path, approve_calls=True),
            replay_loader=lambda **_kwargs: _corpus(row_count=1),
            evaluator_builder=lambda *_args, **_kwargs: {
                "name": "decision_support_quality",
                "scorer": object(),
            },
            evaluation_runner=lambda *_args, **_kwargs: _async_result(_results(row_count=1)),
            printer=lambda _message: None,
        )

    assert not (tmp_path / "jury.jsonl").exists()
    assert not list(tmp_path.glob(".jury.jsonl.*.tmp"))


@pytest.mark.asyncio
async def test_atomic_writer_never_overwrites_output_created_during_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_script()
    real_link = os.link

    def race_link(source: object, destination: object) -> None:
        Path(destination).write_text("concurrent writer\n", encoding="utf-8")
        real_link(source, destination)

    monkeypatch.setattr(runner.os, "link", race_link)
    with pytest.raises(runner.JuryReplayError, match="output already exists"):
        await runner.run(
            _args(tmp_path, approve_calls=True),
            replay_loader=lambda **_kwargs: _corpus(row_count=1),
            evaluator_builder=lambda *_args, **_kwargs: {
                "name": "decision_support_quality",
                "scorer": object(),
            },
            evaluation_runner=lambda *_args, **_kwargs: _async_result(
                _results(row_count=1)
            ),
            printer=lambda _message: None,
        )

    assert (tmp_path / "jury.jsonl").read_text(encoding="utf-8") == "concurrent writer\n"
    assert not list(tmp_path.glob(".jury.jsonl.*.tmp"))


async def _async_result(value: Any) -> Any:
    return value


@pytest.mark.parametrize(
    ("raw_output", "message"),
    [
        (None, "missing raw_output.jury"),
        ({}, "missing raw_output.jury"),
        ({"jury": {"votes": []}}, "invalid evaluatorq jury record"),
        (
            {
                "jury": {
                    "votes": [
                        {"repetitions": [1, 2, 3]},
                        {"repetitions": [1, 2, 3]},
                        {"repetitions": [1, 2]},
                    ]
                }
            },
            "invalid evaluatorq jury record",
        ),
    ],
)
def test_jury_validation_rejects_missing_or_incomplete_records(
    raw_output: object,
    message: str,
) -> None:
    runner = _load_script()

    with pytest.raises(runner.JuryReplayError, match=message):
        runner.validate_jury_record(raw_output)


def test_jury_validation_returns_the_complete_object_unchanged() -> None:
    runner = _load_script()
    jury = _jury()

    assert runner.validate_jury_record({"jury": jury}) is jury


@pytest.mark.parametrize(
    ("level", "field"),
    [
        *(("panel", field) for field in (
            "judges_configured",
            "judges_succeeded",
            "judges_failed",
            "replacements_used",
            "tie",
            "inconclusive",
            "votes",
            "stats",
            "raw_agreement",
        )),
        *(("vote", field) for field in (
            "model",
            "replacement",
            "success",
            "abstained",
            "value",
            "explanation",
            "error",
            "repetitions",
            "repetitions_failed",
        )),
        ("repetition", "value"),
        ("repetition", "explanation"),
    ],
)
def test_jury_validation_requires_every_released_raw_field(
    level: str,
    field: str,
) -> None:
    runner = _load_script()
    jury = _jury()
    target = jury
    if level == "vote":
        target = jury["votes"][0]
    elif level == "repetition":
        target = jury["votes"][0]["repetitions"][0]
    del target[field]

    with pytest.raises(runner.JuryReplayError, match=rf"{level}.*{field}"):
        runner.validate_jury_record({"jury": jury})


@pytest.mark.parametrize(
    ("level", "field", "value"),
    [
        ("panel", "judges_configured", "3"),
        ("vote", "replacement", 0),
        ("repetition", "explanation", b"coercible explanation"),
    ],
)
def test_jury_validation_rejects_coercible_wrong_raw_types(
    level: str,
    field: str,
    value: object,
) -> None:
    runner = _load_script()
    jury = _jury()
    target = jury
    if level == "vote":
        target = jury["votes"][0]
    elif level == "repetition":
        target = jury["votes"][0]["repetitions"][0]
    target[field] = value

    with pytest.raises(runner.JuryReplayError, match="invalid evaluatorq jury record"):
        runner.validate_jury_record({"jury": jury})


def test_jury_validation_requires_exact_ordered_models_and_repetition_objects() -> None:
    runner = _load_script()
    wrong_model = _jury()
    wrong_model["votes"][0]["model"] = "openai/not-the-configured-model"
    with pytest.raises(runner.JuryReplayError, match="ordered configured models"):
        runner.validate_jury_record({"jury": wrong_model})

    missing_explanation = _jury()
    del missing_explanation["votes"][0]["repetitions"][0]["explanation"]
    with pytest.raises(runner.JuryReplayError, match="repetition.*explanation"):
        runner.validate_jury_record({"jury": missing_explanation})


def test_jury_validation_rejects_top_level_evaluation_errors() -> None:
    runner = _load_script()
    for evaluation_error in ("provider transport failed", None):
        with pytest.raises(runner.JuryReplayError, match="evaluation_error"):
            runner.validate_jury_record(
                {"jury": _jury(), "evaluation_error": evaluation_error}
            )



def test_jury_validation_preserves_complete_mechanical_failures() -> None:
    runner = _load_script()
    mechanical = _jury()
    mechanical["judges_succeeded"] = 2
    mechanical["judges_failed"] = 1
    mechanical["votes"][2].update(
        success=False,
        value=None,
        explanation="",
        error="provider transport failed",
        repetitions=[],
        repetitions_failed=3,
    )

    assert runner.validate_jury_record({"jury": mechanical}) is mechanical


def test_jury_validation_requires_three_repetitions_for_successful_votes() -> None:
    runner = _load_script()
    incomplete = _jury()
    incomplete["votes"][0]["repetitions"].pop()

    with pytest.raises(runner.JuryReplayError, match="successful.*three repetitions"):
        runner.validate_jury_record({"jury": incomplete})


@pytest.mark.asyncio
async def test_jury_validation_rejects_nine_fake_provider_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_script()
    counters = {model: 0 for model in DEFAULT_JUDGES}

    async def fake_provider_error(*, model: str, **_kwargs: Any) -> Prediction:
        repetition = counters[model]
        counters[model] += 1
        return Prediction(error=f"provider failure {model} repetition {repetition}")

    monkeypatch.setattr(
        import_module("evaluatorq.llm_jury"),
        "_run_single_judge",
        fake_provider_error,
    )
    evaluator = llm_jury(
        name="decision_support_quality",
        criteria="Does the response support the decision?",
        judges=list(DEFAULT_JUDGES),
        repetitions=3,
        assignment="all",
        min_successful_judges=2,
        labels=["pass", "fail", "not_applicable"],
        passing_labels=["pass"],
        aggregator="majority",
        client=object(),
    )
    score = await evaluator["scorer"](
        {"data": DataPoint(inputs={"question": "Q"}), "output": "A"}
    )

    assert counters == {model: 3 for model in DEFAULT_JUDGES}
    with pytest.raises(
        runner.JuryReplayError,
        match="evaluation_error|mechanical judge failure",
    ):
        runner.validate_jury_record(score.raw_output)


@pytest.mark.parametrize("outcome", ["disagreement", "tie", "inconclusive"])
def test_jury_validation_accepts_genuine_non_mechanical_outcomes(outcome: str) -> None:
    runner = _load_script()
    jury = _jury()
    if outcome == "disagreement":
        for vote, value in zip(jury["votes"], ["pass", "pass", "fail"], strict=True):
            vote["value"] = value
            vote["repetitions"] = [
                {"value": value, "explanation": f"{value} repetition {index}"}
                for index in range(3)
            ]
    elif outcome == "tie":
        jury["judges_succeeded"] = 2
        jury["votes"][0]["value"] = "pass"
        jury["votes"][1]["value"] = "fail"
        jury["votes"][2].update(
            abstained=True,
            value=None,
            repetitions=[
                {"value": None, "explanation": f"abstained repetition {index}"}
                for index in range(3)
            ],
        )
        jury.update(tie=True, raw_agreement=0.5, stats=None)
    else:
        jury["judges_succeeded"] = 0
        for vote in jury["votes"]:
            vote.update(
                abstained=True,
                value=None,
                repetitions=[
                    {"value": None, "explanation": f"abstained repetition {index}"}
                    for index in range(3)
                ],
            )
        jury.update(inconclusive=True, raw_agreement=None, stats=None)

    assert runner.validate_jury_record({"jury": jury}) is jury


@pytest.mark.asyncio
async def test_approved_run_rejects_any_result_shape_or_jury_error(tmp_path: Path) -> None:
    runner = _load_script()
    invalid_results = _results(row_count=1)
    invalid_results[0].job_results[0].evaluator_scores[0].score.raw_output = None

    with pytest.raises(runner.JuryReplayError, match="missing raw_output.jury"):
        await runner.run(
            _args(tmp_path, approve_calls=True),
            replay_loader=lambda **_kwargs: _corpus(row_count=1),
            evaluator_builder=lambda *_args, **_kwargs: {
                "name": "decision_support_quality",
                "scorer": object(),
            },
            evaluation_runner=lambda *_args, **_kwargs: _async_result(invalid_results),
            printer=lambda _message: None,
        )

    assert not (tmp_path / "jury.jsonl").exists()
