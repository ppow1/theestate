"""Execution attempt lease, cancellation, and recovery runtime.

This runtime adds operational controls around governed provider execution. It
records evidence only: it never authorizes execution, starts retries, schedules
work, or grants institutional acceptance.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from estate.core.execution_activity import EVENTS_OUTPUT as ACTIVITY_EVENTS_OUTPUT, generate_execution_activity_surface
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.paths import ESTATE_ROOT

ATTEMPTS_DIR = Path("runtime/execution_adapters/attempts")
LEASES_DIR = Path("runtime/execution_adapters/leases")
CANCELLATIONS_DIR = Path("runtime/execution_adapters/cancellations")
RECOVERY_DIR = Path("runtime/execution_adapters/recovery")
STATUS_DIR = Path("runtime/execution_adapters/status")
REPORTS_DIR = Path("runtime/execution_adapters/reports")

ACTIVE_STATES = {"prepared", "starting", "running", "cancellation_requested"}
TERMINAL_STATES = {"cancelled", "completed", "failed", "stale", "abandoned", "completed_unreconciled", "superseded"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


class ProcessController(Protocol):
    def observe(self, *, process_id: int | None, process_identity: str | None, attempt: "ExecutionAttemptRecord") -> str: ...
    def request_cancel(self, *, process_id: int | None, process_identity: str | None, attempt: "ExecutionAttemptRecord") -> dict[str, Any]: ...


class UnknownProcessController:
    def observe(self, *, process_id: int | None, process_identity: str | None, attempt: "ExecutionAttemptRecord") -> str:
        return "process_unknown"

    def request_cancel(self, *, process_id: int | None, process_identity: str | None, attempt: "ExecutionAttemptRecord") -> dict[str, Any]:
        return {"status": "cancellation_failed", "verified_owner": False, "signal_sent": False, "reason": "no process controller configured"}


@dataclass
class ExecutionAttemptRecord:
    execution_attempt_id: str
    dispatch_id: str
    adapter_request_id: str
    provider_id: str
    provider_type: str
    work_package_id: str | None = None
    execution_authorization_id: str | None = None
    workspace_commit: str | None = None
    state: str = "prepared"
    started_at: str | None = None
    last_heartbeat_at: str | None = None
    finished_at: str | None = None
    process_id: int | None = None
    process_identity: str | None = None
    lease_owner: str | None = None
    lease_acquired_at: str | None = None
    lease_expires_at: str | None = None
    cancellation_requested: bool = False
    cancellation_requested_at: str | None = None
    cancellation_requested_by: str | None = None
    cancellation_reason: str | None = None
    cancellation_signal_sent: bool = False
    cancellation_signal_status: str | None = None
    provider_call_started: str | None = None
    provider_call_finished: str | None = None
    result_reference: str | None = None
    reconciliation_reference: str | None = None
    supersedes_attempt_id: str | None = None
    superseded_by_attempt_id: str | None = None
    retry_eligible: bool = False
    retry_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionAttemptRecord":
        allowed = {f.name for f in fields(cls)}
        values = {k: v for k, v in data.items() if k in allowed}
        values["metadata"] = values.get("metadata") if isinstance(values.get("metadata"), dict) else {}
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionAttemptRuntime:
    def __init__(self, *, root: str | Path | None = None, clock: Any | None = None, process_controller: ProcessController | None = None, stale_after_seconds: int = 900) -> None:
        self.root = _root(root)
        self.clock = clock
        self.process_controller = process_controller or UnknownProcessController()
        self.stale_after_seconds = stale_after_seconds

    def now(self) -> str:
        if self.clock:
            value = self.clock()
            if isinstance(value, datetime):
                return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            return str(value)
        return utc_now()

    def acquire_lease(self, *, dispatch_id: str, adapter_request_id: str, provider_id: str, provider_type: str, work_package_id: str | None = None, execution_authorization_id: str | None = None, workspace_commit: str | None = None, process_id: int | None = None, process_identity: str | None = None, lease_ttl_seconds: int | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        lease_path = self.root / LEASES_DIR / f"{dispatch_id}.json"
        if lease_path.exists():
            lease = _read_json(lease_path)
            if not isinstance(lease, dict) or not lease.get("execution_attempt_id"):
                raise ValueError("malformed active lease blocks acquisition")
            existing = self.load_attempt(str(lease["execution_attempt_id"]))
            inspection = self.inspect_recovery(dispatch_id)
            if existing.state in ACTIVE_STATES and not inspection.get("stale_release_safe"):
                raise ValueError("active execution lease already exists for dispatch")
            raise ValueError("stale lease requires explicit release before a new attempt")
        now = self.now()
        attempt_id = f"attempt-{uuid4().hex[:12]}"
        record = ExecutionAttemptRecord(attempt_id, dispatch_id, adapter_request_id, provider_id, provider_type, work_package_id, execution_authorization_id, workspace_commit, "running", now, now, None, process_id, process_identity, attempt_id, now, None, metadata=metadata or {})
        if lease_ttl_seconds:
            record.lease_expires_at = now
            record.metadata["lease_ttl_seconds"] = lease_ttl_seconds
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        lease_payload = {"dispatch_id": dispatch_id, "execution_attempt_id": attempt_id, "adapter_request_id": adapter_request_id, "lease_owner": attempt_id, "process_id": process_id, "process_identity": process_identity, "workspace_commit": workspace_commit, "lease_acquired_at": now}
        lease_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lease_path, flags)
        with os.fdopen(fd, "w", encoding="utf-8") as h:
            h.write(json.dumps(lease_payload, indent=2, sort_keys=True) + "\n")
        self._save_attempt(record)
        self._activity(record, "execution_attempt_started", "Execution attempt started.")
        return {"status": "acquired", "attempt": record.to_dict(), "lease_path": _rel(lease_path, self.root)}

    def load_attempt(self, attempt_id: str) -> ExecutionAttemptRecord:
        data = _read_json(self.root / ATTEMPTS_DIR / f"{attempt_id}.json")
        if not data:
            raise ValueError("execution attempt does not exist")
        return ExecutionAttemptRecord.from_dict(data)

    def active_for_dispatch(self, dispatch_id: str) -> ExecutionAttemptRecord | None:
        lease = _read_json(self.root / LEASES_DIR / f"{dispatch_id}.json")
        if not lease:
            return None
        if not isinstance(lease, dict) or not lease.get("execution_attempt_id"):
            raise ValueError("malformed active lease")
        return self.load_attempt(str(lease["execution_attempt_id"]))

    def heartbeat(self, dispatch_id: str, attempt_id: str, *, state: str = "running", observer_state: str | None = None) -> dict[str, Any]:
        attempt = self.active_for_dispatch(dispatch_id)
        if not attempt or attempt.execution_attempt_id != attempt_id:
            raise ValueError("heartbeat rejected because attempt does not own active lease")
        if attempt.state in TERMINAL_STATES:
            raise ValueError("heartbeat rejected for terminal attempt")
        if state not in ACTIVE_STATES:
            raise ValueError("heartbeat state must be active")
        attempt.state = "cancellation_requested" if attempt.cancellation_requested else state
        attempt.last_heartbeat_at = self.now()
        if observer_state:
            attempt.metadata["last_process_observer_state"] = observer_state
        self._save_attempt(attempt)
        self._activity(attempt, "execution_attempt_heartbeat", f"Execution attempt heartbeat observed: {observer_state or 'not_observed'}.")
        return {"status": "heartbeat_recorded", "attempt": attempt.to_dict()}

    def request_cancellation(self, dispatch_id: str, attempt_id: str, *, requested_by: str = "operator", reason: str, cooperative: bool = True) -> dict[str, Any]:
        attempt = self.active_for_dispatch(dispatch_id)
        if not attempt or attempt.execution_attempt_id != attempt_id:
            raise ValueError("cancellation rejected because attempt does not own active lease")
        now = self.now()
        attempt.cancellation_requested = True
        attempt.cancellation_requested_at = now
        attempt.cancellation_requested_by = requested_by
        attempt.cancellation_reason = reason
        attempt.state = "cancellation_requested"
        signal = {"status": "cancellation_not_attempted", "signal_sent": False}
        if cooperative:
            signal = self.process_controller.request_cancel(process_id=attempt.process_id, process_identity=attempt.process_identity, attempt=attempt)
            attempt.cancellation_signal_sent = bool(signal.get("signal_sent"))
            attempt.cancellation_signal_status = str(signal.get("status"))
            if attempt.cancellation_signal_sent:
                self._activity(attempt, "execution_cancellation_signal_sent", "Cooperative cancellation signal sent through verified process-control seam.")
        self._save_attempt(attempt)
        artifact = {"dispatch_id": dispatch_id, "execution_attempt_id": attempt_id, "requested_at": now, "requested_by": requested_by, "reason": reason, "cooperative_signal": signal}
        _write_json(self.root / CANCELLATIONS_DIR / f"{attempt_id}.json", artifact)
        self._activity(attempt, "execution_cancellation_requested", "Execution cancellation requested; rollback is not implied.")
        return {"status": "cancellation_requested", "attempt": attempt.to_dict(), "cooperative_signal": signal}

    def complete_attempt(self, attempt_id: str, *, status: str, result_reference: str | None = None, reconciliation_reference: str | None = None) -> dict[str, Any]:
        attempt = self.load_attempt(attempt_id)
        if status not in {"completed", "failed", "cancelled"}:
            raise ValueError("completion status must be completed, failed, or cancelled")
        attempt.state = status
        attempt.finished_at = self.now()
        attempt.provider_call_finished = attempt.provider_call_finished or attempt.finished_at
        attempt.result_reference = result_reference or attempt.result_reference
        attempt.reconciliation_reference = reconciliation_reference or attempt.reconciliation_reference
        self._save_attempt(attempt)
        lease_path = self.root / LEASES_DIR / f"{attempt.dispatch_id}.json"
        lease = _read_json(lease_path)
        if lease and lease.get("execution_attempt_id") == attempt_id:
            lease_path.unlink()
        self._activity(attempt, {"completed":"execution_attempt_completed_unreconciled","failed":"execution_attempt_failed","cancelled":"execution_attempt_cancelled"}[status], f"Execution attempt marked {status}.")
        return {"status": status, "attempt": attempt.to_dict(), "lease_released": True}

    def status(self, dispatch_id: str | None = None) -> dict[str, Any]:
        attempts = [ExecutionAttemptRecord.from_dict(json.loads(p.read_text(encoding="utf-8"))).to_dict() for p in sorted((self.root / ATTEMPTS_DIR).glob("*.json"))]
        if dispatch_id:
            attempts = [a for a in attempts if a.get("dispatch_id") == dispatch_id]
        summary = self._summary(attempts)
        payload = {"status": "ok", "dispatch_id": dispatch_id, "summary": summary, "attempts": attempts, "live_provider_called": False}
        _write_json(self.root / STATUS_DIR / "attempts_summary.json", payload)
        return payload

    def inspect_recovery(self, dispatch_id: str) -> dict[str, Any]:
        attempt = self.active_for_dispatch(dispatch_id)
        if not attempt:
            payload = {"status": "no_active_attempt", "dispatch_id": dispatch_id, "classification": "manual review required", "stale_release_safe": False}
        else:
            observer = self.process_controller.observe(process_id=attempt.process_id, process_identity=attempt.process_identity, attempt=attempt)
            stale = self._is_stale(attempt)
            if attempt.cancellation_requested and attempt.state not in {"cancelled", "failed", "completed"}:
                classification = "cancellation requested but outcome unknown"
            elif attempt.state == "completed" and not attempt.reconciliation_reference:
                classification = "result exists but reconciliation missing"
                attempt.state = "completed_unreconciled"
                self._save_attempt(attempt)
                self._activity(attempt, "execution_attempt_completed_unreconciled", "Completed provider attempt lacks reconciliation.")
            elif attempt.state in {"failed", "cancelled", "completed"}:
                classification = {"failed":"confirmed failed","cancelled":"confirmed cancelled","completed":"completed and reconciled"}[attempt.state]
            elif observer == "process_missing":
                classification = "process missing and no result"
                attempt.state = "abandoned"
                self._save_attempt(attempt)
                self._activity(attempt, "execution_attempt_abandoned", "Execution attempt process is missing and no result is confirmed.")
            elif stale:
                classification = "running but heartbeat stale"
                self._activity(attempt, "execution_attempt_stale", "Execution attempt heartbeat is stale.")
            elif observer == "process_alive":
                classification = "running and healthy"
            else:
                classification = "manual review required"
            payload = {"status": "inspected", "dispatch_id": dispatch_id, "execution_attempt_id": attempt.execution_attempt_id, "classification": classification, "process_observer_state": observer, "heartbeat_stale": stale, "stale_release_safe": stale and observer in {"process_missing", "process_unknown"}, "attempt": attempt.to_dict()}
        _write_json(self.root / RECOVERY_DIR / f"{dispatch_id}.json", payload)
        return payload

    def release_stale(self, dispatch_id: str, attempt_id: str, *, confirm_stale_release: bool = False, released_by: str = "operator", reason: str = "explicit stale release") -> dict[str, Any]:
        if not confirm_stale_release:
            raise ValueError("--confirm-stale-release is required")
        inspection = self.inspect_recovery(dispatch_id)
        if not inspection.get("stale_release_safe") or inspection.get("execution_attempt_id") != attempt_id:
            raise ValueError("active lease is not proven stale-safe for release")
        attempt = self.load_attempt(attempt_id)
        attempt.state = "stale"
        attempt.finished_at = self.now()
        attempt.metadata["stale_released_by"] = released_by
        attempt.metadata["stale_release_reason"] = reason
        self._save_attempt(attempt)
        (self.root / LEASES_DIR / f"{dispatch_id}.json").unlink(missing_ok=True)
        self._activity(attempt, "execution_attempt_recovered", "Stale execution lease explicitly released; retry not authorized.")
        return {"status": "stale_released", "attempt": attempt.to_dict(), "retry_authorized": False}

    def retry_eligibility(self, dispatch_id: str) -> dict[str, Any]:
        attempts = self.status(dispatch_id)["attempts"]
        prior = attempts[-1] if attempts else None
        blocking = []
        eligible = False
        if not prior:
            blocking.append("no prior attempt evidence")
        elif prior.get("state") in {"failed", "stale", "abandoned", "cancelled"}:
            eligible = True
        else:
            blocking.append(f"prior attempt state is {prior.get('state')}")
        payload = {"retry_eligible": eligible, "blocking_reasons": blocking, "required_authorization": "new Steward/Traffic Controller retry authorization required", "prior_attempt_id": prior.get("execution_attempt_id") if prior else None, "prior_result_reference": prior.get("result_reference") if prior else None, "workspace_commit_match": True if prior and prior.get("workspace_commit") else None, "provider_side_effect_risk": "manual_review_required", "manual_review_required": True, "automatic_retry_started": False}
        if prior:
            rec = self.load_attempt(prior["execution_attempt_id"]); rec.retry_eligible = eligible; rec.retry_reason = "; ".join(blocking) or "eligible for governed retry review"; self._save_attempt(rec)
        self._activity(ExecutionAttemptRecord("retry-review", dispatch_id, "", "", ""), "execution_retry_review_required", "Retry eligibility evidence generated; retry is not authorized or started.")
        return payload

    def preserve_late_result(self, result: ExecutionProviderAdapterResult | dict[str, Any], *, attempt_id: str, result_reference: str) -> dict[str, Any]:
        attempt = self.load_attempt(attempt_id)
        late = attempt.state in {"cancelled", "stale", "abandoned", "superseded", "cancellation_requested"}
        attempt.result_reference = result_reference
        attempt.metadata["late_result"] = late
        attempt.metadata["late_result_requires_attention"] = late
        self._save_attempt(attempt)
        payload = {"status": "late_result_preserved" if late else "result_preserved", "execution_attempt_id": attempt_id, "result_reference": result_reference, "late_or_superseded": late, "requires_attention": late, "result": result.to_dict() if hasattr(result, "to_dict") else result}
        _write_json(self.root / RECOVERY_DIR / f"{attempt_id}_late_result.json", payload)
        return payload

    def _is_stale(self, attempt: ExecutionAttemptRecord) -> bool:
        hb = _parse_time(attempt.last_heartbeat_at or attempt.started_at)
        now = _parse_time(self.now())
        return bool(hb and now and (now - hb).total_seconds() > self.stale_after_seconds)

    def _save_attempt(self, attempt: ExecutionAttemptRecord) -> None:
        _write_json(self.root / ATTEMPTS_DIR / f"{attempt.execution_attempt_id}.json", attempt.to_dict())
        report = self.root / REPORTS_DIR / f"{attempt.execution_attempt_id}_attempt.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(f"# Execution Attempt Report\n\nDispatch: `{attempt.dispatch_id}`\nAttempt: `{attempt.execution_attempt_id}`\nState: `{attempt.state}`\nCancellation requested: `{attempt.cancellation_requested}`\nRetry eligible: `{attempt.retry_eligible}`\n\nThis is operational evidence only.\n", encoding="utf-8")
        self.status(None) if False else None

    def _activity(self, attempt: ExecutionAttemptRecord, event_type: str, summary: str) -> None:
        path = self.root / ACTIVITY_EVENTS_OUTPUT
        path.parent.mkdir(parents=True, exist_ok=True)
        event = {"event_id": f"{attempt.execution_attempt_id}-{event_type}-{self.now()}", "request_id": attempt.dispatch_id, "work_package_id": attempt.work_package_id, "source": "execution_attempt_runtime", "provider": attempt.provider_id, "state": attempt.state, "event_type": event_type, "timestamp": self.now(), "attention_required": event_type in {"execution_attempt_stale", "execution_attempt_abandoned", "execution_attempt_completed_unreconciled", "execution_retry_review_required"}, "summary": summary, "metadata": {"execution_attempt_id": attempt.execution_attempt_id}}
        with path.open("a", encoding="utf-8") as h:
            h.write(json.dumps(event, sort_keys=True) + "\n")
        generate_execution_activity_surface(self.root, write=True)

    def _summary(self, attempts: list[dict[str, Any]]) -> dict[str, Any]:
        return {"active_attempt_count": sum(1 for a in attempts if a.get("state") in ACTIVE_STATES), "stale_attempt_count": sum(1 for a in attempts if a.get("state") == "stale"), "cancellation_requested_count": sum(1 for a in attempts if a.get("cancellation_requested")), "completed_unreconciled_count": sum(1 for a in attempts if a.get("state") == "completed_unreconciled"), "human_attention_required_count": sum(1 for a in attempts if a.get("state") in {"stale", "abandoned", "completed_unreconciled"} or a.get("cancellation_requested")), "attempt_count": len(attempts)}
