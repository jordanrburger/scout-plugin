"""Startup-latency tests for scoutctl.

These assert that import + help + version paths stay fast so the
scout-app UI doesn't feel laggy when invoking scoutctl on user actions.

Budgets have CI headroom; local Macs hit them in half the listed time.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

HELP_BUDGET_MS = 250
VERSION_BUDGET_MS = 150


@pytest.mark.perf
def test_scoutctl_help_latency() -> None:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "scout.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert result.returncode == 0
    assert elapsed_ms < HELP_BUDGET_MS, (
        f"scoutctl --help took {elapsed_ms:.0f}ms "
        f"(budget: {HELP_BUDGET_MS}ms). Check for heavy top-level imports."
    )


@pytest.mark.perf
def test_scoutctl_version_latency() -> None:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "scout.cli", "version"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert result.returncode == 0
    assert result.stdout.strip(), "version should emit to stdout"
    assert elapsed_ms < VERSION_BUDGET_MS, (
        f"scoutctl version took {elapsed_ms:.0f}ms "
        f"(budget: {VERSION_BUDGET_MS}ms)."
    )
