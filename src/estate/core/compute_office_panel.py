"""Office of the Steward projection for canonical compute-resource evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from estate.core.compute_resources import GPU_SNAPSHOT, build_compute_projection, discover_grace_gpus, write_compute_projection
from estate.core.paths import ESTATE_ROOT


def build_compute_panel(root: str | Path | None = None, *, observations=None, live: bool = False) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    if observations is None:
        observations = discover_grace_gpus() if live else []
    payload = build_compute_projection(observations)
    payload.update({"available": True, "kind": "steward_compute_resources", "control_surface": "Office of the Steward / Compute", "read_only": True, "source_artifact": str(GPU_SNAPSHOT).replace("\\", "/"), "actions": {"refresh": "compute refresh --live", "inspect": "compute inspect", "placement_explain": "compute explain-placement"}})
    return payload


def refresh_compute_panel(root: str | Path | None = None, *, live: bool = False) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    observations = discover_grace_gpus() if live else []
    return {**write_compute_projection(observations, base), **{"available": True, "kind": "steward_compute_resources", "control_surface": "Office of the Steward / Compute", "read_only": True, "source_artifact": str(GPU_SNAPSHOT).replace("\\", "/")}}
