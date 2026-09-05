from __future__ import annotations

import importlib.util
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_evaluatorq_replay.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("run_evaluatorq_replay", SCRIPT_PATH)
assert SCRIPT_SPEC is not None
assert SCRIPT_SPEC.loader is not None
run_evaluatorq_replay = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(run_evaluatorq_replay)


def test_parser_requires_an_explicit_evaluator_version() -> None:
    parser = run_evaluatorq_replay.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_defaults_experiment_upload_to_pydata_project() -> None:
    args = run_evaluatorq_replay.build_parser().parse_args(
        ["--evaluator-version", "1.0.0"]
    )

    assert args.project_path == "pydata2026"


@pytest.mark.asyncio
async def test_latest_is_rejected_before_loading_credentials() -> None:
    dotenv_called = False

    def fake_load_dotenv(path: object, *, override: bool) -> None:
        nonlocal dotenv_called
        dotenv_called = True

    with pytest.raises(
        run_evaluatorq_replay.ReplayPreparationError,
        match="latest.*not allowed",
    ):
        await run_evaluatorq_replay.run(
            Namespace(evaluator_version=["latest"]),
            dotenv_loader=fake_load_dotenv,
        )

    assert dotenv_called is False


@pytest.mark.asyncio
async def test_run_prepares_all_samples_and_invokes_native_replay_once() -> None:
    events: list[str] = []
    environment: dict[str, str] = {}
    opaque_evaluator_id = "opaque-runtime-evaluator-id"

    def fake_load_dotenv(path: object, *, override: bool) -> None:
        events.append(f"dotenv:{path}")
        assert override is True
        environment["ORQ_API_KEY"] = "secret-not-for-output"

    version_calls: list[dict[str, Any]] = []

    class FakeEvals:
        def list_versions(self, **kwargs: Any) -> object:
            version_calls.append(kwargs)
            return SimpleNamespace(
                data=[
                    SimpleNamespace(id="opaque-version-record-1", version="1.0.0"),
                    SimpleNamespace(id="opaque-version-record-2", version="1.1.0"),
                ],
                has_more=False,
            )

    fake_client = SimpleNamespace(evals=FakeEvals())

    class FakeGateway:
        client = fake_client

        def snapshot(self, bundle: object) -> object:
            events.append("snapshot")
            assert bundle == "resource-bundle"
            return SimpleNamespace(
                evaluators=[
                    SimpleNamespace(
                        key="analytics-answer-correctness",
                        entity_id=opaque_evaluator_id,
                    )
                ]
            )

    def fake_gateway_factory(api_key: str) -> FakeGateway:
        assert events and events[0].startswith("dotenv:")
        assert api_key == "secret-not-for-output"
        events.append("gateway")
        return FakeGateway()

    def fake_replay_loader(**kwargs: Any) -> object:
        events.append("replay")
        assert kwargs["cases_path"].name == "simulation-cases-v2.jsonl"
        assert kwargs["results_path"].name == "evaluatorq-simulation-v2-20260905.jsonl"
        samples = [SimpleNamespace(row={"case_id": f"case-{index}"}) for index in range(50)]
        samples[7].row["behavioral_failure"] = True
        return SimpleNamespace(
            samples=tuple(samples),
            warnings=("warning-a", "warning-b"),
            rejected=(),
            duplicates=(),
        )

    scorer_calls: list[dict[str, Any]] = []

    def fake_scorer_factory(**kwargs: Any) -> object:
        scorer_calls.append(kwargs)
        return SimpleNamespace(name=kwargs["scorer_name"])

    runner_calls: list[tuple[list[object], dict[str, Any]]] = []

    async def fake_evaluation_runner(rows: list[object], **kwargs: Any) -> list[object]:
        runner_calls.append((rows, kwargs))
        evaluator_names = [evaluator.name for evaluator in kwargs["evaluators"]]
        return [
            SimpleNamespace(
                error=None,
                job_results=[
                    SimpleNamespace(
                        error=None,
                        evaluator_scores=[
                            SimpleNamespace(
                                evaluator_name=name,
                                error=None,
                                score=SimpleNamespace(value="pass"),
                            )
                            for name in evaluator_names
                        ],
                    )
                ],
            )
            for _row in rows
        ]

    fake_http_client = SimpleNamespace(post="async-post")

    class FakeAsyncHttpClientContext:
        async def __aenter__(self) -> object:
            events.append("http-enter")
            return fake_http_client

        async def __aexit__(self, *args: object) -> None:
            events.append("http-exit")

    def fake_async_http_client_factory(**kwargs: Any) -> FakeAsyncHttpClientContext:
        assert kwargs == {"timeout": 600.0}
        return FakeAsyncHttpClientContext()

    printed: list[str] = []
    args = Namespace(
        cases=run_evaluatorq_replay.DEFAULT_CASES_PATH,
        results=run_evaluatorq_replay.DEFAULT_RESULTS_PATH,
        resources=run_evaluatorq_replay.DEFAULT_RESOURCES_PATH,
        evaluator_version=["1.0.0", "1.1.0"],
        experiment_name="stored-v2-replay",
        project_path="pydata2026",
        datapoint_parallelism=4,
        llm_parallelism=3,
        print_results=False,
    )

    exit_code = await run_evaluatorq_replay.run(
        args,
        dotenv_loader=fake_load_dotenv,
        gateway_factory=fake_gateway_factory,
        bundle_loader=lambda path: "resource-bundle",
        replay_loader=fake_replay_loader,
        scorer_factory=fake_scorer_factory,
        evaluation_runner=fake_evaluation_runner,
        async_http_client_factory=fake_async_http_client_factory,
        environ=environment,
        printer=printed.append,
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    rows, runner_kwargs = runner_calls[0]
    assert len(rows) == 50
    assert rows[7]["behavioral_failure"] is True
    assert [scorer.name for scorer in runner_kwargs["evaluators"]] == [
        "answer_correctness@1.0.0",
        "answer_correctness@1.1.0",
    ]
    assert runner_kwargs == {
        "evaluators": runner_kwargs["evaluators"],
        "experiment_name": "stored-v2-replay",
        "experiment_path": "pydata2026",
        "datapoint_parallelism": 4,
        "llm_parallelism": 3,
        "print_results": False,
    }
    assert version_calls == [
        {"id": opaque_evaluator_id, "limit": 200, "starting_after": None}
    ]
    assert [call["evaluator_selector"] for call in scorer_calls] == [
        f"{opaque_evaluator_id}@1.0.0",
        f"{opaque_evaluator_id}@1.1.0",
    ]
    assert all(call["http_client"] is fake_http_client for call in scorer_calls)
    assert all(call["api_key"] == "secret-not-for-output" for call in scorer_calls)
    assert events[-1] == "http-exit"
    assert all(opaque_evaluator_id not in line for line in printed)
    assert any("50" in line and "2 QC warning" in line for line in printed)


def test_replay_result_validation_rejects_captured_evaluator_errors() -> None:
    results = [
        SimpleNamespace(
            error=None,
            job_results=[
                SimpleNamespace(
                    error=None,
                    evaluator_scores=[
                        SimpleNamespace(
                            evaluator_name="answer_correctness@1.0.0",
                            error="remote evaluator failed",
                            score=SimpleNamespace(value=""),
                        )
                    ],
                )
            ],
        )
    ]

    with pytest.raises(
        run_evaluatorq_replay.ReplayPreparationError,
        match="1 evaluator error.*1 empty score",
    ):
        run_evaluatorq_replay._validate_evaluation_results(
            results,
            expected_rows=1,
            expected_evaluator_names=("answer_correctness@1.0.0",),
        )


def test_replay_result_validation_rejects_scores_shifted_between_rows() -> None:
    duplicate_score = SimpleNamespace(
        evaluator_name="answer_correctness@1.0.0",
        error=None,
        score=SimpleNamespace(value="pass"),
    )
    results = [
        SimpleNamespace(
            error=None,
            job_results=[
                SimpleNamespace(
                    error=None,
                    evaluator_scores=[duplicate_score, duplicate_score],
                )
            ],
        ),
        SimpleNamespace(
            error=None,
            job_results=[SimpleNamespace(error=None, evaluator_scores=[])],
        ),
    ]

    with pytest.raises(
        run_evaluatorq_replay.ReplayPreparationError,
        match="2 row score-set error",
    ):
        run_evaluatorq_replay._validate_evaluation_results(
            results,
            expected_rows=2,
            expected_evaluator_names=("answer_correctness@1.0.0",),
        )


@pytest.mark.asyncio
async def test_missing_pinned_version_fails_without_exposing_runtime_id() -> None:
    opaque_evaluator_id = "opaque-runtime-evaluator-id"
    environment: dict[str, str] = {}

    def fake_load_dotenv(path: object, *, override: bool) -> None:
        environment["ORQ_API_KEY"] = "secret-not-for-output"

    fake_client = SimpleNamespace(
        evals=SimpleNamespace(
            list_versions=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(id="opaque-version-record", version="1.0.0")],
                has_more=False,
            )
        )
    )
    gateway = SimpleNamespace(
        client=fake_client,
        snapshot=lambda bundle: SimpleNamespace(
            evaluators=[
                SimpleNamespace(
                    key="analytics-answer-correctness",
                    entity_id=opaque_evaluator_id,
                )
            ]
        ),
    )
    args = Namespace(
        resources=run_evaluatorq_replay.DEFAULT_RESOURCES_PATH,
        evaluator_version=["9.9.9"],
    )

    with pytest.raises(run_evaluatorq_replay.ReplayPreparationError) as exc_info:
        await run_evaluatorq_replay.run(
            args,
            dotenv_loader=fake_load_dotenv,
            gateway_factory=lambda api_key: gateway,
            bundle_loader=lambda path: "resource-bundle",
            replay_loader=lambda **kwargs: pytest.fail("replay must not load"),
            evaluation_runner=lambda *args, **kwargs: pytest.fail("runner must not run"),
            environ=environment,
        )

    message = str(exc_info.value)
    assert "9.9.9" in message
    assert "analytics-answer-correctness" in message
    assert opaque_evaluator_id not in message
