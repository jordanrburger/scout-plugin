"""Engine capability manifest.

The manifest is the contract between scout-plugin (engine) and scout-app.
It declares which features and CLI subcommands this engine version
supports. Scout-app reads it at launch and refuses (with a helpful
banner) to use features the engine cannot provide.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from scout import __version__

ENGINE_DIR = Path(__file__).parent.parent


@dataclass
class EngineManifest:
    """Serializable capability manifest."""

    version: str
    schema_version: int
    features: dict[str, bool] = field(default_factory=dict)
    subcommands: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def build_manifest() -> EngineManifest:
    """Construct the manifest from package state.

    Feature flags reflect what this version of the engine promises.
    Plans 2 and 3 flip individual flags to True as subsystems land.
    """
    return EngineManifest(
        version=__version__,
        schema_version=1,
        features={
            "session_tokens_v1": False,
            "connector_health_v1": False,
            "action_items_cli_v1": False,
            "kb_ontology_v1": False,
            "tui_v1": False,
        },
        subcommands=[
            "version",
            "manifest",
        ],
    )


def write_manifest(path: Path | None = None) -> Path:
    """Write the manifest to disk. Returns the path written."""
    target = path or (ENGINE_DIR / "manifest.json")
    target.write_text(build_manifest().to_json() + "\n")
    return target
