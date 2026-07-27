"""Read-only, deterministic capture and replay of published campaign projections."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SNAPSHOT_VERSION = "estate.engineering-campaign-snapshot/v1"
MANIFEST_VERSION = "estate.engineering-campaign-replay-manifest/v1"
COMPARISON_VERSION = "estate.engineering-campaign-snapshot-comparison/v1"
PROVENANCE_VERSION = "estate.engineering-campaign-provenance/v1"
REQUIRED_SOURCES = ("engineering_queue", "dashboard", "integration", "recommendations", "decision_ledger", "analytics")


class ReplayError(ValueError):
    """A captured artifact is malformed, incompatible, or has lost integrity."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def content_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _without_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(value)); result.pop("deterministic_content_hash", None)
    return result


def _source_hash(value: Mapping[str, Any]) -> str:
    existing = value.get("deterministic_content_hash")
    return existing if isinstance(existing, str) else content_hash(value)


def create_snapshot(sources: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    """Capture supplied published outputs verbatim; never opens or regenerates sources."""
    if set(sources) != set(REQUIRED_SOURCES):
        raise ReplayError(f"sources must contain exactly: {', '.join(REQUIRED_SOURCES)}")
    if not isinstance(generated_at, str) or not generated_at:
        raise ReplayError("generated_at is required")
    captured = {name: copy.deepcopy(sources[name]) for name in REQUIRED_SOURCES}
    if any(not isinstance(value, dict) for value in captured.values()):
        raise ReplayError("every published source must be an object")
    revisions = {name: _source_hash(value) for name, value in captured.items()}
    integration = captured["integration"]
    snapshot = {
        "snapshot_schema_version": SNAPSHOT_VERSION,
        "generation_timestamp": generated_at,
        "advisory_only": True,
        "authority": "none",
        "immutable": True,
        "source_records": captured,
        "schema_versions": {name: next((v for k, v in value.items() if "schema_version" in k), "unspecified") for name, value in captured.items()},
        "provider_health": copy.deepcopy(integration.get("provider_diagnostics", integration.get("provider_health", []))),
        "freshness": copy.deepcopy(integration.get("freshness", captured["dashboard"].get("freshness", "unspecified"))),
        "degradation_state": copy.deepcopy(integration.get("degradation_reasons", [])),
        "provenance": {"provenance_schema_version": PROVENANCE_VERSION, "source_hashes": revisions},
    }
    snapshot["snapshot_identifier"] = content_hash(snapshot)[7:27]
    snapshot["deterministic_content_hash"] = content_hash(snapshot)
    return snapshot


def validate_snapshot(snapshot: Any) -> list[str]:
    if not isinstance(snapshot, dict): raise ReplayError("snapshot must be an object")
    if snapshot.get("snapshot_schema_version") != SNAPSHOT_VERSION: raise ReplayError("unsupported snapshot_schema_version")
    if snapshot.get("advisory_only") is not True or snapshot.get("authority") != "none" or snapshot.get("immutable") is not True:
        raise ReplayError("snapshot violates read-only authority boundary")
    records = snapshot.get("source_records")
    if not isinstance(records, dict) or set(records) != set(REQUIRED_SOURCES): raise ReplayError("snapshot source set is malformed")
    expected = content_hash(_without_hash(snapshot))
    if snapshot.get("deterministic_content_hash") != expected: raise ReplayError("deterministic_content_hash mismatch")
    hashes = snapshot.get("provenance", {}).get("source_hashes", {})
    for name in REQUIRED_SOURCES:
        if hashes.get(name) != _source_hash(records[name]): raise ReplayError(f"provenance mismatch: {name}")
    return []


def replay(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return captured projections only; no recommendation or metric policy executes."""
    validate_snapshot(snapshot)
    s = copy.deepcopy(snapshot["source_records"])
    dashboard = s["dashboard"].get("dashboard_snapshot", s["dashboard"])
    panels = dashboard.get("panels", {}) if isinstance(dashboard, dict) else {}
    manifest = {
        "replay_manifest_schema_version": MANIFEST_VERSION,
        "snapshot_identifier": snapshot["snapshot_identifier"],
        "snapshot_hash": snapshot["deterministic_content_hash"],
        "dashboard": s["dashboard"], "recommendations": s["recommendations"], "analytics": s["analytics"],
        "decision_history": s["decision_ledger"],
        "dependency_graph": copy.deepcopy(panels.get("dependency_graph", s["engineering_queue"].get("dependency_graph", {}))),
        "merge_risk_analysis": copy.deepcopy(panels.get("merge_risk", {})),
        "engineering_metrics": copy.deepcopy(s["analytics"].get("metrics", {})),
        "provenance": copy.deepcopy(snapshot["provenance"]), "read_only": True,
    }
    manifest["deterministic_content_hash"] = content_hash(manifest)
    return manifest


def _items(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    queue = snapshot["source_records"]["engineering_queue"]
    rows = queue.get("candidates", queue.get("items", []))
    return {str(row.get("item_identifier", row.get("id"))): row for row in rows if isinstance(row, dict)}


def compare(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(left); validate_snapshot(right)
    a, b = _items(left), _items(right); common = sorted(set(a) & set(b))
    changed = lambda keys: [i for i in common if any(a[i].get(k) != b[i].get(k) for k in keys)]
    ar, br = left["source_records"], right["source_records"]
    report = {"comparison_schema_version": COMPARISON_VERSION, "left_snapshot": left["snapshot_identifier"], "right_snapshot": right["snapshot_identifier"],
        "new_work": sorted(set(b)-set(a)), "completed_work": sorted(i for i in common if a[i].get("current_lifecycle_state") != b[i].get("current_lifecycle_state") and b[i].get("current_lifecycle_state") in {"completed", "merged"}),
        "removed_work": sorted(set(a)-set(b)), "changed_recommendations": ar["recommendations"] != br["recommendations"],
        "changed_priorities": changed(("priority",)), "changed_dependencies": changed(("dependencies",)),
        "analytics_deltas": _numeric_delta(ar["analytics"].get("metrics", {}), br["analytics"].get("metrics", {})),
        "health_changes": {"before": left["provider_health"], "after": right["provider_health"]} if left["provider_health"] != right["provider_health"] else {},
        "degradation_changes": {"before": left["degradation_state"], "after": right["degradation_state"]} if left["degradation_state"] != right["degradation_state"] else {},
        "note": "priorities and analytics are reported from captured records; never recomputed"}
    report["deterministic_content_hash"] = content_hash(report)
    return report


def _numeric_delta(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, float]:
    return {k: round(float(b[k])-float(a[k]), 6) for k in sorted(set(a)&set(b)) if isinstance(a[k], (int,float)) and not isinstance(a[k], bool) and isinstance(b[k], (int,float)) and not isinstance(b[k], bool)}


def history(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in snapshots: validate_snapshot(item)
    return [{"snapshot_identifier": s["snapshot_identifier"], "generation_timestamp": s["generation_timestamp"], "deterministic_content_hash": s["deterministic_content_hash"]} for s in sorted(snapshots, key=lambda x:(x["generation_timestamp"], x["snapshot_identifier"]))]


def load(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as stream: return json.load(stream)
