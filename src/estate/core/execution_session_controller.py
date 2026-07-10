"""Governed execution session controller for one dispatch item and one attempt."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from estate.core.codex_live_execution_gate import CodexLiveExecutionGate, current_workspace, load_authorization
from estate.core.execution_adapter_handoff_runtime import prepare_handoff, validate_handoff
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.execution_dispatch import inspect_dispatch_item
from estate.core.execution_provider_adapter_runtime import RESULTS_DIR
from estate.core.execution_result_reconciliation_runtime import reconcile_result
from estate.core.paths import ESTATE_ROOT

RUNTIME_DIR = Path("runtime/execution_adapters")
SESSIONS_DIR = RUNTIME_DIR / "sessions"
SESSION_STAGES_DIR = RUNTIME_DIR / "session_stages"
STATUS_DIR = RUNTIME_DIR / "status"
REPORTS_DIR = RUNTIME_DIR / "reports"

SESSION_STATES = ["prepared","previewed","authorized","lease_acquired","provider_starting","provider_running","provider_result_received","reconciling","validation_ready","blocked","cancellation_requested","cancelled","failed","completed_execution"]
SESSION_STAGES = ["dispatch_inspection","handoff_validation","authorization_validation","workspace_validation","attempt_lease_acquisition","provider_execution_preview_or_start","provider_result_persistence","result_reconciliation","lease_release","validation_readiness_publication","session_report_publication"]


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _rel(path: str | Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


@dataclass
class ExecutionSessionStageRecord:
    stage: str
    started_at: str
    finished_at: str | None = None
    status: str = "started"
    input_references: dict[str, Any] = field(default_factory=dict)
    output_references: dict[str, Any] = field(default_factory=dict)
    live_provider_called: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionSessionRecord:
    execution_session_id: str
    dispatch_id: str
    work_package_id: str | None = None
    adapter_request_id: str | None = None
    execution_authorization_id: str | None = None
    execution_attempt_id: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    workspace_commit: str | None = None
    state: str = "prepared"
    current_stage: str = "dispatch_inspection"
    stages_completed: list[str] = field(default_factory=list)
    started_at: str | None = None
    updated_at: str | None = None
    finished_at: str | None = None
    preview_only: bool = False
    live_provider_called: bool = False
    cancellation_requested: bool = False
    result_reference: str | None = None
    reconciliation_reference: str | None = None
    validation_reference: str | None = None
    attention_required: bool = False
    attention_reason: str | None = None
    blocking_reasons: list[str] = field(default_factory=list)
    failure_stage: str | None = None
    failure_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionSessionController:
    def __init__(self, *, root: str | Path | None = None, gate: CodexLiveExecutionGate | None = None, gate_factory: Callable[[], CodexLiveExecutionGate] | None = None, attempt_runtime: ExecutionAttemptRuntime | None = None) -> None:
        self.root = _root(root)
        self.gate = gate
        self.gate_factory = gate_factory
        self.attempt_runtime = attempt_runtime or ExecutionAttemptRuntime(root=self.root)

    def _session_path(self, sid: str) -> Path: return self.root / SESSIONS_DIR / f"{sid}.json"
    def _stages_path(self, sid: str) -> Path: return self.root / SESSION_STAGES_DIR / f"{sid}.jsonl"

    def _save(self, rec: ExecutionSessionRecord) -> dict[str, Any]:
        rec.updated_at = _now()
        _write_json(self._session_path(rec.execution_session_id), rec.to_dict())
        self._write_summary()
        return rec.to_dict()

    def _load(self, sid: str) -> ExecutionSessionRecord:
        return ExecutionSessionRecord(**json.loads(self._session_path(sid).read_text(encoding="utf-8")))

    def _stage(self, rec: ExecutionSessionRecord, stage: str, status: str = "completed", **kw: Any) -> None:
        row = ExecutionSessionStageRecord(stage=stage, started_at=_now(), finished_at=_now(), status=status, **kw).to_dict()
        p = self._stages_path(rec.execution_session_id); p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as h: h.write(json.dumps(row, sort_keys=True) + "\n")
        rec.current_stage = stage
        if status == "completed" and stage not in rec.stages_completed: rec.stages_completed.append(stage)

    def _block(self, rec: ExecutionSessionRecord, stage: str, reasons: list[str], kind: str = "blocked") -> dict[str, Any]:
        rec.state = kind; rec.attention_required = True; rec.attention_reason = "; ".join(reasons); rec.blocking_reasons = reasons; rec.failure_stage = stage if kind == "failed" else None; rec.failure_summary = rec.attention_reason if kind == "failed" else None; rec.finished_at = _now()
        self._stage(rec, stage, "failed" if kind == "failed" else "blocked", errors=reasons, live_provider_called=rec.live_provider_called)
        self._publish_report(rec)
        return self._save(rec)

    def preview(self, dispatch_id: str, authorization_path: str | Path) -> dict[str, Any]:
        rec = ExecutionSessionRecord(execution_session_id=f"session-{uuid4().hex[:12]}", dispatch_id=dispatch_id, started_at=_now(), preview_only=True)
        try:
            item = inspect_dispatch_item(dispatch_id, self.root); rec.work_package_id = item.work_package_id; rec.provider_id = item.provider; rec.provider_type = (item.provider_metadata or {}).get("provider_type") or item.provider; self._stage(rec, "dispatch_inspection")
            handoff = prepare_handoff(dispatch_id, self.root); rec.adapter_request_id = (handoff.get("adapter_request") or {}).get("adapter_request_id"); self._stage(rec, "handoff_validation", "completed" if not handoff.get("errors") else "blocked", output_references=handoff.get("artifacts", {}), errors=handoff.get("errors", []), warnings=handoff.get("warnings", []))
            if handoff.get("errors"): return self._block(rec, "handoff_validation", handoff["errors"])
            auth = load_authorization(authorization_path); rec.execution_authorization_id = auth.execution_authorization_id; self._stage(rec, "authorization_validation", input_references={"authorization_path": str(authorization_path)})
            ws = current_workspace(self.root); rec.workspace_commit = ws.get("commit"); self._stage(rec, "workspace_validation", "blocked" if ws.get("dirty") else "completed", warnings=[ws.get("dirty_status", "")] if ws.get("dirty") else [])
            gate = self._gate(); decision = gate.preview(dispatch_id, authorization_path); rec.live_provider_called = False
            if decision.get("errors"): return self._block(rec, "provider_execution_preview_or_start", list(decision.get("errors", [])))
            rec.state = "previewed"; self._stage(rec, "provider_execution_preview_or_start", output_references={"next_operations": ["acquire execution lease", "call live execution gate once", "persist result", "reconcile", "release lease", "publish report"]}, live_provider_called=False)
            self._publish_report(rec); return self._save(rec)
        except Exception as exc:
            return self._block(rec, rec.current_stage, [str(exc)])

    def start(self, dispatch_id: str, authorization_path: str | Path, *, confirm_live_execution: bool = False) -> dict[str, Any]:
        if not confirm_live_execution:
            rec = ExecutionSessionRecord(execution_session_id=f"session-{uuid4().hex[:12]}", dispatch_id=dispatch_id, started_at=_now())
            return self._block(rec, "authorization_validation", ["explicit live execution confirmation is required"])
        rec = ExecutionSessionRecord(execution_session_id=f"session-{uuid4().hex[:12]}", dispatch_id=dispatch_id, started_at=_now())
        try:
            item = inspect_dispatch_item(dispatch_id, self.root); rec.work_package_id = item.work_package_id; rec.provider_id = item.provider; rec.provider_type = (item.provider_metadata or {}).get("provider_type") or item.provider; rec.adapter_request_id = item.handoff_reference; self._stage(rec, "dispatch_inspection")
            handoff = validate_handoff(dispatch_id, self.root); self._stage(rec, "handoff_validation", "completed" if not handoff.get("errors") else "blocked", errors=handoff.get("errors", []))
            if handoff.get("errors"): return self._block(rec, "handoff_validation", handoff["errors"])
            auth = load_authorization(authorization_path); rec.execution_authorization_id = auth.execution_authorization_id; rec.adapter_request_id = auth.adapter_request_id; self._stage(rec, "authorization_validation")
            ws = current_workspace(self.root); rec.workspace_commit = ws.get("commit");
            if ws.get("dirty") and not auth.metadata.get("workspace_dirty_exception_approved"): return self._block(rec, "workspace_validation", ["workspace is dirty"])
            self._stage(rec, "workspace_validation")
            active = self.attempt_runtime.active_for_dispatch(dispatch_id)
            if active: return self._block(rec, "attempt_lease_acquisition", ["active execution lease already exists for dispatch"])
            self._stage(rec, "attempt_lease_acquisition")
            rec.state = "provider_starting"; self._save(rec)
            decision = self._gate().execute(dispatch_id, authorization_path, confirm_live_execution=True)
            rec.live_provider_called = bool(decision.get("live_provider_called")); rec.result_reference = (decision.get("artifacts") or {}).get("result_path"); rec.execution_attempt_id = self._latest_attempt(dispatch_id)
            self._stage(rec, "provider_execution_preview_or_start", "completed" if rec.live_provider_called else "blocked", output_references=decision.get("artifacts", {}), errors=decision.get("errors", []), live_provider_called=rec.live_provider_called)
            if decision.get("errors"): return self._block(rec, "provider_execution_preview_or_start", decision.get("errors", []), "failed" if rec.live_provider_called else "blocked")
            self._stage(rec, "provider_result_persistence", output_references={"result_reference": rec.result_reference}, live_provider_called=rec.live_provider_called)
            if decision.get("status") == "failed": return self._block(rec, "provider_execution_preview_or_start", [decision.get("result", {}).get("summary") or "provider execution failure"], "failed")
            rec.state = "reconciling"; self._stage(rec, "result_reconciliation", "started", live_provider_called=rec.live_provider_called); self._save(rec)
            try:
                rec_payload = reconcile_result(dispatch_id, self.root / (rec.result_reference or ""), self.root); rec.reconciliation_reference = rec_payload.get("reconciliation_path"); rec.validation_reference = rec_payload.get("report_path") if rec_payload.get("dispatch_state") == "Validation" else None
            except Exception as exc:
                return self._block(rec, "result_reconciliation", [str(exc)], "failed")
            self._stage(rec, "result_reconciliation", output_references={"reconciliation_reference": rec.reconciliation_reference}, live_provider_called=rec.live_provider_called)
            self._stage(rec, "lease_release", live_provider_called=rec.live_provider_called)
            rec.state = "validation_ready"; self._stage(rec, "validation_readiness_publication", output_references={"validation_reference": rec.validation_reference}, live_provider_called=rec.live_provider_called)
            rec.state = "completed_execution"; rec.finished_at = _now(); self._publish_report(rec); self._stage(rec, "session_report_publication", output_references={"report": f"runtime/execution_adapters/reports/{rec.execution_session_id}_session.md"}, live_provider_called=rec.live_provider_called)
            return self._save(rec)
        except Exception as exc:
            return self._block(rec, rec.current_stage, [str(exc)], "failed" if rec.live_provider_called else "blocked")

    def resume(self, session_id: str) -> dict[str, Any]:
        rec = self._load(session_id)
        if rec.live_provider_called and not rec.result_reference:
            return self._block(rec, rec.current_stage, ["ambiguous interrupted execution; provider call may have occurred and no result is recorded"], "failed")
        if rec.result_reference and not rec.reconciliation_reference:
            try:
                payload = reconcile_result(rec.dispatch_id, self.root / rec.result_reference, self.root); rec.reconciliation_reference = payload.get("reconciliation_path"); rec.state = "validation_ready"; self._stage(rec, "result_reconciliation", output_references={"reconciliation_reference": rec.reconciliation_reference}, live_provider_called=rec.live_provider_called)
            except Exception as exc: return self._block(rec, "result_reconciliation", [str(exc)], "failed")
        self._publish_report(rec)
        return self._save(rec)

    def status(self, session_id: str) -> dict[str, Any]:
        return self._load(session_id).to_dict()

    def report(self, session_id: str) -> str:
        rec = self._load(session_id); return self._publish_report(rec).read_text(encoding="utf-8")

    def _gate(self) -> CodexLiveExecutionGate:
        return self.gate or (self.gate_factory() if self.gate_factory else CodexLiveExecutionGate(root=self.root))

    def _latest_attempt(self, dispatch_id: str) -> str | None:
        attempts = self.attempt_runtime.status(dispatch_id).get("attempts", [])
        return attempts[-1].get("execution_attempt_id") if attempts else None

    def _publish_report(self, rec: ExecutionSessionRecord) -> Path:
        p = self.root / REPORTS_DIR / f"{rec.execution_session_id}_session.md"; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(["# Governed Execution Session Report", "", f"Session: `{rec.execution_session_id}`", f"Dispatch: `{rec.dispatch_id}`", f"Work package: `{rec.work_package_id}`", f"Provider: `{rec.provider_id}`", f"State: `{rec.state}`", f"Current stage: `{rec.current_stage}`", f"Attempt: `{rec.execution_attempt_id}`", f"Live provider called: `{rec.live_provider_called}`", f"Cancellation requested: `{rec.cancellation_requested}`", f"Result: `{rec.result_reference}`", f"Reconciliation: `{rec.reconciliation_reference}`", f"Validation: `{rec.validation_reference}`", f"Attention required: `{rec.attention_required}`", f"Reason: `{rec.attention_reason}`", "", "Provider execution and validation evidence do not grant institutional acceptance.", ""]) , encoding="utf-8")
        return p

    def _write_summary(self) -> None:
        sessions = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.root / SESSIONS_DIR).glob("*.json"))]
        _write_json(self.root / STATUS_DIR / "sessions_summary.json", {"updated_at": _now(), "session_count": len(sessions), "sessions": sessions})
