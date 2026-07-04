"""Local-first resident runtime presence model.

Presence describes visible local runtime state only. It does not grant Estate
residents authority, start autonomous execution, or bypass Steward, mailbox, or
validation boundaries.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

INITIAL_RESIDENT_NAMES = ("Alfred", "Helen")
PRESENCE_STATES = {"offline", "available", "working", "waiting_for_steward", "degraded", "error"}
RUNTIME_PATH = Path("runtime/residents/presence.json")
STALE_AFTER_MINUTES = 60 * 24


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _read_json(path: Path, warnings: list[dict[str, Any]], *, required: bool = False) -> Any:
    if not path.exists():
        warnings.append({"type": "missing_artifact", "path": str(path), "required": required})
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": str(path), "message": str(exc), "required": required})
        return None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _is_stale(value: Any, now: datetime | None = None) -> bool:
    parsed = _parse_dt(value)
    if not parsed:
        return False
    return ((now or datetime.now(timezone.utc)) - parsed) > timedelta(minutes=STALE_AFTER_MINUTES)


def _runtime_entries(runtime: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(runtime, dict):
        return {}
    if isinstance(runtime.get("residents"), list):
        return {_slug(r.get("resident_id") or r.get("name")): r for r in runtime["residents"] if isinstance(r, dict)}
    return {_slug(k): v for k, v in runtime.items() if isinstance(v, dict)}


def _mailbox_path(mailbox_id: Any, root: Path) -> str | None:
    if mailbox_id is None:
        return None
    for candidate in (root / "collaboration" / "mailboxes" / str(mailbox_id), root / "collaboration" / "mailboxes" / f"mailbox.{mailbox_id}"):
        if candidate.exists():
            return _rel(candidate, root)
    return f"collaboration/mailboxes/{mailbox_id}"


def _linked_personnel(name: str, resident: dict[str, Any], personnel: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((p for p in personnel if p.get("resident_id") == resident.get("id") or _slug(p.get("display_name")) == _slug(name)), None)


def _resident_details(root: Path, resident: dict[str, Any]) -> str | None:
    if resident.get("id") and (root / "data" / "objects" / f"{resident['id']}.json").exists():
        return _rel(root / "data" / "objects" / f"{resident['id']}.json", root)
    profile = root / "residents" / f"{_slug(resident.get('name'))}.md"
    if profile.exists():
        return _rel(profile, root)
    return resident.get("canonical")


def build_resident_presence(root: str | Path | None = None, names: tuple[str, ...] = INITIAL_RESIDENT_NAMES) -> dict[str, Any]:
    root = _root(root)
    warnings: list[dict[str, Any]] = []
    residents = _read_json(root / "data/registry/residents.json", warnings) or []
    personnel = _read_json(root / "data/registry/personnel.json", warnings) or []
    runtime = _read_json(root / RUNTIME_PATH, warnings) or _read_json(root / "runtime/residents/status.json", warnings) or {}
    entries = _runtime_entries(runtime)
    by_name = {_slug(r.get("name")): r for r in residents if isinstance(r, dict)}
    by_id = {_slug(r.get("id")): r for r in residents if isinstance(r, dict)}
    items = []
    for name in names:
        resident = by_name.get(_slug(name), {"name": name})
        entry = entries.get(_slug(name)) or entries.get(_slug(resident.get("id"))) or {}
        person = _linked_personnel(name, resident, personnel if isinstance(personnel, list) else []) or {}
        heartbeat = entry.get("last_heartbeat") or entry.get("heartbeat_at")
        state = entry.get("presence_state") or entry.get("state") or ("available" if resident.get("id") else "degraded")
        if state not in PRESENCE_STATES:
            state = "degraded"
        stale = _is_stale(heartbeat)
        limitations = []
        if not resident.get("id"):
            limitations.append("Resident registry record is missing; visible presence is degraded.")
        if not entry:
            limitations.append("No dedicated resident runtime presence entry is available; registry-derived placeholder is shown.")
        if stale:
            limitations.append("Last heartbeat is stale; presence may not reflect live activity.")
            if state in {"available", "working"}:
                state = "degraded"
        items.append({
            "resident_id": resident.get("id"),
            "name": resident.get("name") or name,
            "display_name": person.get("display_name") or resident.get("name") or name,
            "role": resident.get("role") or resident.get("office"),
            "office": person.get("current_office") or resident.get("department") or resident.get("office"),
            "mailbox_id": person.get("mailbox_id") or entry.get("mailbox_id"),
            "mailbox_path": entry.get("mailbox_path") or _mailbox_path(person.get("mailbox_id") or entry.get("mailbox_id"), root),
            "presence_state": state,
            "current_duty": entry.get("current_duty") or entry.get("duty"),
            "last_heartbeat": heartbeat,
            "last_activity": entry.get("last_activity"),
            "heartbeat_stale": stale,
            "needs_steward": bool(entry.get("needs_steward") or state == "waiting_for_steward"),
            "status_reason": entry.get("status_reason") or ("; ".join(limitations) if limitations else "Presence is visible local runtime state only; no autonomous execution authority is implied."),
            "visible_presence_only": True,
            "autonomous_execution": False,
            "source_artifacts": [p for p in ["data/registry/residents.json", "data/registry/personnel.json", str(RUNTIME_PATH), _resident_details(root, resident)] if p],
        })
    selected = [i for i in items if not names or any(_slug(i["name"]) == _slug(n) or _slug(i.get("resident_id")) == _slug(n) for n in names)]
    return {"version": 1, "generated_at": _now(), "runtime_artifact": str(RUNTIME_PATH), "residents": selected, "warnings": warnings, "authority_statement": "Resident presence is informational and does not grant authority to act."}


def filter_resident(payload: dict[str, Any], resident: str | None) -> dict[str, Any]:
    if not resident:
        return payload
    wanted = _slug(resident)
    copy = dict(payload)
    copy["residents"] = [r for r in payload.get("residents", []) if _slug(r.get("name")) == wanted or _slug(r.get("resident_id")) == wanted]
    if not copy["residents"]:
        copy.setdefault("warnings", []).append({"type": "resident_not_found", "resident": resident, "required": False})
    return copy


def format_resident_presence(payload: dict[str, Any]) -> str:
    lines = ["Resident Runtime Presence", payload.get("authority_statement", "")]
    for r in payload.get("residents", []):
        lines += ["", f"- {r.get('display_name')} ({r.get('resident_id') or 'unregistered'})", f"  State: {r.get('presence_state')} (visible only; autonomous_execution={r.get('autonomous_execution')})", f"  Duty: {r.get('current_duty') or 'Not available yet'}", f"  Heartbeat: {r.get('last_heartbeat') or 'Not available yet'} stale={r.get('heartbeat_stale')}", f"  Mailbox: {r.get('mailbox_id') or 'Not available yet'} {r.get('mailbox_path') or ''}", f"  Needs Steward: {r.get('needs_steward')}", f"  Reason: {r.get('status_reason')}"]
    return "\n".join(lines)
