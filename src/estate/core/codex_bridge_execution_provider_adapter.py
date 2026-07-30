"""Execution Provider Adapter implementation for the existing Codex Bridge."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from estate.core.codex_bridge import (
    ALLOWED_PROVIDER_PROFILES,
    APPROVAL_POLICY,
    PROHIBITED_SANDBOX,
    SANDBOX_READ_ONLY,
    CodexBridgeRequest,
    CodexBridgeResult,
    run_codex_bridge_request,
    validate_bridge_request,
)
from estate.core.execution_provider_adapter import (
    AdapterValidationStatus,
    ExecutionProviderAdapter,
    ExecutionProviderAdapterRequest,
    ExecutionProviderAdapterResult,
    utc_now,
)
from estate.core.execution_provider_adapter_runtime import (
    LATEST_STATUS,
    REQUESTS_DIR,
    RESULTS_DIR,
    STATUS_DIR,
    write_adapter_request,
    write_adapter_result,
    write_status_artifacts,
)
from estate.core.paths import ESTATE_ROOT

SUPPORTED_PROVIDER_TYPES = {"codex-cli", "codex_bridge"}
CANONICAL_PROVIDER_ID = "codex.execution.cli"
SUPPORTED_PROVIDER_IDS = set(ALLOWED_PROVIDER_PROFILES) | {CANONICAL_PROVIDER_ID}
REPORTS_DIR = Path("runtime/execution_adapters/reports")


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _metadata(request: ExecutionProviderAdapterRequest, key: str, default: Any = None) -> Any:
    return request.metadata.get(key, default)


def bridge_request_from_adapter_request(request: ExecutionProviderAdapterRequest) -> CodexBridgeRequest:
    """Translate a provider-neutral adapter request into a Codex Bridge request."""

    sandbox = str(_metadata(request, "sandbox", SANDBOX_READ_ONLY))
    return CodexBridgeRequest(
        request_id=f"cbr-{request.adapter_request_id}",
        prompt_source=request.prompt_source or request.work_package_path or "",
        classification=request.classification,
        work_package_id=request.work_package_id,
        requested_by=str(_metadata(request, "requested_by", "traffic-controller")),
        provider=str(_metadata(request, "codex_provider_profile", "codex-cli-openai")) if request.provider_id == CANONICAL_PROVIDER_ID else request.provider_id,
        model=_metadata(request, "model"),
        codex_home_profile=str(_metadata(request, "codex_home_profile", request.profile_label or "default")),
        worker_label=str(_metadata(request, "worker_label", "codex-bridge-adapter")),
        cwd=_metadata(request, "cwd", "."),
        sandbox=sandbox,
        allowed_read_paths=list(request.read_scope_paths),
        allowed_write_paths=list(request.write_scope_paths),
        approval_policy=str(_metadata(request, "approval_policy", APPROVAL_POLICY)),
        json_mode=bool(_metadata(request, "json_mode", True)),
        session_persistence_required=bool(_metadata(request, "session_persistence_required", False)),
        timeout_seconds=(int(_metadata(request, "timeout_seconds")) if _metadata(request, "timeout_seconds") is not None else None),
        cloud_allowed=bool(_metadata(request, "cloud_allowed", False)),
        cloud_apply_requested=bool(_metadata(request, "cloud_apply_requested", False)),
        cloud_dispatch_requested=bool(_metadata(request, "cloud_dispatch_requested", False)),
        danger_full_access_requested=sandbox == PROHIBITED_SANDBOX or bool(_metadata(request, "danger_full_access_requested", False)),
        bypass_flags=list(_metadata(request, "bypass_flags", []) or []),
        validation_commands=list(_metadata(request, "validation_commands", []) or []),
        expected_outputs=list(request.expected_outputs),
        attention_policy=_metadata(request, "attention_policy"),
        codex_binary=str(_metadata(request, "codex_binary", "codex")),
    )


def adapter_result_from_bridge_result(
    request: ExecutionProviderAdapterRequest,
    bridge_request: CodexBridgeRequest,
    bridge_result: CodexBridgeResult,
    *,
    live_provider_called: bool,
) -> ExecutionProviderAdapterResult:
    status_map = {
        "dry_run_validated": "dry_run_completed",
        "succeeded": "completed",
        "failed": "failed",
        "policy_denied": "blocked",
    }
    status = status_map.get(bridge_result.status, "failed")
    artifacts = [p for p in [bridge_result.events_path, bridge_result.status_snapshot_path, bridge_result.audit_path] if p]
    return ExecutionProviderAdapterResult(
        adapter_request_id=request.adapter_request_id,
        dispatch_id=request.dispatch_id,
        provider_id=request.provider_id,
        status=status,
        started_at=bridge_result.started_at,
        finished_at=bridge_result.finished_at,
        summary=bridge_result.final_message or f"Codex Bridge returned {bridge_result.status}.",
        artifacts=artifacts,
        events=list(bridge_result.lifecycle_events),
        validation_status="passed" if bridge_result.status in {"dry_run_validated", "succeeded"} else "failed",
        errors=list(bridge_result.validation_errors) + ([bridge_result.stderr] if bridge_result.status == "failed" and bridge_result.stderr else []),
        warnings=list(bridge_result.known_limitations),
        metadata={
            "adapter_id": "codex-bridge-execution-provider-adapter",
            "provider_type": request.provider_type,
            "live_provider_called": live_provider_called,
            "codex_bridge_request_id": bridge_request.request_id,
            "codex_bridge_status": bridge_result.status,
            "codex_bridge_provider": bridge_result.provider,
            "codex_bridge_profile_label": bridge_result.profile_label,
            "codex_bridge_sandbox": bridge_result.sandbox,
            "exit_code": bridge_result.exit_code,
            "command": bridge_result.command,
            "changed_files": bridge_result.changed_files,
            "tests_run": bridge_result.tests_run,
            "usage": bridge_result.usage,
            "promotion_recommendation": bridge_result.promotion_recommendation,
        },
    )


class CodexBridgeExecutionProviderAdapter(ExecutionProviderAdapter):
    """Concrete adapter that places Codex Bridge behind the adapter contract."""

    adapter_id = "codex-bridge-execution-provider-adapter"
    provider_id = "codex-cli-openai"
    provider_type = "codex-cli"

    def __init__(self, *, root: str | Path | None = None, bridge_runner: Callable[..., CodexBridgeResult] | None = None) -> None:
        self.root = _root(root)
        self.bridge_runner = bridge_runner

    def supports(self, request: ExecutionProviderAdapterRequest) -> bool:
        return request.provider_id in SUPPORTED_PROVIDER_IDS and request.provider_type in SUPPORTED_PROVIDER_TYPES

    def validate_request(self, request: ExecutionProviderAdapterRequest) -> AdapterValidationStatus:
        base = request.validate()
        errors = list(base.errors)
        warnings = list(base.warnings)
        if not self.supports(request):
            errors.append("unsupported Codex Bridge execution provider")
        if not request.decision_reference:
            errors.append("decision_reference authorization is required")
        bridge_request = bridge_request_from_adapter_request(request)
        bridge_validation = validate_bridge_request(bridge_request, self.root)
        errors.extend(bridge_validation.errors)
        warnings.extend(bridge_validation.warnings)
        return AdapterValidationStatus(status="accepted" if not errors else "blocked", errors=errors, warnings=warnings)

    def dry_run(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        bridge_request = bridge_request_from_adapter_request(request)
        validation = self.validate_request(request)
        if not validation.ok:
            now = utc_now()
            return ExecutionProviderAdapterResult(
                adapter_request_id=request.adapter_request_id,
                dispatch_id=request.dispatch_id,
                provider_id=request.provider_id,
                status="blocked",
                started_at=now,
                finished_at=utc_now(),
                summary="Codex Bridge adapter request blocked during deterministic validation.",
                validation_status="failed",
                errors=validation.errors,
                warnings=validation.warnings,
                metadata={"adapter_id": self.adapter_id, "live_provider_called": False, "codex_bridge_request": asdict(bridge_request)},
            )
        bridge_result = run_codex_bridge_request(bridge_request, root=self.root, dry_run=True)
        result = adapter_result_from_bridge_result(request, bridge_request, bridge_result, live_provider_called=False)
        result.warnings = validation.warnings + result.warnings
        return result

    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        bridge_request = bridge_request_from_adapter_request(request)
        validation = self.validate_request(request)
        if not validation.ok:
            now = utc_now()
            return ExecutionProviderAdapterResult(
                adapter_request_id=request.adapter_request_id,
                dispatch_id=request.dispatch_id,
                provider_id=request.provider_id,
                status="blocked",
                started_at=now,
                finished_at=utc_now(),
                summary="Codex Bridge adapter request blocked before submit.",
                validation_status="failed",
                errors=validation.errors,
                warnings=validation.warnings,
                metadata={"adapter_id": self.adapter_id, "live_provider_called": False, "codex_bridge_request_id": bridge_request.request_id},
            )
        runner = self.bridge_runner
        if runner is None:
            now = utc_now()
            return ExecutionProviderAdapterResult(
                adapter_request_id=request.adapter_request_id,
                dispatch_id=request.dispatch_id,
                provider_id=request.provider_id,
                status="blocked",
                started_at=now,
                finished_at=utc_now(),
                summary="Codex Bridge submit requires an explicit injectable bridge runner.",
                validation_status="failed",
                errors=["bridge_runner is required for submit"],
                warnings=validation.warnings,
                metadata={"adapter_id": self.adapter_id, "live_provider_called": False, "codex_bridge_request_id": bridge_request.request_id},
            )
        bridge_result = runner(bridge_request, root=self.root, dry_run=False)
        return adapter_result_from_bridge_result(request, bridge_request, bridge_result, live_provider_called=True)


def _write_report(result: ExecutionProviderAdapterResult, root: str | Path | None = None) -> Path:
    base = _root(root)
    path = base / REPORTS_DIR / f"{result.adapter_request_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join([
            "# Codex Bridge Execution Provider Adapter Report",
            "",
            f"Adapter request: {result.adapter_request_id}",
            f"Dispatch: {result.dispatch_id}",
            f"Provider: {result.provider_id}",
            f"Status: {result.status}",
            f"Validation: {result.validation_status}",
            f"Live provider called: {bool(result.metadata.get('live_provider_called', False))}",
            f"Codex Bridge request: {result.metadata.get('codex_bridge_request_id', 'not-created')}",
            "",
        ]),
        encoding="utf-8",
    )
    return path


def run_codex_bridge_adapter_dry_run(request: ExecutionProviderAdapterRequest, root: str | Path | None = None) -> dict[str, Any]:
    adapter = CodexBridgeExecutionProviderAdapter(root=root)
    request_path = write_adapter_request(request, root=root)
    result = adapter.dry_run(request)
    result_path = write_adapter_result(result, root=root)
    status_paths = write_status_artifacts(result, root=root)
    report_path = _write_report(result, root=root)
    payload = result.to_dict()
    payload.update({"request_path": str(request_path), "result_path": str(result_path), "report_path": str(report_path), **status_paths})
    return payload


class CodexCliExecutionProviderAdapter(CodexBridgeExecutionProviderAdapter):
    """Canonical bounded Codex CLI adapter with strict work-product evidence."""

    adapter_id = "codex-cli-execution-adapter"
    provider_id = CANONICAL_PROVIDER_ID
    provider_type = "execution"
    version = "1.0.0"

    def __init__(self, *, root: str | Path | None = None, bridge_runner: Callable[..., CodexBridgeResult] | None = None) -> None:
        super().__init__(root=root, bridge_runner=bridge_runner or run_codex_bridge_request)

    def supports(self, request: ExecutionProviderAdapterRequest) -> bool:
        return request.provider_id == self.provider_id and request.provider_type in {"execution", "codex-cli", "codex_bridge"}

    def _write_provider_receipt(self, request: ExecutionProviderAdapterRequest, result: ExecutionProviderAdapterResult, artifacts: list[str]) -> str:
        receipt_dir = self.root / "runtime" / "engineering_adapter_receipts"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "estate.provider-receipt.v1",
            "receipt_id": f"receipt-{request.adapter_request_id}",
            "provider_id": self.provider_id,
            "adapter_id": self.adapter_id,
            "adapter_version": self.version,
            "dispatch_id": request.dispatch_id,
            "adapter_request_id": request.adapter_request_id,
            "codex_bridge_request_id": result.metadata.get("codex_bridge_request_id"),
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "exit_code": result.metadata.get("exit_code"),
            "status": result.status,
            "artifacts": [{"path": path, "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest()} for path in artifacts],
            "command": result.metadata.get("command", []),
            "validation": "provider_process_and_declared_artifacts_verified",
        }
        path = receipt_dir / f"{request.adapter_request_id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return str(path.relative_to(self.root)).replace("\\", "/")

    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        if request.metadata.get("cancel_requested") is True:
            now = utc_now()
            return ExecutionProviderAdapterResult(
                adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id,
                provider_id=request.provider_id, status="blocked", started_at=now, finished_at=utc_now(),
                summary="Codex execution was cancelled before provider invocation.", validation_status="failed",
                errors=["cancellation requested before submit"], metadata={"adapter_id": self.adapter_id, "live_provider_called": False},
            )
        result = super().submit(request)
        result.metadata["adapter_id"] = self.adapter_id
        if result.status != "completed":
            return result
        if not request.expected_outputs:
            result.status = "blocked"
            result.validation_status = "failed"
            result.errors.append("codex adapter requires explicit expected_outputs for truthful completion")
            return result
        artifacts: list[str] = []
        for raw in request.expected_outputs:
            path = (self.root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
            try:
                path.relative_to(self.root.resolve())
            except ValueError:
                result.status = "blocked"
                result.validation_status = "failed"
                result.errors.append(f"artifact outside authorized repository root: {raw}")
                continue
            if not path.is_file():
                result.status = "blocked"
                result.validation_status = "failed"
                result.errors.append(f"missing declared artifact: {raw}")
                continue
            artifacts.append(str(path.relative_to(self.root.resolve())).replace("\\", "/"))
        if result.status != "completed":
            return result
        receipt = self._write_provider_receipt(request, result, artifacts)
        result.artifacts = artifacts + [receipt]
        result.metadata["provider_receipt"] = receipt
        result.metadata["receipt_reference"] = receipt
        result.metadata["adapter_version"] = self.version
        result.validation_status = "passed"
        return result
