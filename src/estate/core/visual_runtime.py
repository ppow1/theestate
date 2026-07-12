"""Estate resident visual architecture runtime.

The visual runtime keeps resident likeness, wardrobe, canonical locations,
poses, gallery entries, portraits, archive records, generated scene briefs, and
visual timeline events in data files instead of introducing another asset
system.  It validates references against the resident registry and existing
asset/catalog locations so generated images remain traceable Estate artifacts.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate_visual_runtime.v1"
VISUAL_DATA_DIR = Path("data/visuals")
IDENTITIES = VISUAL_DATA_DIR / "resident_visual_identities.json"
WARDROBE = VISUAL_DATA_DIR / "estate_wardrobe.json"
LOCATIONS = VISUAL_DATA_DIR / "canonical_locations.json"
POSES = VISUAL_DATA_DIR / "presentation_poses.json"
CONTINUITY = VISUAL_DATA_DIR / "visual_continuity.json"
GALLERY = VISUAL_DATA_DIR / "living_gallery.json"
PORTRAITS = VISUAL_DATA_DIR / "resident_portraits.json"
ARCHIVE = VISUAL_DATA_DIR / "historical_archive.json"
SCENES = VISUAL_DATA_DIR / "dynamic_scene_generation.json"
TIMELINE = VISUAL_DATA_DIR / "visual_timeline.json"
DATA_FILES = [IDENTITIES, WARDROBE, LOCATIONS, POSES, CONTINUITY, GALLERY, PORTRAITS, ARCHIVE, SCENES, TIMELINE]
ASSET_PREFIXES = ("assets/", "archive/", "docs/", "runtime/", "data/")


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load(root: Path, rel: Path) -> dict[str, Any]:
    path = root / rel
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "items": []}
    data = _read_json(path)
    if isinstance(data, list):
        return {"schema_version": SCHEMA_VERSION, "items": data}
    return data


def _items(data: Mapping[str, Any], key: str = "items") -> list[dict[str, Any]]:
    value = data.get(key, [])
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resident_keys(root: Path) -> set[str]:
    residents = _read_json(root / "data/registry/residents.json")
    keys: set[str] = set()
    for row in residents:
        rid = str(row.get("id", "")).lower()
        name = str(row.get("name", "")).lower()
        if rid:
            keys.add(rid)
        if name:
            keys.add(name)
    return keys


def _index(items: Iterable[Mapping[str, Any]], field: str) -> set[str]:
    return {str(item.get(field, "")).lower() for item in items if item.get(field)}


def build_visual_runtime(root: str | Path | None = None) -> dict[str, Any]:
    """Load the complete Estate visual architecture as one inspectable payload."""
    rootp = _root(root)
    identities = _load(rootp, IDENTITIES)
    wardrobe = _load(rootp, WARDROBE)
    locations = _load(rootp, LOCATIONS)
    poses = _load(rootp, POSES)
    continuity = _load(rootp, CONTINUITY)
    gallery = _load(rootp, GALLERY)
    portraits = _load(rootp, PORTRAITS)
    archive = _load(rootp, ARCHIVE)
    scenes = _load(rootp, SCENES)
    timeline = _load(rootp, TIMELINE)
    validation = validate_visual_runtime(rootp)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "resident_visual_identity": identities,
        "wardrobe": wardrobe,
        "canonical_locations": locations,
        "poses": poses,
        "continuity": continuity,
        "gallery": gallery,
        "portraits": portraits,
        "historical_archive": archive,
        "scene_generation": scenes,
        "timeline": timeline,
        "validation": validation,
    }


def validate_visual_runtime(root: str | Path | None = None) -> dict[str, Any]:
    """Validate gallery consistency and cross-file asset references."""
    rootp = _root(root)
    diagnostics: list[dict[str, Any]] = []
    for rel in DATA_FILES:
        if not (rootp / rel).exists():
            diagnostics.append({"severity": "error", "code": "missing_visual_file", "path": str(rel)})

    resident_keys = _resident_keys(rootp)
    identities = _items(_load(rootp, IDENTITIES), "residents")
    wardrobe = _items(_load(rootp, WARDROBE), "wardrobe_items")
    locations = _items(_load(rootp, LOCATIONS), "locations")
    poses = _items(_load(rootp, POSES), "poses")
    gallery_entries = _items(_load(rootp, GALLERY), "gallery_entries")
    portraits = _items(_load(rootp, PORTRAITS), "portraits")
    scenes = _items(_load(rootp, SCENES), "scene_templates")
    timeline_events = _items(_load(rootp, TIMELINE), "events")

    identity_residents = _index(identities, "resident_id")
    wardrobe_ids = _index(wardrobe, "wardrobe_id")
    location_ids = _index(locations, "location_id")
    pose_ids = _index(poses, "pose_id")
    gallery_ids = _index(gallery_entries, "gallery_id")
    portrait_ids = _index(portraits, "portrait_id")

    for item in identities:
        rid = str(item.get("resident_id", "")).lower()
        if rid not in resident_keys:
            diagnostics.append({"severity": "error", "code": "unknown_identity_resident", "resident_id": item.get("resident_id")})
        if not item.get("canonical_traits") or not item.get("negative_prompts"):
            diagnostics.append({"severity": "error", "code": "incomplete_visual_identity", "resident_id": item.get("resident_id")})

    def check_ref(kind: str, owner: Mapping[str, Any], value: Any, allowed: set[str]) -> None:
        if str(value or "").lower() not in allowed:
            diagnostics.append({"severity": "error", "code": f"unknown_{kind}", "owner_id": owner.get("gallery_id") or owner.get("portrait_id") or owner.get("scene_id") or owner.get("event_id"), kind: value})

    for entry in gallery_entries:
        check_ref("resident_id", entry, entry.get("resident_id"), identity_residents)
        check_ref("wardrobe_id", entry, entry.get("wardrobe_id"), wardrobe_ids)
        check_ref("location_id", entry, entry.get("location_id"), location_ids)
        check_ref("pose_id", entry, entry.get("pose_id"), pose_ids)
        asset = str(entry.get("asset_ref", ""))
        if not asset.startswith(ASSET_PREFIXES):
            diagnostics.append({"severity": "error", "code": "noncanonical_asset_reference", "gallery_id": entry.get("gallery_id"), "asset_ref": asset})

    for portrait in portraits:
        check_ref("resident_id", portrait, portrait.get("resident_id"), identity_residents)
        gallery_id = portrait.get("gallery_id")
        if gallery_id and str(gallery_id).lower() not in gallery_ids:
            diagnostics.append({"severity": "error", "code": "portrait_missing_gallery_entry", "portrait_id": portrait.get("portrait_id"), "gallery_id": gallery_id})

    for scene in scenes:
        for key, allowed in (("location_id", location_ids), ("pose_id", pose_ids), ("wardrobe_id", wardrobe_ids)):
            if scene.get(key):
                check_ref(key, scene, scene.get(key), allowed)

    for event in timeline_events:
        if event.get("resident_id"):
            check_ref("resident_id", event, event.get("resident_id"), identity_residents)
        for gid in event.get("gallery_refs", []):
            check_ref("gallery_id", event, gid, gallery_ids)
        for pid in event.get("portrait_refs", []):
            check_ref("portrait_id", event, pid, portrait_ids)

    return {"ok": not any(d.get("severity") == "error" for d in diagnostics), "checked_at": _now(), "diagnostics": diagnostics, "counts": {"identities": len(identities), "wardrobe_items": len(wardrobe), "locations": len(locations), "poses": len(poses), "gallery_entries": len(gallery_entries), "portraits": len(portraits), "scene_templates": len(scenes), "timeline_events": len(timeline_events)}}


def format_visual_runtime_summary(payload: Mapping[str, Any]) -> str:
    validation = payload.get("validation", {}) if isinstance(payload, Mapping) else {}
    counts = validation.get("counts", {}) if isinstance(validation, Mapping) else {}
    lines = ["Estate Visual Runtime", f"Schema: {payload.get('schema_version', SCHEMA_VERSION)}", f"Validation: {'ok' if validation.get('ok') else 'failed'}"]
    lines.extend(f"- {key}: {value}" for key, value in sorted(counts.items()))
    diagnostics = validation.get("diagnostics", [])
    if diagnostics:
        lines.append("Diagnostics:")
        lines.extend(f"- {d.get('severity')}: {d.get('code')} ({d})" for d in diagnostics)
    return "\n".join(lines)
