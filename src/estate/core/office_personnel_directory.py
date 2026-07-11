"""Office personnel directory and org-chart control payloads.

Read-only aggregation over canonical personnel/mailbox/resident/worker artifacts.
It intentionally does not create a second personnel registry or mailbox system.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.assignment_queue import generate_assignment_queue
from estate.core.capability_dependency_visualization import generate_capability_dependency_visualization
from estate.core.mailbox_index import generate_mailbox_index
from estate.core.paths import ESTATE_ROOT
from estate.core.resident_lifecycle import office_lifecycle_summary

PERSONNEL_SOURCE = "data/registry/personnel.json"
MAILBOX_SOURCE = "data/registry/mailboxes.json"
RESIDENT_SOURCE = "data/registry/residents.json"
WORKER_SOURCES = ["data/registry/workers.json", "runtime/workers/worker_runtime_monitor.json", "runtime/workers/heartbeat.json"]
RUNTIME_PAYLOAD = "runtime/steward/office_personnel_directory.json"


def _root(root: Path | str | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(root: Path, path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(root)).replace("\\", "/") if p.is_absolute() else str(p).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _read_json(root: Path, rel: str, warnings: list[dict[str, Any]], *, required: bool = False) -> Any:
    path = root / rel
    if not path.exists():
        if required:
            warnings.append({"type": "missing_source", "path": rel, "message": f"Required source artifact is missing: {rel}"})
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_source", "path": rel, "message": str(exc)})
        return None


def _as_id(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _mailbox_path(root: Path, mailbox_id: Any) -> str | None:
    mid = _as_id(mailbox_id)
    if not mid:
        return None
    for rel in (f"collaboration/mailboxes/{mid}", f"collaboration/mailboxes/{int(mid):04d}" if mid.isdigit() else ""):
        if rel and (root / rel).exists():
            return rel
    return f"collaboration/mailboxes/{mid}"


def _profile_path(root: Path, kind: str, identity: str | None) -> str | None:
    if not identity:
        return None
    candidates = [
        f"data/registry/{kind}s.json",
        f"runtime/{kind}s/{identity}.json",
        f"operations/{kind}s/{identity}.md",
        f"docs/onboarding/{identity}.md",
    ]
    return next((rel for rel in candidates if (root / rel).exists()), None)


def _work_packages_for(person: dict[str, Any], queue: dict[str, Any]) -> list[dict[str, Any]]:
    hay = " ".join(str(v) for v in [person.get("display_name"), person.get("current_title"), person.get("employee_id"), person.get("current_office"), person.get("resident_id"), person.get("worker_id")] if v).lower()
    out = []
    for wp in queue.get("work_packages") or []:
        text = " ".join(str(wp.get(k) or "") for k in ("work_package_id", "owner", "next_action", "path")).lower()
        if any(tok and tok in text for tok in {str(person.get("display_name") or "").lower(), str(person.get("employee_id") or "").lower(), str(person.get("resident_id") or "").lower(), str(person.get("worker_id") or "").lower()}):
            out.append({"work_package_id": wp.get("work_package_id"), "path": wp.get("path"), "state": wp.get("state"), "owner": wp.get("owner")})
    return out[:20]


def _detect_cycles(manager_by_id: dict[str, str | None]) -> list[dict[str, Any]]:
    cycles = []
    for start in manager_by_id:
        seen, cur = [], start
        while cur:
            if cur in seen:
                cyc = seen[seen.index(cur):] + [cur]
                if not any(set(c["employee_ids"]) == set(cyc) for c in cycles):
                    cycles.append({"type": "manager_cycle", "employee_ids": cyc, "message": "Manager relationship cycle detected."})
                break
            seen.append(cur)
            cur = manager_by_id.get(cur)
    return cycles


def build_office_personnel_directory(root: Path | str | None = None, *, write: bool = False, selected_employee_id: str | int | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    root = _root(root)
    warnings: list[dict[str, Any]] = []
    personnel_raw = _read_json(root, PERSONNEL_SOURCE, warnings, required=True)
    mailbox_raw = _read_json(root, MAILBOX_SOURCE, warnings, required=False)
    residents_raw = _read_json(root, RESIDENT_SOURCE, warnings, required=False)
    queue = generate_assignment_queue(root, write=False)
    caps = generate_capability_dependency_visualization(root, write=False)
    mailbox_index = generate_mailbox_index(root=root, write=False) if (root / "collaboration" / "messages").exists() else {"messages": []}

    records = personnel_raw if isinstance(personnel_raw, list) else []
    mailboxes = {str(m.get("mailbox_id")): m for m in mailbox_raw if isinstance(m, dict) and m.get("mailbox_id") is not None} if isinstance(mailbox_raw, list) else {}
    residents = {str(r.get("id")): r for r in residents_raw if isinstance(r, dict) and r.get("id") is not None} if isinstance(residents_raw, list) else {}
    messages_by_mailbox: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for msg in mailbox_index.get("messages") or []:
        if isinstance(msg, dict) and msg.get("destination_mailbox_id") is not None:
            messages_by_mailbox[str(msg.get("destination_mailbox_id"))].append(msg)

    duplicate_ids = sorted([eid for eid, count in defaultdict(int, ((str(p.get("employee_id")), 0) for p in [])).items() if count > 1])
    counts = defaultdict(int)
    for p in records:
        if isinstance(p, dict) and p.get("employee_id") is not None:
            counts[str(p.get("employee_id"))] += 1
    duplicate_ids = sorted(eid for eid, c in counts.items() if c > 1)

    employees = []
    by_id = {}
    malformed_count = 0
    for idx, person in enumerate(records):
        if not isinstance(person, dict) or person.get("employee_id") is None or not person.get("display_name"):
            malformed_count += 1
            warnings.append({"type": "malformed_personnel_record", "path": PERSONNEL_SOURCE, "index": idx, "message": "Personnel record lacks employee_id or display_name."})
            continue
        eid = str(person.get("employee_id"))
        mailbox_id = _as_id(person.get("mailbox_id"))
        direct_capabilities = person.get("capabilities") or person.get("capability_ids") or []
        if isinstance(direct_capabilities, str):
            direct_capabilities = [direct_capabilities]
        capability_matches = [n for n in caps.get("nodes", []) if any(str(v).lower() in json.dumps(n).lower() for v in [person.get("current_title"), person.get("current_office")] if v)]
        capabilities = list(dict.fromkeys([str(c) for c in direct_capabilities] + [n.get("id") for n in capability_matches if n.get("id")]))[:12]
        dependencies = sorted({d for n in capability_matches for d in (n.get("upstream_dependencies") or [])})[:20]
        msgs = messages_by_mailbox.get(mailbox_id or "", [])
        classification = "resident" if person.get("resident_id") else ("worker" if person.get("worker_id") else "employee")
        employee = {
            "employee_id": eid,
            "mailbox_id": mailbox_id,
            "display_name": person.get("display_name"),
            "current_title": person.get("current_title"),
            "office": person.get("current_office") or person.get("office") or person.get("department"),
            "role": person.get("current_title") or person.get("role"),
            "worker_resident_classification": classification,
            "manager_employee_id": _as_id(person.get("manager_employee_id") or person.get("manager_id")),
            "manager": None,
            "direct_reports": [],
            "status": person.get("status"),
            "active_assignments": _work_packages_for(person, queue),
            "capabilities": capabilities,
            "capability_dependencies": dependencies,
            "mailbox_path": _mailbox_path(root, mailbox_id),
            "mailbox_unread_attention_summary": {"open_count": len(msgs), "attention_count": sum(1 for m in msgs if m.get("requires_ack"))},
            "resident_id": person.get("resident_id"),
            "resident_profile_path": _profile_path(root, "resident", person.get("resident_id")),
            "worker_id": person.get("worker_id"),
            "worker_profile_path": _profile_path(root, "worker", person.get("worker_id")),
            "related_work_packages": _work_packages_for(person, queue),
            "related_evidence": [rel for rel in ["runtime/work_packages/assignment_queue.json", "runtime/capabilities/capability_dependency_visualization.json"] if (root / rel).exists()],
            "source_artifact_references": [PERSONNEL_SOURCE] + ([MAILBOX_SOURCE] if mailbox_id in mailboxes else []) + ([RESIDENT_SOURCE] if person.get("resident_id") in residents else []),
            "last_refreshed": _now(),
            "warnings": [],
        }
        if mailbox_id and mailbox_id not in mailboxes:
            employee["warnings"].append({"type": "missing_mailbox_registry_record", "message": f"Mailbox {mailbox_id} is not present in {MAILBOX_SOURCE}."})
        if classification == "resident" and not employee["resident_profile_path"]:
            employee["warnings"].append({"type": "missing_resident_profile", "message": "Resident profile artifact unavailable."})
        employees.append(employee); by_id[eid] = employee

    for e in employees:
        mid = e.get("manager_employee_id")
        if mid and mid in by_id:
            e["manager"] = by_id[mid]["display_name"]
            by_id[mid]["direct_reports"].append({"employee_id": e["employee_id"], "display_name": e["display_name"]})
        elif mid:
            w = {"type": "orphaned_manager", "employee_id": e["employee_id"], "manager_employee_id": mid, "message": "Manager employee ID does not resolve."}
            e["warnings"].append(w); warnings.append(w)

    manager_by_id = {e["employee_id"]: e.get("manager_employee_id") for e in employees}
    cycles = _detect_cycles(manager_by_id)
    warnings.extend(cycles)
    for did in duplicate_ids:
        warnings.append({"type": "duplicate_employee_id", "employee_id": did, "message": "Duplicate personnel employee_id detected."})

    offices = sorted({e.get("office") or "Unavailable" for e in employees})
    org_nodes = [{"id": f"office:{office}", "label": office, "type": "office", "employee_id": None, "filter": {"office": office}} for office in offices]
    org_edges = []
    for e in employees:
        node = {"id": f"employee:{e['employee_id']}", "label": f"{e['display_name']} ({e['employee_id']})", "type": "employee", "employee_id": e["employee_id"], "office": e.get("office"), "click_action": "open_employee_detail", "keyboard_action": "enter_open_employee_detail", "warnings": e.get("warnings", [])}
        org_nodes.append(node)
        org_edges.append({"source": f"office:{e.get('office') or 'Unavailable'}", "target": node["id"], "relationship": "office_membership"})
        if e.get("manager_employee_id"):
            org_edges.append({"source": f"employee:{e['manager_employee_id']}", "target": node["id"], "relationship": "manager_direct_report", "orphaned": e.get("manager_employee_id") not in by_id})

    lifecycle_summary = office_lifecycle_summary(root)
    lifecycle_by_resident = {r["resident_id"]: r for r in lifecycle_summary.get("records", [])}
    for employee in employees:
        if employee.get("resident_id") in lifecycle_by_resident:
            employee["resident_lifecycle"] = lifecycle_by_resident[employee["resident_id"]]
            employee["source_artifact_references"].append(lifecycle_summary["source"])

    payload = {
        "version": 1, "generated_at": _now(), "kind": "office_personnel_directory",
        "resident_lifecycle_status": lifecycle_summary,
        "selected_employee_id": _as_id(selected_employee_id) if _as_id(selected_employee_id) in by_id else None,
        "filters": filters or {}, "employees": sorted(employees, key=lambda e: (str(e.get("display_name") or ""), e["employee_id"])),
        "employees_by_id": by_id, "org_chart": {"nodes": org_nodes, "edges": org_edges, "cycles": cycles, "disconnected_nodes": [n for n in org_nodes if n["type"] == "employee" and not any(ed["target"] == n["id"] for ed in org_edges)]},
        "summary": {"employee_count": len(employees), "valid_record_count": len(employees), "malformed_record_count": malformed_count, "duplicate_employee_id_count": len(duplicate_ids), "orphaned_manager_count": sum(1 for w in warnings if w.get("type") == "orphaned_manager"), "cycle_count": len(cycles), "added_count": 0, "changed_count": 0, "removed_count": 0},
        "available_filters": {"office": offices, "role": sorted({e.get("role") or "Unavailable" for e in employees}), "status": sorted({e.get("status") or "Unavailable" for e in employees}), "capability": sorted({c for e in employees for c in e.get("capabilities", [])}), "worker_resident_classification": sorted({e.get("worker_resident_classification") for e in employees})},
        "sort_fields": ["name", "role", "office", "status", "employee_id"],
        "search_fields": ["display_name", "current_title", "employee_id", "mailbox_id", "office", "capabilities"],
        "actions": personnel_action_contracts(),
        "warnings": warnings,
        "source_artifacts": [PERSONNEL_SOURCE, MAILBOX_SOURCE, RESIDENT_SOURCE, "collaboration/messages", "collaboration/work_packages", "data/registry/capabilities.json", lifecycle_summary["source"]],
        "new_personnel_registry_introduced": False, "new_mailbox_system_introduced": False,
    }
    if write:
        out = root / RUNTIME_PAYLOAD; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def personnel_action_contracts() -> list[dict[str, Any]]:
    base = {"artifacts_written": [], "runtime_state_changed": [], "authority_gating": "read_only_or_existing_route_only"}
    return [
        {**base, "action_id": "personnel.open_employee_detail", "label": "Open employee details", "required_inputs": ["employee_id"], "canonical_handler": "estate.core.office_personnel_directory.open_employee_detail", "artifacts_read": [PERSONNEL_SOURCE], "completed_result": "employee detail payload", "blocked_result": "unknown employee_id", "failed_result": "malformed source"},
        {**base, "action_id": "personnel.open_mailbox", "label": "Open mailbox", "required_inputs": ["employee_id", "mailbox_id"], "canonical_handler": "estate.core.office_personnel_directory.route_personnel_mailbox", "artifacts_read": [PERSONNEL_SOURCE, MAILBOX_SOURCE, "collaboration/messages"], "completed_result": "mailbox route with selected mailbox", "blocked_result": "missing mailbox", "failed_result": "malformed source"},
        {**base, "action_id": "personnel.open_conversation", "label": "Open conversation", "required_inputs": ["employee_id"], "canonical_handler": "estate.core.office_personnel_directory.route_personnel_conversation", "artifacts_read": [PERSONNEL_SOURCE, RESIDENT_SOURCE], "completed_result": "resident/worker conversation route", "blocked_result": "conversation unsupported", "failed_result": "malformed source"},
        {**base, "action_id": "personnel.refresh", "label": "Refresh Personnel", "required_inputs": [], "canonical_handler": "estate.core.office_personnel_directory.refresh_personnel_directory", "artifacts_read": [PERSONNEL_SOURCE, MAILBOX_SOURCE, "collaboration/work_packages"], "artifacts_written": [RUNTIME_PAYLOAD], "runtime_state_changed": ["office personnel payload refreshed"], "completed_result": "refreshed summary", "blocked_result": "missing personnel registry", "failed_result": "write failed"},
    ]


def open_employee_detail(employee_id: str | int, root: Path | str | None = None) -> dict[str, Any]:
    payload = build_office_personnel_directory(root, write=False, selected_employee_id=employee_id)
    employee = payload["employees_by_id"].get(str(employee_id))
    if not employee:
        return {"outcome": "blocked", "message": f"Employee {employee_id} is unavailable.", "artifacts_read": [PERSONNEL_SOURCE]}
    return {"outcome": "completed", "employee": employee, "artifacts_read": employee.get("source_artifact_references", [])}


def route_personnel_mailbox(employee_id: str | int, root: Path | str | None = None) -> dict[str, Any]:
    detail = open_employee_detail(employee_id, root)
    if detail.get("outcome") != "completed": return detail
    emp = detail["employee"]
    if not emp.get("mailbox_id"):
        return {"outcome": "blocked", "message": "Employee has no mailbox_id.", "artifacts_read": [PERSONNEL_SOURCE]}
    return {"outcome": "completed", "route": {"tab": "mailboxes", "hash": f"#mailboxes?mailbox_id={emp['mailbox_id']}&employee_id={emp['employee_id']}", "mailbox_id": emp["mailbox_id"], "employee_id": emp["employee_id"]}, "artifacts_read": [PERSONNEL_SOURCE, MAILBOX_SOURCE]}


def route_personnel_conversation(employee_id: str | int, root: Path | str | None = None) -> dict[str, Any]:
    detail = open_employee_detail(employee_id, root)
    if detail.get("outcome") != "completed": return detail
    emp = detail["employee"]
    if not (emp.get("resident_id") or emp.get("worker_id")):
        return {"outcome": "blocked", "message": "No resident/worker conversation capability is indexed for this employee.", "artifacts_read": emp.get("source_artifact_references", [])}
    selected = emp.get("resident_id") or emp.get("worker_id")
    return {"outcome": "completed", "route": {"tab": "resident-conversations", "hash": f"#resident-conversations?employee_id={emp['employee_id']}&selected={selected}", "employee_id": emp["employee_id"], "selected": selected}, "artifacts_read": emp.get("source_artifact_references", [])}


def refresh_personnel_directory(root: Path | str | None = None, selected_employee_id: str | int | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_office_personnel_directory(root, write=True, selected_employee_id=selected_employee_id, filters=filters)
