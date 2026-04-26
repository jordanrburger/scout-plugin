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


def format_items(items: list[ActionItem]) -> str:
    """Format a list of ActionItems for plain-text CLI output.

    Each line shows `<priority> [<status>] [#XXXX] <title>` when the item has
    a short prefix; the bracketed prefix is omitted entirely (no extra space)
    when no prefix is present. This is the v0.4 surface form for stable IDs.
    """
    lines: list[str] = []
    for i in items:
        prefix_part = f"[#{i.short_prefix}] " if i.short_prefix else ""
        lines.append(f"{i.priority} [{i.status}] {prefix_part}{i.title}")
    return "\n".join(lines) + ("\n" if lines else "")
