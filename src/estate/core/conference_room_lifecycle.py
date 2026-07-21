"""Authoritative, persistent conference membership and moderator lifecycle."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.resident_registry_snapshot import build_resident_registry_snapshot

CONFIG_PATH = Path("config/conference_room_config.json")
SESSION_DIRECTORY = Path("runtime/conference_room/sessions")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _base(root=None) -> Path:
    return Path(root) if root is not None else Path.cwd()


def _canon_base(root=None) -> Path:
    """Use a supplied repository overlay when it contains canon, otherwise source checkout canon."""
    base = _base(root)
    return base if (base / "data/registry/residents.json").exists() else Path(__file__).resolve().parents[3]


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def resident_index(root=None) -> dict[str, dict[str, Any]]:
    snapshot = build_resident_registry_snapshot(_canon_base(root))
    result = {}
    for resident in snapshot.get("active_residents", []):
        for key in (resident.get("id"), resident.get("name")):
            result[str(key or "").strip().lower()] = resident
    return result


def resolve_active_resident(value: str, root=None) -> dict[str, Any]:
    resident = resident_index(root).get(str(value).strip().lower())
    if not resident:
        raise ValueError(f"unknown or inactive resident: {value}")
    return resident


def load_config(root=None) -> dict[str, Any]:
    path = _base(root) / CONFIG_PATH
    if not path.exists(): path = Path(__file__).resolve().parents[3] / CONFIG_PATH
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != "conference_room_config.v1" or config.get("auto_invite_all_residents") is not False:
        raise ValueError("invalid conference-room configuration")
    resolve_active_resident(config.get("default_moderator_resident_id", ""), root)
    return config


def update_default_moderator(value: str, root=None) -> dict[str, Any]:
    base = _base(root); path = base / CONFIG_PATH
    resident = resolve_active_resident(value, root); config = load_config(root)
    former = resolve_active_resident(config["default_moderator_resident_id"], root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(f"{path.name}.{stamp}.bak")
    backup.write_bytes(path.read_bytes())
    config["default_moderator_resident_id"] = resident["id"]
    _atomic_json(path, config)
    audit = base / "runtime/conference_room/config_audit.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"timestamp": _now(), "event": "default_moderator_changed", "former": former["id"], "new": resident["id"], "backup": backup.name, "initiating_authority": "operator"}) + "\n")
    return {"former": former, "new": resident, "backup_path": str(backup), "restart_required": False}


def _session_path(session_id: str, root=None) -> Path:
    digest = hashlib.sha256(session_id.encode()).hexdigest()
    return _base(root) / SESSION_DIRECTORY / f"{digest}.json"


def save_session(state: dict[str, Any], root=None) -> None:
    state["updated_at"] = _now(); _atomic_json(_session_path(state["session_id"], root), state)


def load_or_create_session(session_id: str, root=None) -> tuple[dict[str, Any], bool]:
    path = _session_path(session_id, root)
    if path.exists(): return json.loads(path.read_text(encoding="utf-8")), False
    moderator = resolve_active_resident(load_config(root)["default_moderator_resident_id"], root)
    rid = str(moderator["name"]).lower(); now = _now()
    state = {"schema_version":"conference_room_session.v1", "room_id":f"conference-{hashlib.sha256(session_id.encode()).hexdigest()[:16]}", "session_id":session_id,
             "default_moderator_at_creation":rid, "current_moderator":rid, "backup_moderator":None,
             "active_participants":["steward", rid], "pending_acknowledgement":[], "departed_participants":[], "removed_participants":[],
             "role_history":[{"timestamp":now,"event":"moderator_assigned","resident_id":rid,"initiating_authority":"configuration"}],
             "participant_history":[{"timestamp":now,"event":"room_opened","resident_id":rid,"initiating_authority":"configuration"}], "audit_events":[], "status":"active", "created_at":now}
    save_session(state, root); return state, True


def _event(state, collection, event, resident_id=None, authority="steward", **extra):
    item={"timestamp":_now(),"event":event,"initiating_authority":authority, **extra}
    if resident_id: item["resident_id"]=resident_id
    state[collection].append(item)


def invite(state, values: list[str], root=None) -> list[str]:
    admitted=[]
    for value in values:
        try: resident=resolve_active_resident(value, root)
        except ValueError:
            _event(state,"audit_events","operation_rejected",requested=value,reason="unknown_or_inactive_resident"); continue
        rid=str(resident["name"]).lower()
        if rid in state["active_participants"]: continue
        state["pending_acknowledgement"].append(rid); _event(state,"participant_history","invited",rid)
        # Admission is completed only by the invited resident's own dispatch.
        state["pending_acknowledgement"].remove(rid); state["active_participants"].append(rid)
        for collection in ("departed_participants","removed_participants"):
            if rid in state[collection]: state[collection].remove(rid)
        _event(state,"participant_history","acknowledged",rid,authority=rid); admitted.append(rid)
    return admitted


def transfer(state, value: str, root=None) -> str:
    rid=str(resolve_active_resident(value,root)["name"]).lower()
    if rid not in state["active_participants"]: raise ValueError("moderator must be an active participant")
    former=state["current_moderator"]; state["current_moderator"]=rid
    _event(state,"role_history","moderator_transferred",rid,former_moderator=former)
    return rid


def set_backup(state, value: str | None, root=None) -> str | None:
    if value is None:
        former=state.get("backup_moderator"); state["backup_moderator"]=None; _event(state,"role_history","backup_cleared",former); return None
    rid=str(resolve_active_resident(value,root)["name"]).lower()
    if rid not in state["active_participants"]: raise ValueError("backup moderator must be an active participant")
    state["backup_moderator"]=rid; _event(state,"role_history","backup_assigned",rid); return rid


def depart(state, value: str, *, removed=False, root=None) -> dict[str, Any]:
    rid=str(resolve_active_resident(value,root)["name"]).lower()
    if rid not in state["active_participants"]: raise ValueError("resident is not present")
    if rid == "steward": raise ValueError("Steward lifecycle is controlled by room closure")
    state["active_participants"].remove(rid); bucket="removed_participants" if removed else "departed_participants"; state[bucket].append(rid)
    _event(state,"participant_history","removed" if removed else "departed",rid)
    if state.get("backup_moderator")==rid: state["backup_moderator"]=None
    succession=None
    if state.get("current_moderator")==rid:
        backup=state.get("backup_moderator")
        if backup and backup in state["active_participants"]:
            state["current_moderator"]=backup; state["backup_moderator"]=None; succession=backup
            _event(state,"role_history","backup_activated",backup,former_moderator=rid)
        else:
            state["current_moderator"]=None; state["status"]="paused_for_moderator"
            _event(state,"role_history","moderator_absent",rid)
    return {"resident_id":rid,"successor":succession}


def names_from_text(text: str, root=None) -> list[str]:
    lower=text.lower(); found=[]
    for resident in {r["id"]:r for r in resident_index(root).values()}.values():
        name=str(resident["name"])
        if re.search(rf"\b{re.escape(name.lower())}\b",lower): found.append(name)
    return sorted(found, key=lambda name: lower.find(name.lower()))


def recognize_intent(text: str, root=None) -> dict[str, Any]:
    lower=text.lower(); names=names_from_text(text,root)
    if "who is currently present" in lower or "who is here" in lower: return {"intent":"roster"}
    if "who is the moderator" in lower: return {"intent":"moderator_status"}
    if "clear the backup" in lower: return {"intent":"clear_backup"}
    if "close the meeting" in lower or "close the conference" in lower: return {"intent":"close"}
    if "invite" in lower: return {"intent":"invite","residents":names}
    if "backup moderator" in lower and names:
        if len(names) > 1 and ("make" in lower or "transfer" in lower):
            return {"intent":"assign_roles","moderator":names[0],"backup":names[-1]}
        return {"intent":"set_backup","resident":names[-1]}
    if ("moderator" in lower or "take over" in lower or "transfer moderation" in lower) and names:
        target=names[-1] if " to " in lower or "transfer" in lower else names[0]
        return {"intent":"transfer","resident":target}
    if ("remove" in lower or "leave" in lower) and names: return {"intent":"remove" if "remove" in lower else "depart","resident":names[-1]}
    addressed=[n for n in names if re.search(rf"(^|ask\s+){re.escape(n.lower())}\b",lower)]
    return {"intent":"speak","residents":addressed}
