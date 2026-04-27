"""Unit tests for the action-items Typer sub-app's per-command surface.

Subprocess-style coverage of the same commands lives in
tests/integration/test_action_items_cli.py.
"""

from __future__ import annotations

from typer.testing import CliRunner


def test_cli_watch_help_text_is_projection_consumer_contract() -> None:
    """Per spec §13.3, watch's help text describes a stream of changes,
    not a file-watcher. This test pins that wording."""
    from scout.action_items.cli import app

    result = CliRunner().invoke(app, ["watch", "--help"])
    assert result.exit_code == 0
    assert "stream" in result.stdout.lower()
    assert "changes" in result.stdout.lower()


def test_cli_watch_rejects_missing_target(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SCOUT_DATA_DIR", str(tmp_path))
    from scout.action_items.cli import app

    # No daily file exists in tmp_path/action-items/, and we pass no target.
    result = CliRunner().invoke(app, ["watch"])
    assert result.exit_code != 0
    # The ActionItemError message surfaces via the exception or stderr/stdout.
    err_text = (str(result.exception) if result.exception else "") + result.output
    assert "does not exist" in err_text.lower()
