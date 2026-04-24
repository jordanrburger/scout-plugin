"""Insert a comment under a matched task in daily action-items markdown.

Comments are written as indented blockquote lines directly under the matched
task bullet:

    - [ ] Task subject — body
      > jordan (2026-04-18 10:20 AM ET): text here
      > scout  (2026-04-18 11:00 AM ET): reply

This mirrors the schema parsed by the action-items parser.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from scout import paths
from scout.action_items.writer import atomic_write_lines
from scout.errors import ActionItemError

EASTERN = ZoneInfo("America/New_York")
TASK_RE = re.compile(r"^(?P<indent>\s*)- \[(?P<mark>[ xX])\]\s+(?P<rest>.+?)\s*$")


def _timestamp() -> str:
    """Return current timestamp in Eastern time (YYYY-MM-DD HH:MM AM/PM ET format)."""
    return dt.datetime.now(EASTERN).strftime("%Y-%m-%d %-I:%M %p ET")


def _strip_markdown_tokens(text: str) -> str:
    """Collapse a task subject to plain text for matching."""
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def _first_separator_outside_tokens(text: str, separators: tuple[str, ...]) -> int:
    """Return the earliest offset where any of ``separators`` starts outside
    markdown tokens (bold, strike, code, wiki links, links). -1 if none found.
    """
    in_bold = in_strike = in_code = False
    bracket_depth = 0
    i = 0
    n = len(text)
    while i < n:
        two = text[i : i + 2]
        ch = text[i]
        if ch == "`" and not in_bold and not in_strike:
            in_code = not in_code
            i += 1
            continue
        if in_code:
            i += 1
            continue
        if two == "**":
            in_bold = not in_bold
            i += 2
            continue
        if two == "~~":
            in_strike = not in_strike
            i += 2
            continue
        if two == "[[":
            bracket_depth += 1
            i += 2
            continue
        if two == "]]" and bracket_depth > 0:
            bracket_depth -= 1
            i += 2
            continue
        if ch == "[" and bracket_depth == 0:
            bracket_depth = 1
            i += 1
            continue
        if ch == "]" and bracket_depth > 0 and two != "]]":
            bracket_depth = 0
            i += 1
            continue
        if not in_bold and not in_strike and bracket_depth == 0:
            for sep in separators:
                if text[i : i + len(sep)] == sep:
                    return i
        i += 1
    return -1


def _task_subject(rest: str) -> str:
    """Extract the subject (title) part of a task line."""
    idx = _first_separator_outside_tokens(rest, (" — ", " – ", " - "))
    if idx != -1:
        return rest[:idx]
    idx = _first_separator_outside_tokens(rest, (": ",))
    if idx != -1:
        return rest[:idx]
    return rest


def _matching_lines(lines: list[str], subject: str) -> list[tuple[int, str]]:
    """Find all task lines whose subject contains the substring (case-insensitive).

    Returns list of (1-indexed line number, line text) tuples.
    """
    needle = subject.casefold()
    out: list[tuple[int, str]] = []
    for i, line in enumerate(lines, start=1):
        m = TASK_RE.match(line)
        if not m:
            continue
        subject_plain = _strip_markdown_tokens(_task_subject(m.group("rest"))).lower()
        if needle in subject_plain:
            out.append((i, line))
    return out


def _insert_comment_line(
    lines: list[str],
    task_idx: int,
    author: str,
    text: str,
    timestamp: str,
) -> list[str]:
    """Insert a comment line after the task and its existing comment block.

    Args:
        lines: List of markdown lines.
        task_idx: 0-indexed line number of the task.
        author: Author name for the comment.
        text: Comment body.
        timestamp: Timestamp string.

    Returns: modified lines list.
    """
    task_indent = TASK_RE.match(lines[task_idx]).group("indent")  # type: ignore[union-attr]
    comment_indent = task_indent + "  "
    insert_at = task_idx + 1

    # Skip continuation lines that belong to this task: comment lines
    # (blockquotes starting with >) or indented non-bullet prose.
    # Stop at blank line, new bullet at same/shallower indent, or header.
    while insert_at < len(lines):
        cur = lines[insert_at]
        if not cur.strip():
            break
        if cur.lstrip().startswith("#"):
            break
        m = TASK_RE.match(cur)
        if m and len(m.group("indent")) <= len(task_indent):
            break
        if re.match(r"^\s*-\s+", cur) and len(cur) - len(cur.lstrip()) <= len(task_indent):
            break
        insert_at += 1

    new_line = f"{comment_indent}> {author} ({timestamp}): {text}"
    return lines[:insert_at] + [new_line] + lines[insert_at:]


def add_comment(
    path: Path | None,
    *,
    subject: str,
    text: str,
    author: str = "jordan",
    timestamp: bool = True,
) -> Path:
    """Insert a comment beneath the unique matching task.

    Args:
        path: Daily markdown file. None resolves to today's file in SCOUT_DATA_DIR.
        subject: Case-insensitive substring of the task title.
        text: Comment body.
        author: Author name for the comment (default: "jordan").
        timestamp: If True, prepend a timestamp decoration (default: True).

    Returns: the file modified.

    Raises ActionItemError on no-match or ambiguous match.
    """
    target = path or paths.action_items_daily_path()
    if not target.exists():
        raise ActionItemError(f"add_comment: no daily file at {target}")

    lines = target.read_text(encoding="utf-8").splitlines()
    matches = _matching_lines(lines, subject)

    if not matches:
        raise ActionItemError(f"add_comment: no match for subject '{subject}' in {target.name}")
    if len(matches) > 1:
        listing = "\n".join(f"  {ln}: {ln_text}" for ln, ln_text in matches)
        raise ActionItemError(f"add_comment: ambiguous match for '{subject}' ({len(matches)} candidates):\n{listing}")

    line_number, _ = matches[0]
    task_idx = line_number - 1
    ts = _timestamp() if timestamp else ""
    new_lines = _insert_comment_line(lines, task_idx, author, text, ts)
    atomic_write_lines(target, new_lines)
    return target
