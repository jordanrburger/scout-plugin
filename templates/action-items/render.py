#!/usr/bin/env python3
"""
Render a Scout action-items markdown file into the HTML dashboard.

Usage:
    python render.py action-items-2026-04-17.md
    # → writes action-items-2026-04-17.html next to it

The markdown file is the source of truth. This script is a pure view renderer —
if something is wrong in the dashboard, fix the markdown and re-run.
"""

from __future__ import annotations

import html
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


@dataclass
class Task:
    done: bool
    subject: str
    body: str
    raw: str


@dataclass
class BulletLine:
    """A non-task bullet (used in Today's Focus, Scout Digest, etc.)."""

    text: str


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]


@dataclass
class Section:
    emoji: str
    title: str
    subtitle: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)
    bullets: list[BulletLine] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    subheads: list[str] = field(default_factory=list)  # ### subheads


SECTION_RE = re.compile(r"^## (?P<emoji>\S+?)\s+(?P<title>.+?)(?:\s*\(.*?\))?\s*$")
SIMPLE_SECTION_RE = re.compile(r"^## (?P<title>.+?)\s*$")
TASK_RE = re.compile(r"^\s*- \[(?P<mark>[ xX])\]\s+(?P<rest>.+?)\s*$")
BULLET_RE = re.compile(r"^\s*-\s+(?P<rest>.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")


def parse(md_path: Path) -> tuple[str, list[str], list[Section]]:
    """Return (title, preamble_paragraphs, sections)."""

    text = md_path.read_text()
    lines = text.splitlines()

    title = ""
    preamble: list[str] = []
    sections: list[Section] = []
    current: Optional[Section] = None
    in_table = False
    table: Optional[Table] = None

    # Find title
    for i, line in enumerate(lines):
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            start = i + 1
            break
    else:
        start = 0

    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Horizontal rules are separators
        if stripped in ("---", "***"):
            in_table = False
            table = None
            i += 1
            continue

        # Section header. Try "## <emoji> <title>" first; fall back to plain "## <title>".
        if line.startswith("## "):
            m = SECTION_RE.match(line)
            if m:
                emoji = m.group("emoji")
                rest = m.group("title")
                if not re.match(
                    r"^[\u2600-\u27BF\U0001F300-\U0001FAFF✅🔴🟡🟢💡📋📅]", emoji
                ):
                    # First token wasn't an emoji — treat whole thing as plain title.
                    emoji = ""
                    rest = line[3:].strip()
            else:
                emoji = ""
                rest = line[3:].strip()
            current = Section(emoji=emoji, title=rest)
            sections.append(current)
            in_table = False
            i += 1
            continue

        # Sub-heading
        if line.startswith("### ") and current is not None:
            current.subheads.append(line[4:].strip())
            in_table = False
            i += 1
            continue

        # Preamble (before first section)
        if current is None:
            if stripped:
                preamble.append(stripped)
            i += 1
            continue

        # Table detection
        if TABLE_ROW_RE.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # Separator row: ignore
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                i += 1
                continue
            if not in_table:
                in_table = True
                table = Table(headers=cells, rows=[])
                current.tables.append(table)
            else:
                assert table is not None
                table.rows.append(cells)
            i += 1
            continue
        else:
            in_table = False
            table = None

        # Task line
        t = TASK_RE.match(line)
        if t and current is not None:
            done = t.group("mark").lower() == "x"
            rest = t.group("rest")
            # Split subject/body: first " — " or " – " after optional bold/strike
            subject, body = _split_subject(rest)
            current.tasks.append(Task(done=done, subject=subject, body=body, raw=rest))
            i += 1
            continue

        # Regular bullet line (section-level)
        b = BULLET_RE.match(line)
        if b and current is not None:
            current.bullets.append(BulletLine(text=b.group("rest")))
            i += 1
            continue

        # Paragraph line inside a section
        if stripped and current is not None:
            current.bullets.append(BulletLine(text=stripped))

        i += 1

    return title, preamble, sections


def _split_subject(rest: str) -> tuple[str, str]:
    """Split a task line into (subject, body-remainder).

    The dash separator must be *outside* of bold (`**...**`), strike (`~~...~~`),
    inline code (`` ` ``), wikilinks (`[[...]]`), and markdown links (`[...](...)`).
    Otherwise splits land in the middle of a markdown token and break rendering.
    """
    dashes = (" — ", " – ", " - ")

    def find_outside_tokens(text: str) -> int:
        in_bold = False
        in_strike = False
        in_code = False
        bracket_depth = 0  # inside [[ or [
        paren_depth = 0    # inside (...) of a link
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
            if ch == "]" and bracket_depth > 0 and text[i : i + 2] != "]]":
                bracket_depth = 0
                if i + 1 < n and text[i + 1] == "(":
                    paren_depth = 1
                    i += 2
                    continue
                i += 1
                continue
            if ch == ")" and paren_depth > 0:
                paren_depth -= 1
                i += 1
                continue
            # Clean spot — is this a separator?
            if (
                not in_bold
                and not in_strike
                and bracket_depth == 0
                and paren_depth == 0
            ):
                for d in dashes:
                    if text[i : i + len(d)] == d:
                        return i
            i += 1
        return -1

    idx = find_outside_tokens(rest)
    if idx != -1:
        # Determine which dash matched
        for d in dashes:
            if rest[idx : idx + len(d)] == d:
                return rest[:idx].rstrip(), rest[idx + len(d) :].lstrip()

    # Fallback: a colon split outside tokens
    idx = -1
    in_bold = False
    in_strike = False
    in_code = False
    i = 0
    while i < len(rest):
        two = rest[i : i + 2]
        if rest[i] == "`" and not in_bold and not in_strike:
            in_code = not in_code
        elif not in_code and two == "**":
            in_bold = not in_bold
            i += 2
            continue
        elif not in_code and two == "~~":
            in_strike = not in_strike
            i += 2
            continue
        elif (
            not in_code
            and not in_bold
            and not in_strike
            and rest[i : i + 2] == ": "
        ):
            idx = i
            break
        i += 1
    if idx != -1:
        return rest[:idx].rstrip(), rest[idx + 2 :].lstrip()
    return rest, ""


# ---------------------------------------------------------------------------
# Inline markdown → HTML
# ---------------------------------------------------------------------------


WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
STRIKE_RE = re.compile(r"~~(.+?)~~")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<![\*_])\*(?!\*)([^*]+?)\*(?!\*)")
CODE_RE = re.compile(r"`([^`]+)`")


def inline(text: str) -> str:
    """Render inline markdown to HTML."""
    # Escape first, then re-substitute for markdown tokens. Tokens are chosen
    # so we can safely find them after escaping.
    s = html.escape(text, quote=False)
    # Wikilinks become pills
    s = WIKILINK_RE.sub(lambda m: _wiki_pill(m.group(1), m.group(2)), s)
    # Regular links
    s = LINK_RE.sub(
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        s,
    )
    s = CODE_RE.sub(r"<code>\1</code>", s)
    s = STRIKE_RE.sub(r"<s>\1</s>", s)
    s = BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = ITALIC_RE.sub(r"<em>\1</em>", s)
    return s


def _wiki_pill(target: str, label: Optional[str]) -> str:
    display = label or target.split("/")[-1]
    return f'<span class="wiki">{html.escape(display)}</span>'


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


SECTION_STYLES = {
    "🔴": ("urgent", "Urgent / Time-sensitive"),
    "🟡": ("todo", "To do"),
    "🟢": ("watching", "Watching"),
    "💡": ("focus", "Today's focus"),
    "📅": ("meetings", "Today's meetings"),
    "✅": ("done", "Recently completed"),
    "📋": ("digest", "Scout digest"),
}


def section_kind(section: Section) -> str:
    if section.emoji in SECTION_STYLES:
        return SECTION_STYLES[section.emoji][0]
    t = section.title.lower()
    if "personal" in t:
        return "personal"
    return "neutral"


def render(title: str, preamble: list[str], sections: list[Section]) -> str:
    # Compute summary stats from task counts
    def count(kind: str) -> int:
        return sum(
            sum(1 for t in s.tasks if not t.done)
            for s in sections
            if section_kind(s) == kind
        )

    n_urgent = count("urgent")
    n_todo = count("todo")
    n_watching = count("watching")
    n_personal = count("personal")
    n_done = sum(
        sum(1 for t in s.tasks if t.done) for s in sections if section_kind(s) == "done"
    )

    stats = [
        ("urgent", n_urgent, "🔥 Urgent"),
        ("warn", n_todo, "📋 To do"),
        ("info", n_watching, "👀 Watching"),
        ("muted", n_personal, "🏡 Personal"),
        ("ok", n_done, "✅ Done"),
    ]

    body_sections: list[str] = []

    for s in sections:
        kind = section_kind(s)
        if kind == "focus":
            body_sections.append(_render_focus(s))
        elif kind in ("urgent", "todo", "watching", "personal"):
            body_sections.append(_render_cards(s, kind))
        elif kind == "meetings":
            body_sections.append(_render_meetings(s))
        elif kind == "done":
            body_sections.append(_render_completed(s))
        elif kind == "digest":
            body_sections.append(_render_digest(s))
        else:
            body_sections.append(_render_cards(s, "neutral"))

    preamble_html = "".join(f"<p>{inline(p)}</p>" for p in preamble)

    stat_cards = "".join(
        f'<div class="stat {cls}"><div class="num">{n}</div><div class="label">{label}</div></div>'
        for cls, n, label in stats
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="site-header">
  <div>
    <h1>{html.escape(title)}</h1>
    <div class="preamble">{preamble_html}</div>
  </div>
</header>

<section class="summary">{stat_cards}</section>

{''.join(body_sections)}

<footer>
  <div>Rendered from <code>action-items-2026-04-17.md</code>. Markdown is the source of truth — edit it and re-run <code>render.py</code>.</div>
</footer>
</body>
</html>"""


def _render_focus(s: Section) -> str:
    items = "".join(f"<li>{inline(b.text)}</li>" for b in s.bullets)
    return f"""
<section class="focus-box">
  <h2>{html.escape(s.emoji)} {html.escape(s.title)}</h2>
  <ul>{items}</ul>
</section>
"""


def _render_cards(s: Section, kind: str) -> str:
    cards: list[str] = []
    for t in s.tasks:
        subj = inline(t.subject)
        body = inline(t.body) if t.body else ""
        done_cls = " done" if t.done else ""
        stamp = '<span class="stamp">✅ Done</span>' if t.done else ""
        cards.append(
            f"""
<article class="card kind-{kind}{done_cls}">
  {stamp}
  <h3>{subj}</h3>
  {f'<div class="body">{body}</div>' if body else ''}
</article>
"""
        )
    # Also render non-task bullets if any
    if s.bullets:
        bullets_html = "".join(f"<li>{inline(b.text)}</li>" for b in s.bullets)
        cards.append(f'<div class="extra-notes"><ul>{bullets_html}</ul></div>')
    grid = "".join(cards) if cards else '<p class="muted">Nothing here.</p>'
    return f"""
<section class="section section-{kind}">
  <h2>{html.escape(s.emoji)} {html.escape(s.title)}</h2>
  <div class="grid">{grid}</div>
</section>
"""


def _render_meetings(s: Section) -> str:
    parts: list[str] = [f'<h2>{html.escape(s.emoji)} {html.escape(s.title)}</h2>']
    for idx, table in enumerate(s.tables):
        subhead = s.subheads[idx - 1] if idx > 0 and idx - 1 < len(s.subheads) else ""
        if subhead:
            parts.append(f"<h3>{html.escape(subhead)}</h3>")
        head = "".join(f"<th>{inline(h)}</th>" for h in table.headers)
        rows_html = []
        for row in table.rows:
            cells = "".join(f"<td>{inline(c)}</td>" for c in row)
            rows_html.append(f"<tr>{cells}</tr>")
        parts.append(
            f'<table class="mtg"><thead><tr>{head}</tr></thead><tbody>{"".join(rows_html)}</tbody></table>'
        )
    return f'<section class="section section-meetings">{"".join(parts)}</section>'


def _render_completed(s: Section) -> str:
    items = []
    for t in s.tasks:
        if not t.done:
            continue
        items.append(
            f'<li><strong>{inline(t.subject)}</strong>{" — " + inline(t.body) if t.body else ""}</li>'
        )
    return f"""
<details class="completed" open>
  <summary><h2>{html.escape(s.emoji)} {html.escape(s.title)} <span class="count">({len(items)})</span></h2></summary>
  <ul>{''.join(items)}</ul>
</details>
"""


def _render_digest(s: Section) -> str:
    blocks: list[str] = []
    buffer: list[str] = []

    def flush():
        if buffer:
            blocks.append('<div class="digest-block">' + "".join(buffer) + "</div>")
            buffer.clear()

    for b in s.bullets:
        t = b.text
        # Bold-only lines act as subheads within the digest
        if re.match(r"^\*\*[^*]+\*\*:?\s*$", t):
            flush()
            blocks.append(f"<h3>{inline(t)}</h3>")
        else:
            buffer.append(f"<p>{inline(t)}</p>")
    flush()
    return f"""
<details class="digest">
  <summary><h2>{html.escape(s.emoji)} {html.escape(s.title)}</h2></summary>
  {''.join(blocks)}
</details>
"""


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------


CSS = """
:root {
  --bg: #0f1115;
  --panel: #171a21;
  --panel-2: #1f2430;
  --border: #2a2f3c;
  --text: #e7ecf3;
  --muted: #9aa3b2;
  --accent: #6ea8ff;
  --urgent: #ff5370;
  --warn: #f7b955;
  --ok: #50c878;
  --info: #59c7ff;
  --purple: #b085f5;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background:
    radial-gradient(1200px 600px at 10% -10%, #1a2033 0%, transparent 60%),
    radial-gradient(900px 500px at 110% 0%, #24183a 0%, transparent 55%),
    var(--bg);
  color: var(--text);
  padding: 32px;
  line-height: 1.5;
  max-width: 1200px;
  margin: 0 auto;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  font-family: ui-monospace, Menlo, monospace;
  background: var(--panel-2);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.9em;
  color: #c7cedb;
}
s { color: var(--muted); }
.site-header {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}
h1 { font-size: 28px; margin: 0 0 6px 0; letter-spacing: -0.4px; }
.preamble { color: var(--muted); font-size: 13px; }
.preamble p { margin: 4px 0; }

.summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}
.stat {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}
.stat .num { font-size: 28px; font-weight: 700; line-height: 1; }
.stat .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 6px; }
.stat.urgent .num { color: var(--urgent); }
.stat.warn   .num { color: var(--warn); }
.stat.info   .num { color: var(--info); }
.stat.ok     .num { color: var(--ok); }
.stat.muted  .num { color: var(--muted); }

.focus-box {
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 28px;
}
.focus-box h2 { margin: 0 0 10px 0; font-size: 16px; }
.focus-box ul { margin: 0; padding-left: 18px; }
.focus-box li { margin: 6px 0; font-size: 13px; color: #c7cedb; }

.section { margin-bottom: 28px; }
.section > h2 { font-size: 18px; margin: 0 0 14px 0; }
.section-urgent   > h2 { color: var(--urgent); }
.section-todo     > h2 { color: var(--warn); }
.section-watching > h2 { color: var(--info); }
.section-personal > h2 { color: var(--muted); }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  position: relative;
  transition: border-color 0.15s, transform 0.15s;
}
.card:hover { border-color: var(--accent); transform: translateY(-1px); }
.card.kind-urgent   { border-left: 3px solid var(--urgent); }
.card.kind-todo     { border-left: 3px solid var(--warn); }
.card.kind-watching { border-left: 3px solid var(--info); }
.card.kind-personal { border-left: 3px solid var(--muted); }
.card.kind-neutral  { border-left: 3px solid var(--border); }
.card h3 { margin: 0 0 6px 0; font-size: 14px; font-weight: 600; }
.card .body { font-size: 13px; color: #c7cedb; }
.card .body p { margin: 4px 0; }

.card.done {
  background: linear-gradient(90deg, rgba(80,200,120,0.08), var(--panel) 60%);
  opacity: 0.85;
}
.card.done h3 {
  text-decoration: line-through;
  text-decoration-color: rgba(80,200,120,0.5);
  color: var(--muted);
}
.card .stamp {
  position: absolute;
  top: 10px;
  right: 12px;
  background: rgba(80,200,120,0.12);
  color: var(--ok);
  border: 1px solid rgba(80,200,120,0.3);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.wiki {
  display: inline-block;
  background: var(--panel-2);
  color: var(--muted);
  border: 1px solid var(--border);
  padding: 0 6px;
  margin: 0 2px;
  border-radius: 4px;
  font-size: 0.82em;
  font-family: ui-monospace, Menlo, monospace;
}

.mtg {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}
.mtg th, .mtg td {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.mtg th { background: var(--panel-2); color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
.mtg tr:last-child td { border-bottom: none; }

details.completed, details.digest {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0 18px;
  margin-bottom: 20px;
}
details.completed summary, details.digest summary {
  list-style: none;
  cursor: pointer;
  padding: 14px 0;
  display: flex;
  align-items: center;
}
details.completed summary::-webkit-details-marker,
details.digest summary::-webkit-details-marker { display: none; }
details.completed summary h2, details.digest summary h2 {
  display: inline;
  margin: 0;
  font-size: 16px;
}
details.completed .count { color: var(--muted); font-weight: 400; font-size: 13px; margin-left: 6px; }
details.completed ul { margin: 0 0 16px 0; padding-left: 20px; color: var(--muted); font-size: 13px; }
details.completed ul li { margin: 4px 0; }
details.digest h3 { color: var(--muted); font-size: 13px; margin: 14px 0 6px 0; }
details.digest p { font-size: 12px; color: var(--muted); margin: 4px 0; }
details.digest .digest-block { margin-bottom: 10px; }

footer {
  margin-top: 40px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 12px;
  text-align: center;
}
.extra-notes {
  grid-column: 1 / -1;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 16px;
}
.extra-notes ul { margin: 4px 0; padding-left: 20px; }
.extra-notes li { font-size: 12px; color: var(--muted); margin: 3px 0; }

@media (max-width: 760px) {
  .summary { grid-template-columns: repeat(2, 1fr); }
}
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python render.py <action-items.md> [output.html]", file=sys.stderr)
        return 2

    md_path = Path(sys.argv[1]).expanduser().resolve()
    if not md_path.exists():
        print(f"Not found: {md_path}", file=sys.stderr)
        return 1

    out_path = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else md_path.with_suffix(".html")

    title, preamble, sections = parse(md_path)
    html_text = render(title, preamble, sections)
    out_path.write_text(html_text)

    print(f"Wrote {out_path} ({len(html_text):,} bytes, {sum(len(s.tasks) for s in sections)} tasks across {len(sections)} sections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
