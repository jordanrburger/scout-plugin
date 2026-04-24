"""Unit tests for scout.manifest."""

from __future__ import annotations

import json
from pathlib import Path

from scout import __version__
from scout.manifest import build_manifest, write_manifest


def test_build_manifest_has_version() -> None:
    m = build_manifest()
    assert m.version == __version__


def test_build_manifest_has_schema_version() -> None:
    assert build_manifest().schema_version == 1


def test_build_manifest_exposes_known_features() -> None:
    m = build_manifest()
    expected = {
        "session_tokens_v1",
        "connector_health_v1",
        "action_items_cli_v1",
        "kb_ontology_v1",
        "tui_v1",
    }
    assert expected.issubset(m.features.keys())


def test_build_manifest_exposes_baseline_subcommands() -> None:
    m = build_manifest()
    assert "version" in m.subcommands
    assert "manifest" in m.subcommands


def test_manifest_json_is_stable_and_decodable() -> None:
    js = build_manifest().to_json()
    decoded = json.loads(js)
    assert decoded["version"] == __version__
    assert "features" in decoded
    assert "subcommands" in decoded


def test_write_manifest_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "manifest.json"
    written = write_manifest(target)
    assert written == target
    decoded = json.loads(target.read_text())
    assert decoded["version"] == __version__
