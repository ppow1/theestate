"""Local resident conversation sessions and audit trail.

Conversation sessions are local interface records only. They preserve transcript
and provenance for review, but do not create governance, validation, merge, or
Steward authority unless outcomes are promoted into canonical Estate artifacts.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_authority import check_authority

SESSION_STORE = Path("runtime/resident_conversations/sessions")
DEFAULT_PARTICIPANTS = [{"role": "operator", "label": "Local operator"}, {"role": "resident", "label": "Resident"}]
VALID_OUTCOMES = {"informational", "needs_steward", "work_package_candidate", "decision_candidate", "validation_follow_up", "no_action"}
AUTHORITY_LIMITATIONS = [
    "Conversation transcripts are non-authoritative interface records.",
    "No Steward approval, validation success, merge authority, governance authority, hiring/termination authority, or work-package execution authority is implied by a session.",
    "Important outcomes must be promoted to canonical Estate artifacts before becoming institutional source-of-truth.",
]


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text or "resident"


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def storage_path(root: str | Path | None = None) -> Path:
    return _root(root) / SESSION_STORE


def _session_path(root: Path, session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    return storage_path(root) / f"{safe}.json"


def create_session(
    root: str | Path | None = None,
    *,
    resident: str,
    participant_role: str = "operator",
    status: str = "open",
    source_artifacts: list[str] | None = None,
    prompt: str | None = None,
    response: str | None = None,
    operator_note: str | None = None,
    outcome: str = "informational",
    canonical_links: list[str] | None = None,
    action: str | None = None,
) -> dict[str, Any]:
    root_path = _root(root)
    created_at = _now()
    safe_resident = _slug(resident)
    base = created_at.replace(":", "").replace("+", "Z").replace("-", "").replace("T", "-")
    session_id = f"rcs-{safe_resident}-{base}"
    outcome_value = outcome if outcome in VALID_OUTCOMES else "informational"
    authority_decision = check_authority(resident, action or outcome_value, source_refs=source_artifacts or [], root=root_path, audit=False)
    events = []
    if prompt:
        events.append({"type": "prompt", "role": participant_role, "timestamp": created_at, "content": prompt})
    if response:
        events.append({"type": "response", "role": "resident", "timestamp": created_at, "content": response})
    if operator_note:
        events.append({"type": "operator_note", "role": participant_role, "timestamp": created_at, "content": operator_note})
    record = {
        "version": 1,
        "kind": "resident_conversation_session",
        "session_id": session_id,
        "resident": str(resident),
        "resident_slug": safe_resident,
        "status": status,
        "created_at": created_at,
        "updated_at": created_at,
        "participants": [{"role": participant_role, "label": "Session operator"}, {"role": "resident", "label": str(resident)}],
        "source_artifacts": [str(item) for item in (source_artifacts or []) if item],
        "events": events,
        "outcome": {"label": outcome_value, "canonical_artifact_links": [str(item) for item in (canonical_links or []) if item], "authoritative": False, "authority_decision": authority_decision.get("decision"), "authority_classification": authority_decision.get("authority_classification")},
        "authority_boundary": {"authoritative_record": False, "limitations": AUTHORITY_LIMITATIONS, "decision": authority_decision},
        "schema_notes": "Session transcript/audit record only; canonical decisions must live in linked Estate artifacts.",
    }
    out = _session_path(root_path, session_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def load_session(session_id: str, root: str | Path | None = None) -> dict[str, Any] | None:
    data = _read_json(_session_path(_root(root), session_id))
    return data if isinstance(data, dict) else None


def _summary(record: dict[str, Any], path: Path | None = None, root: Path | None = None) -> dict[str, Any]:
    events = record.get("events") if isinstance(record.get("events"), list) else []
    outcome = record.get("outcome") if isinstance(record.get("outcome"), dict) else {}
    return {
        "session_id": record.get("session_id") or (path.stem if path else "unknown"),
        "resident": record.get("resident") or "Unknown resident",
        "status": record.get("status") or "unknown",
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at") or record.get("created_at"),
        "participants": record.get("participants") if isinstance(record.get("participants"), list) else [],
        "event_count": len(events),
        "source_artifacts": record.get("source_artifacts") if isinstance(record.get("source_artifacts"), list) else [],
        "outcome_label": outcome.get("label") or "informational",
        "authoritative": bool(outcome.get("authoritative")) and False,
        "canonical_artifact_links": outcome.get("canonical_artifact_links") if isinstance(outcome.get("canonical_artifact_links"), list) else [],
        "path": str(path.relative_to(root)).replace('\\', '/') if path and root else None,
        "authority_label": "non-authoritative conversation session",
    }


def list_sessions(root: str | Path | None = None, *, resident: str | None = None) -> dict[str, Any]:
    root_path = _root(root)
    warnings = []
    summaries = []
    folder = storage_path(root_path)
    if not folder.exists():
        warnings.append({"type": "missing_session_store", "path": str(SESSION_STORE), "required": False})
    else:
        for path in sorted(folder.glob("*.json")):
            data = _read_json(path)
            if not isinstance(data, dict):
                warnings.append({"type": "malformed_session", "path": str(path.relative_to(root_path))})
                continue
            if resident and _slug(data.get("resident")) != _slug(resident):
                continue
            summaries.append(_summary(data, path, root_path))
    summaries.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return {"version": 1, "kind": "resident_conversation_session_list", "generated_at": _now(), "storage_path": str(SESSION_STORE), "sessions": summaries, "warnings": warnings, "authority_boundary": {"authoritative_record": False, "limitations": AUTHORITY_LIMITATIONS}}


def session_summaries_for_workspace(root: str | Path | None = None, *, resident: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    return list_sessions(root, resident=resident)["sessions"][:limit]


def format_session_list(payload: dict[str, Any]) -> str:
    lines = ["Resident Conversation Sessions", f"Storage: {payload.get('storage_path')}", "Authority: non-authoritative conversation audit only"]
    for item in payload.get("sessions") or []:
        lines.append(f"- {item.get('session_id')} | {item.get('resident')} | {item.get('status')} | {item.get('outcome_label')} | events={item.get('event_count')}")
    if not payload.get("sessions"):
        lines.append("No resident conversation sessions recorded yet.")
    return "\n".join(lines)
