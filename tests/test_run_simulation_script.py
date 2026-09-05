import subprocess
import sys


def test_runner_exposes_versioned_experiment_and_report_paths() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_simulation.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--evaluation-name" in result.stdout
    assert "--report" in result.stdout
