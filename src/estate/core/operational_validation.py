"""Continuous operational validation reporting for The Estate.

This module reports evidence and evidence gaps for capability maturity review.
It does not change lifecycle state, create lifecycle states, or make governance
promotion decisions.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

INPUTS = [
    "runtime/capabilities/capability_lifecycle_report.json",
    "runtime/operations/operations_board.json",
    "runtime/audit/latest.json",
    "runtime/collaboration/events/events.jsonl",
    "collaboration/status/worker_inbox_summary.json",
]
GLOBS = ["collaboration/audit/results/*.json", "operations/**/*.md"]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _warn(warnings, kind, path, message):
    warnings.append({"type": kind, "path": path, "message": message})


def _read_json(path, root, warnings):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _warn(warnings, "malformed_input", _rel(path, root), str(exc))
        return None


def _read_jsonl(path, root, warnings):
    rows = []
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception as exc:
                _warn(warnings, "malformed_input", f"{_rel(path, root)}:{lineno}", str(exc))
    except Exception as exc:
        _warn(warnings, "malformed_input", _rel(path, root), str(exc))
    return rows


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("capabilities", "items", "results", "events", "workers"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _capabilities_from_lifecycle(payload):
    caps = []
    for item in _as_list(payload):
        if not isinstance(item, dict):
            continue
        caps.append({
            "id": item.get("id") or item.get("capability_id") or item.get("name"),
            "name": item.get("title") or item.get("name") or item.get("id"),
            "lifecycle_state": item.get("lifecycle_state"),
            "implementation_references": item.get("implementation_references", []) or [],
            "evidence_references": item.get("evidence_references", []) or [],
            "operational_evidence_references": item.get("operational_evidence_references", []) or [],
            "institutionalization_references": item.get("institutionalization_references", []) or [],
        })
    return caps


def _contains_capability(obj, cap):
    text = json.dumps(obj, sort_keys=True, default=str).lower() if not isinstance(obj, str) else obj.lower()
    needles = [str(cap.get("id") or "").lower(), str(cap.get("name") or "").lower()]
    return any(n and n in text for n in needles)


def _evidence_for(cap, artifacts):
    evidence = []
    for ref in cap.get("implementation_references", []):
        evidence.append({"type": "implementation_reference", "source": str(ref)})
    for ref in cap.get("evidence_references", []):
        evidence.append({"type": "evidence_reference", "source": str(ref)})
    for ref in cap.get("operational_evidence_references", []):
        evidence.append({"type": "operational_evidence_reference", "source": str(ref)})
    for rel, data in artifacts.items():
        if rel == "operations/**/*.md":
            for md in data:
                if _contains_capability(md, cap):
                    evidence.append({"type": "operations_markdown", "source": md["path"]})
        elif rel == "runtime/capabilities/capability_lifecycle_report.json":
            continue
        elif _contains_capability(data, cap):
            kind = "audit" if "audit" in rel else "runtime"
            evidence.append({"type": kind, "source": rel})
    # De-duplicate while preserving order.
    seen = set(); out = []
    for item in evidence:
        key = (item["type"], item["source"])
        if key not in seen:
            seen.add(key); out.append(item)
    return out


def _gaps(cap, evidence):
    kinds = {e["type"] for e in evidence}
    gaps = []
    if "implementation_reference" not in kinds:
        gaps.append("implementation_reference")
    if not ({"evidence_reference", "audit", "runtime", "operations_markdown"} & kinds):
        gaps.append("validation_evidence")
    if "operational_evidence_reference" not in kinds and cap.get("lifecycle_state") in ("Operationally Validated", "Institutionalized"):
        gaps.append("operational_evidence_reference")
    if cap.get("lifecycle_state") == "Institutionalized" and not cap.get("institutionalization_references"):
        gaps.append("institutionalization_reference")
    return gaps


def generate_operational_validation_report(root=None, write=True):
    root = estate_root(root)
    warnings = []
    missing = []
    inputs = {"used": [], "missing": []}
    artifacts = {}

    for rel in INPUTS:
        path = root / rel
        if not path.exists():
            missing.append(rel); inputs["missing"].append(rel)
            _warn(warnings, "missing_input", rel, "Input artifact is unavailable.")
            continue
        inputs["used"].append(rel)
        artifacts[rel] = _read_jsonl(path, root, warnings) if path.suffix == ".jsonl" else _read_json(path, root, warnings)

    for pattern in GLOBS:
        found = sorted(root.glob(pattern))
        if not found:
            missing.append(pattern); inputs["missing"].append(pattern)
            _warn(warnings, "missing_input", pattern, "Input artifact is unavailable.")
            continue
        inputs["used"].extend(_rel(p, root) for p in found)
        if pattern.endswith("*.json"):
            artifacts[pattern] = [d for p in found for d in [_read_json(p, root, warnings)] if d is not None]
        else:
            generated_md = "operations/validation/operational_validation_report.md"
            artifacts[pattern] = [
                {"path": _rel(p, root), "text": p.read_text(encoding="utf-8", errors="replace")}
                for p in found
                if _rel(p, root) != generated_md
            ]

    capabilities = _capabilities_from_lifecycle(artifacts.get("runtime/capabilities/capability_lifecycle_report.json"))
    reviewed = []
    ov_candidates = []
    inst_candidates = []
    for cap in capabilities:
        evidence = _evidence_for(cap, artifacts)
        gaps = _gaps(cap, evidence)
        row = {**cap, "validation_evidence_found": evidence, "evidence_gaps": gaps}
        reviewed.append(row)
        if cap.get("lifecycle_state") == "Implemented" and not gaps:
            ov_candidates.append({"id": cap.get("id"), "name": cap.get("name"), "basis": "Implemented capability with implementation and validation evidence found."})
        if cap.get("lifecycle_state") == "Operationally Validated" and evidence and "validation_evidence" not in gaps:
            inst_candidates.append({"id": cap.get("id"), "name": cap.get("name"), "basis": "Operationally Validated capability with continuing operational evidence found; governance review still required."})

    report = {
        "version": 1,
        "generated_at": _now(),
        "purpose": "Report evidence for capability maturity review without changing lifecycle state.",
        "capabilities_reviewed": reviewed,
        "validation_evidence_found": [e for cap in reviewed for e in cap["validation_evidence_found"]],
        "evidence_gaps": [{"id": cap.get("id"), "name": cap.get("name"), "gaps": cap["evidence_gaps"]} for cap in reviewed if cap["evidence_gaps"]],
        "candidates_for_operationally_validated_review": ov_candidates,
        "candidates_for_institutionalized_review": inst_candidates,
        "warnings": warnings,
        "missing_inputs": missing,
        "inputs": inputs,
        "limitations": ["This report does not promote capabilities or alter lifecycle state.", "Lifecycle promotion remains a governance/review decision."],
    }
    if write:
        _write_json(root / "runtime/validation/operational_validation_report.json", report)
        md = root / "operations/validation/operational_validation_report.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(format_operational_validation_markdown(report) + "\n", encoding="utf-8")
    return report


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _md_list(items, empty="- None"):
    return "\n".join(f"- {item}" for item in items) if items else empty


def format_operational_validation_summary(report):
    return "\n".join([
        "Estate Operational Validation Report",
        f"Generated: {report.get('generated_at')}",
        f"Capabilities reviewed: {len(report.get('capabilities_reviewed', []))}",
        f"Operationally Validated review candidates: {len(report.get('candidates_for_operationally_validated_review', []))}",
        f"Institutionalized review candidates: {len(report.get('candidates_for_institutionalized_review', []))}",
        f"Evidence gaps: {len(report.get('evidence_gaps', []))}",
        f"Warnings: {len(report.get('warnings', []))}",
    ])


def format_operational_validation_markdown(report):
    lines = [
        "# Continuous Operational Validation Report", "",
        f"Generated: {report.get('generated_at')}", "",
        "## Purpose", report.get("purpose", ""), "",
        "## Inputs", _md_list(report.get("inputs", {}).get("used", [])), "",
        "## Outputs", "- runtime/validation/operational_validation_report.json", "- operations/validation/operational_validation_report.md", "",
        "## Evidence Rules", "- Implementation references count as implementation evidence.", "- Lifecycle evidence references, audit artifacts, runtime artifacts, collaboration events, worker inbox summaries, and operations Markdown mentions count as validation evidence when they identify the capability.", "- Operational evidence references are required before an already Operationally Validated or Institutionalized claim is considered complete.", "- This report only identifies review candidates; it never changes lifecycle state.", "",
        "## Relationship to Capability Lifecycle States", "This report uses the existing Designed, Implemented, Operationally Validated, and Institutionalized lifecycle states as inputs. It does not create or redefine lifecycle states.", "",
        "## Capabilities Reviewed",
    ]
    for cap in report.get("capabilities_reviewed", []):
        lines.append(f"- {cap.get('id')} — {cap.get('name')} ({cap.get('lifecycle_state') or 'Missing state'}): {len(cap.get('validation_evidence_found', []))} evidence item(s), {len(cap.get('evidence_gaps', []))} gap(s)")
    if not report.get("capabilities_reviewed"):
        lines.append("- None")
    lines += ["", "## Validation Evidence Found"]
    evidence = report.get("validation_evidence_found", [])
    lines.extend(f"- {e.get('type')}: {e.get('source')}" for e in evidence) if evidence else lines.append("- None")
    lines += ["", "## Evidence Gaps"]
    gaps = report.get("evidence_gaps", [])
    lines.extend(f"- {g.get('id')} — {g.get('name')}: {', '.join(g.get('gaps', []))}" for g in gaps) if gaps else lines.append("- None")
    lines += ["", "## Candidates for Operationally Validated Review"]
    lines.extend(f"- {c.get('id')} — {c.get('name')}: {c.get('basis')}" for c in report.get("candidates_for_operationally_validated_review", [])) or lines.append("- None")
    lines += ["", "## Candidates for Institutionalized Review"]
    lines.extend(f"- {c.get('id')} — {c.get('name')}: {c.get('basis')}" for c in report.get("candidates_for_institutionalized_review", [])) or lines.append("- None")
    lines += ["", "## Warnings"]
    lines.extend(f"- {w.get('type')}: {w.get('path')} {w.get('message')}" for w in report.get("warnings", [])) if report.get("warnings") else lines.append("- None")
    lines += ["", "## Missing Inputs", _md_list(report.get("missing_inputs", [])), "", "## Limitations"]
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines)
