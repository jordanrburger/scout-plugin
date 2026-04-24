"""Static import-graph test: forbids heavy imports at scoutctl startup.

Scout-app invokes scoutctl on every user action. If scout.cli imports
textual / rich / jinja2 / watchdog / scout.kb.*, startup balloons past
the latency budget. This test parses scout/cli.py's AST and fails on
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
    "scout.action_items",
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


CLI_PATH = Path(__file__).parent.parent.parent / "scout" / "cli.py"


@pytest.mark.perf
def test_cli_has_no_banned_top_level_imports() -> None:
    source = CLI_PATH.read_text()
    imports = _top_level_imports(source)
    offenders = imports & BANNED_TOP_LEVEL
    assert not offenders, (
        f"scout/cli.py has banned top-level imports: {offenders}. "
        f"Move them inside subcommand functions to preserve startup latency."
    )
