"""Smoke tests for the TUI port: confirm imports work and the
Textual App class is constructable without actually running the UI.

A full UI test requires Textual's pilot framework. Plan 2 keeps
testing minimal — Plan 6 (scout-app) is where TUI wins matter.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "scout.tui",
        "scout.tui.app",
        "scout.tui.config",
        "scout.tui.screens.dashboard",
        "scout.tui.screens.context",
        "scout.tui.screens.note_modal",
        "scout.tui.screens.spawn",
    ],
)
def test_tui_module_imports(module: str) -> None:
    pytest.importorskip("textual")  # skip whole test if textual is not installed
    importlib.import_module(module)


def test_tui_app_class_exists() -> None:
    """Sanity-check that scout.tui.app exposes the Textual App subclass
    that scoutctl tui will instantiate."""
    pytest.importorskip("textual")
    mod = importlib.import_module("scout.tui.app")
    # Class name varies — read tui/app.py to confirm. Accept either name pattern.
    classes = [n for n in dir(mod) if not n.startswith("_")]
    has_app = any(n.endswith("App") or n in {"ScoutTUI", "ScoutApp", "App"} for n in classes)
    assert has_app, f"scout.tui.app must expose a Textual App subclass. Found: {sorted(classes)}"
