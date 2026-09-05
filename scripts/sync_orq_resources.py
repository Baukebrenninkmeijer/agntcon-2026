#!/usr/bin/env python3
"""Plan or apply repository-owned Orq resources."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from analytics_chatbot.orq_resources import load_resource_bundle
from analytics_chatbot.orq_sync import OrqReconciler, OrqSdkGateway, SyncError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resources",
        type=Path,
        default=REPOSITORY_ROOT / "orq" / "resources",
        help="repository resource directory",
    )
    parser.add_argument("--apply", action="store_true", help="apply the reviewed semantic plan")
    parser.add_argument(
        "--kinds",
        nargs="+",
        choices=("tool", "agent", "evaluator"),
        default=("tool", "agent", "evaluator"),
        help="resource kinds to include; defaults to the complete bundle",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        default=None,
        help="resource keys to include; defaults to every key of the selected kinds",
    )
    return parser


def _select(actions: list, args: argparse.Namespace) -> list:
    return [
        action
        for action in actions
        if action.kind in args.kinds and (args.keys is None or action.key in args.keys)
    ]


def _summary(plan: object) -> dict[str, object]:
    return {
        "project": plan.project_key,
        "model": plan.model_id,
        "mode": "apply" if getattr(plan, "apply", False) else "dry-run",
        "resources": [
            {"operation": action.operation, "kind": action.kind, "name": action.key}
            for action in plan.actions
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    load_dotenv(REPOSITORY_ROOT / ".env", override=True)
    api_key = os.getenv("ORQ_API_KEY", "")
    if not api_key:
        raise SyncError("ORQ_API_KEY is required; add the pydata2026 key to .env")

    bundle = load_resource_bundle(args.resources)
    gateway = OrqSdkGateway(api_key)
    reconciler = OrqReconciler(bundle)
    before = reconciler.plan(gateway.snapshot(bundle))
    before = before.model_copy(update={"actions": _select(before.actions, args)})
    result = _summary(before)
    result["mode"] = "apply" if args.apply else "dry-run"
    print(json.dumps(result, indent=2))
    if not args.apply:
        return 0

    bundle.assert_llm_evaluators_syncable(
        keys=[action.key for action in before.actions if action.kind == "evaluator"]
    )
    gateway.apply(before.actions)
    after = reconciler.plan(gateway.snapshot(bundle))
    after = after.model_copy(update={"actions": _select(after.actions, args)})
    if after.changed:
        pending = [
            f"{action.kind}:{action.key}:{action.operation}"
            for action in after.actions
            if action.operation != "noop"
        ]
        raise SyncError(f"Orq sync verification failed; pending changes: {pending}")
    print(
        json.dumps(
            {
                "project": after.project_key,
                "verified": True,
                "resources": [
                    {"kind": action.kind, "name": action.key, "status": "present"}
                    for action in after.actions
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
