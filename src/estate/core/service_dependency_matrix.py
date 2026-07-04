"""Service dependency matrix for explicit Estate service dependencies.

This module builds on the read-only Estate service catalog and records only
service-to-service dependencies that are explicitly declared in authoritative
source artifacts. It is an operational view, not a duplicate dependency registry.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.estate_service_catalog import generate_estate_service_catalog
from estate.core.paths import ESTATE_ROOT

SERVICE_REGISTRY = "data/registry/services.json"
PROVIDER_REGISTRY = "data/registry/providers.json"
JSON_OUTPUT = "runtime/services/service_dependency_matrix.json"
MARKDOWN_OUTPUT = "operations/services/service_dependency_matrix.md"
DEPENDENCY_FIELDS = ("dependencies", "depends_on", "required_services")


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(root, rel, warnings):
    path = root / rel
    if not path.exists():
        warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional source artifact is unavailable."})
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": rel, "message": str(exc)})
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("services", "providers", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    warnings.append({"type": "unexpected_schema", "path": rel, "message": "Expected a list or an object containing services/providers/items."})
    return []


def _as_refs(value):
    if value is None:
        return []
    if isinstance(value, (str, int, float, dict)):
        value = [value]
    if not isinstance(value, list):
        return []
    refs = []
    for item in value:
        if isinstance(item, dict):
            ref = item.get("id") or item.get("service_id") or item.get("name") or item.get("ref")
        else:
            ref = item
        if ref is not None and str(ref).strip():
            refs.append(str(ref).strip())
    return refs


def _topological_order(service_ids, dependencies):
    remaining = {sid: set(dependencies.get(sid, [])) & set(service_ids) for sid in service_ids}
    order = []
    while remaining:
        ready = sorted(sid for sid, deps in remaining.items() if not deps)
        if not ready:
            order.extend(sorted(remaining))
            break
        order.extend(ready)
        for sid in ready:
            del remaining[sid]
        for deps in remaining.values():
            deps.difference_update(ready)
    return order


def generate_service_dependency_matrix(root=None, write=True):
    root = _root(root)
    warnings = []
    catalog = generate_estate_service_catalog(root, write=False)
    registry_services = _read_json(root, SERVICE_REGISTRY, warnings)
    providers = _read_json(root, PROVIDER_REGISTRY, warnings)

    catalog_by_id = {svc["id"]: svc for svc in catalog.get("services", [])}
    service_names = {svc["id"]: svc.get("name", svc["id"]) for svc in catalog.get("services", [])}
    service_ids_by_token = {sid.lower(): sid for sid in catalog_by_id}
    service_ids_by_token.update({name.lower(): sid for sid, name in service_names.items()})

    explicit_dependencies = {sid: [] for sid in catalog_by_id}
    dependency_sources = {sid: [] for sid in catalog_by_id}
    for svc in registry_services:
        sid = svc.get("id") or svc.get("name")
        if sid not in catalog_by_id:
            continue
        found = False
        for field in DEPENDENCY_FIELDS:
            for dep in _as_refs(svc.get(field)):
                found = True
                explicit_dependencies[sid].append(dep)
                dependency_sources[sid].append({"field": field, "target": dep, "source_artifact": SERVICE_REGISTRY})
                if dep.lower() not in service_ids_by_token:
                    warnings.append({"type": "unresolved_service_dependency", "service_id": sid, "target": dep, "path": SERVICE_REGISTRY, "message": f"{sid} declares dependency {dep}, but no matching catalog service id or name was found."})
        if not found:
            warnings.append({"type": "incomplete_dependency_metadata", "service_id": sid, "path": SERVICE_REGISTRY, "message": f"{sid} has no explicit service dependency metadata."})

    providers_by_service = {sid: [] for sid in catalog_by_id}
    for provider in providers:
        token = str(provider.get("service") or provider.get("service_id") or "").strip().lower()
        sid = service_ids_by_token.get(token)
        if sid:
            providers_by_service[sid].append({"id": provider.get("id"), "name": provider.get("name"), "status": provider.get("status"), "source_artifact": PROVIDER_REGISTRY})
        elif token:
            warnings.append({"type": "unmatched_provider_service", "provider_id": provider.get("id"), "service": provider.get("service"), "path": PROVIDER_REGISTRY, "message": "Provider service field does not exactly match a catalog service id or name; not attached to the matrix."})

    resolved_deps = {
        sid: [service_ids_by_token[d.lower()] for d in deps if d.lower() in service_ids_by_token]
        for sid, deps in explicit_dependencies.items()
    }
    dependents = {sid: [] for sid in catalog_by_id}
    for sid, deps in resolved_deps.items():
        for dep in deps:
            dependents.setdefault(dep, []).append(sid)
    startup_order_ids = _topological_order(list(catalog_by_id), resolved_deps)

    rows = []
    for sid in startup_order_ids:
        svc = catalog_by_id[sid]
        rows.append({
            "service_id": sid,
            "service_name": svc.get("name"),
            "owner": svc.get("owner"),
            "operational_status": svc.get("operational_status"),
            "required_services": explicit_dependencies.get(sid, []),
            "required_providers": providers_by_service.get(sid, []),
            "optional_integrations": [],
            "startup_after": resolved_deps.get(sid, []),
            "startup_sequence": startup_order_ids.index(sid) + 1,
            "failure_impact": "Impacts explicit dependents: " + ", ".join(sorted(dependents.get(sid, []))) if dependents.get(sid) else "No explicit downstream dependents recorded.",
            "source_artifacts": sorted(set(svc.get("source_artifact_links", []) + [s["source_artifact"] for s in dependency_sources.get(sid, [])])),
            "metadata_warnings": [w for w in warnings if w.get("service_id") == sid],
        })

    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "read_only_aggregation_not_dependency_registry",
        "inputs": {"service_catalog": "generated in memory", "used": [SERVICE_REGISTRY, PROVIDER_REGISTRY], "unavailable": catalog.get("inputs", {}).get("unavailable", [])},
        "summary": {"service_count": len(rows), "explicit_dependency_count": sum(len(v) for v in explicit_dependencies.values()), "startup_steps": len(startup_order_ids), "warning_count": len(warnings) + len(catalog.get("warnings", []))},
        "startup_order": [{"sequence": i + 1, "service_id": sid, "service_name": service_names.get(sid)} for i, sid in enumerate(startup_order_ids)],
        "matrix": rows,
        "warnings": catalog.get("warnings", []) + warnings,
        "operations_center_integration": {"status": "supported_by_json_and_markdown_outputs", "json_output": JSON_OUTPUT, "markdown_output": MARKDOWN_OUTPUT},
    }
    if write:
        (root / "runtime/services").mkdir(parents=True, exist_ok=True)
        (root / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "operations/services").mkdir(parents=True, exist_ok=True)
        (root / MARKDOWN_OUTPUT).write_text(format_service_dependency_matrix(payload) + "\n", encoding="utf-8")
    return payload


def format_service_dependency_matrix(payload):
    s = payload.get("summary", {})
    lines = [
        "# Estate Service Dependency Matrix",
        "",
        "Read-only operational view. This document does not create a duplicate dependency registry and records only explicit source-backed service dependencies.",
        "",
        f"Generated: {payload.get('generated_at')}",
        "",
        "## Summary",
        f"- Services: {s.get('service_count', 0)}",
        f"- Explicit service dependencies: {s.get('explicit_dependency_count', 0)}",
        f"- Startup steps: {s.get('startup_steps', 0)}",
        f"- Warnings: {s.get('warning_count', 0)}",
        "",
        "## Startup order",
    ]
    for step in payload.get("startup_order", []):
        lines.append(f"{step['sequence']}. `{step['service_id']}` — {step.get('service_name')}")
    lines.extend(["", "## Matrix"])
    for row in payload.get("matrix", []):
        providers = row.get("required_providers") or []
        lines += [
            "",
            f"### {row.get('service_name')} (`{row.get('service_id')}`)",
            f"- Owner: {row.get('owner')}",
            f"- Operational status: {row.get('operational_status')}",
            f"- Required services: {', '.join(row.get('required_services') or []) or 'None explicitly recorded'}",
            f"- Required providers: {', '.join(p.get('name') or p.get('id') or 'unnamed' for p in providers) or 'None explicitly matched'}",
            f"- Optional integrations: {', '.join(row.get('optional_integrations') or []) or 'None explicitly recorded'}",
            f"- Startup after: {', '.join(row.get('startup_after') or []) or 'No explicit startup prerequisite'}",
            f"- Failure impact: {row.get('failure_impact')}",
            f"- Source artifacts: {', '.join(row.get('source_artifacts') or []) or 'None recorded'}",
        ]
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        for warning in payload["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('path', '')} — {warning.get('message') or warning.get('service') or ''}")
    return "\n".join(lines)


def format_service_dependency_matrix_summary(payload):
    s = payload.get("summary", {})
    return "\n".join(["Estate Service Dependency Matrix", f"Generated: {payload.get('generated_at')}", f"Services: {s.get('service_count', 0)}", f"Explicit dependencies: {s.get('explicit_dependency_count', 0)}", f"Warnings: {s.get('warning_count', 0)}"])
