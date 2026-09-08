from __future__ import annotations

import importlib.util
import json
from argparse import Namespace
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upload_decision_support_jury_comparison.py"
DATA = ROOT / "orq/resources/datasets/decision-support-v4"


def _load_script() -> ModuleType:
    assert SCRIPT.exists(), "the comparison uploader must exist"
    spec = importlib.util.spec_from_file_location("upload_jury_comparison", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _args(tmp_path: Path, *, approve_upload: bool) -> Namespace:
    return Namespace(
        labels=DATA / "human-labels-dev-v1.jsonl",
        baseline=DATA / "jury-baseline/jury-results.jsonl",
        human_rules=DATA / "jury-human-rules-v1/jury-results.jsonl",
        prompt_v3=DATA / "jury-prompt-v3/jury-results.jsonl",
        output=tmp_path / "receipt.json",
        approve_upload=approve_upload,
    )


def test_comparison_uses_three_versions_and_only_labelled_development_rows() -> None:
    uploader = _load_script()

    comparison = uploader.load_comparison(_args(Path("/tmp"), approve_upload=False))

    assert len(comparison.data) == 30
    assert [job.__name__ for job in comparison.jobs] == [
        "prompt_v1_baseline",
        "prompt_v2_human_rules",
        "prompt_v3_materiality",
    ]
    assert [evaluator["name"] for evaluator in comparison.evaluators] == [
        "aligned_with_human",
        "panel_consensus",
        "within_judge_stability",
    ]
    assert comparison.summary["versions"] == {
        "Prompt v1 · baseline": {
            "aligned_with_human": 27,
            "panel_consensus": 26,
            "within_judge_stability": 24,
        },
        "Prompt v2 · human rules": {
            "aligned_with_human": 27,
            "panel_consensus": 22,
            "within_judge_stability": 22,
        },
        "Prompt v3 · materiality": {
            "aligned_with_human": 27,
            "panel_consensus": 27,
            "within_judge_stability": 27,
        },
    }


@pytest.mark.asyncio
async def test_boolean_scorers_return_colourable_values() -> None:
    uploader = _load_script()
    comparison = uploader.load_comparison(_args(Path("/tmp"), approve_upload=False))
    data = comparison.data[0]

    for job in comparison.jobs:
        job_result = await job(data, 0)
        output = job_result["output"]
        for evaluator in comparison.evaluators:
            score = await evaluator["scorer"]({"data": data, "output": output, "row": 0})
            assert type(score.value) is bool
            assert score.pass_ is None
            assert score.explanation


@pytest.mark.asyncio
async def test_dry_run_does_not_upload_or_write(tmp_path: Path) -> None:
    uploader = _load_script()

    async def forbidden_runner(*_args: Any, **_kwargs: Any) -> Any:
        pytest.fail("dry-run must not invoke evaluatorq")

    result = await uploader.run(
        _args(tmp_path, approve_upload=False), evaluator_runner=forbidden_runner
    )

    assert result is None
    assert not (tmp_path / "receipt.json").exists()


@pytest.mark.asyncio
async def test_approved_upload_is_one_three_job_experiment(tmp_path: Path) -> None:
    uploader = _load_script()
    captured: dict[str, Any] = {}

    async def fake_runner(name: str, **kwargs: Any) -> list[object]:
        captured.update(name=name, **kwargs)
        kwargs["_experiment_url_out"].append("https://my.orq.ai/example/comparison")
        return [object() for _ in kwargs["data"]]

    receipt = await uploader.run(_args(tmp_path, approve_upload=True), evaluator_runner=fake_runner)

    assert captured["name"] == "decision-support-quality-prompt-comparison"
    assert captured["path"] == "pydata2026"
    assert captured["inference"] is True
    assert captured["datapoint_parallelism"] == 10
    assert len(captured["data"]) == 30
    assert len(captured["jobs"]) == 3
    assert len(captured["evaluators"]) == 3
    assert receipt["experiment_url"] == "https://my.orq.ai/example/comparison"
    assert receipt["judge_calls"] == 0
    assert json.loads((tmp_path / "receipt.json").read_text()) == receipt
