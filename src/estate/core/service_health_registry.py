"""Read-only Service Health Registry aggregation.

The registry combines service catalog entries and dependency-matrix context into a
common operational health view. It never probes services or invents telemetry; all
status values are derived from existing authoritative artifacts and linked back to
those sources.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.estate_service_catalog import generate_estate_service_catalog
from estate.core.service_dependency_matrix import generate_service_dependency_matrix
from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/services/service_health_registry.json"
MARKDOWN_OUTPUT = "operations/services/service_health_registry.md"

HEALTHY_VALIDATION = {"ready", "source_links_checked", "validated", "passed"}
DEGRADED_VALIDATION = {"degraded", "blocked", "source_link_warnings", "failed", "warning"}
HEALTHY_OPERATIONAL = {"active", "operational", "implemented", "running"}
UNAVAILABLE_OPERATIONAL = {"unavailable", "offline", "down", "failed"}
DEGRADED_OPERATIONAL = {"degraded", "partial", "blocked"}
UNKNOWN_OPERATIONAL = {"unknown", "draft", "planned", "metadata_only"}


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _exists(root, rel):
    return bool(rel) and (root / rel).exists()


def _source_links(root, paths):
    links = []
    seen = set()
    for path in paths or []:
        if not path or path in seen:
            continue
        seen.add(path)
        links.append({"path": path, "available": _exists(root, path)})
    return links


def _status_from_metadata(service, dependency_row, source_links):
    operational = str(service.get("operational_status") or "unknown").lower()
    validation = str(service.get("validation_status") or "unknown").lower()
    warnings = list(service.get("metadata_warnings") or []) + list((dependency_row or {}).get("metadata_warnings") or [])
    missing_sources = [link for link in source_links if not link["available"]]

    if operational in UNAVAILABLE_OPERATIONAL or (source_links and not any(link["available"] for link in source_links)):
        return "unavailable", ["authoritative source or service metadata is unavailable"]
    if operational in DEGRADED_OPERATIONAL or validation in DEGRADED_VALIDATION:
        return "degraded", ["operational or validation metadata indicates degraded service"]
    if missing_sources or warnings:
        return "degraded", ["service has missing metadata or unavailable source links"]
    if operational in HEALTHY_OPERATIONAL and validation in HEALTHY_VALIDATION:
        return "healthy", ["catalog status and validation metadata are healthy"]
    if operational in UNKNOWN_OPERATIONAL or validation in {"unknown", "metadata_only"}:
        return "unknown", ["insufficient source metadata to determine health"]
    return "unknown", ["no explicit health state is recorded by authoritative sources"]


def _dependency_health(service_id, dependency_row, health_by_id):
    deps = list((dependency_row or {}).get("startup_after") or [])
    details = []
    worst = "healthy" if not deps else "healthy"
    rank = {"healthy": 0, "unknown": 1, "degraded": 2, "unavailable": 3}
    for dep in deps:
        state = health_by_id.get(dep, "unknown")
        details.append({"service_id": dep, "health_status": state})
        if rank[state] > rank[worst]:
            worst = state
    if not deps:
        worst = "none_recorded"
    return {"summary": worst, "dependencies": details, "source_artifacts": list((dependency_row or {}).get("source_artifacts") or [])}


def generate_service_health_registry(root=None, write=True):
    root = _root(root)
    catalog = generate_estate_service_catalog(root, write=False)
    matrix = generate_service_dependency_matrix(root, write=False)
    matrix_by_id = {row["service_id"]: row for row in matrix.get("matrix", [])}

    entries = []
    warnings = list(catalog.get("warnings", [])) + list(matrix.get("warnings", []))
    for service in catalog.get("services", []):
        sid = service["id"]
        dependency_row = matrix_by_id.get(sid, {})
        source_paths = sorted(set(service.get("source_artifact_links", []) + dependency_row.get("source_artifacts", [])))
        links = _source_links(root, source_paths)
        health_status, indicators = _status_from_metadata(service, dependency_row, links)
        entries.append({
            "service_id": sid,
            "service_name": service.get("name"),
            "owner": service.get("owner"),
            "resident": service.get("resident"),
            "health_status": health_status,
            "availability": "available" if any(link["available"] for link in links) else "unavailable",
            "health_indicators": indicators,
            "operational_status": service.get("operational_status"),
            "validation_state": service.get("validation_status"),
            "dependency_health": {},
            "last_known_update": catalog.get("generated_at"),
            "authoritative_sources": links,
            "metadata_warnings": list(service.get("metadata_warnings") or []) + list(dependency_row.get("metadata_warnings") or []),
        })

    health_by_id = {entry["service_id"]: entry["health_status"] for entry in entries}
    for entry in entries:
        entry["dependency_health"] = _dependency_health(entry["service_id"], matrix_by_id.get(entry["service_id"], {}), health_by_id)
        if entry["dependency_health"]["summary"] in {"degraded", "unavailable"} and entry["health_status"] == "healthy":
            entry["health_status"] = "degraded"
            entry["health_indicators"].append("one or more explicit dependencies are not healthy")

    counts = {state: sum(1 for e in entries if e["health_status"] == state) for state in ("healthy", "degraded", "unavailable", "unknown")}
    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "read_only_aggregation_not_health_source_of_truth",
        "inputs": {"service_catalog": "generated in memory", "service_dependency_matrix": "generated in memory", "unavailable": catalog.get("inputs", {}).get("unavailable", [])},
        "summary": {"service_count": len(entries), "warning_count": len(warnings), **counts},
        "health_entries": entries,
        "warnings": warnings,
        "operations_center_integration": {"status": "supported_by_json_and_markdown_outputs", "json_output": JSON_OUTPUT, "markdown_output": MARKDOWN_OUTPUT, "dashboard_ready": True, "alert_ready": True},
    }
    if write:
        (root / "runtime/services").mkdir(parents=True, exist_ok=True)
        (root / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "operations/services").mkdir(parents=True, exist_ok=True)
        (root / MARKDOWN_OUTPUT).write_text(format_service_health_registry(payload) + "\n", encoding="utf-8")
    return payload


def format_service_health_registry(payload):
    s = payload.get("summary", {})
    lines = ["# Estate Service Health Registry", "", "Read-only aggregation. This registry does not replace monitoring systems or become the source of truth for service health.", "", f"Generated: {payload.get('generated_at')}", "", "## Summary", f"- Services: {s.get('service_count', 0)}", f"- Healthy: {s.get('healthy', 0)}", f"- Degraded: {s.get('degraded', 0)}", f"- Unavailable: {s.get('unavailable', 0)}", f"- Unknown: {s.get('unknown', 0)}", f"- Warnings: {s.get('warning_count', 0)}", "", "## Health Entries"]
    for e in payload.get("health_entries", []):
        lines += ["", f"### {e.get('service_name')} (`{e.get('service_id')}`)", f"- Owner: {e.get('owner')}", f"- Health status: {e.get('health_status')}", f"- Availability: {e.get('availability')}", f"- Operational status: {e.get('operational_status')}", f"- Validation state: {e.get('validation_state')}", f"- Dependency health: {e.get('dependency_health', {}).get('summary')}", f"- Last-known update: {e.get('last_known_update')}", f"- Health indicators: {', '.join(e.get('health_indicators') or []) or 'None recorded'}", f"- Authoritative sources: {', '.join(link['path'] for link in e.get('authoritative_sources', [])) or 'None recorded'}"]
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        for warning in payload["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('path', '')} — {warning.get('message') or warning.get('service_name') or ''}")
    return "\n".join(lines)


def format_service_health_registry_summary(payload):
    s = payload.get("summary", {})
    return "\n".join(["Estate Service Health Registry", f"Generated: {payload.get('generated_at')}", f"Services: {s.get('service_count', 0)}", f"Healthy: {s.get('healthy', 0)}", f"Degraded: {s.get('degraded', 0)}", f"Unavailable: {s.get('unavailable', 0)}", f"Unknown: {s.get('unknown', 0)}", f"Warnings: {s.get('warning_count', 0)}"])
