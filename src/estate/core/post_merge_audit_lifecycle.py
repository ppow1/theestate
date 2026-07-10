"""Canonical post-merge audit lifecycle classification helpers."""
from __future__ import annotations

from typing import Any

ACTIVE_REQUEST_STATES = {"pending", "claimed", "running_validation", "running_ring2"}
PENDING_REQUEST_STATES = {"pending"}
RUNNING_REQUEST_STATES = {"claimed", "running_validation", "running_ring2"}
FINAL_VERDICTS = {"accepted", "accepted_with_notes", "ring2_required", "needs_repair", "blocked", "not_merged", "workspace_failed", "validation_failed", "no_recipe"}
TERMINAL_REQUEST_STATES = {"completed", "ring2_required", "blocked", "validation_failed", "workspace_failed", "already_audited", "not_merged", "no_recipe"}
RETRYABLE_REQUEST_STATES = {"failed"}
INELIGIBLE_CANDIDATE_STATES = {"superseded", "quarantined", "ambiguous", "manual_hold", "held", "historical_backfill", "retired"}

def duplicate_key(data: dict[str, Any]) -> tuple[Any, Any, Any]:
    md = data.get("metadata") or {}
    return (data.get("target_id") or data.get("canonical_target_id"), data.get("work_package_id"), md.get("canonical_discovery_id") or data.get("canonical_discovery_id") or data.get("source_commit") or data.get("source_reference"))

def is_final_verdict(value: str | None) -> bool:
    return value in FINAL_VERDICTS

def request_state(req: dict[str, Any]) -> str:
    return req.get("state") or req.get("status") or "pending"

def is_active_request(req: dict[str, Any]) -> bool:
    return request_state(req) in ACTIVE_REQUEST_STATES

def is_terminal_request(req: dict[str, Any]) -> bool:
    return request_state(req) in TERMINAL_REQUEST_STATES or is_final_verdict(req.get("verdict"))

def is_retryable_request(req: dict[str, Any]) -> bool:
    return request_state(req) in RETRYABLE_REQUEST_STATES and not is_final_verdict(req.get("verdict"))
