from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest
from test_jury_annotation import _corpus, _jury_rows

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_jury_annotations.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("prepare_jury_annotations", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_jsonl_rejects_malformed_input(tmp_path: Path):
    module = _load_script()
    source = tmp_path / "jury.jsonl"
    source.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        module.load_jsonl(source)


def test_prepare_builds_and_publishes_without_evaluation_calls(tmp_path: Path):
    module = _load_script()
    corpus = _corpus()
    jury_rows = _jury_rows(corpus)
    cases = tmp_path / "cases.jsonl"
    results = tmp_path / "results.jsonl"
    jury = tmp_path / "jury.jsonl"
    for path in (cases, results):
        path.write_text("{}\n", encoding="utf-8")
    jury.write_text(
        "".join(json.dumps(row) + "\n" for row in jury_rows),
        encoding="utf-8",
    )
    destination = tmp_path / "annotation-run"

    prepared = module.prepare(
        cases,
        results,
        jury,
        destination,
        replay_loader=lambda **_kwargs: corpus,
    )

    assert prepared == destination.resolve()
    queue = json.loads((destination / "queue.json").read_text(encoding="utf-8"))
    assert queue["meta"]["n_items"] == 5
    assert queue["meta"]["mode"] == "jury"


def test_prepare_refuses_existing_output_before_loading_inputs(tmp_path: Path):
    module = _load_script()
    destination = tmp_path / "annotation-run"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        module.prepare(
            tmp_path / "missing-cases",
            tmp_path / "missing-results",
            tmp_path / "missing-jury",
            destination,
            replay_loader=lambda **_kwargs: pytest.fail("must not load replay"),
        )
