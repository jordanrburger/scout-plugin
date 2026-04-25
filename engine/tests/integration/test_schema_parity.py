"""Schema-parity check: packaged engine default vs live user vault.

The engine ships ``scout/kb/schema.yaml`` as a default; users may override
by placing their own copy at
``$SCOUT_DATA_DIR/knowledge-base/ontology/schema.yaml`` (see
``scout.kb.paths.resolve_schema_path``). Until the vault becomes the sole
source of truth (Plan 4+), the two copies need to match — otherwise any
consumer that doesn't go through ``resolve_schema_path`` (e.g., a wheel
install with no ``SCOUT_DATA_DIR`` set) silently reads a stale schema.

This test is gated on ``SCOUT_DATA_DIR``: skipped in CI (where it's unset),
runs locally and against any environment with a real vault. ~/Scout's
launchd runners export ``SCOUT_DATA_DIR=$HOME/Scout``, so wiring this into
a pre-session hook there catches drift before it bites.
"""

from __future__ import annotations

import os
from importlib.resources import as_file, files
from pathlib import Path

import pytest


def test_packaged_schema_matches_vault() -> None:
    data_dir = os.environ.get("SCOUT_DATA_DIR")
    if not data_dir:
        pytest.skip("SCOUT_DATA_DIR not set — parity test only runs against a real vault")

    vault_schema = Path(data_dir) / "knowledge-base" / "ontology" / "schema.yaml"
    if not vault_schema.exists():
        pytest.skip(f"No vault schema at {vault_schema}")

    resource = files("scout") / "kb" / "schema.yaml"
    with as_file(resource) as p:
        packaged_schema = Path(p)
        packaged_text = packaged_schema.read_text(encoding="utf-8")

    vault_text = vault_schema.read_text(encoding="utf-8")

    assert vault_text == packaged_text, (
        "Schema drift detected between vault and packaged engine default.\n"
        f"  vault:    {vault_schema}\n"
        f"  packaged: {packaged_schema}\n"
        "Reconcile the two, or document the divergence and update this test."
    )
