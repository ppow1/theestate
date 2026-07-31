"""Governed dispatch-to-adapter handoff runtime.

This module connects an explicitly ready Execution Dispatch Queue item to the
provider-neutral Execution Provider Adapter Contract without invoking a live
provider.
"""

from __future__ import annotations

import json
import hashlib
import os
import posixpath
import stat
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

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
from estate.core.ptm_readiness_integration import PtmReadinessGateError, revalidate_readiness
from estate.core.authority_schema_runtime import canonical_record_digest, validation_errors

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


def _canonical_repo_path(root: Path, raw: str, field: str, *, require_file: bool = False) -> tuple[str, Path]:
    value = str(raw)
    normalized = value.replace("\\", "/")
    if not normalized or PureWindowsPath(normalized).is_absolute() or posixpath.isabs(normalized):
        raise ValueError(f"{field} must be repository-relative")
    parts = PurePosixPath(normalized).parts
    if not parts or normalized in {".", "*", "**"} or any(part in {"", ".", ".."} for part in parts) or ":" in parts[0]:
        raise ValueError(f"{field} contains an unsafe repository path")
    canonical = "/".join(parts)
    candidate = root.joinpath(*parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} escapes repository root") from exc
    current = root.resolve()
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{field} crosses a symlink or reparse point")
        if current.exists():
            info = current.stat()
            if bool(getattr(info, "st_file_attributes", 0) & 0x400) or stat.S_ISLNK(info.st_mode):
                raise ValueError(f"{field} crosses a symlink or reparse point")
    if require_file and not resolved.is_file():
        raise ValueError(f"{field} must reference an existing file")
    return canonical, resolved


def _canonical_path_list(root: Path, values: list[str], field: str) -> tuple[list[str], list[str]]:
    canonical: list[str] = []; errors: list[str] = []
    for raw in values:
        try:
            value, _ = _canonical_repo_path(root, raw, field)
            canonical.append(value)
        except ValueError as exc:
            errors.append(str(exc))
    if len(set(canonical)) != len(canonical):
        errors.append(f"{field} contains duplicate paths")
    return canonical, errors


def _validate_authority_schema(root: Path, authority: dict[str, Any]) -> list[str]:
    try:
        return validation_errors(authority, "estate.engineering.commission-execution-authority.v1", root)
    except (OSError, ValueError) as exc:
        return [f"commission authority schema unavailable: {exc}"]


def _validate_dispatch_metadata_schema(root: Path, metadata: dict[str, Any]) -> list[str]:
    schema_path = root / "schemas/dispatch/execution_metadata_v1.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parents[3] / "schemas/dispatch/execution_metadata_v1.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        engineering_dir = schema_path.parent.parent / "engineering"
        if not engineering_dir.exists():
            engineering_dir = Path(__file__).resolve().parents[3] / "schemas/engineering"
        resources = []
        for name, directory in (("commission_ptm_evidence_v1.schema.json", engineering_dir), ("commission_execution_authority_v1.schema.json", engineering_dir), ("qwen_local_text_execution_extension_v1.schema.json", schema_path.parent.parent / "providers")):
            nested = json.loads((directory / name).read_text(encoding="utf-8"))
            resources.append((nested["$id"], Resource.from_contents(nested)))
        registry = Registry().with_resources(resources)
        validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        return [error.message for error in validator.iter_errors(metadata)]
    except (OSError, ValueError) as exc:
        return [f"Dispatch execution metadata schema unavailable: {exc}"]


def _path_within(path: str, scope: str) -> bool:
    child = PurePosixPath(path); parent = PurePosixPath(scope)
    return child == parent or parent in child.parents


def _validate_provider_extension(root: Path, item: DispatchQueueItem, metadata: dict[str, Any]) -> list[str]:
    if item.provider != "qwen.local.text":
        return []
    errors: list[str] = []
    extension = metadata.get("provider_extension")
    if not isinstance(extension, dict):
        return ["Qwen provider extension is required"]
    try:
        errors.extend(validation_errors(extension, "estate.qwen-local-text.execution-extension.v1", root))
    except (OSError, ValueError) as exc:
        errors.append(f"Qwen provider extension schema unavailable: {exc}")
    if extension.get("provider_id") != item.provider or extension.get("adapter_id") not in str(metadata.get("adapter_reference") or "") or extension.get("adapter_version") not in str(metadata.get("adapter_reference") or ""):
        errors.append("Qwen provider extension identity does not match Dispatch adapter")
    try:
        observed = datetime.fromisoformat(str(extension.get("evidence_observed_at")).replace("Z", "+00:00"))
        expires = datetime.fromisoformat(str(extension.get("evidence_expires_at")).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if observed > now or expires <= now or expires <= observed:
            errors.append("Qwen capability or provider-health evidence is stale")
    except (TypeError, ValueError):
        errors.append("Qwen capability or provider-health evidence timestamps are invalid")
    determination_id = metadata.get("helen_determination_id")
    determination_path = root / "runtime/grace_helen_engineering/helen_determinations" / f"{determination_id}.json"
    try:
        determination = json.loads(determination_path.read_text(encoding="utf-8"))
        if determination.get("capability_class") != extension.get("requested_capability") or determination.get("evidence_observed_at") != extension.get("evidence_observed_at") or determination.get("evidence_expires_at") != extension.get("evidence_expires_at"):
            errors.append("Qwen extension does not match canonical Helen evidence")
    except (OSError, ValueError):
        errors.append("canonical Helen determination is not available")
    outputs = {str(path).replace("\\", "/") for path in item.expected_outputs}
    writes = {str(path).replace("\\", "/") for path in item.allowed_write_paths}
    if extension.get("provider_receipt_path") not in outputs or extension.get("provider_receipt_path") not in writes:
        errors.append("Qwen provider receipt path is outside exact governed outputs")
    if extension.get("artifact_path") not in outputs or extension.get("artifact_path") not in writes:
        errors.append("Qwen artifact path is outside exact governed outputs")
    for path in extension.get("provider_health_evidence") or []:
        try:
            _canonical_repo_path(root, path, "provider_health_evidence", require_file=True)
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    config_path = root / "config/providers/qwen_local_text.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("provider_id") != item.provider:
            fallback = Path(__file__).resolve().parents[3] / "config/providers/qwen_local_text.json"
            config = json.loads(fallback.read_text(encoding="utf-8"))
        if config.get("model_identity") != extension.get("authorized_model_identity") or config.get("provider_id") != item.provider or config.get("adapter_id") != extension.get("adapter_id") or config.get("adapter_version") != extension.get("adapter_version"):
            errors.append("Qwen provider configuration does not match authorized extension")
        if config.get("endpoint_address") != "http://127.0.0.1:11434" or config.get("network_policy") != "loopback_only":
            errors.append("Qwen endpoint policy is not the canonical loopback configuration")
    except (OSError, ValueError) as exc:
        errors.append(f"Qwen provider configuration unavailable: {exc}")
    return errors


def _validate_item(item: DispatchQueueItem, root: Path | None = None) -> HandoffStatus:
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
    technical = (item.provider_metadata or {}).get("technical_execution") is True
    if technical:
        if not item.allowed_write_paths:
            errors.append("technical execution requires allowed_write_paths")
        if not item.expected_outputs:
            errors.append("technical execution requires expected_outputs")
        elif not all(any(_path_within(output, scope) for scope in item.allowed_write_paths) for output in item.expected_outputs):
            errors.append("expected_outputs must remain within authorized write scope")
        if root is not None:
            errors.extend(_validate_governed_correlations(item, root))
    if not _auth_ref(item):
        errors.append("authorization or decision reference is required")
    if item.provider and item.provider in item.forbidden_providers:
        errors.append("provider is forbidden")
    if item.allowed_providers and item.provider not in item.allowed_providers:
        errors.append("provider is outside allowed_providers")
    status = "blocked" if errors else "authorized_for_handoff"
    return HandoffStatus(status=status, dispatch_id=item.dispatch_id, errors=errors)


def _validate_governed_correlations(item: DispatchQueueItem, root: Path) -> list[str]:
    """Validate technical Dispatch metadata against its durable commission/auth."""
    errors: list[str] = []
    if item.provider not in {"qwen.local.text", "codex.execution.cli"}:
        return errors
    metadata = item.provider_metadata or {}
    if item.provider in {"qwen.local.text", "codex.execution.cli"}:
        errors.extend(_validate_dispatch_metadata_schema(root, metadata))
    errors.extend(_validate_provider_extension(root, item, metadata))
    commission_id = str(metadata.get("engineering_commission_id") or "")
    if not commission_id:
        return ["technical execution requires engineering_commission_id"]
    commission_path = root / "runtime/grace_helen_engineering/engineering_commissions" / f"{commission_id}.json"
    try:
        commission = json.loads(commission_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ["engineering commission authority record is not available"]
    authority = commission.get("execution_authority") or {}
    errors.extend(_validate_authority_schema(root, authority))
    if not authority.get("prompt_source_record"):
        errors.append("commission execution authority lacks prompt_source_record")
    try:
        prompt_source, prompt_path = _canonical_repo_path(root, item.prompt_source or "", "prompt_source", require_file=True)
        if prompt_source != authority.get("prompt_source") or prompt_source != authority.get("prompt_source_record"):
            errors.append("prompt_source is not the canonical Grace action record")
        actual_digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        if actual_digest != authority.get("prompt_source_digest") or actual_digest != metadata.get("prompt_source_digest"):
            errors.append("prompt-source digest does not match canonical bytes")
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    if authority:
        if item.prompt_source != authority.get("prompt_source"):
            errors.append("prompt_source does not match commission authority")
        read_paths, read_errors = _canonical_path_list(root, list(item.allowed_read_paths), "allowed_read_paths")
        write_paths, write_errors = _canonical_path_list(root, list(item.allowed_write_paths), "allowed_write_paths")
        output_paths, output_errors = _canonical_path_list(root, list(item.expected_outputs), "expected_outputs")
        errors.extend(read_errors + write_errors + output_errors)
        if read_paths != list(authority.get("allowed_read_paths") or []):
            errors.append("allowed_read_paths do not match commission authority")
        if write_paths != list(authority.get("allowed_write_paths") or []):
            errors.append("allowed_write_paths do not match commission authority")
        if output_paths != list(authority.get("expected_outputs") or []):
            errors.append("expected_outputs do not match commission authority")
        if item.provider == "qwen.local.text" and metadata.get("provider_extension") != authority.get("provider_extension"):
            errors.append("provider extension does not match commission authority")
    elif item.provider in {"qwen.local.text", "codex.execution.cli"}:
        errors.append("technical provider commission lacks execution authority")
    if metadata.get("grace_objective_id") != commission.get("grace_objective_id"):
        errors.append("Grace objective does not match commission")
    if metadata.get("grace_action_id") != commission.get("grace_action_id"):
        errors.append("Grace action does not match commission")
    if metadata.get("helen_determination_id") != commission.get("helen_determination_id"):
        errors.append("Helen assessment does not match commission")
    ptm = metadata.get("ptm_readiness") or {}
    if ptm.get("readiness_resolution_id") != commission.get("readiness_resolution_id") or ptm.get("readiness_projection_digest") != commission.get("readiness_projection_digest"):
        errors.append("PTM readiness reference does not match commission")
    auth_ref = _auth_ref(item)
    expected_auth_ref = f"runtime/grace_helen_engineering/engineering_authorizations/{metadata.get('engineering_authorization_id')}.json"
    if metadata.get("authorization_reference") != expected_auth_ref:
        errors.append("authorization_reference is not the canonical Engineering authorization path")
    if not isinstance(metadata.get("decision_reference"), str) or not metadata["decision_reference"].startswith("operations-control/"):
        errors.append("decision_reference does not identify the canonical Operations decision")
    if not auth_ref or auth_ref != expected_auth_ref:
        errors.append("recognized authorization reference is required")
    else:
        try:
            auth = json.loads((root / auth_ref).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            errors.append("authorization record is not available")
        else:
            try:
                errors.extend(validation_errors(auth, "estate.engineering.authorization.v1", root))
            except (OSError, ValueError) as exc:
                errors.append(f"Engineering authorization schema unavailable: {exc}")
            expected_digest = hashlib.sha256(json.dumps({key: value for key, value in auth.items() if key != "record_digest"}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            if auth.get("record_digest") != metadata.get("authorization_record_digest") or auth.get("record_digest") != expected_digest:
                errors.append("authorization record digest does not match")
            if auth.get("engineering_commission_id") != commission_id or auth.get("dispatch_id") != item.dispatch_id or auth.get("provider_id") != item.provider or auth.get("provider_type") != metadata.get("provider_type") or auth.get("adapter_reference") != metadata.get("adapter_reference") or auth.get("grace_objective_id") != commission.get("grace_objective_id") or auth.get("grace_action_id") != commission.get("grace_action_id") or auth.get("helen_determination_id") != commission.get("helen_determination_id") or auth.get("execution_authority") != authority or auth.get("provider_extension") != metadata.get("provider_extension") or auth.get("prompt_source") != item.prompt_source or auth.get("prompt_source_digest") != metadata.get("prompt_source_digest") or auth.get("allowed_read_paths") != item.allowed_read_paths or auth.get("allowed_write_paths") != item.allowed_write_paths or auth.get("expected_outputs") != item.expected_outputs or auth.get("ptm_readiness") != metadata.get("ptm_readiness") or auth.get("decision_reference") != metadata.get("decision_reference"):
                errors.append("authorization record does not match Dispatch, commission, or provider")
            try:
                if datetime.fromisoformat(str(auth["expires_at"]).replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                    errors.append("Engineering authorization is expired")
            except (KeyError, ValueError, TypeError):
                pass
    decision_ref = metadata.get("decision_reference")
    decision_id = decision_ref.removeprefix("operations-control/") if isinstance(decision_ref, str) and decision_ref.startswith("operations-control/") else ""
    decision_path = root / "runtime/operations/control/decisions" / f"{decision_id}.json"
    if not decision_id:
        errors.append("canonical Operations decision reference is required")
    else:
        candidates = [path for path in (root / "runtime/operations/control/decisions").glob(f"*_{decision_id}.json") if path.is_file()] if (root / "runtime/operations/control/decisions").exists() else []
        if candidates:
            decision_path = candidates[0]
        try:
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            errors.append("canonical Operations decision record is not available")
        else:
            try:
                errors.extend(validation_errors(decision, "estate.operations-control.decision.v1", root))
            except (OSError, ValueError) as exc:
                errors.append(f"Operations decision schema unavailable: {exc}")
            if decision.get("record_digest") != canonical_record_digest(decision):
                errors.append("Operations decision digest does not match")
            expected_decision = {
                "decision_id": decision_id,
                "decision_reference": decision_ref,
                "parent_operations_decision_id": commission.get("operations_decision_id"),
                "engineering_commission_id": commission_id,
                "dispatch_id": item.dispatch_id,
                "selected_provider_id": item.provider,
                "selected_adapter_reference": metadata.get("adapter_reference"),
                "grace_objective_id": commission.get("grace_objective_id"),
                "grace_action_id": commission.get("grace_action_id"),
                "helen_determination_id": commission.get("helen_determination_id"),
                "engineering_authorization_id": metadata.get("engineering_authorization_id"),
                "prompt_source_digest": metadata.get("prompt_source_digest"),
                "provider_extension": metadata.get("provider_extension"),
            }
            for key, expected in expected_decision.items():
                if decision.get(key) != expected:
                    errors.append(f"Operations decision {key} does not match governed Dispatch")
            if decision.get("authorization_reference") != metadata.get("authorization_reference"):
                errors.append("Operations decision authorization reference does not match Dispatch")
            if decision.get("provider_extension") != metadata.get("provider_extension"):
                errors.append("Operations decision provider extension does not match Dispatch")
            if decision.get("ptm_readiness") != metadata.get("ptm_readiness"):
                errors.append("Operations decision PTM evidence does not match Dispatch")
            for field_name, expected in (("prompt_source", item.prompt_source), ("allowed_read_paths", item.allowed_read_paths), ("allowed_write_paths", item.allowed_write_paths), ("expected_outputs", item.expected_outputs)):
                if decision.get(field_name) != expected:
                    errors.append(f"Operations decision {field_name} does not match Dispatch")
            for field_name in ("authorized_at", "expires_at"):
                try:
                    if field_name == "expires_at" and datetime.fromisoformat(str(decision[field_name]).replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                        errors.append("Operations decision is expired")
                except (KeyError, ValueError, TypeError):
                    pass
    try:
        revalidate_readiness(root, metadata.get("ptm_readiness") or {}, commission_id=commission_id)
    except (PtmReadinessGateError, ValueError, OSError) as exc:
        errors.append(f"PTM readiness final-boundary revalidation failed: {exc}")
    return errors


def inspect_handoff(dispatch_id: str, root: str | Path | None = None) -> dict[str, Any]:
    try:
        item = inspect_dispatch_item(dispatch_id, root)
    except KeyError as exc:
        return HandoffStatus(status="not_ready", dispatch_id=dispatch_id, errors=[str(exc)]).to_dict()
    status = _validate_item(item, _root(root))
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
        "expected_outputs": item.expected_outputs or item.allowed_write_paths,
        "provider_extension": dict(metadata.get("provider_extension") or {}),
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
    gate = _validate_item(item, base)
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


def run_handoff_adapter(dispatch_id: str, root: str | Path | None = None, *, adapter: Any, test_only: bool = False) -> dict[str, Any]:
    """Run one already-validated handoff through an injected adapter seam.

    Production callers resolve the registered adapter separately; tests inject a
    bounded fake so this function cannot accidentally invoke a live provider.
    """
    if not test_only:
        raise PermissionError("run_handoff_adapter is restricted to explicit test injection")
    prepared = prepare_handoff(dispatch_id, root, write=True)
    if prepared.get("errors"):
        return prepared
    request = ExecutionProviderAdapterRequest.from_dict(prepared["adapter_request"])
    result = adapter.submit(request)
    return {"status": result.status, "dispatch_id": dispatch_id, "adapter_request": request.to_dict(), "result": result.to_dict(), "live_provider_called": bool(result.metadata.get("live_provider_called", False))}


def run_registered_handoff_adapter(dispatch_id: str, root: str | Path | None = None, *, bridge_runner: Any = None) -> dict[str, Any]:
    """Production runner: validate the canonical handoff before catalog resolution."""
    base = _root(root)
    prepared = prepare_handoff(dispatch_id, base, write=True)
    if prepared.get("errors"):
        return prepared
    request = ExecutionProviderAdapterRequest.from_dict(prepared["adapter_request"])
    # The canonical action record is persisted once.  Provider adapters receive
    # its prompt bytes only in memory, after a second digest check, so the
    # adapter-request record does not duplicate the governed prompt.
    try:
        _, prompt_path = _canonical_repo_path(base, request.prompt_source, "prompt_source", require_file=True)
        prompt_bytes = prompt_path.read_bytes()
        if hashlib.sha256(prompt_bytes).hexdigest() != request.prompt_source_digest:
            return {**prepared, "status": "blocked", "errors": ["prompt source changed before registered adapter invocation"], "live_provider_called": False}
        request.metadata = dict(request.metadata)
        request.metadata["prompt_text"] = prompt_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return {**prepared, "status": "blocked", "errors": [f"canonical prompt could not be loaded: {exc}"], "live_provider_called": False}
    from estate.core.execution_provider_adapter_runtime import load_registered_adapter, write_adapter_result
    adapter = load_registered_adapter(request, root=base, bridge_runner=bridge_runner)
    validation = adapter.validate_request(request)
    if not validation.ok:
        return {**prepared, "status": "blocked", "errors": validation.errors, "warnings": validation.warnings, "live_provider_called": False}
    result = adapter.submit(request)
    result_path = write_adapter_result(result, root=base)
    return {"status": result.status, "dispatch_id": dispatch_id, "adapter_request": request.to_dict(), "result": result.to_dict(), "result_path": _rel(result_path, base), "live_provider_called": bool(result.metadata.get("live_provider_called", False))}
