"""Capability gap reporting for architectural planning.

The report is a read-only comparison of planned, implemented, validated,
and operational capability evidence. It does not promote lifecycle state or
create work packages.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from estate.core.capability_dependency_visualization import generate_capability_dependency_visualization
from estate.core.estate_capability_registry import generate_estate_capability_registry
from estate.core.paths import ESTATE_ROOT


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_text(path):
    return path.read_text(encoding="utf-8")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_status(root, rel):
    return {"path": rel, "available": (root / rel).exists()}


def _load_json_if_available(root, rel, warnings):
    path = root / rel
    if not path.exists():
        return None
    try:
        return _read_json(path)
    except Exception as exc:
        warnings.append({"type": "malformed_input", "path": rel, "message": str(exc)})
        return None


def _extract_roadmap_capabilities(root):
    rel = "operations/boards/roadmap.md"
    path = root / rel
    planned = []
    if not path.exists():
        return planned
    for line in _read_text(path).splitlines():
        if not line.startswith("|") or line.startswith("|---") or "Capability" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[0]:
            planned.append({
                "name": cells[0],
                "current_milestone": cells[1],
                "status": cells[2],
                "key_dependency": cells[3],
                "future_initiative": cells[4],
                "source_artifact": rel,
            })
    return planned


def _extract_pending_capability_titles(root):
    pending_dir = root / "collaboration" / "work_packages" / "pending"
    items = []
    if not pending_dir.exists():
        return items
    for path in sorted(pending_dir.glob("WP-*_SERIES_*.md")):
        stem = path.stem
        match = re.match(r"(WP-\d+)_SERIES_(.+)", stem)
        if match:
            items.append({"work_package_id": match.group(1), "title": match.group(2).replace("_", " ").title(), "source_artifact": str(path.relative_to(root)).replace("\\", "/")})
    return items


def _name_key(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _has_implementation_evidence(cap):
    refs = [r for r in cap.get("source_artifact_links", []) if r not in {"data/registry/capabilities.json"}]
    state = str(cap.get("lifecycle_state") or "").lower()
    status = str(cap.get("implementation_status") or "").lower()
    return bool(refs) or state in {"implemented", "operationally validated", "institutionalized"} or status in {"installed", "operational"}


def _has_validation_evidence(cap):
    status = str(cap.get("validation_status") or "").lower()
    return status in {"evidence_found", "valid", "reviewed"}


def _is_planned(cap):
    state = str(cap.get("lifecycle_state") or "").lower()
    status = str(cap.get("implementation_status") or "").lower()
    maturity = str(cap.get("maturity") or "").lower()
    return state in {"designed", "planned"} or status.startswith("pending") or maturity == "planned"


def generate_capability_gap_report(root=None, write=True):
    """Generate a read-only Capability Gap Report payload."""
    root = _root(root)
    warnings = []
    registry = generate_estate_capability_registry(root, write=False)
    dependency_viz = generate_capability_dependency_visualization(root, write=False)
    readiness = _load_json_if_available(root, "runtime/readiness/operational_readiness_dashboard.json", warnings)
    validation_metrics = _load_json_if_available(root, "runtime/validation/validation_metrics_dashboard.json", warnings)
    if readiness is None and (root / "operations/readiness/operational_readiness_dashboard.md").exists():
        readiness = {"source": "operations/readiness/operational_readiness_dashboard.md", "status": "markdown_only", "degraded_subsystems": ["unavailable_subsystems"] if "Degraded Subsystems" in _read_text(root / "operations/readiness/operational_readiness_dashboard.md") else []}
    roadmap = _extract_roadmap_capabilities(root)
    pending = _extract_pending_capability_titles(root)
    caps = registry.get("capabilities", [])
    cap_keys = {_name_key(c.get("name")): c for c in caps}

    planned_only = []
    implemented_unvalidated = []
    operational = []
    degraded = []
    blocked = []
    future_candidates = []
    observations = []

    for cap in caps:
        deps = cap.get("dependencies") or []
        cap_summary = {"id": cap.get("id"), "name": cap.get("name"), "lifecycle_state": cap.get("lifecycle_state"), "implementation_status": cap.get("implementation_status"), "validation_status": cap.get("validation_status"), "source_artifacts": cap.get("source_artifact_links") or []}
        if _is_planned(cap) and not _has_implementation_evidence(cap):
            planned_only.append({**cap_summary, "gap": "planned_without_implementation_evidence"})
        if _has_implementation_evidence(cap) and not _has_validation_evidence(cap):
            implemented_unvalidated.append({**cap_summary, "gap": "implementation_without_validation_evidence"})
        if str(cap.get("implementation_status")).lower() == "operational" and _has_validation_evidence(cap):
            operational.append(cap_summary)
        if str(cap.get("implementation_status")).lower() in {"degraded", "blocked", "unavailable"}:
            degraded.append({**cap_summary, "status_source": "data/registry/capabilities.json"})
        if deps:
            missing = [d for d in deps if str(d) not in {c.get("id") for c in caps}]
            if missing:
                blocked.append({**cap_summary, "blocked_by": missing, "reason": "dependency_not_present_in_capability_registry"})

    for item in roadmap:
        if _name_key(item["name"]) not in cap_keys:
            planned_only.append({"name": item["name"], "gap": "roadmap_planned_without_capability_registry_record", "source_artifacts": [item["source_artifact"]], "roadmap_status": item["status"], "key_dependency": item["key_dependency"]})
            future_candidates.append({"candidate": item["name"], "reason": "roadmap capability has no capability registry record", "source_artifacts": [item["source_artifact"]]})
    for item in pending:
        if _name_key(item["title"]) not in cap_keys:
            future_candidates.append({"candidate": item["title"], "reason": "pending work package describes capability or capability-adjacent work", "source_artifacts": [item["source_artifact"]], "work_package_id": item["work_package_id"]})

    if readiness:
        status = readiness.get("overall_status") or readiness.get("overall_readiness_status") or readiness.get("status")
        degraded_items = readiness.get("degraded_subsystems") or readiness.get("degraded") or []
        blocking_items = readiness.get("blocking_issues") or []
        if status in {"blocked", "degraded", "markdown_only"} or degraded_items or blocking_items:
            degraded.append({"name": "Operational readiness", "status": status, "degraded_subsystems": degraded_items, "blocking_issues": blocking_items, "source_artifacts": [readiness.get("source", "runtime/readiness/operational_readiness_dashboard.json")]})

    for node in dependency_viz.get("nodes", []):
        warnings_for_node = node.get("warnings") or []
        if any(w.get("type") in {"external_reference", "unresolved_source_link"} for w in warnings_for_node):
            observations.append({"capability": node.get("label"), "observation": "dependency visualization includes unresolved or external references", "source_artifacts": node.get("source_artifact_links") or ["operations/capabilities/capability_dependency_visualization.md"]})

    missing_inputs = [_artifact_status(root, rel) for rel in [
        "data/registry/capabilities.json",
        "operations/capabilities/estate_capability_registry.md",
        "operations/capabilities/capability_dependency_visualization.md",
        "data/registry/missions.json",
        "operations/boards/roadmap.md",
        "operations/validation/validation_metrics_dashboard.md",
        "operations/readiness/operational_readiness_dashboard.md",
        "runtime/validation/validation_metrics_dashboard.json",
        "runtime/steward/mission_control_workspace.json",
    ]]
    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "read_only_gap_report_not_source_of_truth",
        "inputs": missing_inputs,
        "summary": {
            "capabilities_reviewed": len(caps),
            "planned_only_count": len(planned_only),
            "implemented_unvalidated_count": len(implemented_unvalidated),
            "operational_count": len(operational),
            "degraded_count": len(degraded),
            "dependency_blocked_count": len(blocked),
            "future_candidate_count": len(future_candidates),
            "missing_input_count": len([i for i in missing_inputs if not i["available"]]),
        },
        "planned_capabilities_without_implementation_evidence": planned_only,
        "implemented_capabilities_missing_validation_evidence": implemented_unvalidated,
        "operational_capabilities": operational,
        "operational_capabilities_with_degraded_status": degraded,
        "capabilities_blocked_by_dependencies": blocked,
        "future_work_package_candidates": future_candidates,
        "observations_not_confirmed_defects": observations,
        "confirmed_defects": [],
        "missing_data_states": [i for i in missing_inputs if not i["available"]],
        "warnings": warnings,
        "limitations": [
            "Planned items are not treated as implemented.",
            "Only explicit registry, roadmap, validation, readiness, and dependency artifacts are used.",
            "Observations are separated from confirmed defects and do not change capability status.",
        ],
    }
    if write:
        _write_json(root / "runtime" / "capabilities" / "capability_gap_report.json", payload)
        out = root / "operations" / "capabilities" / "capability_gap_report.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(format_capability_gap_report(payload) + "\n", encoding="utf-8")
    return payload


def _artifact_list(items):
    return ", ".join(f"`{item}`" for item in items) if items else "None recorded"


def format_capability_gap_report(payload):
    s = payload.get("summary", {})
    lines = [
        "# Capability Gap Report",
        "",
        "Read-only report for Mission Control and roadmap planning. This artifact is not a source of truth and does not change capability status.",
        "",
        f"Generated: {payload.get('generated_at')}",
        "",
        "## Summary",
    ]
    for key in ["capabilities_reviewed", "planned_only_count", "implemented_unvalidated_count", "operational_count", "degraded_count", "dependency_blocked_count", "future_candidate_count", "missing_input_count"]:
        lines.append(f"- {key.replace('_', ' ').title()}: {s.get(key, 0)}")
    sections = [
        ("Planned Capabilities Without Implementation Evidence", "planned_capabilities_without_implementation_evidence"),
        ("Implemented Capabilities Missing Validation Evidence", "implemented_capabilities_missing_validation_evidence"),
        ("Operational Capabilities", "operational_capabilities"),
        ("Operational Capabilities With Degraded Status", "operational_capabilities_with_degraded_status"),
        ("Capabilities Blocked By Dependencies", "capabilities_blocked_by_dependencies"),
        ("Future Work Package Candidates", "future_work_package_candidates"),
        ("Observations Not Confirmed Defects", "observations_not_confirmed_defects"),
        ("Confirmed Defects", "confirmed_defects"),
        ("Missing Data States", "missing_data_states"),
    ]
    for title, key in sections:
        lines += ["", f"## {title}"]
        items = payload.get(key) or []
        if not items:
            lines.append("- None found.")
            continue
        for item in items:
            name = item.get("name") or item.get("candidate") or item.get("capability") or item.get("path") or item.get("id")
            detail = item.get("gap") or item.get("reason") or item.get("observation") or item.get("status") or ("missing" if item.get("available") is False else "recorded")
            lines.append(f"- **{name}** — {detail}. Sources: {_artifact_list(item.get('source_artifacts') or ([item.get('path')] if item.get('path') else []))}")
    lines += ["", "## Limitations"]
    lines.extend(f"- {item}" for item in payload.get("limitations", []))
    return "\n".join(lines)


def format_capability_gap_summary(payload):
    s = payload.get("summary", {})
    return "Capability Gap Report: " + ", ".join(f"{k}={v}" for k, v in sorted(s.items()))
