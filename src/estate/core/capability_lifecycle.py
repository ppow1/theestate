"""Capability lifecycle validation and operational reporting for The Estate.

This module validates existing capability registry entries against the official
Estate lifecycle states. It does not define new maturity states or governance
meaning; it only reports registry and evidence consistency.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

VALID_LIFECYCLE_STATES = [
    "Designed",
    "Implemented",
    "Operationally Validated",
    "Institutionalized",
]

OPTIONAL_INPUTS = [
    "data/registry/capabilities.json",
    "data/registry/services.json",
    "docs/governance/Capability_Lifecycle_States_v1.md",
    "runtime/operations/operations_board.json",
    "runtime/audit/latest.json",
]

GLOB_INPUTS = [
    "collaboration/audit/results/*.json",
    "docs/collaboration/*.md",
]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


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
        for key in ("capabilities", "items", "results", "services"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _first_value(item, keys):
    for key in keys:
        value = item.get(key)
        if value not in (None, "", []):
            return value
    return None


def _as_refs(value):
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _capability_id(item, index):
    return _first_value(item, ("id", "capability_id", "capabilityId", "identifier")) or f"unidentified-{index}"


def _validate_capability(item, index):
    warnings = []
    if not isinstance(item, dict):
        return {
            "id": f"malformed-{index}",
            "title": None,
            "lifecycle_state": None,
            "valid_lifecycle_state": False,
            "owner": None,
            "implementation_references": [],
            "evidence_references": [],
            "operational_evidence_references": [],
            "institutionalization_references": [],
            "warnings": [{"type": "malformed_capability", "message": "Capability entry is not an object."}],
        }

    cap_id = _capability_id(item, index)
    title = _first_value(item, ("title", "name", "display_name"))
    lifecycle = _first_value(item, ("lifecycle_state", "lifecycle", "maturity", "state"))
    owner = _first_value(item, ("owner", "responsible_office", "office", "responsible"))
    implementation_refs = _as_refs(_first_value(item, ("implementation_references", "implementation_refs", "implementation", "location", "root")))
    evidence_refs = _as_refs(_first_value(item, ("evidence_references", "evidence_refs", "evidence", "documentation")))
    operational_refs = _as_refs(_first_value(item, ("operational_evidence_references", "operational_evidence", "validation_evidence")))
    institutional_refs = _as_refs(_first_value(item, ("institutionalization_references", "institutional_reference", "institutionalization_reference", "sop_reference")))

    if not cap_id or str(cap_id).startswith("unidentified-"):
        warnings.append({"type": "missing_identifier", "message": "Capability is missing a stable identifier."})
    if not title:
        warnings.append({"type": "missing_title", "message": f"Capability {cap_id} is missing a title or name."})
    if not lifecycle:
        warnings.append({"type": "missing_lifecycle_state", "message": f"Capability {cap_id} is missing lifecycle state."})
    elif lifecycle not in VALID_LIFECYCLE_STATES:
        warnings.append({"type": "invalid_lifecycle_state", "message": f"Capability {cap_id} uses invalid lifecycle state: {lifecycle}."})

    valid_lifecycle = lifecycle in VALID_LIFECYCLE_STATES
    if valid_lifecycle and VALID_LIFECYCLE_STATES.index(lifecycle) > 0 and not evidence_refs:
        warnings.append({"type": "missing_evidence", "message": f"Capability {cap_id} claims maturity above Designed without evidence references."})
    if valid_lifecycle and VALID_LIFECYCLE_STATES.index(lifecycle) >= 1 and not implementation_refs:
        warnings.append({"type": "missing_implementation_reference", "message": f"Capability {cap_id} is Implemented or higher without implementation references."})
    if valid_lifecycle and VALID_LIFECYCLE_STATES.index(lifecycle) >= 2 and not operational_refs:
        warnings.append({"type": "missing_operational_evidence", "message": f"Capability {cap_id} is Operationally Validated or higher without operational evidence."})
    if lifecycle == "Institutionalized" and not institutional_refs:
        warnings.append({"type": "missing_institutional_reference", "message": f"Capability {cap_id} is Institutionalized without an institutional reference."})

    return {
        "id": cap_id,
        "title": title,
        "lifecycle_state": lifecycle,
        "valid_lifecycle_state": valid_lifecycle,
        "owner": owner,
        "implementation_references": implementation_refs,
        "evidence_references": evidence_refs,
        "operational_evidence_references": operational_refs,
        "institutionalization_references": institutional_refs,
        "warnings": warnings,
    }


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_capability_lifecycle_report(root=None, write=True):
    root = estate_root(root)
    report_warnings = []
    inputs = {"used": [], "unavailable": []}
    artifacts = {}

    for rel in OPTIONAL_INPUTS:
        path = root / rel
        if path.exists():
            if path.suffix == ".json":
                data = _read_json(path, root, report_warnings)
                if data is not None:
                    artifacts[rel] = data
                    inputs["used"].append(rel)
            else:
                inputs["used"].append(rel)
        else:
            inputs["unavailable"].append(rel)
            report_warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional input artifact is unavailable."})

    for pattern in GLOB_INPUTS:
        found = sorted(root.glob(pattern))
        if not found:
            inputs["unavailable"].append(pattern)
            report_warnings.append({"type": "missing_optional_artifact", "path": pattern, "message": "Optional input artifact is unavailable."})
        else:
            inputs["used"].extend(_rel(p, root) for p in found)

    raw_caps = _as_list(artifacts.get("data/registry/capabilities.json"))
    capabilities = [_validate_capability(item, i + 1) for i, item in enumerate(raw_caps)]
    cap_warnings = [w for cap in capabilities for w in cap["warnings"]]
    all_warnings = report_warnings + cap_warnings
    counts = Counter(cap.get("lifecycle_state") or "Missing" for cap in capabilities)

    def ids_with_warning(kind):
        return [cap["id"] for cap in capabilities if any(w["type"] == kind for w in cap["warnings"])]

    candidates = {
        "missing_lifecycle_state": ids_with_warning("missing_lifecycle_state"),
        "invalid_lifecycle_state": ids_with_warning("invalid_lifecycle_state"),
        "implemented_but_missing_evidence": ids_with_warning("missing_evidence"),
        "operational_validation_candidates": [cap["id"] for cap in capabilities if cap["lifecycle_state"] == "Implemented" and not any(w["type"] in ("missing_evidence", "missing_implementation_reference") for w in cap["warnings"])],
        "institutionalization_review_candidates": [cap["id"] for cap in capabilities if cap["lifecycle_state"] == "Operationally Validated" and cap["operational_evidence_references"]],
    }
    report = {
        "version": 1,
        "generated_at": _now(),
        "summary": {
            "capability_count": len(capabilities),
            "counts_by_lifecycle_state": dict(sorted(counts.items())),
            "invalid_lifecycle_state_count": len(candidates["invalid_lifecycle_state"]),
            "missing_evidence_count": len(ids_with_warning("missing_evidence")),
            "warning_count": len(all_warnings),
        },
        "capabilities": capabilities,
        "candidates": candidates,
        "inputs": inputs,
        "warnings": all_warnings,
    }
    if write:
        _write_json(root / "runtime" / "capabilities" / "capability_lifecycle_report.json", report)
        md_path = root / "operations" / "capabilities" / "lifecycle_status.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(format_capability_lifecycle_markdown(report) + "\n", encoding="utf-8")
    return report


def format_capability_lifecycle_summary(report):
    s = report.get("summary", {})
    return "\n".join([
        "Estate Capability Lifecycle Status",
        f"Generated: {report.get('generated_at')}",
        f"Capabilities: {s.get('capability_count', 0)}",
        f"Invalid lifecycle states: {s.get('invalid_lifecycle_state_count', 0)}",
        f"Missing evidence: {s.get('missing_evidence_count', 0)}",
        f"Warnings: {s.get('warning_count', 0)}",
    ])


def _md_list(items):
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def format_capability_lifecycle_markdown(report):
    s = report.get("summary", {})
    c = report.get("candidates", {})
    lines = [
        "# Estate Capability Lifecycle Status",
        "",
        f"Generated: {report.get('generated_at')}",
        "",
        "This is an operational report generated from registries and evidence. It is not a governance source of truth.",
        "",
        "## Summary",
        f"- Capability count: {s.get('capability_count', 0)}",
        f"- Invalid lifecycle state count: {s.get('invalid_lifecycle_state_count', 0)}",
        f"- Missing evidence count: {s.get('missing_evidence_count', 0)}",
        f"- Warning count: {s.get('warning_count', 0)}",
        "",
        "## Lifecycle Counts",
    ]
    for state, count in s.get("counts_by_lifecycle_state", {}).items():
        lines.append(f"- {state}: {count}")
    lines += [
        "",
        "## Capabilities Missing Lifecycle State",
        _md_list(c.get("missing_lifecycle_state", [])),
        "",
        "## Invalid Lifecycle States",
        _md_list(c.get("invalid_lifecycle_state", [])),
        "",
        "## Operational Validation Candidates",
        _md_list(c.get("operational_validation_candidates", [])),
        "",
        "## Institutionalization Review Candidates",
        _md_list(c.get("institutionalization_review_candidates", [])),
        "",
        "## Warnings",
    ]
    warnings = report.get("warnings", [])
    lines.extend(f"- {w.get('type')}: {w.get('path', '')} {w.get('message', '')}".rstrip() for w in warnings) if warnings else lines.append("- None")
    return "\n".join(lines)
