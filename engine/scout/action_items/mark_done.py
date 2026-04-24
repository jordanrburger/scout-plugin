"""Toggle a task's checkbox to done in a daily action-items markdown.

Match is case-insensitive substring on the task title; must be unambiguous.
Undo flips `[x]` back to `[ ]`. Atomic rewrite via scout.action_items.writer.
"""

from __future__ import annotations

import re
from pathlib import Path

from scout import paths
from scout.action_items.writer import flip_checkbox
from scout.errors import ActionItemError

TASK_RE = re.compile(r"^(?P<indent>\s*)- \[(?P<mark>[ xX])\] (?P<rest>.+?)\s*$")


def _matching_lines(lines: list[str], subject: str, *, want_mark: str) -> list[tuple[int, str]]:
    needle = subject.casefold()
    out: list[tuple[int, str]] = []
    for i, line in enumerate(lines, start=1):
        m = TASK_RE.match(line)
        if not m:
            continue
        if m.group("mark") not in want_mark:
            continue
        if needle in m.group("rest").casefold():
            out.append((i, line))
    return out


def mark_done(path: Path | None, *, subject: str, undo: bool = False) -> Path:
    """Mark the unique matching task done (or open if undo=True).

    Args:
        path: Daily markdown file. None resolves to today's file in SCOUT_DATA_DIR.
        subject: Case-insensitive substring of the task title.
        undo: If True, flip `[x]` back to `[ ]`.

    Returns: the file actually modified (useful when `path is None`).

    Raises ActionItemError on no-match or ambiguous match.
    """
    target = path or paths.action_items_daily_path()
    if not target.exists():
        raise ActionItemError(f"no daily file at {target}")

    lines = target.read_text(encoding="utf-8").splitlines()
    want_mark = "x X" if undo else " "
    matches = _matching_lines(lines, subject, want_mark=want_mark)

    if not matches:
        raise ActionItemError(f"mark_done: no match for subject '{subject}' in {target.name}")
    if len(matches) > 1:
        listing = "\n".join(f"  {ln}: {ln_text}" for ln, ln_text in matches)
        raise ActionItemError(f"mark_done: ambiguous match for '{subject}' ({len(matches)} candidates):\n{listing}")

    line_number, _ = matches[0]
    flip_checkbox(target, line_number=line_number, to_done=not undo)
    return target
