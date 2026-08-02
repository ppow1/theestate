"""Bounded, fail-closed Engineering Notebook continuity runtime.

The notebook is a verified projection. It is not an authority registry,
dispatch queue, receipt authority, event store, or institutional acceptance
surface. Persistence is intentionally limited to atomic snapshots and
append-only receipt files supplied by the caller.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
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
SHA256 = re.compile(r"^[a-f0-9]{64}$")
SECRET = re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key|cookie|authorization)\s*[:=]\s*[^\s,;]+")
ALLOWED_STATUSES = {"current", "stale", "conflicted", "incomplete", "blocked", "completed", "archived"}
ALLOWED_SEVERITIES = {"none", "low", "medium", "high", "critical"}
ALLOWED_STAGE_STATUSES = {"pending", "active", "complete", "blocked"}
PROVENANCE = {"worker_proposed", "harness_observed", "validator_produced", "operator_authorized", "repository_derived"}
TRUSTED_PROVENANCE = PROVENANCE - {"worker_proposed"}

# Worker updates are deliberately path based.  Parent objects may be supplied
# for ergonomic replacement, but only these leaf paths may differ from the
# verified state.  Identity, authority, scope, policy, provenance, and audit
# fields are therefore protected even when nested in an otherwise mutable
# object.
MUTABLE_UPDATE_PATHS = frozenset({
    "task.current_stage", "task.stage_status", "task.completed_stages",
    "task.remaining_stages", "task.next_action", "task.current_blocker",
    "task.blocking_severity", "task.repair_count",
    "evidence.files", "evidence.last_results", "evidence.unresolved_failures",
    "evidence.test_counts", "evidence.schema_state", "evidence.compilation_state",
    "evidence.fixture_integrity", "evidence.receipts",
    "continuity.previous_session", "continuity.handoff_reason",
    "continuity.compaction_summary", "continuity.safe_facts",
    "continuity.omitted_information", "continuity.next_stage_files", "status",
})


class NotebookError(ValueError):
    """A notebook operation was rejected."""


class NotebookConflict(NotebookError):
    """Authoritative state is stale or conflicts with the notebook."""


class NotebookRejection(NotebookError):
    """Rejected operation carrying a structured, non-mutating receipt."""

    def __init__(self, message: str, receipt: dict[str, Any]):
        super().__init__(message)
        self.receipt = receipt


class NotebookCorruption(NotebookError):
    """A persisted snapshot is malformed or fails its digest."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _canonical_state(state: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(state)
    value.pop("state_digest", None)
    return value


def state_digest(state: dict[str, Any]) -> str:
    return digest_json(_canonical_state(state))


def _safe_ref(value: Any) -> bool:
    if not isinstance(value, str) or not SAFE_REF.fullmatch(value):
        return False
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    return not normalized.startswith(("/", "\\")) and not re.match(r"^[A-Za-z]:", normalized) and ".." not in parts


def _safe_text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NotebookError(f"{field} must be non-empty text")
    if SECRET.search(value):
        raise NotebookError(f"{field} contains a prohibited secret-like value")


def _scan_untrusted(value: Any, field: str) -> None:
    if isinstance(value, str):
        if SECRET.search(value):
            raise NotebookError(f"{field} contains a prohibited secret-like value")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise NotebookError(f"{field} contains an invalid key")
            _scan_untrusted(item, f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_untrusted(item, f"{field}[{index}]")
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise NotebookError(f"{field} contains an unsupported value")


def _timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise NotebookError(f"{field} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NotebookError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise NotebookError(f"{field} must include a timezone")


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


def _text_list(values: Any, label: str) -> None:
    if not isinstance(values, list):
        raise NotebookError(f"{label} must be a list")
    for value in values:
        _safe_text(value, label)


def _bounded_text_list(values: Any, label: str) -> None:
    _text_list(values, label)
    for value in values:
        if "\n" in value or "\r" in value or ".." in value:
            raise NotebookError(f"{label} contains an unsafe command/action")


def _validate_provenance(items: Any, label: str = "provenance") -> None:
    if not isinstance(items, list):
        raise NotebookError(f"{label} must be a list")
    for item in items:
        _strict(item, {"source", "category", "digest", "observed_at", "claim"}, label)
        _required(item, {"source", "category", "observed_at", "claim"}, label)
        _safe_text(item["source"], f"{label}.source")
        if item["category"] not in PROVENANCE:
            raise NotebookError(f"{label} has invalid category")
        if item.get("digest") is not None and (not isinstance(item["digest"], str) or not SHA256.fullmatch(item["digest"])):
            raise NotebookError(f"{label}.digest must be a SHA-256 digest")
        _timestamp(item["observed_at"], f"{label}.observed_at")
        _safe_text(item["claim"], f"{label}.claim")


def _validate_task(task: dict[str, Any]) -> None:
    allowed = {"original_objective", "current_stage", "stage_status", "completed_stages", "remaining_stages", "next_action", "current_blocker", "blocking_severity", "repair_count", "retry_limit", "stop_condition"}
    _strict(task, allowed, "task")
    _required(task, allowed, "task")
    for key in ("original_objective", "current_stage", "stage_status", "next_action", "current_blocker", "stop_condition"):
        _safe_text(task[key], f"task.{key}")
    if task["stage_status"] not in ALLOWED_STAGE_STATUSES:
        raise NotebookError("invalid task.stage_status")
    for key in ("completed_stages", "remaining_stages"):
        _text_list(task[key], f"task.{key}")
        if len(set(task[key])) != len(task[key]):
            raise NotebookError(f"{key} contains duplicate stages")
    if set(task["completed_stages"]) & set(task["remaining_stages"]):
        raise NotebookError("completed and remaining stages overlap")
    if task["stage_status"] == "complete" and (task["current_stage"] not in task["completed_stages"] or task["remaining_stages"]):
        raise NotebookError("complete stage has incomplete stage list")
    if task["stage_status"] == "active" and task["current_stage"] in task["completed_stages"]:
        raise NotebookError("active stage is already completed")
    if task["blocking_severity"] not in ALLOWED_SEVERITIES:
        raise NotebookError("invalid blocker severity")
    if not isinstance(task["repair_count"], int) or not isinstance(task["retry_limit"], int) or task["repair_count"] < 0 or task["retry_limit"] < 1 or task["repair_count"] > task["retry_limit"]:
        raise NotebookError("invalid repair counters")


def _validate_evidence(evidence: dict[str, Any]) -> None:
    allowed = {"files", "commands", "last_results", "unresolved_failures", "test_counts", "schema_state", "compilation_state", "fixture_integrity", "sources", "receipts"}
    _strict(evidence, allowed, "evidence")
    _required(evidence, allowed, "evidence")
    _paths(evidence["files"] + evidence["sources"] + evidence["receipts"], "evidence.references")
    _bounded_text_list(evidence["commands"], "evidence.commands")
    if not isinstance(evidence["last_results"], list) or not isinstance(evidence["test_counts"], dict):
        raise NotebookError("evidence result fields have invalid types")
    _scan_untrusted(evidence["last_results"], "evidence.last_results")
    _scan_untrusted(evidence["test_counts"], "evidence.test_counts")
    for key in ("schema_state", "compilation_state", "fixture_integrity"):
        if evidence[key] not in {"unknown", "pass", "fail", "stale"}:
            raise NotebookError(f"invalid evidence state: {key}")
    _text_list(evidence["unresolved_failures"], "evidence.unresolved_failures")


def _validate_freshness(freshness: dict[str, Any]) -> None:
    allowed = {"state", "checked_at", "source_digests", "max_age_seconds", "conflicts"}
    _strict(freshness, allowed, "freshness")
    _required(freshness, allowed, "freshness")
    if freshness["state"] not in {"current", "stale", "conflicted"} or not isinstance(freshness["source_digests"], dict) or not isinstance(freshness["conflicts"], list):
        raise NotebookError("invalid freshness record")
    _timestamp(freshness["checked_at"], "freshness.checked_at")
    if not isinstance(freshness["max_age_seconds"], int) or freshness["max_age_seconds"] < 1:
        raise NotebookError("invalid freshness.max_age_seconds")
    for key, value in freshness["source_digests"].items():
        if not _safe_ref(key) or not isinstance(value, str) or not SHA256.fullmatch(value):
            raise NotebookError("invalid source digest")
    _paths(freshness["conflicts"], "freshness.conflicts")


def _validate_state_shape(state: dict[str, Any]) -> None:
    allowed = {"schema_version", "notebook_id", "notebook_type", "owner", "assigned_worker", "objective_id", "work_package_ref", "created_at", "last_verified_at", "source_commit", "status", "revision", "last_update_id", "last_receipt_id", "last_idempotency_key", "prior_state_digest", "state_digest", "applied_update_ids", "applied_idempotency_keys", "task", "authority", "constraints", "architecture", "evidence", "continuity", "freshness", "provenance", "institutional_acceptance"}
    _strict(state, allowed, "notebook")
    _required(state, allowed, "notebook")
    if state["schema_version"] != NOTEBOOK_SCHEMA or state["notebook_type"] != "engineering_working_state":
        raise NotebookError("unsupported notebook schema or type")
    for key in ("notebook_id", "owner", "assigned_worker", "objective_id", "work_package_ref", "source_commit"):
        _safe_text(state[key], key)
    if not SAFE_ID.fullmatch(state["notebook_id"]) or not SAFE_ID.fullmatch(state["assigned_worker"]):
        raise NotebookError("invalid notebook or worker identity")
    _timestamp(state["created_at"], "created_at")
    _timestamp(state["last_verified_at"], "last_verified_at")
    if state["status"] not in ALLOWED_STATUSES or not isinstance(state["revision"], int) or state["revision"] < 0:
        raise NotebookError("invalid notebook status or revision")
    for key in ("last_update_id", "last_receipt_id", "last_idempotency_key", "prior_state_digest"):
        if state[key] is not None and (not isinstance(state[key], str) or not SAFE_ID.fullmatch(state[key])):
            raise NotebookError(f"invalid {key}")
    if not isinstance(state["state_digest"], str) or not SHA256.fullmatch(state["state_digest"]):
        raise NotebookError("invalid state_digest")
    if state["prior_state_digest"] is not None and not SHA256.fullmatch(state["prior_state_digest"]):
        raise NotebookError("invalid prior_state_digest")
    for key in ("applied_update_ids", "applied_idempotency_keys"):
        _text_list(state[key], key)
        if any(not SAFE_ID.fullmatch(item) for item in state[key]) or len(set(state[key])) != len(state[key]):
            raise NotebookError(f"invalid {key}")
    _validate_task(state["task"])
    _strict(state["authority"], {"references", "required", "merge", "network", "model_mutation", "destructive", "institutional_acceptance"}, "authority")
    _required(state["authority"], {"references", "required", "merge", "network", "model_mutation", "destructive", "institutional_acceptance"}, "authority")
    _paths(state["authority"]["references"], "authority.references")
    _text_list(state["authority"]["required"], "authority.required")
    for key in ("merge", "network", "model_mutation", "destructive"):
        if not isinstance(state["authority"][key], bool):
            raise NotebookError(f"authority.{key} must be boolean")
    if state["authority"]["institutional_acceptance"] != "not_granted" or state["institutional_acceptance"] != "not_granted":
        raise NotebookError("institutional acceptance must remain not_granted")
    _strict(state["constraints"], {"permitted_repository", "permitted_read_paths", "permitted_write_paths", "permitted_commands", "prohibited_actions"}, "constraints")
    _required(state["constraints"], {"permitted_repository", "permitted_read_paths", "permitted_write_paths", "permitted_commands", "prohibited_actions"}, "constraints")
    for key in ("permitted_repository", "permitted_read_paths", "permitted_write_paths"):
        _paths(state["constraints"][key], f"constraints.{key}")
    _bounded_text_list(state["constraints"]["permitted_commands"], "constraints.permitted_commands")
    _bounded_text_list(state["constraints"]["prohibited_actions"], "constraints.prohibited_actions")
    _strict(state["architecture"], {"protected_components", "runtime_boundaries", "do_not_redesign", "required_interfaces", "governing_documents", "accepted_decisions", "unresolved_decisions"}, "architecture")
    _required(state["architecture"], {"protected_components", "runtime_boundaries", "do_not_redesign", "required_interfaces", "governing_documents", "accepted_decisions", "unresolved_decisions"}, "architecture")
    for key, value in state["architecture"].items():
        _paths(value, f"architecture.{key}")
    _validate_evidence(state["evidence"])
    continuity = state["continuity"]
    _strict(continuity, {"previous_session", "handoff_reason", "compaction_summary", "safe_facts", "omitted_information", "next_stage_files", "expires_at"}, "continuity")
    _required(continuity, {"previous_session", "handoff_reason", "compaction_summary", "safe_facts", "omitted_information", "next_stage_files", "expires_at"}, "continuity")
    if continuity["previous_session"] is not None and not SAFE_ID.fullmatch(continuity["previous_session"]):
        raise NotebookError("invalid previous session")
    _safe_text(continuity["handoff_reason"], "continuity.handoff_reason")
    _safe_text(continuity["compaction_summary"], "continuity.compaction_summary")
    _text_list(continuity["safe_facts"], "continuity.safe_facts")
    _text_list(continuity["omitted_information"], "continuity.omitted_information")
    _paths(continuity["next_stage_files"], "continuity.next_stage_files")
    if continuity["expires_at"] is not None:
        _timestamp(continuity["expires_at"], "continuity.expires_at")
    _validate_freshness(state["freshness"])
    _validate_provenance(state["provenance"])


def _changed_paths(before: Any, after: Any, prefix: str = "") -> list[str]:
    """Return every changed leaf/path, including additions and deletions."""
    if isinstance(before, dict) and isinstance(after, dict):
        paths: list[str] = []
        for key in sorted(set(before) | set(after)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in before or key not in after:
                paths.append(path)
            else:
                paths.extend(_changed_paths(before[key], after[key], path))
        return paths
    return [] if before == after else [prefix]


def _proposal_candidate(state: dict[str, Any], changes: Any) -> dict[str, Any]:
    candidate = deepcopy(state)
    if isinstance(changes, dict):
        for key, value in changes.items():
            candidate[key] = deepcopy(value)
    return candidate


def _proposal_paths(state: dict[str, Any], proposal: dict[str, Any]) -> list[str]:
    return _changed_paths(state, _proposal_candidate(state, proposal.get("changes")))


def _list_contains_all(existing: list[Any], updated: list[Any]) -> bool:
    return all(any(item == candidate for candidate in updated) for item in existing)


def _reject_paths(state: dict[str, Any], proposal: dict[str, Any]) -> list[str]:
    paths = _proposal_paths(state, proposal)
    return paths or sorted(proposal.get("changes", {})) or ["proposal"]


def validate_notebook(state: dict[str, Any], *, verify_digest: bool = True) -> dict[str, Any]:
    _validate_state_shape(state)
    if state["status"] == "completed":
        _require_completion(state, {})
    if verify_digest and state["state_digest"] != state_digest(state):
        raise NotebookCorruption("notebook state digest does not match content")
    return state


def _require_completion(state: dict[str, Any], observed: dict[str, Any]) -> None:
    task = state["task"]
    evidence = state["evidence"]
    if task["stage_status"] != "complete" or task["remaining_stages"] or task["current_blocker"] != "none" or evidence["unresolved_failures"]:
        raise NotebookError("completion requires a terminal stage with no blocker")
    if any(evidence[key] != "pass" for key in ("schema_state", "compilation_state", "fixture_integrity")):
        raise NotebookError("completion requires all required validation states to pass")
    if not evidence["files"] or not evidence["last_results"]:
        raise NotebookError("completion requires artifacts and validator results")
    if observed and (observed.get("artifacts_exist") is not True or observed.get("required_validators_passed") is not True):
        raise NotebookError("completion lacks observed artifact and validator facts")


def create_notebook(*, notebook_id: str, owner: str, assigned_worker: str, objective_id: str, work_package_ref: str, source_commit: str, objective: str, stage: str, remaining_stages: list[str], repository: str, read_paths: list[str], write_paths: list[str], source_digests: dict[str, str], authorization_refs: list[str] | None = None) -> dict[str, Any]:
    if not authorization_refs:
        raise NotebookError("an explicit authorization reference is required")
    now = utc_now()
    state = {"schema_version": NOTEBOOK_SCHEMA, "notebook_id": notebook_id, "notebook_type": "engineering_working_state", "owner": owner, "assigned_worker": assigned_worker, "objective_id": objective_id, "work_package_ref": work_package_ref, "created_at": now, "last_verified_at": now, "source_commit": source_commit, "status": "incomplete", "revision": 0, "last_update_id": None, "last_receipt_id": None, "last_idempotency_key": None, "prior_state_digest": None, "state_digest": "0" * 64, "applied_update_ids": [], "applied_idempotency_keys": [], "task": {"original_objective": objective, "current_stage": stage, "stage_status": "active", "completed_stages": [], "remaining_stages": remaining_stages, "next_action": "Perform the current bounded stage.", "current_blocker": "none", "blocking_severity": "none", "repair_count": 0, "retry_limit": 3, "stop_condition": "Stop on scope, authority, safety, or unresolved validation conflict."}, "authority": {"references": authorization_refs or [work_package_ref], "required": ["explicit assigned objective"], "merge": False, "network": False, "model_mutation": False, "destructive": False, "institutional_acceptance": "not_granted"}, "constraints": {"permitted_repository": [repository], "permitted_read_paths": read_paths, "permitted_write_paths": write_paths, "permitted_commands": ["approved validation commands"], "prohibited_actions": ["secret storage", "scope widening", "repository mutation outside permitted writes", "self-authorizing", "merging", "deletion"]}, "architecture": {"protected_components": [], "runtime_boundaries": [], "do_not_redesign": [], "required_interfaces": [], "governing_documents": [], "accepted_decisions": [], "unresolved_decisions": []}, "evidence": {"files": [], "commands": [], "last_results": [], "unresolved_failures": [], "test_counts": {"passed": 0, "failed": 0}, "schema_state": "unknown", "compilation_state": "unknown", "fixture_integrity": "unknown", "sources": [], "receipts": []}, "continuity": {"previous_session": None, "handoff_reason": "initial creation", "compaction_summary": "No prior session.", "safe_facts": ["Notebook is subordinate to authoritative repository and runtime records."], "omitted_information": ["full prior transcript", "model chain-of-thought", "unrelated repository content"], "next_stage_files": [], "expires_at": None}, "freshness": {"state": "current", "checked_at": now, "source_digests": source_digests, "max_age_seconds": 3600, "conflicts": []}, "provenance": [{"source": work_package_ref, "category": "operator_authorized", "digest": None, "observed_at": now, "claim": "Bounded objective and initial scope were authorized."}], "institutional_acceptance": "not_granted"}
    state["state_digest"] = state_digest(state)
    return validate_notebook(state)


def detect_freshness(state: dict[str, Any], current_source_digests: dict[str, str], *, now: datetime | None = None, current_source_commit: str | None = None) -> dict[str, Any]:
    validate_notebook(state)
    now = now or datetime.now(timezone.utc)
    conflicts = sorted(key for key in set(state["freshness"]["source_digests"]) | set(current_source_digests) if state["freshness"]["source_digests"].get(key) != current_source_digests.get(key))
    age = (now - datetime.fromisoformat(state["last_verified_at"].replace("Z", "+00:00"))).total_seconds()
    stale = age > state["freshness"]["max_age_seconds"]
    if current_source_commit is not None and current_source_commit != state["source_commit"]:
        conflicts.append("source_commit")
    return {"state": "conflicted" if conflicts else "stale" if stale else "current", "conflicts": conflicts, "age_seconds": int(age)}


def build_packet(state: dict[str, Any], *, current_stage_files: list[str], failures: list[str]) -> dict[str, Any]:
    validate_notebook(state)
    _paths(current_stage_files, "current_stage_files")
    _text_list(failures, "failures")
    return {"schema_version": NOTEBOOK_SCHEMA, "notebook_id": state["notebook_id"], "revision": state["revision"], "state_digest": state["state_digest"], "snapshot_verified_at": state["last_verified_at"], "objective": state["task"]["original_objective"], "current_stage": state["task"]["current_stage"], "assigned_worker": state["assigned_worker"], "authority_digest": digest_json(state["authority"]), "evidence_digest": digest_json(state["evidence"]), "permitted_repository": state["constraints"]["permitted_repository"], "permitted_write_paths": state["constraints"]["permitted_write_paths"], "current_blocker": state["task"]["current_blocker"], "required_validation": state["evidence"]["commands"], "prohibited_actions": state["constraints"]["prohibited_actions"], "stage_files": current_stage_files, "current_failures": failures}


def _rejection(state: dict[str, Any], *, rejected_fields: list[str], reason: str, conflicts: list[str] | None = None, operation_id: str | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
    return {"schema_version": RECEIPT_SCHEMA, "receipt_id": f"rejection-{state['notebook_id']}-{state['revision']}-{digest_json({'fields': rejected_fields, 'reason': reason})[:12]}", "proposal_id": operation_id or "acknowledgment", "notebook_id": state["notebook_id"], "status": "rejected", "accepted_at": utc_now(), "accepted_fields": [], "rejected_fields": rejected_fields, "observed_facts": {"reason": reason, "authoritative_conflicts": conflicts or []}, "state_digest": state["state_digest"], "institutional_acceptance": "not_granted", "revision": state["revision"], "idempotency_key": idempotency_key or "rejection", "prior_state_digest": state["state_digest"], "resulting_state_digest": state["state_digest"], "provenance": []}


def acknowledge(state: dict[str, Any], ack: dict[str, Any], *, current_source_digests: dict[str, str], current_source_commit: str, current_stage_files: list[str], current_authority_digest: str, current_evidence_digest: str, current_assigned_worker: str, now: datetime | None = None) -> bool:
    try:
        validate_notebook(state)
        _strict(ack, {"notebook_id", "objective", "stage", "permitted_repository", "permitted_write_paths", "blocker", "required_validation", "prohibited_actions", "stage_files"}, "acknowledgment")
        expected = build_packet(state, current_stage_files=current_stage_files, failures=[])
        checks = {"notebook_id": expected["notebook_id"], "objective": expected["objective"], "stage": expected["current_stage"], "permitted_repository": expected["permitted_repository"], "permitted_write_paths": expected["permitted_write_paths"], "blocker": expected["current_blocker"], "required_validation": expected["required_validation"], "prohibited_actions": expected["prohibited_actions"], "stage_files": expected["stage_files"]}
        mismatches = [key for key, value in checks.items() if ack.get(key) != value]
        if mismatches:
            raise NotebookRejection("acknowledgment does not match verified packet", _rejection(state, rejected_fields=mismatches, reason="acknowledgment mismatch"))
        authoritative_mismatches = []
        if current_authority_digest != digest_json(state["authority"]): authoritative_mismatches.append("authority")
        if current_evidence_digest != digest_json(state["evidence"]): authoritative_mismatches.append("evidence")
        if current_assigned_worker != state["assigned_worker"]: authoritative_mismatches.append("assigned_worker")
        if authoritative_mismatches:
            raise NotebookRejection("authoritative context changed", _rejection(state, rejected_fields=authoritative_mismatches, reason="authority, evidence, or worker identity mismatch", conflicts=authoritative_mismatches))
        freshness = detect_freshness(state, current_source_digests, now=now, current_source_commit=current_source_commit)
        if freshness["state"] != "current":
            raise NotebookRejection("notebook is stale or conflicted", _rejection(state, rejected_fields=["freshness"], reason="execution requires current authoritative state", conflicts=freshness["conflicts"]))
        expires_at = state["continuity"]["expires_at"]
        if expires_at is not None and datetime.fromisoformat(expires_at.replace("Z", "+00:00")) <= (now or datetime.now(timezone.utc)):
            raise NotebookRejection("notebook packet has expired", _rejection(state, rejected_fields=["continuity.expires_at"], reason="expired packet"))
        if state["status"] in {"stale", "conflicted", "archived", "blocked", "completed"} or state["task"]["repair_count"] >= state["task"]["retry_limit"]:
            raise NotebookRejection("notebook cannot authorize execution", _rejection(state, rejected_fields=["status", "task.repair_count"], reason="terminal or retry-exhausted state"))
        return True
    except NotebookRejection:
        raise
    except NotebookError as exc:
        receipt = _rejection(state, rejected_fields=["acknowledgment"], reason=str(exc))
        raise NotebookRejection(str(exc), receipt) from exc


def validate_update_proposal(proposal: dict[str, Any], state: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    validate_notebook(state)
    allowed = {"schema_version", "proposal_id", "notebook_id", "worker", "proposed_at", "idempotency_key", "prior_state_digest", "changes", "provenance", "reason"}
    _strict(proposal, allowed, "update proposal")
    _required(proposal, allowed, "update proposal")
    if proposal["schema_version"] != UPDATE_SCHEMA or proposal["notebook_id"] != state["notebook_id"]:
        raise NotebookError("proposal schema or notebook identity mismatch")
    if not SAFE_ID.fullmatch(proposal["proposal_id"]) or not SAFE_ID.fullmatch(proposal["idempotency_key"]) or not SAFE_ID.fullmatch(proposal["worker"]):
        raise NotebookError("invalid proposal identity")
    if proposal["worker"] != state["assigned_worker"]:
        raise NotebookError("proposal worker does not match assigned worker")
    _timestamp(proposal["proposed_at"], "proposal.proposed_at")
    _safe_text(proposal["reason"], "proposal.reason")
    if proposal["prior_state_digest"] != state["state_digest"]:
        raise NotebookError("proposal prior-state digest is stale")
    if not isinstance(proposal["changes"], dict) or not proposal["changes"]:
        raise NotebookError("proposal changes must be non-empty object")
    changed_paths = _proposal_paths(state, proposal)
    forbidden_paths = sorted(path for path in changed_paths if path not in MUTABLE_UPDATE_PATHS)
    if forbidden_paths:
        raise NotebookError("proposal contains protected or unsupported paths: " + ", ".join(forbidden_paths))
    _validate_provenance(proposal["provenance"], "update proposal provenance")
    if not proposal["provenance"] or not any(item["category"] in TRUSTED_PROVENANCE for item in proposal["provenance"]):
        raise NotebookError("proposal requires trusted observed provenance")
    if not isinstance(observed, dict):
        raise NotebookError("observed facts must be an object")
    _scan_untrusted(observed, "observed")
    missing = [key for key in proposal["changes"] if key not in observed]
    if missing:
        raise NotebookError(f"missing observed facts for changed fields: {missing}")
    for key, expected in observed.items():
        if key in proposal["changes"] and proposal["changes"][key] != expected:
            raise NotebookError(f"proposal claim is not supported by observed fact: {key}")
    if "freshness" in proposal["changes"]:
        raise NotebookError("workers cannot refresh freshness; use authoritative refresh")
    if "task" in proposal["changes"]:
        _validate_task(proposal["changes"]["task"])
        old_task = state["task"]; new_task = proposal["changes"]["task"]
        if new_task["repair_count"] < old_task["repair_count"]:
            raise NotebookError("repair count cannot roll back")
        if old_task["current_blocker"] != "none" and new_task["current_blocker"] == "none":
            if observed.get("blocker_resolution") is not True or not any(item["category"] in {"operator_authorized", "validator_produced"} for item in proposal["provenance"]):
                raise NotebookError("worker cannot erase a blocker without observed resolution evidence")
        if not set(old_task["completed_stages"]).issubset(new_task["completed_stages"]):
            raise NotebookError("completed stages cannot be removed")
    if "evidence" in proposal["changes"]:
        _validate_evidence(proposal["changes"]["evidence"])
        old_evidence = state["evidence"]; new_evidence = proposal["changes"]["evidence"]
        for key in ("files", "last_results", "receipts"):
            if not _list_contains_all(old_evidence[key], new_evidence[key]):
                raise NotebookError(f"evidence.{key} is append-only")
        if old_evidence["unresolved_failures"] and not new_evidence["unresolved_failures"] and observed.get("failures_resolved") is not True:
            raise NotebookError("worker cannot erase unresolved failures without observed resolution evidence")
    if "status" in proposal["changes"]:
        status = proposal["changes"]["status"]
        if status not in {"incomplete", "current", "blocked", "completed"}:
            raise NotebookError("worker cannot set stale, conflicted, or archived status")
        if status == "current" and state["status"] in {"stale", "conflicted"}:
            raise NotebookError("worker cannot clear stale/conflicted state")
        if status == "completed":
            candidate = deepcopy(state); candidate["status"] = status
            if "task" in proposal["changes"]: candidate["task"] = deepcopy(proposal["changes"]["task"])
            if "evidence" in proposal["changes"]: candidate["evidence"] = deepcopy(proposal["changes"]["evidence"])
            _require_completion(candidate, observed)
    return {"valid": True, "proposal_id": proposal["proposal_id"], "accepted_fields": sorted(proposal["changes"])}


def _accepted_receipt(state: dict[str, Any], proposal: dict[str, Any], observed: dict[str, Any], updated: dict[str, Any], status: str = "accepted", prior_digest: str | None = None) -> dict[str, Any]:
    return {"schema_version": RECEIPT_SCHEMA, "receipt_id": f"receipt-{proposal['proposal_id']}", "proposal_id": proposal["proposal_id"], "notebook_id": state["notebook_id"], "status": status, "accepted_at": updated["last_verified_at"], "accepted_fields": _proposal_paths(state, proposal), "rejected_fields": [], "observed_facts": observed, "state_digest": updated["state_digest"], "institutional_acceptance": "not_granted", "revision": updated["revision"], "idempotency_key": proposal["idempotency_key"], "prior_state_digest": prior_digest or state["state_digest"], "resulting_state_digest": updated["state_digest"], "provenance": proposal.get("provenance", [])}


def apply_verified_update(state: dict[str, Any], proposal: dict[str, Any], observed: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        validate_notebook(state)
        if proposal.get("idempotency_key") in state["applied_idempotency_keys"]:
            if proposal.get("proposal_id") == state["last_update_id"]:
                return state, _accepted_receipt(state, proposal, observed, state, status="replayed", prior_digest=state["prior_state_digest"])
            raise NotebookError("conflicting replay")
        if proposal.get("proposal_id") in state["applied_update_ids"]:
            raise NotebookError("duplicate update proposal")
        validate_update_proposal(proposal, state, observed)
    except NotebookError as exc:
        receipt = _rejection(state, rejected_fields=_reject_paths(state, proposal), reason=str(exc), operation_id=proposal.get("proposal_id"), idempotency_key=proposal.get("idempotency_key"))
        raise NotebookRejection(str(exc), receipt) from exc
    updated = deepcopy(state)
    for key, value in proposal["changes"].items():
        updated[key] = deepcopy(value)
    try:
        if updated["status"] == "completed":
            _require_completion(updated, observed)
        updated["revision"] = state["revision"] + 1
        updated["prior_state_digest"] = state["state_digest"]
        updated["last_update_id"] = proposal["proposal_id"]
        updated["last_idempotency_key"] = proposal["idempotency_key"]
        updated["last_verified_at"] = utc_now()
        updated["applied_update_ids"] = [*state["applied_update_ids"], proposal["proposal_id"]]
        updated["applied_idempotency_keys"] = [*state["applied_idempotency_keys"], proposal["idempotency_key"]]
        updated["provenance"] = [*state["provenance"], *proposal["provenance"]]
        updated["last_receipt_id"] = f"receipt-{proposal['proposal_id']}"
        updated["state_digest"] = state_digest(updated)
        validate_notebook(updated)
    except NotebookError as exc:
        raise NotebookRejection(str(exc), _rejection(state, rejected_fields=sorted(proposal["changes"]), reason=str(exc), operation_id=proposal["proposal_id"], idempotency_key=proposal["idempotency_key"])) from exc
    receipt = _accepted_receipt(state, proposal, observed, updated)
    return updated, receipt


def refresh_notebook(state: dict[str, Any], *, current_source_digests: dict[str, str], current_source_commit: str, update_id: str, idempotency_key: str, reason: str = "authoritative freshness refresh") -> tuple[dict[str, Any], dict[str, Any]]:
    validate_notebook(state)
    if not SAFE_ID.fullmatch(update_id) or not SAFE_ID.fullmatch(idempotency_key):
        raise NotebookError("invalid refresh identity")
    check = detect_freshness(state, current_source_digests, current_source_commit=current_source_commit)
    if check["state"] != "current":
        raise NotebookConflict(f"authoritative refresh still conflicts: {check['conflicts']}")
    if idempotency_key in state["applied_idempotency_keys"] or update_id in state["applied_update_ids"]:
        raise NotebookError("duplicate refresh")
    updated = deepcopy(state)
    updated["status"] = "current" if state["status"] in {"stale", "conflicted", "incomplete"} else state["status"]
    updated["freshness"] = {**state["freshness"], "state": "current", "checked_at": utc_now(), "source_digests": current_source_digests, "conflicts": []}
    updated["revision"] += 1; updated["prior_state_digest"] = state["state_digest"]; updated["last_update_id"] = update_id; updated["last_idempotency_key"] = idempotency_key; updated["last_verified_at"] = utc_now(); updated["applied_update_ids"].append(update_id); updated["applied_idempotency_keys"].append(idempotency_key)
    updated["provenance"].append({"source": "authoritative-refresh", "category": "repository_derived", "digest": digest_json(current_source_digests), "observed_at": utc_now(), "claim": reason})
    updated["last_receipt_id"] = f"receipt-{update_id}"; updated["state_digest"] = state_digest(updated); validate_notebook(updated)
    proposal = {"proposal_id": update_id, "idempotency_key": idempotency_key, "changes": {"freshness": updated["freshness"], "status": updated["status"]}}
    receipt = {"schema_version": RECEIPT_SCHEMA, "receipt_id": f"receipt-{update_id}", "proposal_id": update_id, "notebook_id": state["notebook_id"], "status": "accepted", "accepted_at": updated["last_verified_at"], "accepted_fields": ["freshness", "status"], "rejected_fields": [], "observed_facts": {"reason": reason}, "state_digest": updated["state_digest"], "institutional_acceptance": "not_granted", "revision": updated["revision"], "idempotency_key": idempotency_key, "prior_state_digest": state["state_digest"], "resulting_state_digest": updated["state_digest"], "provenance": [{"source": "authoritative-refresh", "category": "repository_derived", "digest": digest_json(current_source_digests), "observed_at": updated["last_verified_at"], "claim": reason}]}
    return updated, receipt


def close_notebook(state: dict[str, Any], *, update_id: str, idempotency_key: str) -> dict[str, Any]:
    validate_notebook(state)
    if state["status"] != "completed":
        raise NotebookError("only a completed notebook may be archived")
    if not SAFE_ID.fullmatch(update_id) or not SAFE_ID.fullmatch(idempotency_key):
        raise NotebookError("invalid archive identity")
    updated = deepcopy(state); updated["status"] = "archived"; updated["revision"] += 1; updated["prior_state_digest"] = state["state_digest"]; updated["last_update_id"] = update_id; updated["last_idempotency_key"] = idempotency_key; updated["last_verified_at"] = utc_now(); updated["applied_update_ids"].append(update_id); updated["applied_idempotency_keys"].append(idempotency_key); updated["last_receipt_id"] = f"receipt-{update_id}"; updated["state_digest"] = state_digest(updated); return validate_notebook(updated)


def _within(path: Path, root: Path) -> Path:
    root = root.resolve(); target = path.resolve()
    try: target.relative_to(root)
    except ValueError as exc: raise NotebookError("path escapes authorized root") from exc
    return target


def write_notebook_atomic(path: str | Path, state: dict[str, Any], *, root: str | Path, simulate_interrupt: bool = False) -> None:
    validate_notebook(state)
    target = _within(Path(path), Path(root)); target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, indent=2); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        if simulate_interrupt: raise OSError("simulated interrupted atomic write")
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)


def write_receipt_append_only(path: str | Path, receipt: dict[str, Any], *, root: str | Path) -> None:
    target = _within(Path(path), Path(root))
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise NotebookCorruption("receipt file is corrupt") from exc
        if existing != receipt:
            raise NotebookError("receipt path already contains a different receipt")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def load_notebook(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    target = _within(Path(path), Path(root))
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NotebookCorruption("unable to load notebook snapshot") from exc
    try: return validate_notebook(state)
    except NotebookError as exc: raise NotebookCorruption(str(exc)) from exc


def archive_notebook(state: dict[str, Any], path: str | Path, *, root: str | Path, update_id: str, idempotency_key: str) -> dict[str, Any]:
    archived = close_notebook(state, update_id=update_id, idempotency_key=idempotency_key)
    write_notebook_atomic(path, archived, root=root)
    return archived


def render_markdown(state: dict[str, Any]) -> str:
    validate_notebook(state)
    def redact(value: Any) -> str:
        return SECRET.sub("[REDACTED]", str(value)).replace("<", "&lt;").replace(">", "&gt;").replace("`", "\\`")
    def bullets(values: list[str]) -> str:
        return "\n".join(f"- {redact(x)}" for x in values) or "- None recorded"
    task = state["task"]; evidence = state["evidence"]; constraints = state["constraints"]
    return f"""# Engineering Notebook: {redact(state['notebook_id'])}

- Status: **{redact(state['status'])}**
- Revision: `{state['revision']}`
- State digest: `{state['state_digest']}`
- Schema: `{redact(state['schema_version'])}`
- Objective: `{redact(state['objective_id'])}`
- Work package: `{redact(state['work_package_ref'])}`
- Assigned worker: `{redact(state['assigned_worker'])}`
- Last verified: `{redact(state['last_verified_at'])}`

## Current job

- Stage: **{redact(task['current_stage'])}** ({redact(task['stage_status'])})
- Next action: {redact(task['next_action'])}
- Blocker: {redact(task['current_blocker'])} ({redact(task['blocking_severity'])})
- Repair count: {task['repair_count']} / {task['retry_limit']}

## Scope

Permitted repository: {bullets(constraints['permitted_repository'])}

Permitted writes:
{bullets(constraints['permitted_write_paths'])}

Prohibited:
{bullets(constraints['prohibited_actions'])}

## Evidence

- Freshness: **{redact(state['freshness']['state'])}**
- Provenance classes: `worker_proposed`, `harness_observed`, `validator_produced`, `operator_authorized`, `repository_derived`
- Schema state: {redact(evidence['schema_state'])}
- Compilation state: {redact(evidence['compilation_state'])}
- Fixture integrity: {redact(evidence['fixture_integrity'])}
- Unresolved failures:
{bullets(evidence['unresolved_failures'])}

## Continuity

{redact(state['continuity']['compaction_summary'])}

Omitted from this packet:
{bullets(state['continuity']['omitted_information'])}

> This notebook is a verified working-state projection. Repository canon, authorization, receipts, validation records, and institutional acceptance remain authoritative.
"""


def create_handoff(state: dict[str, Any], *, reason: str, next_worker: str, packet_digest: str, session_id: str | None = None) -> dict[str, Any]:
    validate_notebook(state); _safe_text(reason, "handoff.reason")
    if not SAFE_ID.fullmatch(next_worker) or (session_id is not None and not SAFE_ID.fullmatch(session_id)) or not SHA256.fullmatch(packet_digest):
        raise NotebookError("invalid handoff identity or packet digest")
    return {"schema_version": HANDOFF_SCHEMA, "handoff_id": f"handoff-{state['notebook_id']}-{state['revision']}", "notebook_id": state["notebook_id"], "created_at": utc_now(), "previous_worker": state["assigned_worker"], "next_worker": next_worker, "session_id": session_id, "revision": state["revision"], "state_digest": state["state_digest"], "reason": reason, "packet_digest": packet_digest, "resume_required": True, "institutional_acceptance": "not_granted"}
