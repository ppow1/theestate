"""Governed Engineering Notebook state and bounded continuity helpers.

The notebook is a verified working-state projection. It is never an authority
source, capability registry, receipt store, or replacement for repository
canon. Only the harness may persist a verified state transition.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

NOTEBOOK_SCHEMA = "estate.engineering-notebook.state.v1"
UPDATE_SCHEMA = "estate.engineering-notebook.update-proposal.v1"
RECEIPT_SCHEMA = "estate.engineering-notebook.verification-receipt.v1"
HANDOFF_SCHEMA = "estate.engineering-notebook.handoff.v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,511}$")
SECRET = re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key|cookie|authorization)\s*[:=]\s*[^\s,;]+")
ALLOWED_STATUSES = {"current", "stale", "conflicted", "incomplete", "blocked", "completed", "archived"}
ALLOWED_SEVERITIES = {"none", "low", "medium", "high", "critical"}
PROVENANCE = {"worker_proposed", "harness_observed", "validator_produced", "operator_authorized", "repository_derived"}


class NotebookError(ValueError):
    """A notebook cannot be accepted for the requested operation."""


class NotebookConflict(NotebookError):
    """Authoritative source state conflicts with notebook state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _safe_ref(value: Any) -> bool:
    if not isinstance(value, str) or not SAFE_REF.fullmatch(value):
        return False
    normalized = value.replace("\\", "/")
    return not normalized.startswith("/") and ".." not in normalized.split("/") and not re.match(r"^[A-Za-z]:", normalized)


def _safe_text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NotebookError(f"{field} must be non-empty text")
    if SECRET.search(value):
        raise NotebookError(f"{field} contains a prohibited secret-like value")


def _strict(obj: dict[str, Any], allowed: set[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise NotebookError(f"{label} must be an object")
    unknown = set(obj) - allowed
    if unknown:
        raise NotebookError(f"{label} has unknown fields: {sorted(unknown)}")


def _required(obj: dict[str, Any], keys: Iterable[str], label: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise NotebookError(f"{label} missing required fields: {missing}")


def _paths(values: Any, label: str) -> None:
    if not isinstance(values, list) or any(not _safe_ref(x) for x in values):
        raise NotebookError(f"{label} contains an unsafe reference")


def _bounded_text_list(values: Any, label: str) -> None:
    if not isinstance(values, list):
        raise NotebookError(f"{label} must be a list")
    for value in values:
        _safe_text(value, label)
        if "\n" in value or "\r" in value or ".." in value:
            raise NotebookError(f"{label} contains an unsafe command/action")


def _validate_provenance(items: Any, label: str = "provenance") -> None:
    if not isinstance(items, list):
        raise NotebookError(f"{label} must be a list")
    for item in items:
        _strict(item, {"source", "category", "digest", "observed_at", "claim"}, label)
        _required(item, {"source", "category", "observed_at", "claim"}, label)
        if item["category"] not in PROVENANCE:
            raise NotebookError(f"{label} has invalid category")
        if not isinstance(item.get("digest"), (str, type(None))):
            raise NotebookError(f"{label} digest must be text or null")
        _safe_text(item["claim"], f"{label}.claim")


def validate_notebook(state: dict[str, Any]) -> dict[str, Any]:
    allowed = {"schema_version", "notebook_id", "notebook_type", "owner", "assigned_worker", "objective_id", "work_package_ref", "created_at", "last_verified_at", "source_commit", "status", "task", "authority", "constraints", "architecture", "evidence", "continuity", "freshness", "provenance", "institutional_acceptance"}
    _strict(state, allowed, "notebook")
    _required(state, allowed - {"institutional_acceptance"}, "notebook")
    if state["schema_version"] != NOTEBOOK_SCHEMA or state["notebook_type"] != "engineering_working_state":
        raise NotebookError("unsupported notebook schema or type")
    for key in ("notebook_id", "owner", "assigned_worker", "objective_id", "work_package_ref", "source_commit"):
        _safe_text(state[key], key)
    if not SAFE_ID.fullmatch(state["notebook_id"]):
        raise NotebookError("invalid notebook_id")
    if state["status"] not in ALLOWED_STATUSES:
        raise NotebookError("invalid notebook status")
    _validate_task(state["task"])
    _validate_authority(state["authority"])
    _validate_constraints(state["constraints"])
    _validate_architecture(state["architecture"])
    _validate_evidence(state["evidence"])
    _validate_continuity(state["continuity"])
    _validate_freshness(state["freshness"])
    _validate_provenance(state["provenance"])
    if state["status"] == "completed" and (state["evidence"]["unresolved_failures"] or any(state["evidence"][key] != "pass" for key in ("schema_state", "compilation_state", "fixture_integrity"))):
        raise NotebookError("completed notebook lacks passing required validation")
    if state.get("institutional_acceptance", "not_granted") != "not_granted":
        raise NotebookError("notebook cannot grant institutional acceptance")
    return state


def _validate_task(task: dict[str, Any]) -> None:
    _strict(task, {"original_objective", "current_stage", "stage_status", "completed_stages", "remaining_stages", "next_action", "current_blocker", "blocking_severity", "repair_count", "retry_limit", "stop_condition"}, "task")
    _required(task, {"original_objective", "current_stage", "stage_status", "completed_stages", "remaining_stages", "next_action", "current_blocker", "blocking_severity", "repair_count", "retry_limit", "stop_condition"}, "task")
    for key in ("original_objective", "current_stage", "stage_status", "next_action", "current_blocker", "stop_condition"):
        _safe_text(task[key], f"task.{key}")
    if task["blocking_severity"] not in ALLOWED_SEVERITIES or not isinstance(task["repair_count"], int) or not isinstance(task["retry_limit"], int) or task["repair_count"] < 0 or task["retry_limit"] < 0 or task["repair_count"] > task["retry_limit"]:
        raise NotebookError("invalid task counters or blocker severity")
    if not all(isinstance(x, str) and x.strip() for x in task["completed_stages"] + task["remaining_stages"]):
        raise NotebookError("stage lists must contain text")


def _validate_authority(authority: dict[str, Any]) -> None:
    _strict(authority, {"references", "required", "merge", "network", "model_mutation", "destructive", "institutional_acceptance"}, "authority")
    _required(authority, {"references", "required", "merge", "network", "model_mutation", "destructive", "institutional_acceptance"}, "authority")
    _paths(authority["references"], "authority.references")
    for key in ("merge", "network", "model_mutation", "destructive"):
        if not isinstance(authority[key], bool):
            raise NotebookError(f"authority.{key} must be boolean")
    if authority["institutional_acceptance"] != "not_granted":
        raise NotebookError("institutional acceptance must remain not_granted")


def _validate_constraints(constraints: dict[str, Any]) -> None:
    _strict(constraints, {"permitted_repository", "permitted_read_paths", "permitted_write_paths", "permitted_commands", "prohibited_actions"}, "constraints")
    _required(constraints, set(constraints), "constraints")
    for key in ("permitted_repository", "permitted_read_paths", "permitted_write_paths"):
        _paths(constraints[key], f"constraints.{key}")
    for key in ("permitted_commands", "prohibited_actions"):
        _bounded_text_list(constraints[key], f"constraints.{key}")


def _validate_architecture(architecture: dict[str, Any]) -> None:
    _strict(architecture, {"protected_components", "runtime_boundaries", "do_not_redesign", "required_interfaces", "governing_documents", "accepted_decisions", "unresolved_decisions"}, "architecture")
    _required(architecture, set(architecture), "architecture")
    for key in architecture:
        _paths(architecture[key], f"architecture.{key}")


def _validate_evidence(evidence: dict[str, Any]) -> None:
    _strict(evidence, {"files", "commands", "last_results", "unresolved_failures", "test_counts", "schema_state", "compilation_state", "fixture_integrity", "sources", "receipts"}, "evidence")
    _required(evidence, set(evidence), "evidence")
    _paths(evidence["files"] + evidence["sources"] + evidence["receipts"], "evidence.references")
    _bounded_text_list(evidence["commands"], "evidence.commands")
    for key in ("schema_state", "compilation_state", "fixture_integrity"):
        if evidence[key] not in {"unknown", "pass", "fail", "stale"}:
            raise NotebookError(f"invalid evidence state: {key}")


def _validate_continuity(continuity: dict[str, Any]) -> None:
    _strict(continuity, {"previous_session", "handoff_reason", "compaction_summary", "safe_facts", "omitted_information", "next_stage_files", "expires_at"}, "continuity")
    _required(continuity, set(continuity), "continuity")
    for key in ("handoff_reason", "compaction_summary"):
        _safe_text(continuity[key], f"continuity.{key}")
    for key in ("safe_facts", "omitted_information"):
        if not isinstance(continuity[key], list) or any(not isinstance(x, str) for x in continuity[key]):
            raise NotebookError(f"continuity.{key} must be text list")
    _paths(continuity["next_stage_files"], "continuity.next_stage_files")


def _validate_freshness(freshness: dict[str, Any]) -> None:
    _strict(freshness, {"state", "checked_at", "source_digests", "max_age_seconds", "conflicts"}, "freshness")
    _required(freshness, set(freshness), "freshness")
    if freshness["state"] not in {"current", "stale", "conflicted"} or not isinstance(freshness["source_digests"], dict) or not isinstance(freshness["conflicts"], list):
        raise NotebookError("invalid freshness record")
    for key, value in freshness["source_digests"].items():
        if not _safe_ref(key) or not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
            raise NotebookError("invalid source digest")
    for conflict in freshness["conflicts"]:
        _safe_text(conflict, "freshness.conflict")


def create_notebook(*, notebook_id: str, owner: str, assigned_worker: str, objective_id: str, work_package_ref: str, source_commit: str, objective: str, stage: str, remaining_stages: list[str], repository: str, read_paths: list[str], write_paths: list[str], source_digests: dict[str, str], authorization_refs: list[str] | None = None) -> dict[str, Any]:
    now = utc_now()
    state = {"schema_version": NOTEBOOK_SCHEMA, "notebook_id": notebook_id, "notebook_type": "engineering_working_state", "owner": owner, "assigned_worker": assigned_worker, "objective_id": objective_id, "work_package_ref": work_package_ref, "created_at": now, "last_verified_at": now, "source_commit": source_commit, "status": "incomplete", "task": {"original_objective": objective, "current_stage": stage, "stage_status": "active", "completed_stages": [], "remaining_stages": remaining_stages, "next_action": "Perform the current bounded stage.", "current_blocker": "none", "blocking_severity": "none", "repair_count": 0, "retry_limit": 3, "stop_condition": "Stop on scope, authority, safety, or unresolved validation conflict."}, "authority": {"references": authorization_refs or [work_package_ref], "required": ["explicit assigned objective"], "merge": False, "network": False, "model_mutation": False, "destructive": False, "institutional_acceptance": "not_granted"}, "constraints": {"permitted_repository": [repository], "permitted_read_paths": read_paths, "permitted_write_paths": write_paths, "permitted_commands": ["approved validation commands"], "prohibited_actions": ["secret storage", "scope widening", "repository mutation outside permitted writes", "self-authorizing", "merging", "deletion"]}, "architecture": {"protected_components": [], "runtime_boundaries": [], "do_not_redesign": [], "required_interfaces": [], "governing_documents": [], "accepted_decisions": [], "unresolved_decisions": []}, "evidence": {"files": [], "commands": [], "last_results": [], "unresolved_failures": [], "test_counts": {"passed": 0, "failed": 0}, "schema_state": "unknown", "compilation_state": "unknown", "fixture_integrity": "unknown", "sources": [], "receipts": []}, "continuity": {"previous_session": None, "handoff_reason": "initial creation", "compaction_summary": "No prior session.", "safe_facts": ["Notebook is subordinate to authoritative repository and runtime records."], "omitted_information": ["full prior transcript", "model chain-of-thought", "unrelated repository content"], "next_stage_files": [], "expires_at": None}, "freshness": {"state": "current", "checked_at": now, "source_digests": source_digests, "max_age_seconds": 3600, "conflicts": []}, "provenance": [{"source": work_package_ref, "category": "operator_authorized", "digest": None, "observed_at": now, "claim": "Bounded objective and initial scope were authorized."}], "institutional_acceptance": "not_granted"}
    return validate_notebook(state)


def detect_freshness(state: dict[str, Any], current_source_digests: dict[str, str], *, now: datetime | None = None) -> dict[str, Any]:
    validate_notebook(state)
    now = now or datetime.now(timezone.utc)
    conflicts = [key for key, value in state["freshness"]["source_digests"].items() if current_source_digests.get(key) != value]
    age = (now - datetime.fromisoformat(state["last_verified_at"].replace("Z", "+00:00"))).total_seconds()
    stale = age > state["freshness"]["max_age_seconds"]
    result = {"state": "conflicted" if conflicts else "stale" if stale else "current", "conflicts": conflicts, "age_seconds": int(age)}
    return result


def build_packet(state: dict[str, Any], *, current_stage_files: list[str], failures: list[str]) -> dict[str, Any]:
    validate_notebook(state)
    _paths(current_stage_files, "current_stage_files")
    return {"schema_version": NOTEBOOK_SCHEMA, "notebook_id": state["notebook_id"], "snapshot_verified_at": state["last_verified_at"], "objective": state["task"]["original_objective"], "current_stage": state["task"]["current_stage"], "permitted_repository": state["constraints"]["permitted_repository"], "permitted_write_paths": state["constraints"]["permitted_write_paths"], "current_blocker": state["task"]["current_blocker"], "required_validation": state["evidence"]["commands"], "prohibited_actions": state["constraints"]["prohibited_actions"], "stage_files": current_stage_files, "current_failures": failures}


def acknowledge(state: dict[str, Any], ack: dict[str, Any]) -> bool:
    validate_notebook(state)
    _strict(ack, {"notebook_id", "objective", "stage", "permitted_repository", "permitted_write_paths", "blocker", "required_validation", "prohibited_actions"}, "acknowledgment")
    _required(ack, set(ack), "acknowledgment")
    expected = build_packet(state, current_stage_files=[], failures=[])
    checks = {"notebook_id": expected["notebook_id"], "objective": expected["objective"], "stage": expected["current_stage"], "permitted_repository": expected["permitted_repository"], "permitted_write_paths": expected["permitted_write_paths"], "blocker": expected["current_blocker"], "required_validation": expected["required_validation"], "prohibited_actions": expected["prohibited_actions"]}
    if any(ack[key] != value for key, value in checks.items()):
        raise NotebookError("worker acknowledgment does not match verified notebook")
    if state["freshness"]["state"] != "current" or state["status"] in {"stale", "conflicted", "archived"}:
        raise NotebookConflict("notebook is not current and executable")
    return True


def validate_update_proposal(proposal: dict[str, Any], state: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    validate_notebook(state)
    _strict(proposal, {"schema_version", "proposal_id", "notebook_id", "worker", "proposed_at", "changes", "provenance", "reason"}, "update proposal")
    _required(proposal, {"schema_version", "proposal_id", "notebook_id", "worker", "proposed_at", "changes", "provenance", "reason"}, "update proposal")
    if proposal["schema_version"] != UPDATE_SCHEMA or proposal["notebook_id"] != state["notebook_id"]:
        raise NotebookError("proposal schema or notebook identity mismatch")
    if not isinstance(proposal["changes"], dict) or not proposal["changes"]:
        raise NotebookError("proposal changes must be non-empty object")
    _validate_provenance(proposal["provenance"], "update proposal provenance")
    allowed = {"task", "evidence", "continuity", "status", "last_verified_at", "freshness"}
    if set(proposal["changes"]) - allowed:
        raise NotebookError("proposal attempts to change identity, authority, or constraints")
    for key, value in proposal["changes"].items():
        if key == "status" and value not in ALLOWED_STATUSES:
            raise NotebookError("invalid proposed status")
        if key == "last_verified_at" and not isinstance(value, str):
            raise NotebookError("invalid verification timestamp")
        if key == "task":
            _validate_task(value)
        if key == "evidence":
            _validate_evidence(value)
        if key == "continuity":
            _validate_continuity(value)
        if key == "freshness":
            _validate_freshness(value)
    for claim, expected in observed.items():
        if claim in proposal["changes"] and proposal["changes"][claim] != expected:
            raise NotebookError(f"proposal claim is not supported by observed fact: {claim}")
    return {"valid": True, "proposal_id": proposal["proposal_id"], "accepted_fields": sorted(proposal["changes"])}


def apply_verified_update(state: dict[str, Any], proposal: dict[str, Any], observed: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_update_proposal(proposal, state, observed)
    updated = deepcopy(state)
    for key, value in proposal["changes"].items():
        updated[key] = deepcopy(value)
    updated["last_verified_at"] = utc_now()
    updated["provenance"] = updated["provenance"] + proposal["provenance"]
    validate_notebook(updated)
    receipt = {"schema_version": RECEIPT_SCHEMA, "receipt_id": f"receipt-{proposal['proposal_id']}", "proposal_id": proposal["proposal_id"], "notebook_id": state["notebook_id"], "status": "accepted", "accepted_at": updated["last_verified_at"], "accepted_fields": sorted(proposal["changes"]), "rejected_fields": [], "observed_facts": observed, "state_digest": digest_json(updated), "institutional_acceptance": "not_granted"}
    return updated, receipt


def render_markdown(state: dict[str, Any]) -> str:
    validate_notebook(state)
    def bullets(values: list[str]) -> str:
        return "\n".join(f"- {redact(x)}" for x in values) or "- None recorded"
    task = state["task"]; evidence = state["evidence"]; constraints = state["constraints"]
    return f"""# Engineering Notebook: {state['notebook_id']}\n\n- Status: **{state['status']}**\n- Schema: `{state['schema_version']}`\n- Objective: `{redact(state['objective_id'])}`\n- Work package: `{redact(state['work_package_ref'])}`\n- Assigned worker: `{redact(state['assigned_worker'])}`\n- Last verified: `{state['last_verified_at']}`\n- Source commit/state: `{redact(state['source_commit'])}`\n\n## Current job\n\n- Stage: **{redact(task['current_stage'])}** ({redact(task['stage_status'])})\n- Next action: {redact(task['next_action'])}\n- Blocker: {redact(task['current_blocker'])} ({task['blocking_severity']})\n- Repair count: {task['repair_count']} / {task['retry_limit']}\n\n## Scope\n\nPermitted repository: {bullets(constraints['permitted_repository'])}\n\nPermitted writes:\n{bullets(constraints['permitted_write_paths'])}\n\nProhibited:\n{bullets(constraints['prohibited_actions'])}\n\n## Evidence\n\n- Schema state: {evidence['schema_state']}\n- Compilation state: {evidence['compilation_state']}\n- Fixture integrity: {evidence['fixture_integrity']}\n- Unresolved failures:\n{bullets(evidence['unresolved_failures'])}\n\n## Continuity\n\n{redact(state['continuity']['compaction_summary'])}\n\nOmitted from this packet:\n{bullets(state['continuity']['omitted_information'])}\n\n> This notebook is a verified working-state projection. Repository canon, authorization, receipts, validation records, and institutional acceptance remain authoritative.\n"""


def redact(value: Any) -> str:
    text = str(value)
    return SECRET.sub("[REDACTED]", text)


def create_handoff(state: dict[str, Any], *, reason: str, next_worker: str, packet_digest: str) -> dict[str, Any]:
    validate_notebook(state)
    _safe_text(reason, "handoff.reason"); _safe_text(next_worker, "handoff.next_worker"); _safe_text(packet_digest, "handoff.packet_digest")
    return {"schema_version": HANDOFF_SCHEMA, "handoff_id": f"handoff-{state['notebook_id']}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", "notebook_id": state["notebook_id"], "created_at": utc_now(), "previous_worker": state["assigned_worker"], "next_worker": next_worker, "reason": reason, "packet_digest": packet_digest, "resume_required": True, "institutional_acceptance": "not_granted"}
