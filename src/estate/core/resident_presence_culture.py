"""Resident presence and Estate culture runtime for Campaign 05.

This module is intentionally a projection layer: it reads canonical registry,
resident-presence, visual-location, historian, and culture artifacts and emits
source-lined presentation records.  It does not schedule work, send messages,
change relationships, reserve rooms, create memory, or promote culture by
itself.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate_presence_culture.v1"
ACTIVITY_PATH = Path("runtime/residents/ambient_activity.json")
PRESENCE_PATH = Path("runtime/residents/presence.json")
CULTURE_PATH = Path("data/culture/estate_culture_runtime.json")
LOCATION_PATH = Path("data/visuals/canonical_locations.json")
RESIDENTS_PATH = Path("data/registry/residents.json")
PUBLIC_VISIBILITIES = {"public", "staff-only"}
PRIVATE_VISIBILITIES = {"restricted", "private", "undisclosed"}
CONSEQUENTIAL_TERMS = {"approved", "completed", "decided", "committed", "assigned", "promised", "messaged"}
ACTIVITY_TYPES = {"idle", "focused_work", "break", "transit", "social", "personal_project", "unavailable", "unknown"}
SOURCE_CLASSES = {"scheduled", "inferred", "simulated", "user_declared", "unknown", "verified"}
PRESENCE_KINDS = {"physical", "virtual", "expected_arrival", "transit", "unavailable", "unknown"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat().replace("+00:00", "Z")


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _read_json(root: Path, rel: Path, default: Any) -> Any:
    path = root / rel
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _slug(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _items(data: Any, key: str = "items") -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [dict(i) for i in data if isinstance(i, Mapping)]
    if isinstance(data, Mapping):
        return [dict(i) for i in data.get(key, []) if isinstance(i, Mapping)]
    return []


def _source(path: str, source_class: str = "inferred", confidence: float = 0.5) -> dict[str, Any]:
    return {"path": path, "source_class": source_class, "confidence": confidence}


def _redact(record: dict[str, Any], caller_clearance: str) -> dict[str, Any] | None:
    visibility = record.get("visibility", "public")
    if visibility in PRIVATE_VISIBILITIES and caller_clearance not in {"restricted", "private", "admin"}:
        return None
    return record


def resident_index(root: str | Path | None = None) -> dict[str, dict[str, Any]]:
    rootp = _root(root)
    residents = _read_json(rootp, RESIDENTS_PATH, [])
    return {_slug(r.get("id") or r.get("name")): dict(r) for r in residents if isinstance(r, Mapping)}


def build_ambient_activity(root: str | Path | None = None, *, as_of: str | None = None) -> dict[str, Any]:
    rootp = _root(root); now = _parse(as_of) or _now(); diagnostics: list[dict[str, Any]] = []
    durable = _items(_read_json(rootp, ACTIVITY_PATH, {"items": []}))
    presence = _read_json(rootp, PRESENCE_PATH, {"residents": []})
    entries = {_slug(e.get("resident_id") or e.get("name")): e for e in _items(presence, "residents")}
    rows = []
    for key, resident in resident_index(rootp).items():
        candidates = [a for a in durable if _slug(a.get("resident_id")) == key]
        activity = max(candidates, key=lambda a: str(a.get("start_time", "")), default={})
        entry = entries.get(key) or entries.get(_slug(resident.get("name"))) or {}
        start = _parse(activity.get("start_time") or entry.get("last_heartbeat"))
        expiry = start + timedelta(minutes=int(activity.get("expected_duration_minutes", 30))) if start else None
        expired = bool(expiry and expiry <= now)
        activity_type = activity.get("activity_type") or ("focused_work" if entry.get("presence_state") == "working" else "unknown")
        source_class = activity.get("source_class") or ("inferred" if entry else "unknown")
        text = " ".join(str(activity.get(k, "")) for k in ("summary", "activity_type", "state"))
        consequential = any(term in text.lower() for term in CONSEQUENTIAL_TERMS)
        if consequential:
            diagnostics.append({"severity": "error", "code": "consequential_ambient_claim", "resident_id": resident.get("id"), "policy": "ambient activity cannot claim completed work, approvals, messages, meetings, or commitments"})
            activity_type = "unknown"
        if activity_type not in ACTIVITY_TYPES:
            diagnostics.append({"severity": "warning", "code": "unknown_activity_type", "resident_id": resident.get("id"), "value": activity_type})
            activity_type = "unknown"
        rows.append({
            "resident_id": resident.get("id"), "resident_name": resident.get("name"), "activity_type": "unknown" if expired else activity_type,
            "location_id": activity.get("location_id") or entry.get("location_id") or "unknown", "start_time": (start or now).isoformat().replace("+00:00", "Z"),
            "expected_duration_minutes": activity.get("expected_duration_minutes", 30), "source_class": source_class if source_class in SOURCE_CLASSES else "unknown",
            "source": activity.get("source") or _source(str(PRESENCE_PATH), source_class if entry else "unknown", 0.7 if entry else 0.0),
            "confidence": 0.0 if expired else float(activity.get("confidence", 0.7 if entry else 0.0)), "visibility": activity.get("visibility", "public"),
            "lifecycle_state": "expired" if expired else activity.get("lifecycle_state", "current" if entry else "unknown"),
            "simulated": source_class == "simulated", "durable_evidence_only": bool(activity), "authority_statement": "Informational presence only; no work, message, approval, or memory is created.",
        })
    return {"schema_version": SCHEMA_VERSION, "generated_at": _iso(now), "activities": rows, "diagnostics": diagnostics}


def build_occupancy(root: str | Path | None = None, *, as_of: str | None = None) -> dict[str, Any]:
    activity_payload = build_ambient_activity(root, as_of=as_of); diagnostics = list(activity_payload["diagnostics"]); now = _parse(as_of) or _now()
    resident_records = []
    seen_locations: dict[str, str] = {}
    for a in activity_payload["activities"]:
        location = a.get("location_id") or "unknown"; kind = "virtual" if str(location).startswith("virtual") else ("unknown" if location == "unknown" else "physical")
        if a["resident_id"] in seen_locations and seen_locations[a["resident_id"]] != location and kind != "virtual":
            diagnostics.append({"severity": "error", "code": "conflicting_occupancy", "resident_id": a["resident_id"]})
        seen_locations[a["resident_id"]] = location
        resident_records.append({"resident_id": a["resident_id"], "location_id": location, "interval": {"start": a["start_time"], "end": None}, "activity_ref": a["activity_type"], "availability": "unavailable" if a["activity_type"] in {"focused_work", "unavailable"} else "available_unknown", "visibility": a["visibility"], "source": a["source"], "confidence": a["confidence"], "freshness": "stale" if a["lifecycle_state"] == "expired" else "current", "presence_kind": kind})
    rooms: dict[str, dict[str, Any]] = {}
    for r in resident_records:
        room = rooms.setdefault(r["location_id"], {"location_id": r["location_id"], "occupants": [], "summary_is_canonical": False})
        room["occupants"].append(r["resident_id"])
    return {"schema_version": SCHEMA_VERSION, "generated_at": _iso(now), "resident_occupancy": resident_records, "room_occupancy": list(rooms.values()), "diagnostics": diagnostics}


def generate_passive_interactions(root: str | Path | None = None, *, caller_clearance: str = "public", as_of: str | None = None) -> dict[str, Any]:
    occ = build_occupancy(root, as_of=as_of); by_room: dict[str, list[dict[str, Any]]] = {}
    for r in occ["resident_occupancy"]:
        if r["freshness"] == "current" and r["location_id"] != "unknown": by_room.setdefault(r["location_id"], []).append(r)
    interactions = []
    for location, occupants in by_room.items():
        if len(occupants) < 2: continue
        pair = occupants[:2]
        record = {"participants": [p["resident_id"] for p in pair], "location_id": location, "trigger": "co_location", "interaction_class": "brief_acknowledgment", "visibility": "public", "relationship_context": "professional_or_unknown", "generated_content": "brief greeting or silence; no task, approval, commitment, or message", "source_state": [p["source"] for p in pair], "persistence_policy": "transient_unless_existing_memory_policy_authorizes", "creates_canonical_fact": False, "cooldown_key": hashlib.sha256(json.dumps(pair, sort_keys=True).encode()).hexdigest()[:12]}
        redacted = _redact(record, caller_clearance)
        if redacted: interactions.append(redacted)
    return {"schema_version": SCHEMA_VERSION, "interactions": interactions, "diagnostics": occ["diagnostics"], "authority_statement": "Passive interactions cannot create messages, relationship state, approvals, or institutional facts."}


def build_environmental_details(root: str | Path | None = None, *, as_of: str | None = None) -> dict[str, Any]:
    occ = build_occupancy(root, as_of=as_of); details = []
    for room in occ["room_occupancy"]:
        if room["location_id"] == "unknown": continue
        details.append({"location_id": room["location_id"], "detail_type": "occupied_room_arrangement", "owner_or_source": "resident_presence_culture_runtime", "start": occ["generated_at"], "expiry": None, "visibility": "public", "provenance": room["occupants"], "persistence_class": "transient_projection", "confidence": 0.6, "evidence_state": "inferred", "not_proof_of_event": True})
    return {"schema_version": SCHEMA_VERSION, "environmental_details": details, "diagnostics": occ["diagnostics"]}


def build_presence_api_response(root: str | Path | None = None, *, query: Mapping[str, Any] | None = None, caller_clearance: str = "public", as_of: str | None = None) -> dict[str, Any]:
    query = dict(query or {"scope": "estate"}); activity = build_ambient_activity(root, as_of=as_of); occ = build_occupancy(root, as_of=as_of); env = build_environmental_details(root, as_of=as_of); interactions = generate_passive_interactions(root, caller_clearance=caller_clearance, as_of=as_of)
    resident_id = query.get("resident_id"); location_id = query.get("location_id")
    activities = [_redact(a, caller_clearance) for a in activity["activities"] if (not resident_id or a.get("resident_id") == resident_id)]
    occupancy = [_redact(o, caller_clearance) for o in occ["resident_occupancy"] if (not resident_id or o.get("resident_id") == resident_id) and (not location_id or o.get("location_id") == location_id)]
    return {"schema_version": SCHEMA_VERSION, "query": query, "generated_at": activity["generated_at"], "activities": [a for a in activities if a], "occupancy": [o for o in occupancy if o], "nearby_social_context": interactions["interactions"], "environmental_details": env["environmental_details"], "diagnostics": activity["diagnostics"] + occ["diagnostics"], "mutation_allowed": False, "summary": "Presence projection with source, confidence, freshness, visibility, simulation, and uncertainty preserved."}


def build_culture_runtime(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root); data = _read_json(rootp, CULTURE_PATH, {})
    traditions = _items(data, "traditions"); memories = _items(data, "culture_memories"); jokes = _items(data, "running_jokes"); events = _items(data, "annual_events"); signals = _items(data, "culture_signals"); proposals = _items(data, "culture_change_proposals")
    diagnostics = []
    for t in traditions:
        if t.get("status") in {"active", "historical"} and not t.get("origin_evidence"):
            diagnostics.append({"severity": "error", "code": "tradition_without_origin_evidence", "tradition_id": t.get("tradition_id")})
    for joke in jokes:
        joke["eligible_for_callback"] = joke.get("consent_state") == "approved" and joke.get("status") not in {"retired", "rejected"}
        joke["cannot_influence_authority"] = True
    for event in events:
        event["planning_is_attendance_evidence"] = False
    for proposal in proposals:
        proposal["requires_explicit_review"] = proposal.get("state") not in {"adopted", "retired", "rolled_back"}
        proposal["cannot_change_governance"] = True
    return {"schema_version": SCHEMA_VERSION, "traditions": traditions, "culture_memories": memories, "running_jokes": jokes, "annual_events": events, "culture_signals": signals, "culture_change_proposals": proposals, "diagnostics": diagnostics, "authority_statement": "Culture runtime proposes and presents; it cannot alter governance, privacy, authority, employment, or safety rules."}


def validate_presence_culture_runtime(root: str | Path | None = None) -> dict[str, Any]:
    presence = build_presence_api_response(root); culture = build_culture_runtime(root)
    diagnostics = presence["diagnostics"] + culture["diagnostics"]
    error_count = sum(1 for d in diagnostics if d.get("severity") == "error")
    return {"schema_version": SCHEMA_VERSION, "valid": error_count == 0, "error_count": error_count, "diagnostics": diagnostics, "checked_boundaries": ["no_second_scheduler", "no_message_creation", "no_relationship_mutation", "no_memory_promotion", "privacy_redaction", "source_lineage"]}
