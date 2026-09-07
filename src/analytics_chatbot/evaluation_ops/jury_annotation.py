"""Build a reviewer-safe annotation queue from a completed evaluatorq jury."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evaluatorq.contracts import JuryResult

from analytics_chatbot.evaluation_ops import DEFAULT_JUDGES, VERDICT_LABELS
from analytics_chatbot.evaluation_ops.simulation_artifacts import SimulationReplayCorpus

ALGORITHM_VERSION = "jury-annotation-v1"


@dataclass(frozen=True)
class JudgeWobble:
    model: str
    instability: float | None
    non_null_repetitions: int


@dataclass(frozen=True)
class JurySignals:
    tie: bool
    abstention: bool
    inconclusive: bool
    panel_disagreement: bool
    within_judge_wobble: bool
    panel_agreement: float | None
    per_judge: tuple[JudgeWobble, ...]
    mechanical_errors: tuple[str, ...]
    priority_tier: int | None


@dataclass(frozen=True)
class AnnotationBundle:
    queue: dict[str, Any]
    test_manifest: dict[str, Any]
    jury_errors: dict[str, Any]


def annotation_id(case_id: str, transcript_fingerprint: str) -> str:
    """Return the stable identity used by human annotations."""
    return hashlib.sha256(f"{case_id}\0{transcript_fingerprint}".encode()).hexdigest()


def _categorical_instability(values: Sequence[str]) -> float | None:
    if len(values) < 2:
        return None
    entropy = 0.0
    for count in Counter(values).values():
        probability = count / len(values)
        entropy -= probability * math.log(probability)
    return min(1.0, entropy / math.log(len(VERDICT_LABELS)))


def analyze_jury(jury: Mapping[str, Any]) -> JurySignals:
    """Classify ambiguity separately from transport or provider failure."""
    typed = JuryResult.model_validate(jury, strict=True)
    if [vote.model for vote in typed.votes] != list(DEFAULT_JUDGES):
        raise ValueError("jury must retain the exact ordered models")
    if any(vote.success and len(vote.repetitions) != 3 for vote in typed.votes):
        raise ValueError("every jury vote must retain exactly three repetitions")
    errors: list[str] = []
    if typed.judges_failed:
        errors.append(f"{typed.judges_failed} judge(s) failed")
    if typed.replacements_used:
        errors.append(f"{typed.replacements_used} replacement judge(s) used")
    if typed.judges_succeeded < 2:
        errors.append("fewer than two judges succeeded")

    per_judge: list[JudgeWobble] = []
    aggregate_values: list[str] = []
    abstention = False
    for vote in typed.votes:
        if not vote.success or vote.error:
            errors.append(f"judge failed: {vote.model}")
        if vote.repetitions_failed:
            errors.append(f"judge repetitions failed: {vote.model}")
        clean_repetition_abstention = bool(
            vote.success
            and vote.repetitions_failed == 0
            and any(repetition.value is None for repetition in vote.repetitions)
        )
        abstention = abstention or bool(
            vote.success and (vote.abstained or vote.value is None or clean_repetition_abstention)
        )
        if vote.success and not vote.abstained and vote.value is not None:
            aggregate_values.append(str(vote.value))
        repetitions = [
            str(repetition.value)
            for repetition in vote.repetitions
            if repetition.value is not None
        ]
        per_judge.append(
            JudgeWobble(
                model=vote.model,
                instability=_categorical_instability(repetitions),
                non_null_repetitions=len(repetitions),
            )
        )

    mechanical_errors = tuple(dict.fromkeys(errors))
    disagreement = len(set(aggregate_values)) > 1
    wobble = any(
        judge.instability is not None and judge.instability > 0 for judge in per_judge
    )
    if mechanical_errors:
        tier = None
    elif typed.tie or abstention or typed.inconclusive:
        tier = 1
    elif disagreement and wobble:
        tier = 2
    elif disagreement:
        tier = 3
    elif wobble:
        tier = 4
    else:
        tier = 5
    return JurySignals(
        tie=typed.tie,
        abstention=abstention,
        inconclusive=typed.inconclusive,
        panel_disagreement=disagreement,
        within_judge_wobble=wobble,
        panel_agreement=typed.raw_agreement,
        per_judge=tuple(per_judge),
        mechanical_errors=mechanical_errors,
        priority_tier=tier,
    )


def _signals_dict(signals: JurySignals) -> dict[str, Any]:
    value = asdict(signals)
    value["per_judge"] = [asdict(item) for item in signals.per_judge]
    value["mechanical_errors"] = list(signals.mechanical_errors)
    return value


def _priority_reasons(signals: JurySignals) -> list[str]:
    reasons = []
    for name, present in (
        ("tie", signals.tie),
        ("abstention", signals.abstention),
        ("inconclusive", signals.inconclusive),
        ("panel_disagreement", signals.panel_disagreement),
        ("within_judge_wobble", signals.within_judge_wobble),
    ):
        if present:
            reasons.append(name)
    return reasons


def _max_instability(signals: JurySignals) -> float:
    values = [item.instability for item in signals.per_judge if item.instability is not None]
    return max(values, default=0.0)


def _priority_key(item: dict[str, Any]) -> tuple[Any, ...]:
    signals = item["_signals"]
    agreement = signals.panel_agreement
    return (
        signals.priority_tier,
        -len(_priority_reasons(signals)),
        -_max_instability(signals),
        -1.0 if agreement is None else agreement,
        item["annotation_id"],
    )


def _input_fingerprint(identities: Sequence[tuple[str, str]]) -> str:
    payload = json.dumps(list(identities), separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def build_annotation_bundle(
    corpus: SimulationReplayCorpus,
    jury_rows: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
    control_count: int = 5,
) -> AnnotationBundle:
    """Join a canonical 50-row corpus to jury evidence and rank dev review rows."""
    if len(corpus.samples) != 50:
        raise ValueError(f"expected exactly 50 observed cases, got {len(corpus.samples)}")
    if corpus.rejected or corpus.duplicates:
        raise ValueError("simulation replay contains rejected or duplicate observations")
    case_ids = [sample.case_id for sample in corpus.samples]
    if len(set(case_ids)) != 50:
        raise ValueError("observations must contain exactly one row per case ID")
    split_counts = Counter(sample.row.evaluation_split for sample in corpus.samples)
    if split_counts != {"dev": 30, "test": 20}:
        raise ValueError(f"expected frozen 30/20 split, got {dict(split_counts)}")

    jury_by_identity: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in jury_rows:
        identity = (str(row.get("case_id") or ""), str(row.get("transcript_fingerprint") or ""))
        if identity in jury_by_identity:
            raise ValueError(f"duplicate jury identity: {identity}")
        jury_by_identity[identity] = row
    expected_identities = {sample.identity for sample in corpus.samples}
    if set(jury_by_identity) != expected_identities:
        raise ValueError("jury rows do not exactly match the 50 observation identities")

    ranked: list[dict[str, Any]] = []
    stable: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    test_items: list[dict[str, str]] = []
    for source_index, sample in enumerate(corpus.samples):
        row = jury_by_identity[sample.identity]
        if row.get("schema_version") != "decision-support-jury-v1":
            raise ValueError(f"unsupported jury schema for {sample.case_id}")
        if row.get("evaluation_split") != sample.row.evaluation_split:
            raise ValueError(f"split mismatch for {sample.case_id}")
        if row.get("recorded_output") != sample.row.assistant_response:
            raise ValueError(f"recorded output mismatch for {sample.case_id}")
        expected_context = (
            sample.row.decision_context.model_dump(mode="json")
            if sample.row.decision_context is not None
            else None
        )
        if row.get("decision_context") != expected_context:
            raise ValueError(f"decision context mismatch for {sample.case_id}")
        item_id = annotation_id(*sample.identity)
        if sample.row.evaluation_split == "test":
            test_items.append(
                {
                    "annotation_id": item_id,
                    "case_id": sample.case_id,
                    "evaluation_split": "test",
                    "transcript_fingerprint": sample.transcript_fingerprint,
                }
            )
        try:
            signals = analyze_jury(row.get("jury") or {})
        except Exception as error:  # noqa: BLE001 - malformed rows become explicit error records
            errors.append(
                {"annotation_id": item_id, "case_id": sample.case_id, "error": str(error)}
            )
            continue
        if signals.mechanical_errors:
            errors.append(
                {
                    "annotation_id": item_id,
                    "case_id": sample.case_id,
                    "errors": list(signals.mechanical_errors),
                }
            )
            continue
        if sample.row.evaluation_split == "test":
            continue
        item = {
            "annotation_id": item_id,
            "case_id": sample.case_id,
            "transcript_fingerprint": sample.transcript_fingerprint,
            "evaluation_split": "dev",
            "source_index": source_index,
            "verdict_space": {"type": "categorical", "labels": list(VERDICT_LABELS)},
            "priority_reasons": _priority_reasons(signals),
            "signals": _signals_dict(signals),
            "control_sample": False,
            "low_flip_sample": False,
            "evidence": {
                "decision_context": (
                    sample.row.decision_context.model_dump(mode="json")
                    if sample.row.decision_context is not None
                    else None
                ),
                "conversation": [
                    message.model_dump(mode="json") for message in sample.row.conversation
                ],
                "tool_events": [event.model_dump(mode="json") for event in sample.row.tool_events],
                "final_response": sample.row.assistant_response,
            },
            "jury": copy.deepcopy(row["jury"]),
            "_signals": signals,
        }
        (stable if signals.priority_tier == 5 else ranked).append(item)

    ranked.sort(key=_priority_key)
    stable.sort(key=lambda item: item["annotation_id"])
    rng = random.Random(seed)
    controls = rng.sample(stable, min(max(control_count, 0), len(stable)))
    controls.sort(key=lambda item: item["annotation_id"])
    for item in controls:
        item["control_sample"] = True
        item["low_flip_sample"] = True
        item["priority_reasons"] = ["stable_control"]
    selected = ranked + controls
    for rank, item in enumerate(selected, 1):
        item["rank"] = rank
        item.pop("_signals")

    identities = sorted(expected_identities)
    queue = {
        "meta": {
            "mode": "jury",
            "algorithm_version": ALGORITHM_VERSION,
            "seed": seed,
            "control_count": len(controls),
            "n_items": len(selected),
            "n_prioritized": len(ranked),
            "n_errors": len(errors),
            "verdict_space": {"type": "categorical", "labels": list(VERDICT_LABELS)},
            "input_fingerprint": _input_fingerprint(identities),
        },
        "items": selected,
    }
    return AnnotationBundle(
        queue=queue,
        test_manifest={"schema_version": ALGORITHM_VERSION, "items": test_items},
        jury_errors={"schema_version": ALGORITHM_VERSION, "items": errors},
    )


def _write_json(path: Path, value: Mapping[str, Any]) -> str:
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(payload).hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_annotation_bundle(bundle: AnnotationBundle, output_dir: str | Path) -> Path:
    """Publish all annotation artifacts behind one exclusive sibling lock."""
    destination = Path(output_dir).expanduser().resolve()
    parent = destination.parent
    if not parent.is_dir():
        raise FileNotFoundError(f"output parent does not exist: {parent}")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"output already exists: {destination}")
    lock_path = parent / f".{destination.name}.lock"
    lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    staging: Path | None = None
    try:
        os.write(lock_descriptor, f"pid={os.getpid()}\n".encode())
        os.fsync(lock_descriptor)
        staging = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.", suffix=".staging", dir=parent
            )
        )
        hashes = {
            "queue.json": _write_json(staging / "queue.json", bundle.queue),
            "test_manifest.json": _write_json(
                staging / "test_manifest.json", bundle.test_manifest
            ),
            "jury_errors.json": _write_json(staging / "jury_errors.json", bundle.jury_errors),
        }
        manifest = {
            "schema_version": ALGORITHM_VERSION,
            "status": "ready",
            "files": hashes,
        }
        _write_json(staging / "manifest.json", manifest)
        _fsync_directory(staging)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"output already exists: {destination}")
        os.rename(staging, destination)
        staging = None
        _fsync_directory(parent)
        return destination
    finally:
        os.close(lock_descriptor)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        lock_path.unlink(missing_ok=True)
