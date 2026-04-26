"""scoutctl action-items sub-app.

Top-level imports are intentionally minimal — Typer + stdlib + scout.errors.
Each subcommand imports its scout.action_items.* module inside the function
body so scoutctl startup latency is unaffected (Plan 1 perf rule, enforced
by tests/perf/test_no_heavy_imports.py).
"""

from __future__ import annotations

import datetime as _dt
import json as _json
import sys
from pathlib import Path

import typer

from scout.errors import ActionItemError, ScoutError

app = typer.Typer(help="Action-items operations.", no_args_is_help=True)


@app.command("mark-done")
def cli_mark_done(
    subject: str | None = typer.Option(None, "--subject", help="Substring of task title (legacy fallback)."),
    by_id: str | None = typer.Option(None, "--by-id", help="4-char Crockford prefix from `[#XXXX]`."),
    path: Path | None = typer.Argument(
        None,
        help="Daily markdown file (default: today). When given, its grandparent is the data dir.",
    ),
) -> None:
    from scout.action_items.mark_done import mark_done

    if (subject is None) == (by_id is None):
        raise ActionItemError("mark-done requires exactly one of --subject or --by-id")

    # Backward compat: if a path argument is given, its grandparent serves as
    # the data dir (path lives at <data_dir>/action-items/<file>.md). The
    # filename's date is used to pin which daily file to operate on.
    data_dir: Path | None = None
    date: _dt.date | None = None
    if path is not None:
        data_dir = path.parent.parent
        # Filename: action-items-YYYY-MM-DD.md
        stem = path.stem  # e.g. action-items-2026-04-15
        try:
            date = _dt.date.fromisoformat(stem.removeprefix("action-items-"))
        except ValueError as e:
            raise ActionItemError(f"unrecognized daily filename: {path.name}") from e

    mark_done(by_id=by_id, by_subject=subject, date=date, data_dir=data_dir)


@app.command("snooze")
def cli_snooze(
    subject: str = typer.Option(..., "--subject"),
    until: str = typer.Option(..., "--until", help="YYYY-MM-DD"),
    path: Path | None = typer.Argument(None),
) -> None:
    from scout.action_items.snooze import snooze

    try:
        target_date = _dt.date.fromisoformat(until)
    except ValueError as e:
        raise ActionItemError(f"--until: invalid date {until!r}") from e
    snooze(path, subject=subject, until=target_date)


@app.command("add-comment")
def cli_add_comment(
    subject: str = typer.Option(..., "--subject"),
    text: str = typer.Option(..., "--text"),
    path: Path | None = typer.Argument(None),
) -> None:
    from scout.action_items.add_comment import add_comment

    add_comment(path, subject=subject, text=text)


@app.command("render")
def cli_render(
    path: Path | None = typer.Argument(None),
) -> None:
    from scout import paths
    from scout.action_items.render import render

    target = path or paths.action_items_daily_path()
    sys.stdout.write(render(target))


@app.command("list")
def cli_list(
    path: Path | None = typer.Argument(None),
    include_done: bool = typer.Option(False, "--include-done"),
    priority: str | None = typer.Option(None, "--priority"),
    section: str | None = typer.Option(None, "--section"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    from scout import paths
    from scout.action_items.list import list_items

    target = path or paths.action_items_daily_path()
    items = list_items(target, include_done=include_done, priority=priority, section=section)
    if json_out:
        payload = [
            {
                "title": i.title,
                "priority": i.priority,
                "status": i.status,
                "section": i.section,
            }
            for i in items
        ]
        sys.stdout.write(_json.dumps(payload) + "\n")
    else:
        for i in items:
            sys.stdout.write(f"{i.priority} [{i.status}] {i.title}\n")


@app.command("watch")
def cli_watch() -> None:
    raise ScoutError("scoutctl action-items watch is implemented in Plan 3")
