"""Steward-authorized live execution gate for the Codex Bridge adapter.

The gate verifies existing authority and runtime safety before attaching a
Codex Bridge runner. It does not create dispatch, movement, validation, merge,
or institutional acceptance authority.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from estate.core.codex_bridge import ALLOWED_PROVIDER_PROFILES, CodexBridgeResult, run_codex_bridge_request
from estate.core.codex_bridge_execution_provider_adapter import CodexBridgeExecutionProviderAdapter
from estate.core.execution_dispatch import inspect_dispatch_item, update_dispatch_state
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest, ExecutionProviderAdapterResult, utc_now
from estate.core.execution_provider_adapter_runtime import load_adapter_request, write_adapter_request, write_adapter_result, write_status_artifacts
from estate.core.paths import ESTATE_ROOT

AUTHORIZATIONS_DIR = Path("runtime/execution_adapters/authorizations")
EXECUTIONS_DIR = Path("runtime/execution_adapters/executions")
REPORTS_DIR = Path("runtime/execution_adapters/reports")
ALLOWED_SANDBOXES = {"read-only", "workspace-write"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, tuple):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def _norm(path: str) -> str:
    text = str(path).replace("\\", "/").strip()
    while "//" in text:
        text = text.replace("//", "/")
    return text.rstrip("/") or "."


def _overlap(left: str, right: str) -> bool:
    a, b = _norm(left), _norm(right)
    if a == "." or b == ".":
        return True
    pa, pb = PurePosixPath(a), PurePosixPath(b)
    return pa == pb or pa in pb.parents or pb in pa.parents


def _within(path: str, scopes: list[str]) -> bool:
    return any(_overlap(path, scope) and (PurePosixPath(_norm(path)) == PurePosixPath(_norm(scope)) or PurePosixPath(_norm(scope)) in PurePosixPath(_norm(path)).parents) for scope in scopes)


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _git(root: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    except OSError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def current_workspace(root: Path) -> dict[str, Any]:
    commit = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    return {"commit": commit, "dirty": bool(status), "dirty_status": status or "", "checked_at": _now()}


@dataclass
class LiveExecutionAuthorization:
    execution_authorization_id: str
    dispatch_id: str
    adapter_request_id: str
    provider_id: str
    provider_type: str
    work_package_id: str
    decision_reference: str
    traffic_controller_authorization_reference: str
    steward_approval_reference: str
    approved_by: str
    approved_at: str
    approval_scope: str
    allowed_sandbox: str
    allowed_read_paths: list[str] = field(default_factory=list)
    allowed_write_paths: list[str] = field(default_factory=list)
    approved_codex_profile: str = "default"
    workspace_commit: str | None = None
    workspace_clean_required: bool = True
    expires_at: str | None = None
    revoked: bool = False
    revoked_at: str | None = None
    revocation_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LiveExecutionAuthorization":
        allowed = {f.name for f in fields(cls)}
        values = {k: v for k, v in data.items() if k in allowed}
        values["allowed_read_paths"] = _coerce_list(values.get("allowed_read_paths"))
        values["allowed_write_paths"] = _coerce_list(values.get("allowed_write_paths"))
        values["metadata"] = values.get("metadata") if isinstance(values.get("metadata"), dict) else {}
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_authorization(path: str | Path) -> LiveExecutionAuthorization:
    return LiveExecutionAuthorization.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass
class GateDecision:
    status: str
    dispatch_id: str
    adapter_request_id: str | None = None
    execution_authorization_id: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    live_provider_called: bool = False
    workspace: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    request: dict[str, Any] | None = None
    result: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return not self.errors and self.status in {"preview_ready", "completed", "failed"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CodexLiveExecutionGate:
    def __init__(self, *, root: str | Path | None = None, bridge_runner: Callable[..., CodexBridgeResult] | None = None, codex_binary_checker: Callable[[str], bool] | None = None) -> None:
        self.root = _root(root)
        self.bridge_runner = bridge_runner or run_codex_bridge_request
        self.codex_binary_checker = codex_binary_checker or (lambda binary: shutil.which(binary) is not None)

    def _load_request_for_dispatch(self, dispatch_id: str):
        item = inspect_dispatch_item(dispatch_id, self.root)
        if not item.handoff_reference:
            raise ValueError("dispatch handoff_reference is required")
        request_path = self.root / item.handoff_reference
        return item, load_adapter_request(request_path)

    def _validate(self, dispatch_id: str, authorization: LiveExecutionAuthorization, *, require_confirmation: bool) -> tuple[GateDecision, Any, ExecutionProviderAdapterRequest | None]:
        errors: list[str] = []
        warnings: list[str] = []
        request = None
        workspace = current_workspace(self.root)
        try:
            item, request = self._load_request_for_dispatch(dispatch_id)
        except Exception as exc:
            return GateDecision(status="blocked", dispatch_id=dispatch_id, errors=[str(exc)], workspace=workspace), None, None
        if item.state != "Ready": errors.append("dispatch state must be Ready")
        if authorization.dispatch_id != dispatch_id or request.dispatch_id != dispatch_id: errors.append("dispatch_id mismatch")
        if authorization.adapter_request_id != request.adapter_request_id: errors.append("adapter_request_id mismatch")
        if authorization.provider_id != request.provider_id or authorization.provider_type != request.provider_type: errors.append("provider mismatch")
        if authorization.work_package_id != (request.work_package_id or ""): errors.append("work_package_id mismatch")
        for label, value in [("decision_reference", authorization.decision_reference), ("traffic_controller_authorization_reference", authorization.traffic_controller_authorization_reference), ("steward_approval_reference", authorization.steward_approval_reference), ("approved_by", authorization.approved_by), ("approved_at", authorization.approved_at), ("approval_scope", authorization.approval_scope)]:
            if not str(value or "").strip(): errors.append(f"{label} is required")
        if authorization.decision_reference != request.decision_reference: errors.append("decision_reference mismatch")
        if authorization.revoked: errors.append("execution authorization is revoked")
        expires = _parse_time(authorization.expires_at)
        if expires and expires <= datetime.now(timezone.utc): errors.append("execution authorization is expired")
        if authorization.allowed_sandbox not in ALLOWED_SANDBOXES: errors.append("authorized sandbox is prohibited")
        sandbox = str(request.metadata.get("sandbox", "read-only"))
        if sandbox != authorization.allowed_sandbox: errors.append("sandbox mismatch")
        if sandbox == "danger-full-access" or request.metadata.get("danger_full_access_requested"): errors.append("danger-full-access is prohibited")
        if request.metadata.get("bypass_flags"): errors.append("bypass flags are prohibited")
        profile = str(request.metadata.get("codex_home_profile") or request.profile_label or "default")
        allowed_profiles = ALLOWED_PROVIDER_PROFILES.get(request.provider_id, set()) if isinstance(ALLOWED_PROVIDER_PROFILES, dict) else ALLOWED_PROVIDER_PROFILES
        if profile != authorization.approved_codex_profile or profile not in allowed_profiles: errors.append("provider profile is not approved")
        if not authorization.allowed_read_paths: errors.append("allowed_read_paths are required")
        if sandbox == "workspace-write" and not authorization.allowed_write_paths: errors.append("workspace-write requires explicit approved write paths")
        for path in request.read_scope_paths:
            if not _within(path, authorization.allowed_read_paths): errors.append(f"read path outside authorization: {path}")
        for path in request.write_scope_paths:
            if not _within(path, authorization.allowed_write_paths): errors.append(f"write path outside authorization: {path}")
            for blocked in request.blocked_scope_paths + ["archive", "runtime"]:
                if _overlap(path, blocked): errors.append(f"write path conflicts with forbidden path: {path}")
        if authorization.workspace_commit and workspace.get("commit") != authorization.workspace_commit: errors.append("workspace commit does not match authorization")
        dirty_exception = bool(authorization.metadata.get("workspace_dirty_exception_approved"))
        if authorization.workspace_clean_required and workspace.get("dirty") and not dirty_exception: errors.append("workspace is dirty")
        codex_binary = str(request.metadata.get("codex_binary", "codex"))
        if not self.codex_binary_checker(codex_binary): errors.append("Codex binary is not available")
        adapter_validation = CodexBridgeExecutionProviderAdapter(root=self.root).validate_request(request)
        errors.extend(adapter_validation.errors)
        warnings.extend(adapter_validation.warnings)
        if require_confirmation is False: errors.append("explicit live execution confirmation is required")
        status = "blocked" if errors else "preview_ready"
        return GateDecision(status=status, dispatch_id=dispatch_id, adapter_request_id=request.adapter_request_id, execution_authorization_id=authorization.execution_authorization_id, errors=errors, warnings=warnings, workspace=workspace, request=request.to_dict()), item, request

    def preview(self, dispatch_id: str, authorization_path: str | Path) -> dict[str, Any]:
        authorization = load_authorization(authorization_path)
        decision, _, request = self._validate(dispatch_id, authorization, require_confirmation=True)
        decision.live_provider_called = False
        self._persist_decision(decision, authorization, request, "preview")
        return decision.to_dict()

    def execute(self, dispatch_id: str, authorization_path: str | Path, *, confirm_live_execution: bool = False) -> dict[str, Any]:
        authorization = load_authorization(authorization_path)
        decision, _, request = self._validate(dispatch_id, authorization, require_confirmation=confirm_live_execution)
        if decision.errors or request is None:
            decision.status = "blocked"
            decision.live_provider_called = False
            self._persist_decision(decision, authorization, request, "blocked")
            return decision.to_dict()
        write_adapter_request(request, root=self.root)
        self._persist_decision(decision, authorization, request, "started")
        update_dispatch_state(dispatch_id, "Running", self.root, summary="Codex live execution gate approved provider call.")
        result = CodexBridgeExecutionProviderAdapter(root=self.root, bridge_runner=self.bridge_runner).submit(request)
        decision.status = result.status
        decision.live_provider_called = bool(result.metadata.get("live_provider_called", False))
        decision.result = result.to_dict()
        result_path = write_adapter_result(result, root=self.root)
        status_paths = write_status_artifacts(result, root=self.root)
        decision.artifacts.update({"result_path": _rel(result_path, self.root), **{k: _rel(Path(v), self.root) for k, v in status_paths.items()}})
        self._persist_decision(decision, authorization, request, "completed")
        return decision.to_dict()

    def status(self, dispatch_id: str) -> dict[str, Any]:
        path = self.root / EXECUTIONS_DIR / f"{dispatch_id}.json"
        if not path.exists():
            return {"status": "not_found", "dispatch_id": dispatch_id, "live_provider_called": False}
        return json.loads(path.read_text(encoding="utf-8"))

    def report(self, dispatch_id: str) -> str:
        payload = self.status(dispatch_id)
        return "\n".join(["# Steward-Authorized Live Codex Execution", "", f"Dispatch: `{dispatch_id}`", f"Status: `{payload.get('status')}`", f"Live provider called: `{payload.get('live_provider_called', False)}`", "", "Provider execution is not validation or institutional acceptance.", ""])

    def _persist_decision(self, decision: GateDecision, authorization: LiveExecutionAuthorization, request: ExecutionProviderAdapterRequest | None, phase: str) -> None:
        payload = decision.to_dict()
        payload.update({"phase": phase, "updated_at": _now(), "authorization": authorization.to_dict()})
        auth_path = _write_json(self.root / AUTHORIZATIONS_DIR / f"{authorization.execution_authorization_id}.json", authorization.to_dict())
        exec_path = _write_json(self.root / EXECUTIONS_DIR / f"{decision.dispatch_id}.json", payload)
        adapter_id = decision.adapter_request_id or (request.adapter_request_id if request else decision.dispatch_id)
        report_path = self.root / REPORTS_DIR / f"{adapter_id}_live_execution.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(self.report(decision.dispatch_id), encoding="utf-8")
        decision.artifacts.update({"authorization_path": _rel(auth_path, self.root), "execution_path": _rel(exec_path, self.root), "report_path": _rel(report_path, self.root)})
