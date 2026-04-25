"""Enumerate action items from a daily markdown file with filters."""

from __future__ import annotations

from pathlib import Path

from scout.action_items.parser import ActionItem, parse_file

PRIORITY_ALIASES = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
    "🔴": "🔴",
    "🟡": "🟡",
    "🟢": "🟢",
}


def list_items(
    path: Path,
    *,
    include_done: bool = False,
    priority: str | None = None,
    section: str | None = None,
) -> list[ActionItem]:
    """Return ActionItems matching the given filters.

    By default returns only open items (status == 'open').
    """
    items = parse_file(path)
    if not include_done:
        items = [i for i in items if i.status == "open"]
    if priority is not None:
        glyph = PRIORITY_ALIASES.get(priority)
        if glyph is None:
            raise ValueError(f"unknown priority {priority!r}; expected one of {sorted(PRIORITY_ALIASES)}")
        items = [i for i in items if i.priority == glyph]
    if section is not None:
        items = [i for i in items if i.section == section]
    return items
