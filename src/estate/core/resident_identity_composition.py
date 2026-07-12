"""Provider-neutral resident runtime identity composition.

The composer assembles inspectable resident context from canonical Estate
artifacts on every inference. It keeps identity, authority, registry facts,
privacy, relationship, conversation, and task instructions as separate layers so
model memory or chat history cannot become institutional truth.
"""
from __future__ import annotations

import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_authority import list_authority

SCHEMA_VERSION = "resident_runtime_identity_composition.v1"
COMPOSITION_ORDER = [
    "resident_core_identity",
    "authority_and_capability_context",
    "institutional_registry_context",
    "grounded_estate_facts",
    "character_context",
    "privacy_and_disclosure_context",
    "relationship_context",
    "conversation_context",
    "task_specific_instructions",
]
REQUIRED_IDENTITY_FIELDS = ("id", "name", "office", "role", "status")
PRIVATE_CLASSES = {"Estate Restricted — Steward Relationship Layer", "evelyn_private_relationship", "hr_private", "security_private", "workforce_private"}

ROLE_BOUNDARIES = {
    "alfred": ["Chief of Staff / executive coordination; not Operations Director, Engineering, HR, Ingrid, Grace, or Steward."],
    "helen": ["Human Resources and Workforce Development; does not create offices, appoint residents, control mail, or run operations."],
    "grace": ["Director of Operations; does not absorb Traffic Controller, Steward, Engineering, Dispatch, Helen, or Ingrid authority."],
    "ingrid": ["Privacy, classification, connector, protected-source, and boundary authority; ordinary self-description remains allowed."],
    "evelyn": ["Steward Confidant; no HR, Operations, Chief of Staff, therapist, Steward, or institutional command authority."],
}
OFFICE_CORRECTIONS = {"alfred": "Chief of Staff", "helen": "Human Resources / Workforce Development"}


def _root(root=None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _key(value: Any) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", str(value or "").lower()).strip("-")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path: Path, diagnostics: list[dict[str, Any]], *, required: bool = False, root: Path) -> Any:
    if not path.exists():
        diagnostics.append({"type": "missing_source", "path": _rel(path, root), "required": required})
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        diagnostics.append({"type": "malformed_source", "path": _rel(path, root), "required": required, "message": str(exc)})
        return None


def _source(path: str, classification: str = "Estate Internal", version: str | None = None, reason: str = "included") -> dict[str, Any]:
    return {"source": path, "classification": classification, "version_or_timestamp": version, "inclusion_reason": reason}


def _hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _find_resident(registry: Sequence[Mapping[str, Any]], resident: str) -> dict[str, Any] | None:
    wanted = _key(resident)
    for row in registry:
        keys = {_key(row.get("id")), _key(row.get("name")), _key(str(row.get("canonical", "").rsplit("/", 1)[-1]))}
        if wanted in keys:
            return dict(row)
    return None


def compose_resident_identity(
    resident: str,
    *,
    surface_id: str,
    root=None,
    conversation_context: Sequence[Mapping[str, Any]] | None = None,
    task_instructions: str | None = None,
    room_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rootp = _root(root)
    diagnostics: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    registry_path = rootp / "data/registry/residents.json"
    registry = _read_json(registry_path, diagnostics, required=True, root=rootp)
    registry = registry if isinstance(registry, list) else []
    rec = _find_resident(registry, resident)
    rid = _key((rec or {}).get("id") or resident)
    canonical_key = _key((rec or {}).get("name") or resident)
    original_office = (rec or {}).get("office")
    if canonical_key in OFFICE_CORRECTIONS:
        rec = {**(rec or {}), "office": OFFICE_CORRECTIONS[canonical_key]}
    missing = [f for f in REQUIRED_IDENTITY_FIELDS if not (rec or {}).get(f)]
    contradictions = []
    if rec and canonical_key == "alfred" and str(original_office or "") != OFFICE_CORRECTIONS["alfred"]:
        contradictions.append({"field": "office", "source": "data/registry/residents.json", "value": original_office, "canonical_expectation": OFFICE_CORRECTIONS["alfred"]})
    if missing:
        diagnostics.append({"type": "missing_required_identity", "resident": resident, "missing_fields": missing})

    profile_path = rootp / "residents" / f"{canonical_key}.md"
    character_available = profile_path.exists()
    if not character_available:
        excluded.append({"layer": "character_context", "reason": "optional_character_profile_missing", "source": _rel(profile_path, rootp)})

    active = [{"id": r.get("id"), "name": r.get("name"), "office": OFFICE_CORRECTIONS.get(_key(r.get("name")), r.get("office")), "status": r.get("status"), "classification": r.get("classification")} for r in registry if str(r.get("status", "")).lower() == "active"]
    room_safe_active = [{k: v for k, v in r.items() if not (r.get("classification") in PRIVATE_CLASSES and k == "classification")} for r in active]
    if surface_id.startswith("conference") or surface_id.startswith("room"):
        excluded.append({"layer": "relationship_context", "reason": "private_or_steward_specific_relationship_context_not_shared_in_rooms", "source": "privacy_policy_runtime"})

    identity = {
        "resident_id": rid,
        "canonical_name": (rec or {}).get("name") or str(resident).title(),
        "office": (rec or {}).get("office"),
        "department": (rec or {}).get("department"),
        "role": (rec or {}).get("role"),
        "lifecycle_status": (rec or {}).get("status"),
        "reporting_relationship": (rec or {}).get("reports_to") or "unknown",
        "provider_independent_summary": f"{(rec or {}).get('name', resident)} is the Estate resident for {(rec or {}).get('office') or 'an unverified office'}.",
        "role_boundaries": ROLE_BOUNDARIES.get(canonical_key, ["No authority inferred from model capability or chat history."]),
    }
    if missing:
        identity["claimable"] = False
    layers = []
    layers.append({"layer": "resident_core_identity", "classification": (rec or {}).get("classification") or "unknown", "content": identity, "sources": [_source("data/registry/residents.json", (rec or {}).get("classification") or "unknown", (rec or {}).get("registered_at"), "required identity/lifecycle source")]})
    layers.append({"layer": "authority_and_capability_context", "classification": "Estate Internal", "content": {"authority": list_authority(rid), "no_authority_from_model_capability": True}, "sources": [_source("src/estate/core/resident_authority.py", reason="authority source")]})
    layers.append({"layer": "institutional_registry_context", "classification": "Estate Internal", "content": {"active_residents": room_safe_active if surface_id.startswith(("conference", "room")) else active}, "sources": [_source("data/registry/residents.json", reason="active resident registry snapshot")]})
    layers.append({"layer": "grounded_estate_facts", "classification": "Estate Internal", "content": {"pending_work_packages_sample": [p.name for p in sorted((rootp / "collaboration/work_packages/pending").glob("WP-*.md"))[:8]] if (rootp / "collaboration/work_packages/pending").exists() else []}, "sources": [_source("collaboration/work_packages/pending", reason="bounded operational fact sample")]})
    if character_available:
        layers.append({"layer": "character_context", "classification": (rec or {}).get("classification") or "Estate Internal", "content": {"profile_path": _rel(profile_path, rootp), "authority_elevation_allowed": False}, "sources": [_source(_rel(profile_path, rootp), (rec or {}).get("classification") or "Estate Internal", reason="canonical resident profile/character context")]})
    layers.append({"layer": "privacy_and_disclosure_context", "classification": "Estate Internal", "content": {"minimum_necessary": True, "ordinary_identity_allowed": True, "private_room_continuity_excluded": surface_id.startswith(("conference", "room"))}, "sources": [_source("src/estate/core/resident_identity_composition.py", reason="runtime privacy filter")]})
    layers.append({"layer": "relationship_context", "classification": "Estate Restricted" if canonical_key == "evelyn" else "Estate Internal", "content": {"authorized_for_resident": canonical_key, "private_globalization_allowed": False}, "sources": [_source("data/registry/residents.json", (rec or {}).get("classification") or "Estate Internal", reason="relationship scope from resident classification")]})
    layers.append({"layer": "conversation_context", "classification": "surface-local", "content": {"turns": list(conversation_context or [])[-4:], "canonical_truth": False}, "sources": [_source("runtime/resident_interactions/sessions", "surface-local", reason="bounded current conversation only")]})
    layers.append({"layer": "task_specific_instructions", "classification": "surface-local", "content": {"instructions": task_instructions or "Respond within composed identity and authority."}, "sources": [_source("request_payload", "surface-local", reason="current request instructions")]})

    provider_ready = "\n".join([
        f"Runtime identity composition: {SCHEMA_VERSION}; resident={identity['canonical_name']}; surface={surface_id}.",
        f"Identity: {json.dumps(identity, sort_keys=True)}",
        f"Active resident cast: {json.dumps(layers[2]['content']['active_residents'], sort_keys=True)}",
        f"Authority: {json.dumps(layers[1]['content'], sort_keys=True)[:1600]}",
        f"Privacy: {json.dumps(layers[5 if character_available else 4]['content'], sort_keys=True)}",
        "Conversation is not canonical identity or institutional truth.",
    ])
    composition = {"schema_version": SCHEMA_VERSION, "resident_id": rid, "surface_id": surface_id, "composition_timestamp": _now(), "identity_version_or_source_hash": _hash({"identity": identity, "registry": active}), "included_context_layers": layers, "excluded_context_layers": excluded, "source_artifacts": [s for layer in layers for s in layer.get("sources", [])], "classification_summary": sorted({layer.get("classification", "unknown") for layer in layers}), "detected_contradictions": contradictions, "missing_sources": [d for d in diagnostics if d.get("type", "").startswith("missing")], "diagnostics": diagnostics, "provider_ready_context": provider_ready[:6000], "failed_closed": bool(missing or contradictions)}
    return composition
