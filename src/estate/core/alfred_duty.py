"""Local-first Alfred duty runner.

The runner updates Alfred's visible resident presence and writes an operational
summary from local artifacts only. It summarizes and routes attention; it does
not approve, validate, merge, notify externally, or execute work packages.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_presence import RUNTIME_PATH, build_resident_presence
from estate.core.resident_authority import check_authority

DUTY_STATE_PATH = Path("runtime/alfred/duty_state.json")
AUDIT_LOG_PATH = Path("runtime/alfred/duty_runs.jsonl")
OPERATIONS_SUMMARY_PATH = Path("operations/alfred/duty_summary.md")
AUTHORITY_LIMITATIONS = [
    "Alfred may summarize and route; Alfred may not authorize.",
    "Alfred may identify decisions; Alfred may not make Steward decisions.",
    "Alfred may surface validation blockers; Alfred may not declare production readiness without validation artifacts.",
    "Alfred may point to work packages; Alfred may not execute them automatically.",
    "Alfred duty runs are local operational views, not canonical Estate authority.",
]
SOURCE_CANDIDATES = {
    "resident_registry": "data/registry/residents.json",
    "personnel_registry": "data/registry/personnel.json",
    "mailbox_registry": "data/registry/mailboxes.json",
    "resident_presence": "runtime/residents/presence.json",
    "mailbox_index": "runtime/mailboxes/index.json",
    "mailbox_sync_duty": "runtime/mailboxes/sync_duty.json",
    "decision_queue": "runtime/steward/decision_queue.json",
    "operations_board": "runtime/operations_board.json",
    "validation_readiness": "runtime/validation/production_readiness.json",
    "work_package_assignment_queue": "runtime/work_packages/assignment_queue.json",
}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _read_json(root: Path, rel: str, *, required: bool = False) -> tuple[Any, dict[str, Any]]:
    path = root / rel
    meta = {"path": rel, "exists": path.exists(), "required": required}
    if not path.exists():
        meta["status"] = "missing"
        return None, meta
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        meta["status"] = "available"
        return data, meta
    except Exception as exc:
        meta.update({"status": "malformed", "message": str(exc)})
        return None, meta


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _find_alfred_identity(residents: Any, personnel: Any) -> dict[str, Any]:
    resident = next((r for r in residents or [] if isinstance(r, dict) and _slug(r.get("name")) == "alfred"), {})
    person = next((p for p in personnel or [] if isinstance(p, dict) and (p.get("resident_id") == resident.get("id") or _slug(p.get("display_name")) == "alfred")), {})
    return {
        "resident_id": resident.get("id"),
        "name": resident.get("name") or "Alfred",
        "role": resident.get("role") or resident.get("office"),
        "mailbox_id": person.get("mailbox_id"),
        "mailbox_path": f"collaboration/mailboxes/{person.get('mailbox_id')}" if person.get("mailbox_id") is not None else None,
        "source_artifacts": [p for p in ["data/registry/residents.json" if resident else None, "data/registry/personnel.json" if person else None] if p],
    }


def _count_items(data: Any, keys: tuple[str, ...]) -> int:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return len(data[key])
        return len(data)
    return 0


def _summarize_sources(sources: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    steward: list[dict[str, Any]] = []
    decision_queue = sources.get("decision_queue")
    if decision_queue is not None:
        count = _count_items(decision_queue, ("decisions", "items", "queue"))
        findings.append({"type": "decision_queue", "severity": "info", "message": f"Decision queue artifact is available with {count} visible item(s).", "path": SOURCE_CANDIDATES["decision_queue"]})
        if count:
            steward.append({"type": "steward_decisions_present", "message": "Local decision queue contains items for Steward review.", "path": SOURCE_CANDIDATES["decision_queue"]})
    validation = sources.get("validation_readiness")
    if isinstance(validation, dict):
        status = validation.get("status") or validation.get("readiness_state") or validation.get("production_readiness") or validation.get("overall_status")
        findings.append({"type": "validation_readiness", "severity": "info", "message": f"Validation/readiness artifact reports {status or 'unknown'}.", "path": SOURCE_CANDIDATES["validation_readiness"]})
        if str(status).lower() in {"blocked", "fail", "failed", "not_ready"}:
            steward.append({"type": "validation_blocker", "message": "Validation/readiness artifact reports a blocked or failing state.", "path": SOURCE_CANDIDATES["validation_readiness"]})
    for name in ("mailbox_index", "mailbox_sync_duty", "operations_board", "work_package_assignment_queue"):
        if sources.get(name) is not None:
            findings.append({"type": name, "severity": "info", "message": f"{name.replace('_', ' ').title()} artifact is available for operational awareness.", "path": SOURCE_CANDIDATES[name]})
    return findings, steward


def _presence_state(metas: list[dict[str, Any]], steward_items: list[dict[str, Any]]) -> tuple[str, str]:
    required_missing = [m for m in metas if m.get("required") and m.get("status") != "available"]
    if required_missing:
        return "degraded", "Required Alfred identity artifacts are missing or malformed."
    malformed = [m for m in metas if m.get("status") == "malformed"]
    if malformed:
        return "degraded", "One or more optional duty source artifacts are malformed."
    if steward_items:
        return "waiting_for_steward", "Local evidence indicates Steward attention is needed."
    return "working", "Alfred duty runner completed a bounded local operational summary."


def _update_presence(root: Path, identity: dict[str, Any], state: str, reason: str, generated_at: str, needs_steward: bool) -> None:
    presence_path = root / RUNTIME_PATH
    existing, _ = _read_json(root, str(RUNTIME_PATH))
    residents = existing.get("residents") if isinstance(existing, dict) and isinstance(existing.get("residents"), list) else []
    entry = {
        "resident_id": identity.get("resident_id"),
        "name": "Alfred",
        "mailbox_id": identity.get("mailbox_id"),
        "mailbox_path": identity.get("mailbox_path"),
        "presence_state": state,
        "current_duty": "Review local Estate operational inputs and surface Steward attention needs.",
        "last_heartbeat": generated_at,
        "last_activity": str(DUTY_STATE_PATH),
        "needs_steward": needs_steward,
        "status_reason": reason,
    }
    replaced = False
    for index, item in enumerate(residents):
        if _slug(item.get("name")) == "alfred" or _slug(item.get("resident_id")) == _slug(identity.get("resident_id")):
            residents[index] = {**item, **entry}
            replaced = True
            break
    if not replaced:
        residents.append(entry)
    _write_json(presence_path, {"version": 1, "updated_at": generated_at, "residents": residents})


def run_alfred_duty(root: str | Path | None = None, *, write: bool = True) -> dict[str, Any]:
    root = _root(root)
    generated_at = _now()
    sources: dict[str, Any] = {}
    metas: list[dict[str, Any]] = []
    for name, rel in SOURCE_CANDIDATES.items():
        data, meta = _read_json(root, rel, required=name in {"resident_registry", "personnel_registry"})
        sources[name] = data
        metas.append(meta | {"name": name})
    identity = _find_alfred_identity(sources.get("resident_registry"), sources.get("personnel_registry"))
    findings, steward_items = _summarize_sources(sources)
    state, reason = _presence_state(metas, steward_items)
    if write:
        _update_presence(root, identity, state, reason, generated_at, bool(steward_items))
    presence = build_resident_presence(root, ("Alfred",))
    payload = {
        "version": 1,
        "resident": "Alfred",
        "generated_at": generated_at,
        "duty_state": state,
        "presence": (presence.get("residents") or [{}])[0],
        "identity": identity,
        "duty_summary": {
            "headline": reason,
            "informational_findings": findings,
            "steward_attention_items": steward_items,
            "needs_steward": bool(steward_items),
            "source_of_truth_boundary": "Operational summary only; canonical authority remains with source artifacts and Steward-approved validation/governance processes.",
        },
        "source_artifact_references": metas,
        "authority_limitations": AUTHORITY_LIMITATIONS,
        "authority_boundary": {
            "summarize": check_authority("Alfred", "summarize", root=root, audit=False),
            "execute_work_package": check_authority("Alfred", "execute-work-package", root=root, audit=False),
        },
        "runtime_artifacts": {"duty_state": DUTY_STATE_PATH.as_posix(), "audit_log": AUDIT_LOG_PATH.as_posix(), "operations_summary": OPERATIONS_SUMMARY_PATH.as_posix(), "presence": RUNTIME_PATH.as_posix()},
    }
    if write:
        _write_json(root / DUTY_STATE_PATH, payload)
        (root / AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with (root / AUDIT_LOG_PATH).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"generated_at": generated_at, "duty_state": state, "needs_steward": bool(steward_items), "sources": metas}, sort_keys=True) + "\n")
        (root / OPERATIONS_SUMMARY_PATH).parent.mkdir(parents=True, exist_ok=True)
        (root / OPERATIONS_SUMMARY_PATH).write_text(format_alfred_duty(payload), encoding="utf-8")
    return payload


def format_alfred_duty(payload: dict[str, Any]) -> str:
    summary = payload.get("duty_summary") or {}
    lines = ["# Alfred Duty State", "", f"Generated: {payload.get('generated_at')}", f"State: {payload.get('duty_state')}", f"Needs Steward: {summary.get('needs_steward')}", f"Summary: {summary.get('headline')}", "", "## Source Artifacts"]
    for src in payload.get("source_artifact_references") or []:
        lines.append(f"- {src.get('path')}: {src.get('status')}")
    lines += ["", "## Authority Limitations"]
    lines.extend(f"- {item}" for item in payload.get("authority_limitations") or [])
    return "\n".join(lines) + "\n"
