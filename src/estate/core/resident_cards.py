"""Reusable resident-card data model for Office of the Steward surfaces.

Resident cards are local-first summaries assembled from existing Estate
registries and runtime artifacts. They do not create authority, lifecycle
state, or resident-specific business logic; missing data is represented with
explicit placeholders so future residents can reuse the same model.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_presence import build_resident_presence
from estate.core.resident_authority import list_authority

INITIAL_RESIDENT_NAMES = ("Alfred", "Helen")
PLACEHOLDER = "Not available yet"


def _root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value):
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _read_json(path, warnings, required=False):
    if not path.exists():
        warnings.append({"type": "missing_artifact", "path": str(path), "required": required})
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": str(path), "message": str(exc)})
        return None


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_registry(root, name, warnings):
    data = _read_json(root / "data" / "registry" / f"{name}.json", warnings)
    return data if isinstance(data, list) else []


def _resident_detail_path(root, resident):
    object_path = root / "data" / "objects" / f"{resident.get('id')}.json" if resident.get("id") else None
    if object_path and object_path.exists():
        return _rel(object_path, root)
    profile_path = root / "residents" / f"{_slug(resident.get('name'))}.md"
    if profile_path.exists():
        return _rel(profile_path, root)
    if resident.get("canonical"):
        return resident.get("canonical")
    return None


def _mailbox_for_resident(name, resident, personnel, mailboxes):
    linked = next((p for p in personnel if p.get("resident_id") == resident.get("id") or _slug(p.get("display_name")) == _slug(name)), None)
    if linked and linked.get("mailbox_id") is not None:
        return {"mailbox_id": linked.get("mailbox_id"), "display_name": linked.get("display_name") or name, "source": "data/registry/personnel.json"}

    if _slug(name) == "alfred":
        alfred_box = next((m for m in mailboxes if m.get("mailbox_id") == 10100 or "alfred" in str(m.get("display_name", "")).lower()), None)
        if alfred_box:
            return {"mailbox_id": alfred_box.get("mailbox_id"), "display_name": alfred_box.get("display_name"), "source": "data/registry/mailboxes.json"}

    office = str(resident.get("department") or resident.get("office") or "").lower()
    office_box = next((m for m in mailboxes if office and (office in str(m.get("owning_office", "")).lower() or office in str(m.get("display_name", "")).lower())), None)
    if office_box:
        return {"mailbox_id": office_box.get("mailbox_id"), "display_name": office_box.get("display_name"), "source": "data/registry/mailboxes.json"}
    return None


def _activity_for_resident(name, root):
    candidates = []
    slug = _slug(name)
    for pattern in (f"runtime/{slug}/**/*", f"operations/{slug}/**/*", f"docs/operations/{slug}/**/*", f"residents/{slug}.md"):
        candidates.extend(p for p in root.glob(pattern) if p.is_file())
    if not candidates:
        return None
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return {"summary": _rel(latest, root), "timestamp": datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")}


def _current_duty(name, resident, runtime):
    slug = _slug(name)
    if isinstance(runtime, dict):
        for key in (slug, resident.get("id"), name):
            if isinstance(runtime.get(key), dict):
                duty = runtime[key].get("current_duty") or runtime[key].get("duty")
                if duty:
                    return str(duty)
    if _slug(name) == "alfred":
        return "Coordinate Estate routing and protect Steward attention."
    if _slug(name) == "helen":
        return "Maintain HR/personnel coordination awareness."
    return None


def _needs_steward(card_fields, warnings):
    if card_fields.get("operational_status") and str(card_fields["operational_status"]).lower() in {"blocked", "attention", "needs steward"}:
        return True
    return any(w.get("required") for w in warnings)


def build_resident_card(root, resident, *, personnel=None, mailboxes=None, runtime=None):
    """Build one extensible resident card from existing data and placeholders."""
    warnings = []
    root = _root(root)
    name = resident.get("name") or PLACEHOLDER
    mailbox = _mailbox_for_resident(name, resident, personnel or [], mailboxes or [])
    activity = _activity_for_resident(name, root)
    fields = {
        "id": resident.get("id"),
        "name": name,
        "role": resident.get("role") or resident.get("office") or PLACEHOLDER,
        "operational_status": resident.get("status") or PLACEHOLDER,
        "current_duty": _current_duty(name, resident, runtime) or PLACEHOLDER,
        "mailbox": mailbox or {"mailbox_id": None, "display_name": PLACEHOLDER, "source": None},
        "last_activity": activity or {"summary": PLACEHOLDER, "timestamp": None},
        "details_link": _resident_detail_path(root, resident) or PLACEHOLDER,
    }
    fields["needs_steward"] = "Yes" if _needs_steward(fields, warnings) else "No"
    boundary = list_authority(name)["resident_boundaries"].get(_slug(name), {})
    fields["authority_status"] = {"allowed": boundary.get("allowed", []), "approval_required": boundary.get("approval_required", []), "denied": boundary.get("denied", []), "audit_path": "runtime/residents/authority_decisions.jsonl"}
    fields["available"] = bool(resident.get("id"))
    fields["warnings"] = warnings
    return fields


def build_resident_cards(root=None, names=INITIAL_RESIDENT_NAMES):
    """Build resident cards for the requested names using one shared model."""
    root = _root(root)
    warnings = []
    residents = _read_registry(root, "residents", warnings)
    personnel = _read_registry(root, "personnel", warnings)
    mailboxes = _read_registry(root, "mailboxes", warnings)
    runtime = _read_json(root / "runtime" / "residents" / "status.json", warnings) or {}
    presence = build_resident_presence(root, tuple(names))
    presence_by_name = {_slug(item.get("name")): item for item in presence.get("residents", [])}
    by_name = {_slug(r.get("name")): r for r in residents if isinstance(r, dict)}
    cards = []
    for name in names:
        resident = by_name.get(_slug(name), {"name": name})
        card = build_resident_card(root, resident, personnel=personnel, mailboxes=mailboxes, runtime=runtime)
        item = presence_by_name.get(_slug(name), {})
        if item:
            card["presence_state"] = item.get("presence_state")
            card["heartbeat_stale"] = item.get("heartbeat_stale")
            card["visible_presence_only"] = item.get("visible_presence_only")
            card["autonomous_execution"] = item.get("autonomous_execution")
            card["status_reason"] = item.get("status_reason")
            if item.get("current_duty"):
                card["current_duty"] = item.get("current_duty")
            if item.get("mailbox_id") is not None:
                card["mailbox"] = {"mailbox_id": item.get("mailbox_id"), "display_name": item.get("mailbox_path") or card.get("mailbox", {}).get("display_name"), "source": "resident_presence"}
            if item.get("last_activity") or item.get("last_heartbeat"):
                card["last_activity"] = {"summary": item.get("last_activity") or item.get("status_reason"), "timestamp": item.get("last_heartbeat")}
            if item.get("needs_steward"):
                card["needs_steward"] = "Yes"
        cards.append(card)
    return {"version": 1, "generated_at": _now(), "cards": cards, "warnings": warnings}
