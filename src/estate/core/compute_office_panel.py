"""Office projection for canonical compute-resource evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from estate.core.compute_resources import GPU_RESERVATIONS, GPU_SNAPSHOT, build_compute_projection, collect_nvidia_smi, write_compute_projection
from estate.core.paths import ESTATE_ROOT


def _read_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import json
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, ValueError):
        return []


def build_compute_panel(root: str | Path | None = None, *, observations=None, live: bool = False) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    if observations is None:
        if live:
            observations = collect_nvidia_smi()
        else:
            try:
                stored = json.loads((base / GPU_SNAPSHOT).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                stored = None
            if isinstance(stored, dict) and isinstance(stored.get("resources"), list):
                payload = stored
                payload["reservations"] = _read_rows(base / GPU_RESERVATIONS)
            else:
                observations = []
    if "payload" not in locals():
        payload = build_compute_projection(observations, reservations=_read_rows(base / GPU_RESERVATIONS))
    payload.update({"available": True, "kind": "steward_compute_resources", "control_surface": "Office of the Steward / Compute", "read_only": True, "source_artifact": str(GPU_SNAPSHOT).replace("\\", "/"), "actions": {"refresh": "compute refresh --live", "inspect": "compute inspect", "placement_explain": "compute explain-placement"}})
    return payload


def refresh_compute_panel(root: str | Path | None = None, *, live: bool = False) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    if live:
        payload = write_compute_projection(collect_nvidia_smi(), base, reservations=_read_rows(base / GPU_RESERVATIONS))
    else:
        payload = build_compute_panel(base, live=False)
    return {**payload, "available": True, "kind": "steward_compute_resources", "control_surface": "Office of the Steward / Compute", "read_only": True, "source_artifact": str(GPU_SNAPSHOT).replace("\\", "/")}
