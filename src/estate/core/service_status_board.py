"""Operations Center Service Status Board.

Read-only aggregation that combines the Estate Service Catalog, Service
Dependency Matrix, and Service Health Registry into one Operations Center view.
It does not probe services or become the source of truth for status.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.estate_service_catalog import generate_estate_service_catalog
from estate.core.paths import ESTATE_ROOT
from estate.core.service_dependency_matrix import generate_service_dependency_matrix
from estate.core.service_health_registry import generate_service_health_registry

JSON_OUTPUT = "runtime/services/service_status_board.json"
MARKDOWN_OUTPUT = "operations/services/service_status_board.md"
SOURCE_ARTIFACTS = {
    "service_catalog": "runtime/services/estate_service_catalog.json",
    "service_dependency_matrix": "runtime/services/service_dependency_matrix.json",
    "service_health_registry": "runtime/services/service_health_registry.json",
}
STATE_RANK = {"healthy": 0, "unknown": 1, "degraded": 2, "blocked": 3, "unavailable": 4}


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _source_link(root, path, generated_in_memory=False):
    return {"path": path, "available": (root / path).exists(), "generated_in_memory": generated_in_memory}


def _validation_readiness(validation_state):
    state = str(validation_state or "unknown").lower()
    if state in {"ready", "source_links_checked", "validated", "passed"}:
        return "ready"
    if state in {"blocked", "failed"}:
        return "blocked"
    if state in {"degraded", "source_link_warnings", "warning"}:
        return "degraded"
    if state in {"metadata_only", "draft", "planned"}:
        return "partial"
    return "unknown"


def _board_state(health_status, dependency_summary, validation_readiness, operational_status=None):
    health = str(health_status or "unknown").lower()
    dependency = str(dependency_summary or "unknown").lower()
    validation = str(validation_readiness or "unknown").lower()
    operational = str(operational_status or "unknown").lower()
    if health == "unavailable" or dependency == "unavailable":
        return "unavailable"
    if validation == "blocked" or health == "blocked" or operational == "blocked":
        return "blocked"
    if health == "degraded" or dependency == "degraded" or validation == "degraded":
        return "degraded"
    if health == "healthy" and dependency in {"healthy", "none_recorded"} and validation == "ready":
        return "healthy"
    return "degraded" if validation == "partial" else "unknown"


def _worst_state(states):
    if not states:
        return "unavailable"
    return max(states, key=lambda state: STATE_RANK.get(state, 1))


def generate_service_status_board(root=None, write=True):
    root = _root(root)
    catalog = generate_estate_service_catalog(root, write=False)
    matrix = generate_service_dependency_matrix(root, write=False)
    health = generate_service_health_registry(root, write=False)

    catalog_by_id = {svc.get("id"): svc for svc in catalog.get("services", [])}
    matrix_by_id = {row.get("service_id"): row for row in matrix.get("matrix", [])}
    health_by_id = {entry.get("service_id"): entry for entry in health.get("health_entries", [])}
    service_ids = sorted(set(catalog_by_id) | set(matrix_by_id) | set(health_by_id))

    services = []
    for sid in service_ids:
        svc = catalog_by_id.get(sid, {})
        dep = matrix_by_id.get(sid, {})
        entry = health_by_id.get(sid, {})
        dependency_health = entry.get("dependency_health") or {}
        validation = _validation_readiness(entry.get("validation_state") or svc.get("validation_status"))
        operational_status = entry.get("operational_status") or dep.get("operational_status") or svc.get("operational_status")
        state = _board_state(entry.get("health_status"), dependency_health.get("summary"), validation, operational_status)
        source_paths = sorted(set((svc.get("source_artifact_links") or []) + (dep.get("source_artifacts") or []) + [link.get("path") for link in entry.get("authoritative_sources", []) if link.get("path")]))
        services.append({
            "service_id": sid,
            "service_name": entry.get("service_name") or dep.get("service_name") or svc.get("name") or sid,
            "owner": entry.get("owner") or dep.get("owner") or svc.get("owner"),
            "resident": entry.get("resident") or svc.get("resident"),
            "board_state": state,
            "health_status": entry.get("health_status", "unknown"),
            "operational_status": operational_status,
            "readiness": validation,
            "validation_state": entry.get("validation_state") or svc.get("validation_status", "unknown"),
            "dependency_summary": dependency_health.get("summary", "unknown"),
            "dependencies": dependency_health.get("dependencies", []),
            "startup_sequence": dep.get("startup_sequence"),
            "failure_impact": dep.get("failure_impact"),
            "source_artifacts": [_source_link(root, path) for path in source_paths],
            "drill_down_links": {
                "catalog": SOURCE_ARTIFACTS["service_catalog"],
                "dependency_matrix": SOURCE_ARTIFACTS["service_dependency_matrix"],
                "health_registry": SOURCE_ARTIFACTS["service_health_registry"],
            },
            "metadata_warnings": (svc.get("metadata_warnings") or []) + (dep.get("metadata_warnings") or []) + (entry.get("metadata_warnings") or []),
        })

    counts = {state: sum(1 for service in services if service["board_state"] == state) for state in ("healthy", "degraded", "blocked", "unavailable", "unknown")}
    warnings = list(catalog.get("warnings", [])) + list(matrix.get("warnings", [])) + list(health.get("warnings", []))
    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "read_only_operations_center_view_not_source_of_truth",
        "refresh_behavior": "quiet_refresh_no_disruptive_redraws",
        "inputs": {
            "service_catalog": _source_link(root, SOURCE_ARTIFACTS["service_catalog"], generated_in_memory=True),
            "service_dependency_matrix": _source_link(root, SOURCE_ARTIFACTS["service_dependency_matrix"], generated_in_memory=True),
            "service_health_registry": _source_link(root, SOURCE_ARTIFACTS["service_health_registry"], generated_in_memory=True),
            "unavailable": sorted(set(catalog.get("inputs", {}).get("unavailable", []) + matrix.get("inputs", {}).get("unavailable", []) + health.get("inputs", {}).get("unavailable", []))),
        },
        "summary": {"service_count": len(services), "overall_state": _worst_state([s["board_state"] for s in services]), "warning_count": len(warnings), **counts},
        "services": services,
        "warnings": warnings,
        "operations_center_integration": {"status": "ready_for_operations_center_ui", "json_output": JSON_OUTPUT, "markdown_output": MARKDOWN_OUTPUT, "read_only": True},
    }
    if write:
        (root / "runtime/services").mkdir(parents=True, exist_ok=True)
        (root / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "operations/services").mkdir(parents=True, exist_ok=True)
        (root / MARKDOWN_OUTPUT).write_text(format_service_status_board(payload) + "\n", encoding="utf-8")
    return payload


def format_service_status_board(payload):
    s = payload.get("summary", {})
    lines = ["# Operations Center Service Status Board", "", "Read-only Operations Center view. This board aggregates existing artifacts and does not become the source of truth for service status.", "", f"Generated: {payload.get('generated_at')}", f"Refresh behavior: {payload.get('refresh_behavior')}", "", "## Summary", f"- Overall state: {s.get('overall_state')}", f"- Services: {s.get('service_count', 0)}", f"- Healthy: {s.get('healthy', 0)}", f"- Degraded: {s.get('degraded', 0)}", f"- Blocked: {s.get('blocked', 0)}", f"- Unavailable: {s.get('unavailable', 0)}", f"- Unknown: {s.get('unknown', 0)}", f"- Warnings: {s.get('warning_count', 0)}", "", "## Services"]
    for service in payload.get("services", []):
        lines += ["", f"### {service.get('service_name')} (`{service.get('service_id')}`)", f"- Board state: {service.get('board_state')}", f"- Health: {service.get('health_status')}", f"- Readiness: {service.get('readiness')}", f"- Validation: {service.get('validation_state')}", f"- Dependencies: {service.get('dependency_summary')}", f"- Startup sequence: {service.get('startup_sequence') or 'Not recorded'}", f"- Failure impact: {service.get('failure_impact') or 'Not recorded'}", f"- Source artifacts: {', '.join(link['path'] for link in service.get('source_artifacts', [])) or 'None recorded'}", f"- Drill-down: catalog `{service.get('drill_down_links', {}).get('catalog')}`, dependencies `{service.get('drill_down_links', {}).get('dependency_matrix')}`, health `{service.get('drill_down_links', {}).get('health_registry')}`"]
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        for warning in payload["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('path', '')} — {warning.get('message') or warning.get('service_name') or ''}")
    return "\n".join(lines)


def format_service_status_board_summary(payload):
    s = payload.get("summary", {})
    return "\n".join(["Operations Center Service Status Board", f"Generated: {payload.get('generated_at')}", f"Overall state: {s.get('overall_state')}", f"Services: {s.get('service_count', 0)}", f"Healthy: {s.get('healthy', 0)}", f"Degraded: {s.get('degraded', 0)}", f"Blocked: {s.get('blocked', 0)}", f"Unavailable: {s.get('unavailable', 0)}", f"Warnings: {s.get('warning_count', 0)}"])
