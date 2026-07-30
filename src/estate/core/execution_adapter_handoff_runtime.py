"""Governed dispatch-to-adapter handoff runtime.

This module connects an explicitly ready Execution Dispatch Queue item to the
provider-neutral Execution Provider Adapter Contract without invoking a live
provider.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from estate.core.execution_dispatch import (
    DispatchQueueItem,
    generate_current_dispatch_snapshot,
    inspect_dispatch_item,
    load_dispatch_queue,
    _emit_event,
    _now,
    _rel,
    _replace_item,
    _root,
    _write_queue,
)
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.execution_provider_adapter_runtime import run_dry_run_adapter, write_adapter_request

HANDOFF_ELIGIBLE_STATES = {"Ready"}
HANDOFF_STATES = {
    "not_ready",
    "blocked",
    "authorized_for_handoff",
    "handoff_prepared",
    "handoff_validated",
    "dry_run_completed",
    "accepted_for_provider_submission",
}
REPORTS_DIR = Path("runtime/execution_adapters/reports")


@dataclass
class HandoffStatus:
    status: str
    dispatch_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    adapter_request: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
    live_provider_called: bool = False

    @property
    def ok(self) -> bool:
        return self.status in {"authorized_for_handoff", "handoff_prepared", "handoff_validated", "dry_run_completed", "accepted_for_provider_submission"} and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _auth_ref(item: DispatchQueueItem) -> str | None:
    metadata = item.provider_metadata if isinstance(item.provider_metadata, dict) else {}
    for key in ("authorization_reference", "decision_reference", "movement_authorization_reference", "boundary_review_reference"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _provider_type(item: DispatchQueueItem) -> str:
    metadata = item.provider_metadata if isinstance(item.provider_metadata, dict) else {}
    return str(metadata.get("provider_type") or item.provider or "")


def _validate_item(item: DispatchQueueItem) -> HandoffStatus:
    errors: list[str] = []
    if item.state not in HANDOFF_ELIGIBLE_STATES:
        errors.append(f"dispatch state must be one of {sorted(HANDOFF_ELIGIBLE_STATES)}")
    if not item.provider:
        errors.append("provider is required")
    if not item.classification:
        errors.append("classification is required")
    if not item.prompt_source:
        errors.append("prompt_source or work-package source is required")
    if not item.allowed_read_paths:
        errors.append("allowed_read_paths are required")
    if item.sandbox == "workspace-write" and not item.allowed_write_paths:
        errors.append("workspace-write handoff requires allowed_write_paths")
    if not _auth_ref(item):
        errors.append("authorization or decision reference is required")
    if item.provider and item.provider in item.forbidden_providers:
        errors.append("provider is forbidden")
    if item.allowed_providers and item.provider not in item.allowed_providers:
        errors.append("provider is outside allowed_providers")
    status = "blocked" if errors else "authorized_for_handoff"
    return HandoffStatus(status=status, dispatch_id=item.dispatch_id, errors=errors)


def inspect_handoff(dispatch_id: str, root: str | Path | None = None) -> dict[str, Any]:
    try:
        item = inspect_dispatch_item(dispatch_id, root)
    except KeyError as exc:
        return HandoffStatus(status="not_ready", dispatch_id=dispatch_id, errors=[str(exc)]).to_dict()
    status = _validate_item(item)
    payload = status.to_dict()
    payload["dispatch"] = item.to_dict()
    payload["handoff_reference"] = item.handoff_reference
    return payload


def build_adapter_request(item: DispatchQueueItem) -> ExecutionProviderAdapterRequest:
    metadata = dict(item.provider_metadata or {})
    metadata.update({
        "sandbox": item.sandbox,
        "profile_label": item.profile_label,
        "write_scope_paths": item.allowed_write_paths,
        "authorization_reference": _auth_ref(item),
        "source": "execution_adapter_handoff_runtime",
    })
    record = {
        "dispatch_id": item.dispatch_id,
        "provider_id": item.provider,
        "provider_type": _provider_type(item),
        "work_package_id": item.work_package_id,
        "work_package_path": item.prompt_source,
        "classification": item.classification,
        "allowed_paths": item.allowed_read_paths,
        "forbidden_paths": [],
        "expected_outputs": item.allowed_write_paths,
        "validation_required": True,
        "boundary_review_reference": metadata.get("boundary_review_reference"),
        "decision_reference": _auth_ref(item),
        "metadata": metadata,
    }
    return ExecutionProviderAdapterRequest.from_dispatch_record(record, prompt_source=item.prompt_source)


def _write_report(root: Path, payload: dict[str, Any]) -> Path:
    request = payload.get("adapter_request") or {}
    path = root / REPORTS_DIR / f"{request.get('adapter_request_id', payload.get('dispatch_id', 'unknown'))}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([
        "# Execution Adapter Handoff Report",
        "",
        f"Dispatch: `{payload.get('dispatch_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Live provider called: `{payload.get('live_provider_called', False)}`",
        "",
        "This report is handoff evidence only; it is not provider execution or institutional acceptance.",
    ]) + "\n", encoding="utf-8")
    return path


def prepare_handoff(dispatch_id: str, root: str | Path | None = None, *, write: bool = True) -> dict[str, Any]:
    base = _root(root)
    try:
        item = inspect_dispatch_item(dispatch_id, base)
    except KeyError as exc:
        return HandoffStatus(status="not_ready", dispatch_id=dispatch_id, errors=[str(exc)]).to_dict()
    # A Grace-originated Engineering commission is deliberately provider
    # neutral. Engineering selects a provider after receiving this Dispatch
    # handoff, so the generic handoff must not require an adapter request yet.
    commission = (item.provider_metadata or {}).get("commission")
    if not item.provider and isinstance(commission, dict):
        payload = {
            "schema_version": "estate.engineering.dispatch-handoff.v1",
            "dispatch_id": dispatch_id,
            "commission": commission,
            "provider_id": None,
            "provider_selection_owner": "Engineering",
            "dispatch_authority": "Dispatch",
            "created_at": _now(),
        }
        handoff_path = base / "runtime/execution_dispatch/handoffs" / f"{dispatch_id}_engineering_commission.json"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if write:
            item.handoff_reference = _rel(handoff_path, base)
            item.updated_at = _now()
            _write_queue(base, _replace_item(load_dispatch_queue(base), item))
            _emit_event(base, item, "dispatch_handoff_validated", f"Provider-neutral Engineering commission handoff validated for {dispatch_id}.")
            generate_current_dispatch_snapshot(base, write=True)
        return {"status": "handoff_validated", "dispatch_id": dispatch_id, "errors": [], "warnings": [], "adapter_request": None, "validation": {"status": "accepted", "provider_selection_owner": "Engineering"}, "artifacts": {"request_path": _rel(handoff_path, base)}, "dispatch": item.to_dict(), "handoff_reference": _rel(handoff_path, base), "live_provider_called": False}
    gate = _validate_item(item)
    if gate.errors:
        _emit_event(base, item, "dispatch_handoff_blocked", "; ".join(gate.errors))
        return gate.to_dict()
    request = build_adapter_request(item)
    validation = request.validate()
    artifacts: dict[str, str] = {}
    status = "handoff_validated" if validation.ok else "blocked"
    if write and validation.ok:
        req_path = write_adapter_request(request, root=base)
        artifacts["request_path"] = _rel(req_path, base)
        items = load_dispatch_queue(base)
        item = inspect_dispatch_item(dispatch_id, base)
        item.handoff_reference = artifacts["request_path"]
        item.updated_at = _now()
        _write_queue(base, _replace_item(items, item))
        report_payload = {"status": status, "dispatch_id": dispatch_id, "adapter_request": request.to_dict(), "live_provider_called": False}
        artifacts["report_path"] = _rel(_write_report(base, report_payload), base)
        _emit_event(base, item, "dispatch_handoff_validated", f"Adapter handoff validated for {dispatch_id}.")
        generate_current_dispatch_snapshot(base, write=True)
    return HandoffStatus(status=status, dispatch_id=dispatch_id, errors=validation.errors, warnings=validation.warnings, adapter_request=request.to_dict(), validation=validation.to_dict(), artifacts=artifacts).to_dict()


def validate_handoff(dispatch_id: str, root: str | Path | None = None) -> dict[str, Any]:
    return prepare_handoff(dispatch_id, root, write=False)


def dry_run_handoff(dispatch_id: str, root: str | Path | None = None) -> dict[str, Any]:
    prepared = prepare_handoff(dispatch_id, root, write=True)
    if prepared.get("errors"):
        return prepared
    request = ExecutionProviderAdapterRequest.from_dict(prepared["adapter_request"])
    result = run_dry_run_adapter(request, root=_root(root))
    payload = dict(prepared)
    payload.update({"status": "dry_run_completed" if result.get("status") == "dry_run_completed" else result.get("status"), "dry_run_result": result, "live_provider_called": bool((result.get("metadata") or {}).get("live_provider_called", False))})
    return payload
