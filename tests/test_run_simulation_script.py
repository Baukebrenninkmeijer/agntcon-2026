import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_simulation.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_simulation", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_exposes_versioned_experiment_and_report_paths() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_simulation.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--evaluation-name" in result.stdout
    assert "--experiment-path" in result.stdout
    assert "--report" in result.stdout


def test_runner_defaults_every_experiment_to_pydata2026() -> None:
    runner = _load_script()

    args = runner.build_parser().parse_args([])

    assert args.experiment_path == "pydata2026"


@pytest.mark.parametrize("occupied", ["output", "report"])
def test_runner_refuses_existing_final_paths(tmp_path: Path, occupied: str) -> None:
    runner = _load_script()
    output = tmp_path / "observations.jsonl"
    report = tmp_path / "report.json"
    (output if occupied == "output" else report).write_text("existing\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        runner._resolve_output_paths(output, report)


def test_runner_refuses_output_report_alias(tmp_path: Path) -> None:
    runner = _load_script()
    output = tmp_path / "observations.jsonl"

    with pytest.raises(ValueError, match="must be different"):
        runner._resolve_output_paths(output, output)


def test_simulation_options_route_experiment_to_selected_project() -> None:
    runner = _load_script()
    args = SimpleNamespace(
        evaluation_name="sphere-v4",
        experiment_path="pydata2026",
        max_turns=3,
        report=Path("runs/report.json"),
    )

    options = runner._simulation_options(args, target=object(), datapoints=[object()])

    assert options["evaluation_name"] == "sphere-v4"
    assert options["orq_results_path"] == "pydata2026"
    assert options["report"] == Path("runs/report.json")
    assert options["datapoint_parallelism"] == 10
