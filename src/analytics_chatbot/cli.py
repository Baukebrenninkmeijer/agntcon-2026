"""Terminal interface for the analytics chatbot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from analytics_chatbot.agent import AnalyticsChatbot
from analytics_chatbot.config import RunKind, Settings, TraceContext
from analytics_chatbot.data import DEFAULT_ORDER_COUNT, DEFAULT_SEED, seed_database

app = typer.Typer(no_args_is_help=True, help="Observable local business analytics agent.")
console = Console()


def _build_chatbot() -> AnalyticsChatbot:
    return AnalyticsChatbot(Settings())


def _events_path(runs_path: Path, run_id: str) -> Path:
    run_directory = (runs_path / run_id).resolve()
    if runs_path.resolve() not in run_directory.parents:
        raise typer.BadParameter("run ID must identify a run beneath the configured runs path")
    final = run_directory / "events.jsonl"
    partial = run_directory / "events.partial.jsonl"
    if final.exists():
        return final
    if partial.exists():
        return partial
    raise typer.BadParameter(f"no run artifact found for {run_id!r}")


def _read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@app.command("seed-data")
def seed_data(
    database: Annotated[Path | None, typer.Option(help="DuckDB destination.")] = None,
    count: Annotated[int, typer.Option(min=2, help="Number of orders.")] = DEFAULT_ORDER_COUNT,
    seed: Annotated[int, typer.Option(help="Deterministic random seed.")] = DEFAULT_SEED,
) -> None:
    """Generate synthetic orders with Polars and materialize DuckDB."""

    destination = database or Settings().database_path
    manifest = seed_database(destination, count=count, seed=seed)
    console.print(
        f"Seeded [bold]{manifest.row_count:,}[/bold] orders across "
        f"{manifest.month_count} months into {destination}"
    )


@app.command()
def ask(
    message: Annotated[str, typer.Argument(help="Business question for the agent.")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit machine-readable JSON.")
    ] = False,
    show_trajectory: Annotated[
        bool, typer.Option("--show-trajectory", help="Print the saved run events.")
    ] = False,
    identity: Annotated[str | None, typer.Option(help="orq trace identity ID.")] = None,
    split: Annotated[str, typer.Option(help="Evaluation split metadata.")] = "ad_hoc",
    case_id: Annotated[str, typer.Option(help="Evaluation case metadata.")] = "",
    run_kind: Annotated[RunKind, typer.Option(help="Trace run kind.")] = "interactive",
) -> None:
    """Ask one analytics question."""

    chatbot = _build_chatbot()
    context = TraceContext(
        run_kind=run_kind,
        interface="cli",
        evaluation_split=split,
        case_id=case_id,
        identity_id=identity,
        dataset_version=Settings().dataset_version,
        agent_version=Settings().agent_version,
    )
    response = chatbot.ask(message, context=context)
    if json_output:
        typer.echo(response.model_dump_json(indent=2))
    else:
        console.print(response.answer)
        console.print(f"[dim]run {response.run_id} · thread {response.thread_id}[/dim]")
    if show_trajectory and response.artifact_path:
        typer.echo(Path(response.artifact_path).read_text(encoding="utf-8"), nl=False)


@app.command()
def chat(
    identity: Annotated[str | None, typer.Option(help="orq trace identity ID.")] = None,
) -> None:
    """Keep one gateway conversation open until /quit."""

    chatbot = _build_chatbot()
    conversation = chatbot.new_conversation()
    context = TraceContext(interface="cli", identity_id=identity)
    console.print("Analytics chatbot ready. Enter /quit to stop.")
    while True:
        try:
            message = typer.prompt("you")
        except (EOFError, KeyboardInterrupt):
            break
        if message.strip().lower() in {"/quit", "/exit"}:
            break
        response = chatbot.ask(message, conversation=conversation, context=context)
        console.print(response.answer)


@app.command("show-run")
def show_run(
    run_id: Annotated[str, typer.Argument(help="Run identifier.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Render the finalized or partial trajectory for a local run."""

    path = _events_path(Settings().runs_path, run_id)
    events = _read_events(path)
    if json_output:
        typer.echo(json.dumps(events, indent=2, default=str))
        return
    table = Table(title=f"Run {run_id}")
    table.add_column("#", justify="right")
    table.add_column("event")
    table.add_column("details")
    for index, event in enumerate(events, start=1):
        details = {key: value for key, value in event.items() if key not in {"type", "recorded_at"}}
        table.add_row(
            str(index), str(event.get("type", "unknown")), json.dumps(details, default=str)
        )
    console.print(table)


if __name__ == "__main__":
    app()
