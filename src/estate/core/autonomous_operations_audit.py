"""Autonomous Operations Audit Trail.

Append-only, evidence-only audit records for autonomous-operation evaluations.
The audit trail records local recommendations and source evidence without
executing work, sending notifications, or changing Steward authority.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

AUDIT_JSONL = "audit/autonomy/autonomous_operations_audit.jsonl"
AUDIT_MARKDOWN = "operations/autonomy/autonomous_operations_audit.md"
MISSION_CONTROL_JSON = "runtime/mission_control/autonomous_operations_audit.json"

SOURCE_PATHS = {
    "control_loop": "runtime/autonomy/autonomous_operations_state.json",
    "scheduler": "runtime/work_packages/autonomous_work_queue_scheduler.json",
    "worker_monitor": "runtime/workers/worker_runtime_monitor.json",
    "steward_presence": "runtime/steward/steward_presence_state.json",
    "notification_router": "runtime/notifications/notification_router_report.json",
    "recall_audit": "runtime/audit/recall_audit_log.json",
    "local_validation": "runtime/validation/local_operational_validation_run.json",
    "operational_validation": "runtime/validation/operational_validation_report.json",
    "morning_briefing": "runtime/briefings/morning_briefing.json",
    "operations_morning_briefing": "runtime/operations/morning_briefing.json",
}
VALID_DECISIONS = {"continue", "pause", "recall_recommended", "unknown"}
OPERATIONAL_EVENT_KINDS = {"observed_fact", "derived_state", "recommendation", "policy_decision", "authorization", "action", "escalation", "correction"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(root: Path, rel: str) -> tuple[Any | None, dict[str, Any]]:
    path = root / rel
    if not path.exists():
        return None, {"type": "missing_evidence", "path": rel, "message": f"Evidence artifact is unavailable: {rel}"}
    try:
        return json.loads(path.read_text(encoding="utf-8")), {}
    except Exception as exc:
        return None, {"type": "unreadable_evidence", "path": rel, "message": str(exc)}


def _normalize_decision(value: Any) -> str:
    decision = str(value or "unknown").strip().lower().replace("-", "_")
    return decision if decision in VALID_DECISIONS else "unknown"


def _operation_id(control: Any, generated_at: str) -> str:
    if isinstance(control, dict):
        for key in ("operation_cycle_id", "run_id", "cycle_id", "id"):
            if control.get(key):
                return str(control[key])
        if control.get("generated_at"):
            return f"autonomy-{control['generated_at']}"
    return f"autonomy-{generated_at}"


def _validation_failed(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    explicit = str(payload.get("status") or payload.get("overall_status") or "").lower()
    steps = [str(step.get("status", "")).lower() for step in payload.get("steps", []) if isinstance(step, dict)]
    return explicit in {"failed", "fail", "error"} or any(step in {"failed", "fail", "error"} for step in steps)


def _conflicts(sources: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    control = sources.get("control_loop") if isinstance(sources.get("control_loop"), dict) else {}
    steward = sources.get("steward_presence") if isinstance(sources.get("steward_presence"), dict) else {}
    scheduler = sources.get("scheduler") if isinstance(sources.get("scheduler"), dict) else {}
    decision = _normalize_decision(control.get("decision"))
    presence_state = steward.get("current_state")
    ready_count = int((scheduler.get("summary") or {}).get("ready_count") or 0)
    if decision == "continue" and presence_state in {"recall_requested", "recall_sent"}:
        conflicts.append({"type": "continue_vs_recall_state", "message": "Control loop continues while Steward presence reports active recall.", "paths": [SOURCE_PATHS["control_loop"], SOURCE_PATHS["steward_presence"]]})
    if presence_state in {"recall_requested", "recall_sent"} and ready_count > 0:
        conflicts.append({"type": "recall_vs_ready_work", "message": "Recall lifecycle evidence coexists with ready autonomous work evidence.", "paths": [SOURCE_PATHS["steward_presence"], SOURCE_PATHS["scheduler"]]})
    return conflicts


def build_autonomous_operations_audit_record(*, root: str | Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    root_path = _root(root)
    timestamp = _now(now)
    evidence: dict[str, dict[str, Any]] = {}
    missing_or_unreadable: list[dict[str, Any]] = []
    sources: dict[str, Any] = {}
    for name, rel in SOURCE_PATHS.items():
        payload, warning = _read_json(root_path, rel)
        sources[name] = payload
        evidence[name] = {"path": rel, "available": payload is not None}
        if warning:
            missing_or_unreadable.append(warning)

    control = sources.get("control_loop") if isinstance(sources.get("control_loop"), dict) else {}
    decision = _normalize_decision(control.get("decision"))
    blocked_conditions = list(control.get("blocked_conditions") or []) if isinstance(control.get("blocked_conditions"), list) else []
    blocked_conditions.extend(missing_or_unreadable)
    blocked_conditions.extend(_conflicts(sources))
    for key in ("local_validation", "operational_validation"):
        if _validation_failed(sources.get(key)):
            blocked_conditions.append({"type": "failed_validation", "message": f"Validation evidence reports failure: {key}.", "path": SOURCE_PATHS[key]})
    if missing_or_unreadable and decision == "continue":
        decision = "unknown"

    return {
        "version": 1,
        "timestamp": timestamp,
        "operation_cycle_id": _operation_id(control, timestamp),
        "decision": decision,
        "decision_reason": control.get("reason") or "No authoritative control-loop decision reason was available.",
        "evidence_artifact_paths": evidence,
        "originating_component": "autonomous_operations_audit_trail",
        "source_decision_component": "autonomous_operations_control_loop" if control else "unknown",
        "blocked_conditions": blocked_conditions,
        "recommended_next_action": control.get("recommended_next_action") or "Refresh missing evidence and request Alfred/Steward review before autonomous continuation.",
        "steward_authority_required": decision in {"pause", "recall_recommended", "unknown"} or bool(blocked_conditions),
        "warnings": missing_or_unreadable,
    }


def append_autonomous_operations_audit(*, root: str | Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    root_path = _root(root)
    record = build_autonomous_operations_audit_record(root=root_path, now=now)
    jsonl = root_path / AUDIT_JSONL
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    md = root_path / AUDIT_MARKDOWN
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(format_autonomous_operations_audit(root=root_path), encoding="utf-8")
    mission = root_path / MISSION_CONTROL_JSON
    mission.parent.mkdir(parents=True, exist_ok=True)
    mission.write_text(json.dumps({"source": "autonomous_operations_audit_trail", "generated_at": record["timestamp"], "latest_decision": record["decision"], "latest_record": record["operation_cycle_id"], "report": AUDIT_MARKDOWN, "jsonl": AUDIT_JSONL}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def read_audit_records(root: str | Path | None = None) -> list[dict[str, Any]]:
    path = _root(root) / AUDIT_JSONL
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def format_autonomous_operations_audit(*, root: str | Path | None = None) -> str:
    records = read_audit_records(root)
    lines = ["# Autonomous Operations Audit Trail", "", "Append-only institutional history for autonomous-operation evaluations. Advisory only; does not execute work, send notifications, or alter Steward authority.", "", "## Records"]
    if not records:
        lines.append("- No audit records yet.")
    for record in records[-50:]:
        lines.extend(["", f"### {record.get('operation_cycle_id')}", f"- Timestamp: {record.get('timestamp')}", f"- Decision: {record.get('decision')}", f"- Reason: {record.get('decision_reason')}", f"- Originating component: {record.get('originating_component')}", f"- Steward authority required: {record.get('steward_authority_required')}", f"- Recommended next action: {record.get('recommended_next_action')}", "- Evidence:"])
        for name, info in record.get("evidence_artifact_paths", {}).items():
            lines.append(f"  - {name}: {info.get('path')} (available: {info.get('available')})")
        lines.append("- Blocked conditions:")
        if not record.get("blocked_conditions"):
            lines.append("  - None")
        for item in record.get("blocked_conditions", []):
            lines.append(f"  - {item.get('type')}: {item.get('message')}")
    return "\n".join(lines) + "\n"


def append_operational_audit_event(event: dict[str, Any], *, root: str | Path | None = None) -> dict[str, Any]:
    """Append a normalized operational event to the existing audit JSONL."""
    item = json.loads(json.dumps(event))
    required = ["event_id", "event_kind", "occurred_at", "correlations", "source_evidence", "confidence", "policy_disposition", "outcome"]
    missing = [name for name in required if item.get(name) in (None, "", [], {})]
    if missing:
        raise ValueError(f"operational audit event missing: {', '.join(missing)}")
    if item["event_kind"] not in OPERATIONAL_EVENT_KINDS:
        raise ValueError("unknown operational audit event kind")
    if item.get("restricted_payload") is not None or item.get("personal_data") is not None:
        raise ValueError("restricted or personal payloads must remain in their canonical authorized store")
    root_path = _root(root)
    existing = read_audit_records(root_path)
    if any(record.get("event_id") == item["event_id"] for record in existing):
        raise ValueError("operational audit event_id already exists")
    if item["event_kind"] == "correction":
        target = item.get("corrects_event_id")
        if not target or not any(record.get("event_id") == target for record in existing):
            raise ValueError("correction must reference an existing event_id")
    refs = item["source_evidence"]
    if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ValueError("source_evidence must contain canonical references")
    record = {
        "version": 2,
        "record_type": "operational_audit_event",
        "event_id": item["event_id"],
        "event_kind": item["event_kind"],
        "occurred_at": item["occurred_at"],
        "recorded_at": item.get("recorded_at") or item["occurred_at"],
        "correlations": item["correlations"],
        "source_evidence": sorted(set(refs)),
        "freshness": item.get("freshness") or "unknown",
        "confidence": item["confidence"],
        "policy_disposition": item["policy_disposition"],
        "authority": item.get("authority") or {"required": True, "references": []},
        "outcome": item["outcome"],
        "uncertainty": item.get("uncertainty") or [],
        "corrects_event_id": item.get("corrects_event_id"),
        "supersedes_event_id": item.get("supersedes_event_id"),
        "classification": item.get("classification") or "Estate Internal",
        "explanation_inputs": item.get("explanation_inputs") or [],
        "generated_explanation_is_authoritative": False,
    }
    path = root_path / AUDIT_JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def query_operational_audit(*, root: str | Path | None = None, **correlations: str) -> list[dict[str, Any]]:
    records = [record for record in read_audit_records(root) if record.get("record_type") == "operational_audit_event"]
    return [record for record in records if all((record.get("correlations") or {}).get(key) == value for key, value in correlations.items())]


def reconstruct_operational_history(*, root: str | Path | None = None, **correlations: str) -> dict[str, Any]:
    events = query_operational_audit(root=root, **correlations)
    corrected = {record.get("corrects_event_id") for record in events if record.get("corrects_event_id")}
    superseded = {record.get("supersedes_event_id") for record in events if record.get("supersedes_event_id")}
    events.sort(key=lambda record: (record["occurred_at"], record["event_id"]))
    return {
        "correlations": correlations,
        "events": events,
        "corrected_event_ids": sorted(corrected),
        "superseded_event_ids": sorted(superseded),
        "missing_evidence_visible": any(record.get("uncertainty") or record.get("freshness") in {"stale", "unknown"} for record in events),
        "generated_explanation_is_authoritative": False,
    }


def explain_operational_history(history: dict[str, Any]) -> str:
    lines = ["# Operational decision explanation", "", "> Generated explanation only; canonical evidence and authority records control.", ""]
    if not history.get("events"):
        lines.append("No matching operational audit events were found; the reason cannot be reconstructed from this audit view.")
    for event in history.get("events") or []:
        marker = " (later corrected)" if event["event_id"] in history.get("corrected_event_ids", []) else ""
        lines.extend([
            f"## {event['event_id']}{marker}",
            f"- Kind: {event['event_kind']}", f"- At: {event['occurred_at']}",
            f"- Policy: {event['policy_disposition']}", f"- Outcome: {event['outcome']}",
            f"- Evidence: {', '.join(event['source_evidence'])}",
            f"- Uncertainty: {', '.join(event.get('uncertainty') or []) or 'none recorded'}", "",
        ])
    return "\n".join(lines).rstrip() + "\n"
