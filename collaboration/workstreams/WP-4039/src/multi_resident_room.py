"""Staged deterministic multi-resident conversation room core for WP-4039.

This module is intentionally uninstalled.  It performs no gateway routing,
provider calls, privileged actions, or transcript persistence.  Callers provide
normalized resident identifiers, participant metadata, context packets, and
adapter-generated responses.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

SCHEMA_VERSION = "conversation_room_v1"
TURN_SCHEMA_VERSION = "conversation_turn_v1"
STAGED_WORK_IS_INSTALLED = False

PARTICIPANT_STATES = {"invited", "accepted", "declined", "unavailable", "removed", "suspended"}
ROOM_MODES = {"roundtable", "targeted", "moderated", "consultation", "quiet_observer"}
ROOM_STATUSES = {"active", "paused", "archived"}
PROHIBITED_CONTEXT_CLASSES = {"evelyn_private_relationship", "hr_private", "security_private", "workforce_private"}
PRIVILEGED_ACTIONS = {"appoint", "hire", "approve", "merge", "dispatch", "spend", "change_policy"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_hash(parts: Iterable[Any]) -> str:
    body = "|".join(str(p) for p in parts)
    return sha256(body.encode("utf-8")).hexdigest()[:16]


def stable_room_id(display_name: str, created_by: str, created_at: str) -> str:
    return f"room_{_stable_hash([display_name, created_by, created_at])}"


def stable_user_turn_id(room_id: str, user_text: str, idempotency_key: str) -> str:
    return f"uturn_{_stable_hash([room_id, user_text, idempotency_key])}"


def stable_resident_turn_id(room_id: str, user_turn_id: str, resident_id: str, turn_order: int) -> str:
    return f"rturn_{_stable_hash([room_id, user_turn_id, resident_id, turn_order])}"


def create_room(
    *,
    display_name: str,
    created_by: str,
    classification: str = "private-room",
    created_at: Optional[str] = None,
    room_purpose: str = "shared resident discussion",
    room_mode: str = "roundtable",
    speaking_policy: Optional[Mapping[str, Any]] = None,
    context_policy: Optional[Mapping[str, Any]] = None,
    transcript_reference: Optional[Mapping[str, Any]] = None,
    session_reference: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if room_mode not in ROOM_MODES:
        raise ValueError(f"unsupported room mode: {room_mode}")
    created_at = created_at or _utc_now()
    policy = {"type": "alphabetical", "max_responses_per_user_turn": 8}
    if speaking_policy:
        policy.update(deepcopy(dict(speaking_policy)))
    room = {
        "schema_version": SCHEMA_VERSION,
        "room_id": stable_room_id(display_name, created_by, created_at),
        "display_name": display_name,
        "classification": classification,
        "created_by": created_by,
        "created_at": created_at,
        "status": "active",
        "participants": [],
        "resident_participants": [],
        "human_participants": [{"participant_id": created_by, "kind": "human", "state": "accepted", "display_name": created_by}],
        "room_purpose": room_purpose,
        "room_mode": room_mode,
        "speaking_policy": policy,
        "context_policy": deepcopy(dict(context_policy or {"default_private_context": "omit"})),
        "transcript_reference": deepcopy(transcript_reference or {}),
        "session_reference": deepcopy(session_reference or {"resume_token": f"resume_{_stable_hash([display_name, created_by, created_at, 'resume'])}"}),
        "active_topic": None,
        "pending_questions": [],
        "shared_context": [],
        "resident_context_packets": {},
        "turns": [],
        "mode_history": [{"mode": room_mode, "changed_at": created_at, "changed_by": created_by, "reversible": True}],
        "audit_metadata": {"staged": True, "installed": False, "privileged_actions_executed": [], "events": []},
    }
    return room


def _find_participant(room: Mapping[str, Any], participant_id: str) -> Optional[Dict[str, Any]]:
    for p in room.get("participants", []):
        if p.get("participant_id") == participant_id:
            return p
    return None


def invite_participant(room: Dict[str, Any], *, participant_id: str, kind: str, display_name: str,
                       role: Optional[str] = None, office: Optional[str] = None,
                       unavailable: bool = False, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    existing = _find_participant(room, participant_id)
    if existing:
        return deepcopy(room)
    state = "unavailable" if unavailable else "invited"
    participant = {"participant_id": participant_id, "kind": kind, "display_name": display_name, "state": state,
                   "role": role, "office": office, "invited_at": _utc_now(), "idempotency_key": idempotency_key}
    new = deepcopy(room)
    new["participants"].append(participant)
    key = "resident_participants" if kind == "resident" else "human_participants"
    if not any(p.get("participant_id") == participant_id for p in new[key]):
        new[key].append(participant)
    new["audit_metadata"]["events"].append({"event": "participant_invited", "participant_id": participant_id, "state": state})
    return new


def _set_state(room: Dict[str, Any], participant_id: str, state: str, reason: Optional[str] = None) -> Dict[str, Any]:
    if state not in PARTICIPANT_STATES:
        raise ValueError(f"unsupported participant state: {state}")
    new = deepcopy(room)
    found = False
    for collection in ("participants", "resident_participants", "human_participants"):
        for p in new.get(collection, []):
            if p.get("participant_id") == participant_id:
                p["state"] = state
                if reason:
                    p["reason"] = reason
                found = True
    if not found:
        raise ValueError("participant must be explicitly invited before state changes")
    new["audit_metadata"]["events"].append({"event": f"participant_{state}", "participant_id": participant_id, "reason": reason})
    return new


def accept_participant(room: Dict[str, Any], participant_id: str) -> Dict[str, Any]: return _set_state(room, participant_id, "accepted")
def decline_participant(room: Dict[str, Any], participant_id: str, reason: Optional[str] = None) -> Dict[str, Any]: return _set_state(room, participant_id, "declined", reason)
def remove_participant(room: Dict[str, Any], participant_id: str, reason: Optional[str] = None) -> Dict[str, Any]: return _set_state(room, participant_id, "removed", reason)
def mark_unavailable(room: Dict[str, Any], participant_id: str, reason: Optional[str] = None) -> Dict[str, Any]: return _set_state(room, participant_id, "unavailable", reason)


def set_room_mode(room: Dict[str, Any], mode: str, *, changed_by: str, rationale: str = "explicit change") -> Dict[str, Any]:
    if mode not in ROOM_MODES:
        raise ValueError(f"unsupported room mode: {mode}")
    new = deepcopy(room); previous = new["room_mode"]; new["room_mode"] = mode
    new["mode_history"].append({"from": previous, "mode": mode, "changed_by": changed_by, "changed_at": _utc_now(), "rationale": rationale, "reversible": True})
    return new


def add_context(room: Dict[str, Any], *, shared_context: Optional[Sequence[Mapping[str, Any]]] = None,
                resident_context_packets: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None) -> Dict[str, Any]:
    new = deepcopy(room)
    for item in shared_context or []:
        if item.get("classification") in PROHIBITED_CONTEXT_CLASSES and not item.get("authorized_promotion"):
            new["audit_metadata"]["events"].append({"event": "context_omitted", "reason": "prohibited_private_context", "source_reference": item.get("source_reference")})
            continue
        new["shared_context"].append(deepcopy(dict(item)))
    for rid, packets in (resident_context_packets or {}).items():
        new["resident_context_packets"].setdefault(rid, [])
        for item in packets:
            new["resident_context_packets"][rid].append(deepcopy(dict(item)))
    return new


def filtered_context_for(room: Mapping[str, Any], resident_id: str) -> Dict[str, Any]:
    omissions = []
    shared = []
    for item in room.get("shared_context", []):
        if item.get("classification") in PROHIBITED_CONTEXT_CLASSES and not item.get("authorized_promotion"):
            omissions.append({"reason": "prohibited_private_context", "source_reference": item.get("source_reference")})
        else:
            shared.append(deepcopy(item))
    return {"shared_context": shared, "resident_private_context": deepcopy(room.get("resident_context_packets", {}).get(resident_id, [])), "omissions": omissions}


def submit_user_turn(room: Dict[str, Any], *, text: str, submitted_by: str, idempotency_key: str,
                     target_resident_ids: Optional[Sequence[str]] = None, active_topic: Optional[str] = None) -> Dict[str, Any]:
    new = deepcopy(room)
    user_turn_id = stable_user_turn_id(new["room_id"], text, idempotency_key)
    for t in new["turns"]:
        if t.get("user_turn_id") == user_turn_id and t.get("speaker_kind") == "human":
            return new
    if active_topic: new["active_topic"] = active_topic
    new["turns"].append({"schema_version": TURN_SCHEMA_VERSION, "turn_id": user_turn_id, "user_turn_id": user_turn_id, "room_id": new["room_id"], "speaker_kind": "human", "speaker_id": submitted_by, "text": text, "target_resident_ids": list(target_resident_ids or []), "created_at": _utc_now()})
    new["pending_questions"].append({"user_turn_id": user_turn_id, "text": text, "target_resident_ids": list(target_resident_ids or []), "status": "pending"})
    return new


def _accepted_residents(room: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [p for p in room.get("resident_participants", []) if p.get("state") == "accepted"]


def plan_resident_turns(room: Mapping[str, Any], user_turn_id: str, *, target_resident_ids: Optional[Sequence[str]] = None,
                        role_priority: Optional[Sequence[str]] = None, moderator_order: Optional[Sequence[str]] = None,
                        moderator_rationale: Optional[str] = None, max_responses: Optional[int] = None) -> List[Dict[str, Any]]:
    if room.get("status") != "active":
        return []
    accepted = {p["participant_id"]: p for p in _accepted_residents(room)}
    targets = list(target_resident_ids or [])
    mode = room.get("room_mode")
    policy = room.get("speaking_policy", {})
    if mode == "targeted" or targets:
        ordered_ids = [rid for rid in targets if rid in accepted]
    elif mode == "moderated" and moderator_order:
        ordered_ids = [rid for rid in moderator_order if rid in accepted]
    elif policy.get("type") == "explicit":
        ordered_ids = [rid for rid in policy.get("ordered_resident_ids", []) if rid in accepted]
    elif policy.get("type") == "role_priority" or role_priority:
        priority = list(role_priority or policy.get("role_priority", []))
        ordered = sorted(accepted.values(), key=lambda p: (priority.index(p.get("role")) if p.get("role") in priority else 999, p.get("display_name", p["participant_id"])))
        ordered_ids = [p["participant_id"] for p in ordered]
    else:
        ordered_ids = [p["participant_id"] for p in sorted(accepted.values(), key=lambda p: (p.get("display_name", ""), p["participant_id"]))]
    limit = min(max_responses or policy.get("max_responses_per_user_turn", 8), policy.get("max_responses_per_user_turn", 8))
    plans = []
    for idx, rid in enumerate(ordered_ids[:limit], start=1):
        p = accepted[rid]
        plans.append({"room_id": room["room_id"], "source_user_turn_id": user_turn_id, "resident_id": rid, "display_name": p.get("display_name"), "office": p.get("office"), "role": p.get("role"), "turn_order": idx, "planned_status": "ready", "moderator_rationale": moderator_rationale if mode == "moderated" else None, "context_packet": filtered_context_for(room, rid)})
    return plans


def record_resident_turn(room: Dict[str, Any], plan: Mapping[str, Any], *, text: str = "", response_status: str = "responded",
                         model_metadata: Optional[Mapping[str, Any]] = None, fallback_status: str = "not_used",
                         authority_disclaimer: str = "conversation only; no authority expansion") -> Dict[str, Any]:
    new = deepcopy(room)
    turn_id = stable_resident_turn_id(new["room_id"], plan["source_user_turn_id"], plan["resident_id"], plan["turn_order"])
    if any(t.get("turn_id") == turn_id for t in new["turns"]): return new
    ctx = plan.get("context_packet", {})
    new["turns"].append({"schema_version": TURN_SCHEMA_VERSION, "turn_id": turn_id, "room_id": new["room_id"], "source_user_turn_id": plan["source_user_turn_id"], "speaker_kind": "resident", "resident_id": plan["resident_id"], "display_name": plan.get("display_name"), "office": plan.get("office"), "role": plan.get("role"), "turn_order": plan["turn_order"], "response_status": response_status, "text": text, "model_metadata": deepcopy(dict(model_metadata or {})), "fallback_status": fallback_status, "context_omissions": deepcopy(ctx.get("omissions", [])), "authority_disclaimer_metadata": {"disclaimer": authority_disclaimer, "no_authority_expansion": True}, "created_at": _utc_now()})
    return new


def plan_resident_to_resident_turns(room: Mapping[str, Any], *, source_user_turn_id: str, from_resident_id: str,
                                    to_resident_ids: Sequence[str], enabled: bool, max_depth: int, current_depth: int,
                                    max_turn_count: int) -> List[Dict[str, Any]]:
    if not enabled or current_depth >= max_depth or max_turn_count <= 0:
        return []
    return plan_resident_turns(room, source_user_turn_id, target_resident_ids=to_resident_ids, max_responses=max_turn_count)


def pause_room(room: Dict[str, Any], reason: str = "paused by request") -> Dict[str, Any]:
    new = deepcopy(room); new["status"] = "paused"; new["audit_metadata"]["events"].append({"event": "room_paused", "reason": reason}); return new

def resume_room(room: Dict[str, Any], resume_token: str) -> Dict[str, Any]:
    if resume_token != room.get("session_reference", {}).get("resume_token"):
        raise ValueError("invalid resume token")
    new = deepcopy(room); new["status"] = "active"; new["audit_metadata"]["events"].append({"event": "room_resumed"}); return new

def archive_room(room: Dict[str, Any], reason: str = "archived by request") -> Dict[str, Any]:
    new = deepcopy(room); new["status"] = "archived"; new["audit_metadata"]["events"].append({"event": "room_archived", "reason": reason}); return new


def execute_privileged_action(room: Mapping[str, Any], action: str) -> Dict[str, Any]:
    return {"executed": False, "action": action, "blocked": action in PRIVILEGED_ACTIONS, "reason": "room core cannot execute privileged actions"}


def office_projection(room: Mapping[str, Any], current_caller: str) -> Dict[str, Any]:
    invited = [p["participant_id"] for p in room.get("participants", []) if p.get("state") == "invited"]
    blocked = [e for e in room.get("audit_metadata", {}).get("events", []) if "omitted" in e.get("event", "")]
    return {"room_name": room.get("display_name"), "status": room.get("status"), "classification": room.get("classification"), "participants": deepcopy(room.get("participants", [])), "current_mode": room.get("room_mode"), "active_topic": room.get("active_topic"), "pending_invited_speakers": invited, "last_activity": room.get("turns", [{}])[-1].get("created_at") if room.get("turns") else room.get("created_at"), "blocked_reasons": blocked, "transcript_reference": deepcopy(room.get("transcript_reference", {})), "session_reference": deepcopy(room.get("session_reference", {})), "safe_actions": ["invite_participant", "set_room_mode", "submit_user_turn", "pause_room", "resume_room", "archive_room"] if room.get("status") != "archived" else []}


def room_snapshot(room: Mapping[str, Any]) -> Dict[str, Any]:
    snap = deepcopy(dict(room)); snap["staged_work_is_installed"] = STAGED_WORK_IS_INSTALLED; return snap
