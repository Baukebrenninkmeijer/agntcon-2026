from __future__ import annotations

import importlib.util
import json
from argparse import Namespace
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from evaluatorq import EvaluationResult

from analytics_chatbot.evaluation_ops import TraceBackedEvaluationRow

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_decision_support_jury.py"


def _load_script() -> ModuleType:
    assert SCRIPT_PATH.exists(), "the guarded decision-support jury runner must exist"
    spec = importlib.util.spec_from_file_location("run_decision_support_jury", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(index: int = 0) -> TraceBackedEvaluationRow:
    response = f"recorded response {index}"
    return TraceBackedEvaluationRow.model_validate(
        {
            "case_id": f"case-{index}",
            "evaluation_split": "dev" if index == 0 else "test",
            "source": None,
            "conversation": [
                {"role": "user", "content": f"question {index}"},
                {"role": "assistant", "content": response},
            ],
            "assistant_response": response,
            "decision_context": {
                "stakeholder": "CFO",
                "decision": "choose a region",
                "delivery_setting": "board note",
                "communication_need": "lead with the comparison",
            },
            "metadata": {"transcript_fingerprint": f"fingerprint-{index}"},
        }
    )


def _corpus(row_count: int = 2) -> SimpleNamespace:
    samples = [
        SimpleNamespace(
            case_id=f"case-{index}",
            transcript_fingerprint=f"fingerprint-{index}",
            row=_row(index),
        )
        for index in range(row_count)
    ]
    return SimpleNamespace(samples=samples, rejected=[], duplicates=[], warnings=[])


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
                [
                    ("openai/model-a", "pass"),
                    ("anthropic/model-b", "pass"),
                    ("google/model-c", "fail"),
                ]
            )
        ],
        "stats": None,
        "raw_agreement": 2 / 3,
    }


def _results(row_count: int = 2) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            error=None,
            job_results=[
                SimpleNamespace(
                    error=None,
                    evaluator_scores=[
                        SimpleNamespace(
                            evaluator_name="decision_support_quality",
                            error=None,
                            score=EvaluationResult(
                                value="pass",
                                explanation=f"aggregate {index}",
                                pass_=True,
                                raw_output={"jury": _jury()},
                            ),
                        )
                    ],
                )
            ],
        )
        for index in range(row_count)
    ]


def _args(tmp_path: Path, *, approve_calls: bool) -> Namespace:
    return Namespace(
        cases=tmp_path / "cases.jsonl",
        results=tmp_path / "observed.jsonl",
        output=tmp_path / "jury.jsonl",
        approve_calls=approve_calls,
    )


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


def test_expected_calls_multiplies_rows_judges_and_repetitions() -> None:
    runner = _load_script()

    assert runner.EXPECTED_JUDGES == 3
    assert runner.EXPECTED_REPETITIONS == 3
    assert runner.expected_calls(50) == 450


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
async def test_approved_run_uses_only_decision_support_jury_and_no_inference(
    tmp_path: Path,
) -> None:
    runner = _load_script()
    build_calls: list[tuple[Any, dict[str, Any]]] = []
    run_calls: list[tuple[list[TraceBackedEvaluationRow], dict[str, Any]]] = []

    def fake_builder(judge: Any, **kwargs: Any) -> dict[str, Any]:
        build_calls.append((judge, kwargs))
        return {"name": "decision_support_quality", "scorer": object()}

    async def fake_evaluation_runner(
        rows: list[TraceBackedEvaluationRow], **kwargs: Any
    ) -> list[SimpleNamespace]:
        run_calls.append((rows, kwargs))
        return _results()

    await runner.run(
        _args(tmp_path, approve_calls=True),
        replay_loader=lambda **_kwargs: _corpus(),
        evaluator_builder=fake_builder,
        evaluation_runner=fake_evaluation_runner,
        printer=lambda _message: None,
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
        "case_id": "case-0",
        "evaluation_split": "dev",
        "transcript_fingerprint": "fingerprint-0",
        "decision_context": {
            "stakeholder": "CFO",
            "decision": "choose a region",
            "delivery_setting": "board note",
            "communication_need": "lead with the comparison",
        },
        "recorded_output": "recorded response 0",
        "value": "pass",
        "explanation": "aggregate 0",
        "pass": True,
        "jury": expected_jury,
    }


async def _async_result(value: Any) -> Any:
    return value


@pytest.mark.parametrize(
    ("raw_output", "message"),
    [
        (None, "missing raw_output.jury"),
        ({}, "missing raw_output.jury"),
        ({"jury": {"votes": []}}, "exactly three votes"),
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
            "each decision-support vote must retain three repetitions",
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
