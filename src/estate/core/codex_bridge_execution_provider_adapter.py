"""Execution Provider Adapter implementation for the existing Codex Bridge."""

from __future__ import annotations

from dataclasses import asdict, replace
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
SUPPORTED_PROVIDER_IDS = set(ALLOWED_PROVIDER_PROFILES)
REPORTS_DIR = Path("runtime/execution_adapters/reports")
PROMPTS_DIR = Path("docs/prompts")


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _metadata(request: ExecutionProviderAdapterRequest, key: str, default: Any = None) -> Any:
    return request.metadata.get(key, default)


def _provider_request(request: ExecutionProviderAdapterRequest, root: str | Path | None = None) -> ExecutionProviderAdapterRequest:
    """Translate neutral prompt text into the bridge's bounded file contract."""
    base = _root(root).resolve(strict=False)
    source = Path(str(request.prompt_source or ""))
    if not source.is_absolute():
        source = base / source
    if source.is_file():
        return request
    # Bridge validation deliberately denies runtime paths.  Generated neutral
    # prompts therefore live in the repository's governed prompt area.
    prompt_path = base / PROMPTS_DIR / f"generated-{request.adapter_request_id}.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(str(request.prompt_source or ""), encoding="utf-8")
    return replace(request, prompt_source=str(prompt_path.relative_to(base)).replace("\\", "/"))


def bridge_request_from_adapter_request(request: ExecutionProviderAdapterRequest, *, root: str | Path | None = None) -> CodexBridgeRequest:
    """Translate a provider-neutral adapter request into a Codex Bridge request."""
    request = _provider_request(request, root)

    sandbox = str(_metadata(request, "sandbox", SANDBOX_READ_ONLY))
    return CodexBridgeRequest(
        request_id=f"cbr-{request.adapter_request_id}",
        prompt_source=request.prompt_source or request.work_package_path or "",
        classification=request.classification,
        work_package_id=request.work_package_id,
        requested_by=str(_metadata(request, "requested_by", "traffic-controller")),
        provider=request.provider_id,
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
        bridge_request = bridge_request_from_adapter_request(request, root=self.root)
        bridge_validation = validate_bridge_request(bridge_request, self.root)
        errors.extend(bridge_validation.errors)
        warnings.extend(bridge_validation.warnings)
        return AdapterValidationStatus(status="accepted" if not errors else "blocked", errors=errors, warnings=warnings)

    def dry_run(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        bridge_request = bridge_request_from_adapter_request(request, root=self.root)
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
        bridge_request = bridge_request_from_adapter_request(request, root=self.root)
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
