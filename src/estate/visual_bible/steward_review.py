"""WP-4116 Steward-centered visual review records and transition validation.

This module validates append-only records.  It never infers approval from scores.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .validator import ValidationError

STATES = {"draft", "pending_steward_review", "revision_requested", "provisionally_approved", "canonical", "rejected", "superseded"}
SCOPES = {"public", "internal", "restricted", "private"}
ANGLES = ["front", "front_three_quarter", "side", "rear_three_quarter", "rear"]
ANCHORS = {"technical", "facial", "body_proportion", "signature_look", "emotional_presence"}
TRANSITIONS = {
    "draft": {"pending_steward_review"},
    "pending_steward_review": {"revision_requested", "provisionally_approved", "canonical", "rejected"},
    "revision_requested": {"pending_steward_review", "rejected"},
    "provisionally_approved": {"pending_steward_review", "canonical", "revision_requested", "rejected"},
    "canonical": {"superseded"},
    "rejected": set(), "superseded": set(),
}

def _require(value: Any, message: str) -> None:
    if not value:
        raise ValidationError(message)

def _required(record: dict, fields: tuple[str, ...], kind: str) -> None:
    for field in fields:
        _require(field in record and record[field] not in (None, "", []), f"{kind} missing required field: {field}")

def _provenance(record: dict) -> None:
    p = record.get("provenance", {})
    _required(p, ("created_at", "created_by", "source_ids", "content_hash", "lineage", "revision"), "provenance")
    _require(str(p["content_hash"]).startswith("sha256:"), "provenance content_hash must use sha256")

def validate_transition(event: dict) -> None:
    _required(event, ("transition_id", "subject_id", "from_state", "to_state", "occurred_at", "reviewer_id", "reviewer_authority", "reason", "source_asset_ids"), "transition")
    old, new = event["from_state"], event["to_state"]
    _require(old in STATES and new in STATES, "unknown review state")
    _require(new in TRANSITIONS[old], f"invalid review transition: {old} -> {new}")
    if new in {"provisionally_approved", "canonical", "rejected"}:
        _require(event["reviewer_authority"] == "Steward", "Steward authority is required for disposition")
    if new == "canonical":
        _require(bool(event.get("approval_record_id")), "canonical transition requires approval_record_id")
    _provenance(event)

def validate_note(note: dict) -> None:
    _required(note, ("note_id", "resident_id", "recorded_at", "steward_id", "exact_text", "target_refs", "dimension", "provenance"), "Steward Note")
    _require(note.get("authority") == "Steward", "Steward Note authority must be Steward")
    _require(note["dimension"] in {"technical", "emotional", "both"}, "invalid note dimension")
    _require(note.get("exact_text_preserved") is True, "exact Steward feedback must be preserved")
    _require(note.get("normalized_summary") != note["exact_text"] or note.get("normalized_summary") is None, "summary must not masquerade as exact text")
    _provenance(note)

def validate_queue(queue: dict) -> None:
    _required(queue, ("queue_id", "audience_scope", "items", "created_at", "provenance"), "review queue")
    _require(queue["audience_scope"] in SCOPES, "invalid queue audience scope")
    for item in queue["items"]:
        _required(item, ("queue_item_id", "subject_id", "subject_type", "review_state", "priority", "submitted_at", "manifest_id"), "queue item")
        _require(item["review_state"] == "pending_steward_review", "queue items must be pending Steward review")
    _provenance(queue)

def validate_comparison_manifest(record: dict) -> None:
    _required(record, ("manifest_id", "resident_ids", "comparison_type", "layout", "assets", "intended_variables", "fixed_variables", "difference_summary", "review_dimensions", "audience_scope", "provenance"), "comparison manifest")
    _require(record["audience_scope"] in SCOPES, "invalid comparison audience scope")
    _require(record["layout"].get("vertical_stack") is True, "comparisons must be vertically stacked")
    _require(record["layout"].get("angle_order") == ANGLES, "comparison angles must be aligned in canonical order")
    _require(record["layout"].get("labels_outside_image") is True and record["layout"].get("originals_zoomable") is True, "comparison presentation controls incomplete")
    _require(not set(record["intended_variables"]) & set(record["fixed_variables"]), "intended and fixed variables overlap")
    _require(set(record["review_dimensions"]) == {"technical", "emotional"}, "technical and emotional review dimensions are required")
    if record["comparison_type"] == "three_variant":
        _require(len(record["assets"]) == 3, "three-variant review requires exactly three variants")
    if record["comparison_type"] == "turnaround_360":
        _require(all(a.get("angles") == ANGLES for a in record["assets"]), "360 assets require five aligned angles")
    if record.get("heels_applicable"):
        _require(float(record.get("heel_height_inches", 0)) >= 3, "applicable heel review requires at least three inches")
    _provenance(record)

def validate_revision_packet(packet: dict) -> None:
    _required(packet, ("packet_id", "resident_ids", "source_asset_ids", "steward_note_ids", "approved_elements_to_preserve", "defects_to_correct", "exact_requested_changes", "variables_to_change", "variables_to_hold_fixed", "positive_prompt_fragments", "negative_prompt_fragments", "comparison_layout_requirements", "acceptance_tests", "audience_scope", "provenance"), "revision packet")
    _require(packet["audience_scope"] in SCOPES, "invalid revision audience scope")
    _require(not set(packet["variables_to_change"]) & set(packet["variables_to_hold_fixed"]), "revision change and fixed variables overlap")
    _require(all(x.get("exact_text") and x.get("steward_note_id") for x in packet["exact_requested_changes"]), "requested changes must retain exact linked Steward text")
    _require(all(x.get("test") and x.get("pass_condition") and x.get("authority") == "Steward" for x in packet["acceptance_tests"]), "acceptance tests require explicit Steward pass conditions")
    _provenance(packet)

def validate_anchor(record: dict) -> None:
    _required(record, ("anchor_record_id", "resident_id", "anchor_type", "asset_ids", "technical_assessment", "emotional_assessment", "review_state", "audience_scope", "provenance"), "anchor record")
    _require(record["anchor_type"] in ANCHORS, "invalid anchor type")
    _require(record["review_state"] in STATES, "invalid anchor review state")
    _require(record["audience_scope"] in SCOPES, "invalid anchor scope")
    _provenance(record)

def validate_recognition_test(record: dict) -> None:
    _required(record, ("test_id", "group_asset_id", "expected_resident_ids", "captions_hidden", "steward_responses", "recognition_result", "review_state", "provenance"), "recognition test")
    _require(record["captions_hidden"] is True, "recognition test captions must be hidden")
    _require(record.get("reviewer_authority") == "Steward", "recognition result requires Steward authority")
    _require(record["recognition_result"] in {"pass", "fail", "partial", "pending"}, "invalid recognition result")
    _provenance(record)

def validate_approval(record: dict) -> None:
    _required(record, ("approval_id", "subject_ids", "approved_version", "approved_at", "approver_id", "approver_authority", "steward_note_ids", "preserved_elements", "scope", "provenance"), "approval")
    _require(record["approver_authority"] == "Steward", "canonical approval requires Steward authority")
    _require(record.get("explicit_approval") is True, "canonical approval must be explicit")
    _require(record["scope"] in SCOPES, "invalid approval scope")
    _provenance(record)

def create_rollback(current_approval: dict, target_approval: dict, *, steward_id: str, reason: str, occurred_at: str) -> dict:
    """Create an auditable rollback proposal; it still requires a separate transition."""
    validate_approval(current_approval); validate_approval(target_approval)
    _require(reason, "rollback reason is required")
    return {"rollback_id": f"rollback-{current_approval['approval_id']}-to-{target_approval['approval_id']}", "from_approval_id": current_approval["approval_id"], "restore_approval_id": target_approval["approval_id"], "superseded_subject_ids": deepcopy(current_approval["subject_ids"]), "restored_subject_ids": deepcopy(target_approval["subject_ids"]), "requested_by": steward_id, "requester_authority": "Steward", "reason": reason, "occurred_at": occurred_at, "history_preserved": True, "automatic_deletion": False}
