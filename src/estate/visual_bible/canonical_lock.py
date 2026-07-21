"""WP-4117 canonical-lock governance and validation.

Validation establishes eligibility only.  It deliberately cannot make a Steward
decision or mutate a resident into canonical state.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .validator import ValidationError

STATES = ("exploratory", "candidate", "preferred", "provisional", "canonical", "superseded", "rejected")
ACTIVE_TRANSITIONS = {
    "exploratory": {"candidate", "rejected"},
    "candidate": {"preferred", "rejected"},
    "preferred": {"provisional", "candidate", "rejected"},
    "provisional": {"canonical", "candidate", "rejected"},
    "canonical": {"superseded"},
    "superseded": set(),
    "rejected": set(),
}
REQUIRED_ASSET_ROLES = {
    "hero_portrait", "canonical_headshot", "profile_reference", "full_body_reference",
    "turnaround_front", "turnaround_front_three_quarter", "turnaround_side",
    "turnaround_rear_three_quarter", "turnaround_rear", "expression_reference",
    "black_and_white_reference", "thumbnail", "icon", "steward_notes", "revision_history",
}
HASH_FIELDS = {
    "physical_specification", "facial_specification", "wardrobe_specification",
    "asset_manifest", "prompt_manifest", "negative_prompt_manifest",
}

def _require(value: bool, message: str) -> None:
    if not value:
        raise ValidationError(message)


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_asset_manifest(manifest: dict, *, root: Path | None = None) -> None:
    """Validate declared evidence without treating reserved locations as assets."""
    _require(manifest.get("resident_id"), "asset manifest resident_id is required")
    entries = manifest.get("entries", [])
    roles = {entry.get("role") for entry in entries}
    _require(REQUIRED_ASSET_ROLES <= roles, "asset manifest is missing required roles")
    if manifest.get("measurement_comparison_required"):
        _require("measurement_comparison" in roles, "required measurement comparison is missing")
    for entry in entries:
        status = entry.get("status")
        _require(status in {"present", "reserved", "not_applicable"}, "invalid asset role status")
        if status == "present":
            _require(entry.get("asset_id") and entry.get("path") and entry.get("hash"), "present asset needs id, path, and hash")
            if root:
                path = root / entry["path"]
                _require(path.is_file(), f"asset does not exist: {entry['path']}")
                _require("sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() == entry["hash"], f"asset hash mismatch: {entry['path']}")
        else:
            _require(not entry.get("hash"), "reserved/not-applicable roles must not invent hashes")


def validate_lock_record(record: dict, *, root: Path | None = None) -> None:
    _require(record.get("schema_version") == "visual_bible_canonical_lock_v1", "unsupported lock schema")
    _require(record.get("state") in STATES, "invalid canonical-lock state")
    _require(record.get("resident_id") and record.get("canonical_version"), "resident and canonical version are required")
    _require(record.get("visibility") in {"public", "internal", "restricted", "private"}, "invalid visibility")
    evidence = record.get("evidence", {})
    for name in HASH_FIELDS:
        item = evidence.get(name, {})
        if item:
            _require(str(item.get("hash", "")).startswith("sha256:"), f"{name} hash is required")
            _require(item.get("version") and item.get("ref"), f"{name} version and ref are required")
    validate_asset_manifest(record.get("asset_completeness", {}), root=root)
    if record["state"] == "canonical":
        decision = record.get("steward_decision", {})
        _require(decision.get("explicit_approval") is True, "canonical status requires explicit Steward approval")
        _require(decision.get("authority") == "Steward", "canonical authority must be Steward")
        _require(decision.get("decision_id") and decision.get("decided_at") and decision.get("evidence_ref"), "Steward decision evidence is incomplete")
        _require(not record.get("blocking_findings"), "canonical record has blocking findings")
        _require(all(evidence.get(name) for name in HASH_FIELDS), "canonical record is missing accepted evidence hashes")
        _require(all(x.get("status") in {"present", "not_applicable"} for x in record["asset_completeness"]["entries"]), "canonical record has reserved assets")
        _require(record.get("recognition", {}).get("hidden_caption_status") == "passed", "hidden-caption recognition has not passed")
        _require(record.get("group_compatibility", {}).get("readiness") == "ready", "group compatibility is not ready")
        _require(record.get("prompt_reproducibility", {}).get("status") == "passed", "prompt reproducibility has not passed")


def eligibility(record: dict, *, root: Path | None = None) -> dict:
    """Return a non-authoritative diagnostic recommendation."""
    try:
        validate_lock_record(record, root=root)
    except ValidationError as exc:
        return {"recommendation": "blocked", "may_grant_canonical": False, "diagnostics": [str(exc)]}
    return {"recommendation": "eligible_for_steward_review", "may_grant_canonical": False, "diagnostics": []}


def validate_transition(previous: dict, current: dict) -> None:
    _require(current.get("state") in ACTIVE_TRANSITIONS.get(previous.get("state"), set()), "illegal lock-state transition")
    _require(previous.get("resident_id") == current.get("resident_id"), "resident cannot change during transition")
    if current["state"] == "canonical":
        validate_lock_record(current)


def validate_supersession(old: dict, replacement: dict) -> None:
    _require(old.get("state") == "superseded", "old record must be superseded")
    _require(replacement.get("state") == "canonical", "replacement must be canonical")
    _require(old.get("superseded_by") == replacement.get("canonical_version"), "supersession link mismatch")
    _require(replacement.get("supersedes") == old.get("canonical_version"), "replacement backlink mismatch")
    validate_lock_record(replacement)


def validate_rollback(record: dict) -> None:
    _require(record.get("action") == "rollback", "rollback action required")
    _require(record.get("authority") == "Steward" and record.get("explicit_request") is True, "rollback requires explicit Steward request")
    _require(record.get("from_version") != record.get("restore_version"), "rollback versions must differ")
    _require(record.get("new_version") and record.get("reason") and record.get("requested_at"), "rollback audit fields are incomplete")
    _require(record.get("preserve_history") is True and record.get("delete_assets") is False, "rollback must preserve history")
