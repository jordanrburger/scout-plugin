"""Static import-graph test: forbids heavy imports at scoutctl startup.

Scout-app invokes scoutctl on every user action. If scout.cli (or any
sub-CLI module imported transitively at startup) imports textual / rich /
jinja2 / watchdog / scout.kb.* / scout.tui.*, startup balloons past the
latency budget. This test parses each scanned file's AST and fails on
top-level imports of the banned modules.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BANNED_TOP_LEVEL = {
    "textual",
    "rich",
    "jinja2",
    "watchdog",
    "scout.kb",
    "scout.tui",
    # scout.action_items.cli is allowed since it only imports typer + stdlib
    # at top; its heavy submodules are inside function bodies.
    "scout.action_items.parser",
    "scout.action_items.writer",
    "scout.action_items.mark_done",
    "scout.action_items.snooze",
    "scout.action_items.add_comment",
    "scout.action_items.render",
    "scout.action_items.list",
    "scout.runners",
    "scout.hooks",
    "scout.scripts",
}


def _top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
                names.add(node.module.split(".")[0])
    return names


SCANNED_FILES = [
    Path(__file__).parent.parent.parent / "scout" / "cli.py",
    Path(__file__).parent.parent.parent / "scout" / "action_items" / "cli.py",
]


@pytest.mark.perf
@pytest.mark.parametrize("source_file", SCANNED_FILES, ids=lambda p: p.name)
def test_cli_has_no_banned_top_level_imports(source_file: Path) -> None:
    source = source_file.read_text()
    imports = _top_level_imports(source)
    offenders = imports & BANNED_TOP_LEVEL
    assert not offenders, (
        f"{source_file} has banned top-level imports: {offenders}. "
        f"Move them inside subcommand functions to preserve startup latency."
    )
