"""Resident task visibility and governed communications.

This module is a read-only operational view over existing resident, personnel,
presence, mailbox, and message artifacts. It does not create a scheduler,
mailbox registry, dashboard, or communications institution.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "office_resident_task_board.v1"
TASK_STATUS_PATH = Path("runtime/residents/task_status.json")
STALE_AFTER_HOURS = 24
PRIVATE_FIELDS = {"private_journal", "detailed_workforce_assessment", "health_notes", "confidential_notes"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _slug(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _is_stale(value: Any, now: datetime) -> bool:
    parsed = _parse_dt(value)
    if parsed is None:
        return True
    return now - parsed > timedelta(hours=STALE_AFTER_HOURS)


def _messages(root: Path) -> list[dict[str, Any]]:
    items = []
    for path in sorted((root / "collaboration" / "messages").glob("*.json")):
        try:
            message = _read_json(path, {})
        except json.JSONDecodeError:
            continue
        if isinstance(message, dict):
            message["_path"] = str(path.relative_to(root)).replace("\\", "/")
            items.append(message)
    return items


def _dest_aliases(person: dict[str, Any]) -> set[str]:
    mailbox = person.get("mailbox_id")
    display = person.get("display_name")
    office = person.get("current_office")
    aliases = {str(mailbox), f"mailbox.{mailbox}", f"employee.{person.get('employee_id')}", str(display or "")}
    for prefix, value in (("office", office), ("employee", display)):
        aliases.add(f"{prefix}.{str(value or '').strip().lower().replace(' ', '_')}")
    return {a for a in aliases if a and a != "None"}


def unread_message_count(messages: list[dict[str, Any]], person: dict[str, Any]) -> int:
    aliases = _dest_aliases(person)
    return sum(1 for m in messages if str(m.get("destination") or m.get("to") or m.get("destination_mailbox_id") or "") in aliases and m.get("status", "open") not in {"closed", "archived"} and m.get("ack_status") != "acknowledged")


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _status_kind(entry: dict[str, Any], availability: str, blocker: Any, stale: bool) -> str:
    raw = _norm(entry.get("status") or entry.get("state") or availability)
    if stale and raw not in {"waiting", "waiting_on", "waiting_for_steward", "pending"} and not entry.get("waiting_on"):
        return "stale"
    if blocker:
        return "blocked"
    if raw in {"completed", "complete", "done"}:
        return "completed"
    if raw in {"paused", "pause"}:
        return "paused"
    if raw in {"waiting", "waiting_on", "waiting_for_steward", "pending"} or entry.get("waiting_on"):
        return "waiting"
    if raw in {"blocked", "degraded"}:
        return "blocked"
    if raw in {"working", "active", "available", "online"}:
        return "active"
    return "unknown"


def _elapsed_seconds(value: Any, now: datetime) -> int | None:
    parsed = _parse_dt(value)
    if parsed is None:
        return None
    return max(0, int((now - parsed).total_seconds()))


def _matches(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    for field, value in filters.items():
        if value in (None, "", []):
            continue
        hay = row.get(field)
        if field == "staleness":
            want = str(value).lower() in {"1", "true", "stale", "yes"}
            if bool(row.get("stale_status")) != want:
                return False
        elif field == "blocker":
            want = str(value).lower() in {"1", "true", "blocked", "yes"}
            if bool(row.get("blocker")) != want:
                return False
        elif field == "resident":
            if _slug(value) not in {_slug(row.get("resident_id")), _slug(row.get("resident_name")), _slug(row.get("task_owner"))}:
                return False
        elif field == "office":
            if _norm(value) not in _norm(row.get("office")):
                return False
        elif field == "project":
            if _norm(value) not in _norm(row.get("related_work_package_or_project")):
                return False
        elif field == "status":
            if _norm(value) != _norm(row.get("status")) and _norm(value) != _norm(row.get("availability_state")):
                return False
        elif _norm(value) not in _norm(hay):
            return False
    return True


def build_resident_task_board(root: str | Path | None = None, **filters: Any) -> dict[str, Any]:
    base = _root(root)
    now_dt = datetime.now(timezone.utc)
    residents = _read_json(base / "data/registry/residents.json", []) or []
    personnel = _read_json(base / "data/registry/personnel.json", []) or []
    presence = _read_json(base / "runtime/residents/presence.json", {}) or {}
    status = _read_json(base / TASK_STATUS_PATH, {}) or {}
    status_entries = status.get("residents", status if isinstance(status, dict) else [])
    by_status = {_slug(s.get("resident_id") or s.get("name")): s for s in status_entries if isinstance(s, dict)} if isinstance(status_entries, list) else {}
    by_presence = {_slug(p.get("resident_id") or p.get("name")): p for p in presence.get("residents", []) if isinstance(p, dict)}
    all_messages = _messages(base)
    rows = []
    for resident in residents:
        person = next((p for p in personnel if p.get("resident_id") == resident.get("id") or _slug(p.get("display_name")) == _slug(resident.get("name"))), {})
        key = _slug(resident.get("id") or resident.get("name"))
        entry = by_status.get(key) or by_status.get(_slug(resident.get("name"))) or {}
        runtime = by_presence.get(key) or by_presence.get(_slug(resident.get("name"))) or {}
        movement = entry.get("last_meaningful_movement") or runtime.get("last_activity") or runtime.get("last_heartbeat")
        stale = _is_stale(movement, now_dt)
        blocker = entry.get("blocker") or ("status stale or missing" if stale and not entry.get("waiting_on") else None)
        requested_escalation = entry.get("escalation_state")
        escalation = "attention_needed" if runtime.get("needs_steward") or blocker else (requested_escalation or "none")
        public = {k: v for k, v in entry.items() if k not in PRIVATE_FIELDS}
        rows.append({
            "schema_version": SCHEMA_VERSION,
            "resident_id": resident.get("id"),
            "resident_name": resident.get("name"),
            "employee_id": person.get("employee_id"),
            "mailbox_id": person.get("mailbox_id"),
            "current_goal": public.get("current_goal") or public.get("goal") or resident.get("role"),
            "goal": public.get("current_goal") or public.get("goal") or resident.get("role"),
            "current_task": public.get("current_task") or runtime.get("current_duty") or "unknown",
            "task_owner": public.get("task_owner") or person.get("display_name") or resident.get("name"),
            "office": public.get("office") or person.get("current_office") or resident.get("office"),
            "last_meaningful_movement": movement,
            "waiting_on": public.get("waiting_on"),
            "blocker": blocker,
            "next_action": public.get("next_action"),
            "next_checkpoint": public.get("next_checkpoint"),
            "availability_state": public.get("availability_state") or runtime.get("presence_state") or "unknown",
            "status": _status_kind(public, public.get("availability_state") or runtime.get("presence_state") or "unknown", blocker, stale),
            "elapsed_seconds": _elapsed_seconds(movement, now_dt),
            "elapsed_time": None if _elapsed_seconds(movement, now_dt) is None else str(timedelta(seconds=_elapsed_seconds(movement, now_dt))),
            "related_work_package_or_project": public.get("related_work_package") or public.get("work_package") or public.get("project") or "unknown",
            "source_artifact": public.get("source_artifact") or str(TASK_STATUS_PATH),
            "source_last_updated": public.get("source_last_updated") or movement,
            "detail_navigation": {"action_id": "resident_task_board.open_detail", "resident_id": resident.get("id"), "target_tab": "resident-task-board"},
            "unread_message_count": unread_message_count(all_messages, person),
            "escalation_state": escalation,
            "stale_status": stale,
            "source_links": [p for p in ["data/registry/residents.json", "data/registry/personnel.json", str(TASK_STATUS_PATH), "runtime/residents/presence.json"] if (base / p).exists()],
        })
    active_filters = {k: v for k, v in filters.items() if v not in (None, "", [])}
    if active_filters:
        rows = [row for row in rows if _matches(row, active_filters)]
    return {"schema_version": SCHEMA_VERSION, "generated_at": _now(), "privacy": "participant board omits private journals and detailed workforce assessments", "filters": active_filters, "participants": rows}


def write_resident_task_board(root: str | Path | None = None, **filters: Any) -> dict[str, Any]:
    base = _root(root)
    payload = build_resident_task_board(base, **filters)
    path = _write_json(base / "runtime/office/steward_participant_board.json", payload)
    return {"path": str(Path(path).relative_to(base)), "board": payload}


def create_resident_message(sender: str, recipient: str, summary: str, root: str | Path | None = None, *, classification: str = "Estate Internal") -> dict[str, Any]:
    base = _root(root)
    personnel = _read_json(base / "data/registry/personnel.json", []) or []
    by_name = {_slug(p.get("display_name")): p for p in personnel}
    src = by_name.get(_slug(sender))
    dst = by_name.get(_slug(recipient))
    if not src or not dst:
        raise ValueError("sender and recipient must resolve to personnel identities")
    msg_id = f"msg_resident_{_slug(sender)}_to_{_slug(recipient)}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    payload = {"id": msg_id, "version": 1, "created_at": _now(), "created_by": sender, "source": f"mailbox.{src['mailbox_id']}", "destination": f"mailbox.{dst['mailbox_id']}", "classification": classification, "message_type": "resident_operational_message", "priority": "normal", "status": "open", "requires_ack": True, "governance": "existing mailbox/message mechanism; no Steward-as-bus transport", "payload": {"title": "Resident operational message", "summary": summary, "artifact_refs": []}}
    rel = _write_json(base / "collaboration/messages" / f"{msg_id}.json", payload)
    return {"message": payload, "path": str(Path(rel).relative_to(base))}


def alfred_attention_summary(root: str | Path | None = None) -> dict[str, Any]:
    board = build_resident_task_board(root)
    items = [p for p in board["participants"] if p["stale_status"] or p["escalation_state"] != "none" or p["unread_message_count"]]
    return {"generated_at": board["generated_at"], "attention_count": len(items), "items": items[:5]}


def grace_operational_status(root: str | Path | None = None) -> dict[str, Any]:
    board = build_resident_task_board(root)
    return {"generated_at": board["generated_at"], "active_or_blocked": [p for p in board["participants"] if p["availability_state"] in {"working", "waiting_for_steward", "degraded"}], "authority": "status consumption only; does not activate unauthorized roles"}


def helen_availability_constraints(root: str | Path | None = None) -> dict[str, Any]:
    board = build_resident_task_board(root)
    constrained = [{"resident_id": p["resident_id"], "resident_name": p["resident_name"], "availability_state": p["availability_state"], "waiting_on": p["waiting_on"], "blocker": p["blocker"]} for p in board["participants"] if p["availability_state"] != "available" or p["blocker"]]
    return {"generated_at": board["generated_at"], "constraints": constrained, "privacy": "excludes private workforce assessments"}
