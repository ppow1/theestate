"""Office projection for canonical compute-resource evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from estate.core.compute_resources import GPU_RESERVATIONS, GPU_SNAPSHOT, build_compute_projection, collect_nvidia_smi, write_compute_projection
from estate.core.paths import ESTATE_ROOT
from estate.core.gpu_runtime_lanes import LANE_EVIDENCE, load_registered_lanes

OPERATOR_SUMMARY = Path("runtime/compute_resources/operator_summary.json")


def _read_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import json
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, ValueError):
        return []


def _runtime_lane_projection(base: Path) -> list[dict[str, Any]]:
    """Return registered lanes enriched with safe process evidence."""
    evidence_by_id: dict[str, dict[str, Any]] = {}
    try:
        payload = json.loads((base / LANE_EVIDENCE).read_text(encoding="utf-8"))
        evidence_by_id = {str(row.get("runtime_lane_id")): row for row in payload.get("lanes", []) if isinstance(row, dict)}
    except (OSError, ValueError, AttributeError):
        pass
    rows: list[dict[str, Any]] = []
    for lane in load_registered_lanes(base):
        row = lane.to_dict()
        evidence = evidence_by_id.get(lane.runtime_lane_id, {})
        row.update({key: evidence[key] for key in ("process_id", "process_identity", "started_at", "observed_at") if key in evidence})
        row["endpoint_identity"] = lane.runtime_lane_id
        rows.append(row)
    return rows


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
    lanes = _runtime_lane_projection(base)
    for resource in payload.get("resources", []):
        resource["runtime_lanes"] = [lane for lane in lanes if lane.get("compute_resource_id") == resource.get("resource_id")]
    payload.update({"runtime_lanes": lanes, "available": True, "kind": "steward_compute_resources", "control_surface": "Office of the Steward / Compute", "read_only": True, "source_artifact": str(GPU_SNAPSHOT).replace("\\", "/"), "actions": {"refresh": "compute refresh --live", "inspect": "compute inspect", "placement_explain": "compute explain-placement"}})
    return payload


def refresh_compute_panel(root: str | Path | None = None, *, live: bool = False) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    if live:
        payload = write_compute_projection(collect_nvidia_smi(), base, reservations=_read_rows(base / GPU_RESERVATIONS))
    else:
        payload = build_compute_panel(base, live=False)
    lanes = _runtime_lane_projection(base)
    for resource in payload.get("resources", []):
        resource["runtime_lanes"] = [lane for lane in lanes if lane.get("compute_resource_id") == resource.get("resource_id")]
    payload["runtime_lanes"] = lanes
    payload.update({"available": True, "kind": "steward_compute_resources", "control_surface": "Office of the Steward / Compute", "read_only": True, "source_artifact": str(GPU_SNAPSHOT).replace("\\", "/")})
    path = base / OPERATOR_SUMMARY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
