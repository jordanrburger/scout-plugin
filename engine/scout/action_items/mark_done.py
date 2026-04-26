"""Mark an action-item complete by ID prefix or by subject substring.

Returns an `Event` describing the mutation. v0.4 mutators emit Events
but nothing persists them yet; v0.5 will add the SQLite event store.
See v0.4 spec §13.2.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from scout import paths
from scout.action_items.parser import parse_file
from scout.action_items.writer import flip_checkbox
from scout.errors import ActionItemError
from scout.events import Event, now_iso
from scout.id_map import IdMap
from scout.ids import new_ulid


def _today() -> dt.date:
    """Indirection so tests can monkeypatch the date without freezing time."""
    return dt.date.today()


def mark_done(
    *,
    by_id: str | None = None,
    by_subject: str | None = None,
    date: dt.date | None = None,
    data_dir: Path | None = None,
) -> Event:
    """Mark today's (or `date`'s) action item done.

    Exactly one of `by_id` or `by_subject` must be provided. `by_id` is
    a 4-char Crockford prefix; `by_subject` is a case-insensitive
    substring match against open-status raw lines (legacy fallback for
    lines that haven't been prefixed yet).
    """
    if (by_id is None) == (by_subject is None):
        raise ActionItemError("mark_done requires exactly one of by_id or by_subject")

    resolved_data_dir = data_dir if data_dir is not None else paths.data_dir()

    if by_id is not None:
        # ID path: look up the entity ULID via IdMap up front; this gives
        # a clear "prefix not found" error before we read the daily file.
        id_map = IdMap.load(resolved_data_dir)
        entry = id_map.lookup_by_prefix(by_id)
        if entry is None:
            raise ActionItemError(
                f"prefix [#{by_id}] not found in id-map; if this is a legacy line, retry with --by-subject"
            )

    target_path = paths.action_items_daily_path(data=data_dir, date=date or _today())
    if not target_path.exists():
        raise ActionItemError(f"no action items file: {target_path}")

    items = parse_file(target_path)

    if by_id is not None:
        # `entry` was resolved above
        match = next((i for i in items if i.short_prefix == by_id), None)
        if match is None:
            raise ActionItemError(f"prefix [#{by_id}] is in id-map but not present in {target_path.name}")
        item_ulid = entry.ulid  # type: ignore[union-attr]
        via = "id"
    else:
        # Subject path: case-insensitive substring against open-status raw_lines.
        assert by_subject is not None  # enforced by the exactly-one-of check above
        matches = [i for i in items if i.status == "open" and by_subject.lower() in i.raw_line.lower()]
        if len(matches) == 0:
            raise ActionItemError(f"no open task matched subject: {by_subject!r}")
        if len(matches) > 1:
            raise ActionItemError(
                f"ambiguous subject {by_subject!r}; matched:\n" + "\n".join(f"  - {m.title}" for m in matches)
            )
        match = matches[0]
        item_ulid = ""
        if match.short_prefix:
            entry2 = IdMap.load(resolved_data_dir).lookup_by_prefix(match.short_prefix)
            if entry2 is not None:
                item_ulid = entry2.ulid
        via = "subject"

    line_number = _find_line_number(target_path, match.raw_line)
    flip_checkbox(target_path, line_number=line_number, to_done=True)

    return Event(
        id=new_ulid(),
        ts=now_iso(),
        kind="action_item.completed",
        source="cli:mark_done",
        payload={"item_id": item_ulid, "via": via, "title": match.title},
    )


def _find_line_number(path: Path, raw_line: str) -> int:
    """1-indexed line number where `raw_line` first appears as a complete line."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for n, line in enumerate(lines, start=1):
        if line == raw_line:
            return n
    raise ActionItemError(f"could not locate line in {path.name}: {raw_line!r}")
