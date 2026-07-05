"""Local-first Helen duty runner.

The runner updates Helen's visible resident presence and writes an operational
summary from local artifacts only. It summarizes onboarding/personnel operational state; it does
not authorize personnel changes, approve, validate, merge, notify externally, or execute work packages.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_presence import RUNTIME_PATH, build_resident_presence
from estate.core.resident_authority import check_authority

DUTY_STATE_PATH = Path("runtime/helen/duty_state.json")
AUDIT_LOG_PATH = Path("runtime/helen/duty_runs.jsonl")
OPERATIONS_SUMMARY_PATH = Path("operations/helen/duty_summary.md")
AUTHORITY_LIMITATIONS = [
    "Helen may summarize onboarding/personnel operational state; Helen may not authorize personnel changes.",
    "Helen may identify onboarding blockers; Helen may not complete onboarding by assertion.",
    "Helen may surface HR-related artifacts; Helen may not create HR governance.",
    "Helen may point to work packages; Helen may not execute them automatically.",
    "Helen duty runs are local operational views, not canonical Estate authority.",
]
SOURCE_CANDIDATES = {
    "resident_registry": "data/registry/residents.json",
    "personnel_registry": "data/registry/personnel.json",
    "mailbox_registry": "data/registry/mailboxes.json",
    "resident_presence": "runtime/residents/presence.json",
    "mailbox_index": "runtime/mailboxes/index.json",
    "mailbox_sync_duty": "runtime/mailboxes/synchronization_duty.json",
    "onboarding_manifest": "data/onboarding/manifest.json",
    "onboarding_status": "runtime/onboarding/status.json",
    "chief_architect_onboarding_packet": "collaboration/messages/msg_ca2_20260701_0003_ca4_onboarding_packet.md",
    "helen_hr_work_package": "collaboration/work_packages/pending/WP-0020_SERIES_helen_hr_operational_onboarding.md",
    "helen_onboarding_work_package": "collaboration/work_packages/pending/WP-0080_SERIES_helen_employee_onboarding_orchestrator.md",
    "resident_cards": "runtime/residents/cards.json",
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
    if path.suffix.lower() in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8")
        meta.update({"status": "available", "content_type": "text", "bytes": len(text.encode("utf-8"))})
        return {"text_available": True, "bytes": meta["bytes"]}, meta
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


def _find_helen_identity(residents: Any, personnel: Any) -> dict[str, Any]:
    resident = next((r for r in residents or [] if isinstance(r, dict) and _slug(r.get("name")) == "helen"), {})
    person = next((p for p in personnel or [] if isinstance(p, dict) and (p.get("resident_id") == resident.get("id") or _slug(p.get("display_name")) == "helen")), {})
    return {
        "resident_id": resident.get("id"),
        "name": resident.get("name") or "Helen",
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
    onboarding = sources.get("onboarding_status") or sources.get("onboarding_manifest")
    if isinstance(onboarding, dict):
        status = onboarding.get("status") or onboarding.get("state") or onboarding.get("overall_status")
        findings.append({"type": "onboarding_status", "severity": "info", "message": f"Onboarding artifact reports {status or 'unknown'} with {_count_items(onboarding, ('items', 'employees', 'manifests', 'blockers'))} visible item(s).", "path": SOURCE_CANDIDATES["onboarding_status"] if sources.get("onboarding_status") is not None else SOURCE_CANDIDATES["onboarding_manifest"]})
        blockers = onboarding.get("blockers") if isinstance(onboarding.get("blockers"), list) else []
        if blockers or str(status).lower() in {"blocked", "needs_steward", "waiting_for_steward"}:
            steward.append({"type": "onboarding_blocker", "message": "Local onboarding artifact reports a blocker or Steward-needed state.", "path": SOURCE_CANDIDATES["onboarding_status"] if sources.get("onboarding_status") is not None else SOURCE_CANDIDATES["onboarding_manifest"]})
    if isinstance(sources.get("personnel_registry"), list):
        findings.append({"type": "personnel_registry", "severity": "info", "message": f"Personnel registry is available with {len(sources['personnel_registry'])} visible record(s).", "path": SOURCE_CANDIDATES["personnel_registry"]})
    for name in ("mailbox_index", "mailbox_sync_duty", "chief_architect_onboarding_packet", "helen_hr_work_package", "helen_onboarding_work_package", "resident_cards"):
        if sources.get(name) is not None:
            findings.append({"type": name, "severity": "info", "message": f"{name.replace('_', ' ').title()} artifact is available for bounded HR/onboarding awareness.", "path": SOURCE_CANDIDATES[name]})
    return findings, steward


def _presence_state(metas: list[dict[str, Any]], steward_items: list[dict[str, Any]]) -> tuple[str, str]:
    required_missing = [m for m in metas if m.get("required") and m.get("status") != "available"]
    if required_missing:
        return "degraded", "Required Helen identity artifacts are missing or malformed."
    malformed = [m for m in metas if m.get("status") == "malformed"]
    if malformed:
        return "degraded", "One or more optional duty source artifacts are malformed."
    if steward_items:
        return "waiting_for_steward", "Local evidence indicates Steward attention is needed."
    return "working", "Helen duty runner completed a bounded local onboarding/personnel operational summary."


def _update_presence(root: Path, identity: dict[str, Any], state: str, reason: str, generated_at: str, needs_steward: bool) -> None:
    presence_path = root / RUNTIME_PATH
    existing, _ = _read_json(root, str(RUNTIME_PATH))
    residents = existing.get("residents") if isinstance(existing, dict) and isinstance(existing.get("residents"), list) else []
    entry = {
        "resident_id": identity.get("resident_id"),
        "name": "Helen",
        "mailbox_id": identity.get("mailbox_id"),
        "mailbox_path": identity.get("mailbox_path"),
        "presence_state": state,
        "current_duty": "Review local onboarding and personnel inputs and surface Steward attention needs.",
        "last_heartbeat": generated_at,
        "last_activity": str(DUTY_STATE_PATH),
        "needs_steward": needs_steward,
        "status_reason": reason,
    }
    replaced = False
    for index, item in enumerate(residents):
        if _slug(item.get("name")) == "helen" or _slug(item.get("resident_id")) == _slug(identity.get("resident_id")):
            residents[index] = {**item, **entry}
            replaced = True
            break
    if not replaced:
        residents.append(entry)
    _write_json(presence_path, {"version": 1, "updated_at": generated_at, "residents": residents})


def run_helen_duty(root: str | Path | None = None, *, write: bool = True) -> dict[str, Any]:
    root = _root(root)
    generated_at = _now()
    sources: dict[str, Any] = {}
    metas: list[dict[str, Any]] = []
    for name, rel in SOURCE_CANDIDATES.items():
        data, meta = _read_json(root, rel, required=name in {"resident_registry", "personnel_registry"})
        sources[name] = data
        metas.append(meta | {"name": name})
    identity = _find_helen_identity(sources.get("resident_registry"), sources.get("personnel_registry"))
    findings, steward_items = _summarize_sources(sources)
    state, reason = _presence_state(metas, steward_items)
    if write:
        _update_presence(root, identity, state, reason, generated_at, bool(steward_items))
    presence = build_resident_presence(root, ("Helen",))
    payload = {
        "version": 1,
        "resident": "Helen",
        "generated_at": generated_at,
        "duty_state": state,
        "presence": (presence.get("residents") or [{}])[0],
        "identity": identity,
        "duty_summary": {
            "headline": reason,
            "informational_findings": findings,
            "steward_attention_items": steward_items,
            "needs_steward": bool(steward_items),
            "source_of_truth_boundary": "Operational summary only; canonical personnel/onboarding authority remains with source artifacts and explicitly approved Steward/governance processes.",
        },
        "source_artifact_references": metas,
        "authority_limitations": AUTHORITY_LIMITATIONS,
        "authority_boundary": {
            "summarize": check_authority("Helen", "summarize", root=root, audit=False),
            "execute_work_package": check_authority("Helen", "execute-work-package", root=root, audit=False),
        },
        "runtime_artifacts": {"duty_state": DUTY_STATE_PATH.as_posix(), "audit_log": AUDIT_LOG_PATH.as_posix(), "operations_summary": OPERATIONS_SUMMARY_PATH.as_posix(), "presence": RUNTIME_PATH.as_posix()},
    }
    if write:
        _write_json(root / DUTY_STATE_PATH, payload)
        (root / AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with (root / AUDIT_LOG_PATH).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"generated_at": generated_at, "duty_state": state, "needs_steward": bool(steward_items), "sources": metas}, sort_keys=True) + "\n")
        (root / OPERATIONS_SUMMARY_PATH).parent.mkdir(parents=True, exist_ok=True)
        (root / OPERATIONS_SUMMARY_PATH).write_text(format_helen_duty(payload), encoding="utf-8")
    return payload


def format_helen_duty(payload: dict[str, Any]) -> str:
    summary = payload.get("duty_summary") or {}
    lines = ["# Helen Duty State", "", f"Generated: {payload.get('generated_at')}", f"State: {payload.get('duty_state')}", f"Needs Steward: {summary.get('needs_steward')}", f"Summary: {summary.get('headline')}", "", "## Source Artifacts"]
    for src in payload.get("source_artifact_references") or []:
        lines.append(f"- {src.get('path')}: {src.get('status')}")
    lines += ["", "## Authority Limitations"]
    lines.extend(f"- {item}" for item in payload.get("authority_limitations") or [])
    return "\n".join(lines) + "\n"
