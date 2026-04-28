"""scoutctl action-items watch — projection-consumer over today's action items.

Public CLI contract per spec §13.3: this command *streams changes to
today's action items as they happen*. The v0.4 implementation watches
the underlying markdown file via `watchdog`; v0.5 will substitute an
event-store subscriber. The CLI surface and stdout shape are stable.

Heavy imports (watchdog, rich) live inside function bodies so
`scoutctl --help` and other subcommands stay under the latency budget
(spec §4).
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

from scout.action_items.diff import diff
from scout.action_items.parser import ActionItem
from scout.action_items.render import render_changes


def process_change(
    *,
    prev_text: str,
    curr_text: str,
    now: dt.datetime,
    color: bool,
) -> list[str]:
    """Pure core of the watcher: text → text → list of formatted lines.

    Used directly by tests; called from `_handle_modified_event` in the
    real watcher loop.
    """
    prev_items = _parse_text(prev_text)
    curr_items = _parse_text(curr_text)
    events = diff(prev=prev_items, curr=curr_items)
    return render_changes(events, now=now, color=color)


def _parse_text(text: str) -> list[ActionItem]:
    """Run the parser over an in-memory string by writing to a tempfile."""
    # parser.parse_file expects a Path. The watcher always has a real
    # path; this helper exists so process_change() can be tested with
    # arbitrary strings without hitting the real filesystem.
    import tempfile

    from scout.action_items.parser import parse_file

    if not text:
        return []
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
        tmp = Path(f.name)
    try:
        return parse_file(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def run_watch_loop(target: Path, *, color: bool) -> None:
    """Block until SIGINT, emitting one line per detected change.

    Heavy imports inside the body — `scoutctl action-items watch` is
    interactive (a long-running process), so the cost is paid once.
    """
    from watchdog.events import FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    if not target.exists():
        raise FileNotFoundError(target)

    state = {"prev_text": target.read_text(encoding="utf-8")}

    def on_modified(event: FileModifiedEvent) -> None:
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode()
        if Path(src_path) != target:
            return
        try:
            curr_text = target.read_text(encoding="utf-8")
        except FileNotFoundError:
            return  # mid-rename; the next event will deliver the new contents
        if curr_text == state["prev_text"]:
            return
        lines = process_change(
            prev_text=state["prev_text"],
            curr_text=curr_text,
            now=dt.datetime.now(),
            color=color,
        )
        for line in lines:
            print(line, flush=True)
        state["prev_text"] = curr_text

    class _Handler(FileSystemEventHandler):
        # watchdog stubs widen `event` to FileSystemEvent — narrowing here
        # is safe because watchdog only dispatches FileModifiedEvent to
        # on_modified, but mypy correctly flags the Liskov narrowing.
        def on_modified(self, event: FileModifiedEvent) -> None:  # type: ignore[override]
            on_modified(event)

    observer = Observer()
    observer.schedule(_Handler(), str(target.parent), recursive=False)
    observer.start()
    print(
        f"Watching {target.name} for changes — Ctrl-C to stop.",
        file=sys.stderr,
    )
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
