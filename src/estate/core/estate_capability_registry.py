"""Read-only Estate capability registry aggregation.

The registry in this module is a derived operational inventory. It reads
existing Estate artifacts and reports capability metadata without becoming the
authoritative source of truth for any capability.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

INPUT_ARTIFACTS = [
    "data/registry/capabilities.json",
    "data/registry/providers.json",
    "data/registry/services.json",
    "runtime/capabilities/capability_lifecycle_report.json",
    "runtime/validation/operational_validation_report.json",
    "runtime/operations/operations_board.json",
    "docs/operations/Capability_Lifecycle_Reporting.md",
    "docs/operations/Operational_Validation_Reporting.md",
    "docs/operations/Mission_Control_Workspace_v1.md",
    "docs/operations/Operations_Board_Runtime_Integration.md",
    "workers/audit/audit_result_schema.md",
]

Maturity = {"Designed": "planned", "Implemented": "partial", "Operationally Validated": "operational", "Institutionalized": "operational"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path, root, warnings):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": _rel(path, root), "message": str(exc)})
        return None


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("capabilities", "providers", "services", "items", "results"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _first(item, keys, default=None):
    for key in keys:
        value = item.get(key)
        if value not in (None, "", []):
            return value
    return default


def _list(value):
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _status_from_validation(capability_id, lifecycle_by_id, operational_by_id):
    cap = lifecycle_by_id.get(capability_id, {})
    warnings = cap.get("warnings") or []
    if cap:
        if cap.get("valid_lifecycle_state") and not warnings:
            return {"status": "valid", "source": "runtime/capabilities/capability_lifecycle_report.json", "warnings": []}
        return {"status": "warnings", "source": "runtime/capabilities/capability_lifecycle_report.json", "warnings": warnings}

    operational = operational_by_id.get(capability_id, {})
    if operational:
        gaps = operational.get("evidence_gaps") or []
        if gaps:
            return {"status": "evidence_gaps", "source": "runtime/validation/operational_validation_report.json", "warnings": gaps}
        if operational.get("validation_evidence_found"):
            return {"status": "evidence_found", "source": "runtime/validation/operational_validation_report.json", "warnings": []}
        return {"status": "reviewed", "source": "runtime/validation/operational_validation_report.json", "warnings": []}

    return {"status": "unknown", "source": None, "warnings": []}


def generate_estate_capability_registry(root=None, write=True):
    """Generate a read-only, derived inventory of Estate capabilities."""
    root = _root(root)
    warnings = []
    inputs = {"used": [], "unavailable": []}
    artifacts = {}
    for rel in INPUT_ARTIFACTS:
        path = root / rel
        if path.exists():
            inputs["used"].append(rel)
            if path.suffix == ".json":
                artifacts[rel] = _read_json(path, root, warnings)
        else:
            inputs["unavailable"].append(rel)

    capabilities_raw = _as_list(artifacts.get("data/registry/capabilities.json"))
    providers = _as_list(artifacts.get("data/registry/providers.json"))
    services = _as_list(artifacts.get("data/registry/services.json"))
    lifecycle_caps = _as_list(artifacts.get("runtime/capabilities/capability_lifecycle_report.json"))
    lifecycle_by_id = {c.get("id"): c for c in lifecycle_caps if isinstance(c, dict)}
    operational_report = artifacts.get("runtime/validation/operational_validation_report.json")
    operational_caps = _as_list(
        operational_report.get("capabilities_reviewed")
        if isinstance(operational_report, dict)
        else operational_report
    )
    operational_by_id = {c.get("id"): c for c in operational_caps if isinstance(c, dict)}
    providers_by_cap = defaultdict(list)
    for provider in providers:
        if isinstance(provider, dict):
            providers_by_cap[provider.get("capability")].append(provider)
    services_by_id = {svc.get("id"): svc for svc in services if isinstance(svc, dict)}
    services_by_name = {svc.get("name"): svc for svc in services if isinstance(svc, dict)}

    capabilities = []
    for index, raw in enumerate(capabilities_raw, 1):
        if not isinstance(raw, dict):
            cap_id = f"malformed-{index}"
            warnings.append({"type": "malformed_capability", "id": cap_id, "message": "Capability entry is not an object."})
            continue
        cap_id = _first(raw, ("id", "capability_id", "identifier"), f"unidentified-{index}")
        lifecycle_state = _first(raw, ("lifecycle_state", "lifecycle", "state"))
        maturity = Maturity.get(lifecycle_state, "planned" if str(_first(raw, ("status",), "")).lower().startswith("pending") else "partial")
        service_refs = _list(_first(raw, ("related_services", "services", "service")))
        owning_subsystem = _first(raw, ("owner", "owning_subsystem", "subsystem", "category"), "Unknown")
        service_records = []
        for ref in service_refs:
            service_records.append(services_by_id.get(ref) or services_by_name.get(ref) or {"id": ref, "name": ref, "status": "unknown"})
        provider_records = [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "service": p.get("service"),
                "status": p.get("status", "unknown"),
                "location": p.get("location"),
                "source_artifact": "data/registry/providers.json",
            }
            for p in providers_by_cap.get(cap_id, [])
        ]
        validation = _status_from_validation(cap_id, lifecycle_by_id, operational_by_id)
        source_links = []
        for src in ["data/registry/capabilities.json"] + _list(_first(raw, ("implementation_references", "implementation", "root", "location"))) + _list(_first(raw, ("evidence_references", "evidence", "documentation"))):
            if src and src not in source_links:
                source_links.append(src)
        if validation["source"] and validation["source"] not in source_links:
            source_links.append(validation["source"])
        cap_warnings = []
        for key in ("name", "owner", "status", "lifecycle_state"):
            if not raw.get(key):
                cap_warnings.append({"type": f"missing_{key}", "message": f"Capability {cap_id} is missing {key}."})
        capabilities.append({
            "id": cap_id,
            "name": _first(raw, ("name", "title", "display_name"), cap_id),
            "owning_subsystem": owning_subsystem,
            "implementation_status": _first(raw, ("status", "implementation_status"), "unknown"),
            "maturity": maturity,
            "lifecycle_state": lifecycle_state,
            "dependencies": _list(raw.get("dependencies")),
            "providers": provider_records,
            "services": service_records,
            "validation_status": validation["status"],
            "validation_warnings": validation["warnings"],
            "source_artifact_links": source_links,
            "metadata_warnings": cap_warnings,
        })
        warnings.extend({"id": cap_id, **w} for w in cap_warnings)

    provider_orphans = [p.get("id") for p in providers if isinstance(p, dict) and p.get("capability") not in {c["id"] for c in capabilities}]
    if provider_orphans:
        warnings.append({"type": "provider_without_capability_record", "provider_ids": provider_orphans, "message": "Providers reference capabilities not present in data/registry/capabilities.json."})
    counts = Counter(c["maturity"] for c in capabilities)
    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "read_only_aggregation_not_source_of_truth",
        "summary": {"capability_count": len(capabilities), "provider_count": len(providers), "service_count": len(services), "counts_by_maturity": dict(sorted(counts.items())), "warning_count": len(warnings)},
        "capabilities": capabilities,
        "inputs": inputs,
        "warnings": warnings,
    }
    if write:
        out = root / "runtime" / "capabilities" / "estate_capability_registry.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md = root / "operations" / "capabilities" / "estate_capability_registry.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(format_estate_capability_registry(payload) + "\n", encoding="utf-8")
    return payload


def format_estate_capability_registry(payload):
    lines = ["# Estate Capability Registry", "", f"Generated: {payload.get('generated_at')}", "", "Read-only aggregation. This report is not the source of truth.", "", "## Summary"]
    s = payload.get("summary", {})
    lines += [f"- Capabilities: {s.get('capability_count', 0)}", f"- Providers: {s.get('provider_count', 0)}", f"- Services: {s.get('service_count', 0)}", f"- Warnings: {s.get('warning_count', 0)}", "", "## Capabilities"]
    for cap in payload.get("capabilities", []):
        lines += ["", f"### {cap.get('name')} ({cap.get('id')})", f"- Owning subsystem: {cap.get('owning_subsystem')}", f"- Implementation status: {cap.get('implementation_status')}", f"- Maturity: {cap.get('maturity')}", f"- Dependencies: {', '.join(map(str, cap.get('dependencies') or [])) or 'None'}", f"- Validation status: {cap.get('validation_status')}", f"- Providers: {', '.join(p.get('name') or p.get('id') for p in cap.get('providers', [])) or 'None'}", f"- Source artifacts: {', '.join(map(str, cap.get('source_artifact_links') or [])) or 'None'}"]
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        lines.extend(f"- {w.get('type')}: {w.get('message', '')}" for w in payload["warnings"])
    return "\n".join(lines)


def format_estate_capability_registry_summary(payload):
    s = payload.get("summary", {})
    return "\n".join(["Estate Capability Registry", f"Generated: {payload.get('generated_at')}", f"Capabilities: {s.get('capability_count', 0)}", f"Providers: {s.get('provider_count', 0)}", f"Warnings: {s.get('warning_count', 0)}"])
