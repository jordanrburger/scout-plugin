"""Snooze a task to a future-dated daily action-items file.

Two complementary writes happen:

1.  The task in the source file is **removed entirely** (along with any
    immediately-following indented continuation lines).  No marker is left
    on the source side — git history and the destination carry-in annotation
    provide full traceability.
2.  The task is appended (as an open ``[ ]`` item) to a ``## 🛌 Snoozed``
    section in the target day's file.  The file and section are created on
    demand.  A ``_(carried in from YYYY-MM-DD)_`` annotation is appended so
    the origin date is visible.

Ported from ~/Scout/action-items/snooze.py (362 lines).
argparse / __main__ block removed; public surface is the ``snooze()`` function.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from scout import paths
from scout.action_items.writer import atomic_write_lines
from scout.errors import ActionItemError

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

TASK_RE = re.compile(r"^(?P<indent>\s*)- \[(?P<mark>[ xX])\] (?P<rest>.+?)\s*$")
SNOOZE_SUFFIX_RE = re.compile(r"\s*(?:—|–|-)\s*🛌 Snoozed until \d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Matching
#
# NOTE: the source snooze.py matches on ALL tasks regardless of checkbox mark
# (open [ ], done [x], or [X]).  This intentionally differs from
# mark_done._matching_lines, which filters by want_mark.  A local helper is
# kept here rather than importing from mark_done to avoid coupling to the
# want_mark contract.  The subject comparison uses plain .lower() (not
# .casefold()) to match the source's original behaviour.
# ---------------------------------------------------------------------------


def _strip_markdown_tokens(text: str) -> str:
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def _first_separator_outside_tokens(text: str, separators: tuple[str, ...]) -> int:
    """Return the earliest offset where any separator starts outside Markdown
    inline tokens (bold, strike, code, wiki-links, hyperlinks).  -1 if none."""
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
    idx = _first_separator_outside_tokens(rest, (" — ", " – ", " - "))
    if idx != -1:
        return rest[:idx]
    idx = _first_separator_outside_tokens(rest, (": ",))
    if idx != -1:
        return rest[:idx]
    return rest


def _find_task_lines(lines: list[str], needle: str) -> list[int]:
    """Return 0-based indices of lines whose task subject contains *needle*.

    Matches all tasks regardless of checkbox state (open, done, or X-done).
    Case-insensitive substring match on the plain-text subject (markdown tokens
    stripped).
    """
    needle_norm = needle.lower().strip()
    hits: list[int] = []
    for i, line in enumerate(lines):
        m = TASK_RE.match(line)
        if not m:
            continue
        subject_plain = _strip_markdown_tokens(_task_subject(m.group("rest"))).lower()
        if needle_norm in subject_plain:
            hits.append(i)
    return hits


# ---------------------------------------------------------------------------
# Source-file mutation
# ---------------------------------------------------------------------------


def _remove_task_block(lines: list[str], task_idx: int) -> list[str]:
    """Return lines with the task at task_idx and its indented continuation
    lines removed.

    The source removes the task entirely rather than leaving a snooze-marker
    stub.  See remove_task_block() in ~/Scout/action-items/snooze.py for the
    original rationale (git history + destination carry-in provide traceability).
    """
    m = TASK_RE.match(lines[task_idx])
    task_indent_len = len(m.group("indent")) if m else 0
    end = task_idx + 1
    while end < len(lines):
        line = lines[end]
        if not line.strip():
            break
        line_indent_len = len(line) - len(line.lstrip())
        if line_indent_len > task_indent_len:
            end += 1
        else:
            break
    return lines[:task_idx] + lines[end:]


# ---------------------------------------------------------------------------
# Destination-file mutation
# ---------------------------------------------------------------------------


def _append_to_target(target_path: Path, task_line: str, source_date: str) -> None:
    """Append the task to a ## 🛌 Snoozed section in target_path.

    Creates the file (with a minimal header + section) if it does not exist.
    Flips the checkbox back to open [ ] and drops any snooze suffix; the
    carry-in annotation _(carried in from <source_date>)_ replaces it.
    Deduplicates: if the same subject is already present in the section, skips.
    """
    m = TASK_RE.match(task_line)
    rest = m.group("rest") if m else task_line.strip()
    rest = SNOOZE_SUFFIX_RE.sub("", rest)
    indent = m.group("indent") if m else ""
    subject_key = _strip_markdown_tokens(_task_subject(rest)).strip().lower()
    carry_line = f"{indent}- [ ] {rest} _(carried in from {source_date})_"

    if target_path.exists():
        text = target_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        section_idx = next(
            (i for i, ln in enumerate(lines) if ln.strip().lower().startswith("## 🛌 snoozed")),
            None,
        )
        if section_idx is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append("## 🛌 Snoozed")
            lines.append("")
            lines.append(carry_line)
        else:
            section_end = len(lines)
            for j in range(section_idx + 1, len(lines)):
                if lines[j].startswith("## "):
                    section_end = j
                    break
            # Dedupe: skip if same subject already present.
            for j in range(section_idx + 1, section_end):
                mt = TASK_RE.match(lines[j])
                if not mt:
                    continue
                existing_subject = _strip_markdown_tokens(_task_subject(mt.group("rest"))).strip().lower()
                if existing_subject == subject_key:
                    return
            insert_at = section_end
            while insert_at > section_idx + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            lines.insert(insert_at, carry_line)
        atomic_write_lines(target_path, lines)
        return

    # Fresh target file: minimal header + snoozed section.
    date_label = target_path.stem.replace("action-items-", "")
    header_lines = [
        f"# Action Items — {date_label}",
        "",
        "## 🛌 Snoozed",
        "",
        carry_line,
    ]
    atomic_write_lines(target_path, header_lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def snooze(src: Path | None, *, subject: str, until: dt.date) -> Path:
    """Snooze the uniquely matching task to a future daily file.

    Args:
        src:     Source daily markdown file.  None resolves to today's file.
        subject: Case-insensitive substring of the task subject to snooze.
        until:   Target date (must be strictly after today).

    Returns:
        Path to the destination daily file the task was moved into.

    Raises:
        ActionItemError: no match, ambiguous match, or until is in the past.
    """
    today = dt.date.today()
    if until <= today:
        raise ActionItemError(
            f"until date {until.isoformat()} is in the past or today "
            f"(today is {today.isoformat()}); must be a future date"
        )

    source_path = src if src is not None else paths.action_items_daily_path()
    if not source_path.exists():
        raise ActionItemError(f"snooze: source file not found: {source_path}")

    # Extract the date label from the filename (e.g. "action-items-2026-04-15.md" → "2026-04-15").
    source_date = source_path.stem.replace("action-items-", "")

    lines = source_path.read_text(encoding="utf-8").splitlines()
    hits = _find_task_lines(lines, subject)

    if not hits:
        raise ActionItemError(f"snooze: no match for subject {subject!r} in {source_path.name}")
    if len(hits) > 1:
        listing = "\n".join(f"  line {i + 1}: {lines[i].strip()}" for i in hits)
        raise ActionItemError(f"snooze: ambiguous match for {subject!r} ({len(hits)} candidates):\n{listing}")

    task_idx = hits[0]
    original_line = lines[task_idx]

    # Remove the task (and any continuation lines) from the source file.
    new_lines = _remove_task_block(lines, task_idx)
    atomic_write_lines(source_path, new_lines)

    # Write the carry-in entry to the target daily file.
    target_path = source_path.parent / f"action-items-{until.isoformat()}.md"
    _append_to_target(target_path, original_line, source_date)

    return target_path
