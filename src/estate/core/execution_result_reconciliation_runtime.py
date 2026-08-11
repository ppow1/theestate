"""Reconcile execution provider adapter results back into dispatch lifecycle.

Provider completion is operational evidence only; this runtime never grants
institutional acceptance, authorizes movement, or calls a live provider.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from estate.core.execution_activity import EVENTS_OUTPUT as ACTIVITY_EVENTS_OUTPUT, generate_execution_activity_surface
from estate.core.execution_dispatch import (
    EVENTS_OUTPUT as DISPATCH_EVENTS_OUTPUT,
    TERMINAL_STATES,
    _emit_event,
    _rel,
    _replace_item,
    _root,
    _write_queue,
    generate_current_dispatch_snapshot,
    inspect_dispatch_item,
    load_dispatch_queue,
)
from estate.core.execution_provider_adapter import ADAPTER_RESULT_STATUSES, ExecutionProviderAdapterResult, utc_now
from estate.core.execution_provider_adapter_runtime import load_adapter_result

RECONCILIATION_DIR = Path("runtime/execution_adapters/reconciliation")
REPORTS_DIR = Path("runtime/execution_adapters/reports")
_ALLOWED_FROM_TERMINAL_SAME_STATE = {"Completed", "Failed"}
_ALLOWED_TRANSITIONS = {
    "accepted": {"Queued": "Queued", "Waiting": "Waiting", "Ready": "Ready", "Running": "Running"},
    "completed": {"Queued": "Validation", "Waiting": "Validation", "Ready": "Validation", "Running": "Validation", "Validation": "Validation", "Completed": "Completed"},
    "failed": {"Queued": "Failed", "Waiting": "Failed", "Ready": "Failed", "Running": "Failed", "Validation": "Failed", "Failed": "Failed"},
    "blocked": {"Queued": "Blocked", "Waiting": "Blocked", "Ready": "Blocked", "Running": "Blocked", "Validation": "Blocked", "Blocked": "Blocked"},
    "dry_run_completed": {"Queued": "Queued", "Waiting": "Waiting", "Ready": "Ready", "Running": "Running", "Validation": "Validation"},
}


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _append_activity_event(root: Path, event: dict[str, Any]) -> None:
    path = root / ACTIVITY_EVENTS_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    event_id = event["event_id"]
    for line in existing:
        if line.strip():
            try:
                if json.loads(line).get("event_id") == event_id:
                    return
            except json.JSONDecodeError:
                continue
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _expected_request_id(item: Any) -> str | None:
    meta = item.provider_metadata or {}
    for key in ("adapter_request_id", "linked_adapter_request_id"):
        if meta.get(key):
            return str(meta[key])
    if item.handoff_reference:
        path = Path(item.handoff_reference)
        stem = path.stem
        if stem.endswith("_codex_bridge_request"):
            return item.dispatch_id
        if stem:
            return stem
    return None


def _validate_result(item: Any, result: ExecutionProviderAdapterResult) -> None:
    result.validate()
    if result.dispatch_id != item.dispatch_id:
        raise ValueError("result dispatch ID does not match dispatch item")
    expected_request_id = _expected_request_id(item)
    if expected_request_id and result.adapter_request_id != expected_request_id:
        raise ValueError("result adapter request ID does not match dispatch handoff reference")
    if item.provider and result.provider_id != item.provider:
        raise ValueError("result provider ID does not match dispatch provider")
    if result.status not in ADAPTER_RESULT_STATUSES:
        raise ValueError("result status is unknown")
    if result.status in {"completed", "failed", "blocked", "dry_run_completed"} and not result.artifacts:
        raise ValueError("result artifact is malformed or missing")
    if any(not isinstance(a, str) or not a.strip() for a in result.artifacts):
        raise ValueError("result artifact is malformed")


def _target_state(item: Any, result: ExecutionProviderAdapterResult) -> str:
    if result.status == "completed" and item.provider_metadata.get("validation_required") is False:
        mapping = dict(_ALLOWED_TRANSITIONS["completed"])
        mapping.update({"Queued": "Completed", "Waiting": "Completed", "Ready": "Completed", "Running": "Completed", "Validation": "Completed"})
    else:
        mapping = _ALLOWED_TRANSITIONS[result.status]
    if item.state in TERMINAL_STATES and item.state not in _ALLOWED_FROM_TERMINAL_SAME_STATE:
        raise ValueError("reconciliation would regress a terminal state without override authority")
    if item.state in TERMINAL_STATES and mapping.get(item.state) != item.state:
        raise ValueError("reconciliation would regress a terminal state without override authority")
    if item.state not in mapping:
        raise ValueError(f"impossible lifecycle transition from {item.state} for adapter status {result.status}")
    return mapping[item.state]


def _activity_events(item: Any, result: ExecutionProviderAdapterResult, target_state: str, content_hash: str) -> list[dict[str, Any]]:
    provider_metadata = item.provider_metadata or {}
    requirements = item.compute_resource_requirements or {}
    extension = provider_metadata.get("provider_extension") or {}
    base = {
        "request_id": item.dispatch_id,
        "work_package_id": item.work_package_id,
        "source": "execution_result_reconciliation",
        "worker_label": item.assigned_worker,
        "provider": item.provider,
        "profile_label": item.profile_label,
        "classification": item.classification,
        "validation_status": "prepared" if target_state == "Validation" else result.validation_status,
        "compute_resource_id": requirements.get("required_resource_id"),
        "gpu_uuid": requirements.get("required_gpu_uuid"),
        "runtime_lane_id": extension.get("runtime_lane_id") or result.metadata.get("runtime_lane_id"),
        "model_identity": extension.get("authorized_model_identity") or result.metadata.get("actual_model_identity"),
        "reservation_reference": requirements.get("reservation_reference"),
        "metadata": {"adapter_request_id": result.adapter_request_id, "result_content_hash": content_hash, "institutional_acceptance_state": "not_granted"},
    }
    status_event = {
        "completed": "provider_execution_completed",
        "failed": "provider_execution_failed",
        "blocked": "provider_result_blocked",
        "accepted": "provider_result_received",
        "dry_run_completed": "provider_result_received",
    }[result.status]
    types = ["provider_result_received"] if status_event == "provider_result_received" else ["provider_result_received", status_event]
    if target_state == "Validation":
        types.append("provider_result_ready_for_validation")
    if target_state in {"Blocked", "Failed"}:
        types.append("provider_result_requires_attention")
    out = []
    for event_type in types:
        out.append({**base, "event_id": f"{item.dispatch_id}-{result.adapter_request_id}-{content_hash[:12]}-{event_type}", "event_type": event_type, "state": target_state, "timestamp": utc_now(), "attention_required": target_state in {"Blocked", "Failed"}, "summary": f"Provider result {result.status} reconciled for dispatch {item.dispatch_id}; dispatch state {target_state}; institutional acceptance not granted."})
    return out


def inspect_reconciliation(dispatch_id: str, root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    item = inspect_dispatch_item(dispatch_id, base)
    rec = _read_json(base / RECONCILIATION_DIR / f"{dispatch_id}.json")
    return {"status": "available" if rec else "not_reconciled", "dispatch_item": item.to_dict(), "reconciliation": rec, "institutional_acceptance_state": "not_granted"}


def reconcile_result(dispatch_id: str, result_path: str | Path, root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    result = load_adapter_result(result_path)
    items = load_dispatch_queue(base)
    item = next((i for i in items if i.dispatch_id == dispatch_id), None)
    if item is None:
        raise ValueError("dispatch item does not exist")
    _validate_result(item, result)
    target = _target_state(item, result)
    result_payload = result.to_dict()
    content_hash = _hash_payload(result_payload)
    rec_path = base / RECONCILIATION_DIR / f"{dispatch_id}.json"
    prior = _read_json(rec_path)
    if prior and prior.get("result_content_hash") == content_hash:
        return {**prior, "status": "replayed", "idempotent_replay": True}

    item.state = target
    item.result_reference = _rel(Path(result_path), base)
    item.provider_metadata = {**(item.provider_metadata or {}), "adapter_result_reference": item.result_reference, "adapter_result_content_hash": content_hash, "provider_execution_state": result.status, "validation_state": "prepared" if target == "Validation" else result.validation_status, "institutional_acceptance_state": "not_granted", "result_artifacts": list(result.artifacts)}
    item.attention_required = target in {"Blocked", "Failed"}
    item.attention_reason = result.summary if item.attention_required else None
    item.block_reason = result.summary if target == "Blocked" else item.block_reason
    item.updated_at = utc_now()
    _write_queue(base, _replace_item(items, item))
    _emit_event(base, item, {"Validation": "dispatch_validation", "Completed": "dispatch_completed", "Failed": "dispatch_failed", "Blocked": "dispatch_blocked"}.get(target, "dispatch_state_updated"), f"Provider result {result.status} reconciled; institutional acceptance not granted.")
    for event in _activity_events(item, result, target, content_hash):
        _append_activity_event(base, event)
    generate_current_dispatch_snapshot(base, write=True)
    generate_execution_activity_surface(base, write=True)
    payload = {"status": "reconciled", "dispatch_id": dispatch_id, "adapter_request_id": result.adapter_request_id, "provider_id": result.provider_id, "result_status": result.status, "dispatch_state": target, "validation_state": item.provider_metadata["validation_state"], "attention_required": item.attention_required, "institutional_acceptance_state": "not_granted", "result_reference": item.result_reference, "result_artifacts": result.artifacts, "result_content_hash": content_hash, "activity_events_emitted": [e["event_type"] for e in _activity_events(item, result, target, content_hash)], "live_provider_called": False, "reconciled_at": utc_now()}
    _write_json(rec_path, payload)
    report_path = base / REPORTS_DIR / f"{dispatch_id}_reconciliation.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(format_reconciliation_report(payload) + "\n", encoding="utf-8")
    payload["reconciliation_path"] = _rel(rec_path, base)
    payload["report_path"] = _rel(report_path, base)
    _write_json(rec_path, payload)
    return payload


def format_reconciliation_report(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Execution Result Reconciliation Report", "", f"Dispatch: {payload.get('dispatch_id')}", f"Adapter request: {payload.get('adapter_request_id')}", f"Provider: {payload.get('provider_id')}", f"Provider result status: {payload.get('result_status')}", f"Dispatch state: {payload.get('dispatch_state')}", f"Validation state: {payload.get('validation_state')}", f"Attention required: {payload.get('attention_required')}", f"Institutional acceptance: {payload.get('institutional_acceptance_state')}", "", "Provider results are evidence only and do not grant institutional acceptance.",
    ])
