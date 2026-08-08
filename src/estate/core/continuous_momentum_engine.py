"""Bounded Continuous Momentum Engine over canonical projections and adapters."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from uuid import uuid4
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

SCHEMA_VERSION = "estate.continuous-momentum-cycle.v1"
MODES = {"simulation", "dry_run", "live"}
PERMISSIONS = {"recommendation", "preauthorized", "delegated", "protected", "prohibited"}
STAGES = ("observe", "reconcile", "classify", "propose", "authorize", "act", "verify", "record")

REASONING_OWNER_STATES = {"IDLE", "WAKE_PENDING", "STARTING", "PROCESSING", "WAITING_FOR_AUTHORITATIVE_COMPLETION", "STOPPED", "ERROR", "ESCALATED", "ABANDONED"}
DEFAULT_REASONING_STATE = Path(r"A:\theestate-data\chatgpt-mailbox-worker\cme-owner-state.json")
DEFAULT_REASONING_LOCK = Path(r"A:\theestate-data\chatgpt-mailbox-worker\cme-owner.lock")
CANONICAL_WORKER_WRAPPER = Path(r"A:\theestate\tools\start_chatgpt_mailbox_worker_canonical.ps1")


def _time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def run_momentum_cycle(
    *, cycle_id: str, observed_at: str, inputs: dict[str, Any],
    candidates: Iterable[dict[str, Any]], mode: str = "dry_run",
    prior_action_keys: Iterable[str] = (), cooldown_seconds: int = 300,
    last_action_at: str | None = None,
    action_adapter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run one reproducible cycle; only a supplied canonical adapter may act."""
    copied_inputs = deepcopy(inputs)
    copied_candidates = [deepcopy(item) for item in candidates]
    prior_keys = sorted(set(prior_action_keys))
    now = _time(observed_at)
    if not cycle_id or now is None or mode not in MODES or cooldown_seconds < 0:
        raise ValueError("cycle identity, timestamp, mode, and cooldown must be valid")
    warnings: list[str] = []
    holds: list[str] = []
    references: set[str] = set()
    for name, projection in sorted(copied_inputs.items()):
        refs = projection.get("evidence_references") or projection.get("canonical_evidence_references") or []
        references.update(str(ref) for ref in refs if ref)
        if projection.get("authorizes_action") is not False:
            holds.append(f"{name}: input projection does not explicitly deny authority")
        if projection.get("stale") or projection.get("state") in {"stale", "indeterminate", "contradictory"}:
            holds.append(f"{name}: evidence is stale or indeterminate")
        if projection.get("state") in {"failed", "blocked", "degraded"}:
            holds.append(f"{name}: dependency is {projection.get('state')} and requires canonical recovery or clearance")
        if projection.get("warnings"):
            warnings.extend(f"{name}: {warning}" for warning in projection["warnings"])
        if projection.get("protected_decision"):
            holds.append(f"{name}: protected decision required")
    if not copied_inputs:
        holds.append("no canonical input projections supplied")

    normalized: list[dict[str, Any]] = []
    for candidate in copied_candidates:
        permission = str(candidate.get("permission") or "").strip()
        key = str(candidate.get("idempotency_key") or "").strip()
        refs = sorted({str(ref) for ref in candidate.get("source_refs") or [] if ref})
        problems: list[str] = []
        if permission not in PERMISSIONS:
            problems.append("unknown permission classification")
        if not candidate.get("action_id") or not key or not refs or not candidate.get("canonical_mechanism"):
            problems.append("candidate lacks identity, idempotency, source evidence, or canonical mechanism")
        if permission in {"preauthorized", "delegated"} and not candidate.get("authority_refs"):
            problems.append("actionable candidate lacks explicit authority evidence")
        if permission in {"protected", "prohibited"}:
            problems.append("candidate is protected or prohibited")
        if key in prior_keys:
            problems.append("duplicate idempotency key")
        references.update(refs)
        normalized.append({
            **candidate,
            "permission": permission,
            "idempotency_key": key,
            "source_refs": refs,
            "priority": int(candidate.get("priority", 0)),
            "authorization_problems": problems,
            "eligible": not problems and permission in {"recommendation", "preauthorized", "delegated"},
        })
    normalized.sort(key=lambda item: (-item["priority"], str(item.get("action_id"))))

    last = _time(last_action_at)
    cooldown_active = bool(last and (now - last).total_seconds() < cooldown_seconds)
    if cooldown_active:
        holds.append("cycle cooldown has not elapsed")
    selected = next((item for item in normalized if item["eligible"]), None)
    disposition = "safe_idle"
    proposed = None
    result = None
    executed = False
    if holds:
        disposition = "escalate" if any("protected" in hold or "indeterminate" in hold for hold in holds) else "safe_idle"
    elif selected:
        proposed = selected
        if selected["permission"] == "recommendation":
            disposition = "recommend"
        elif mode in {"simulation", "dry_run"}:
            disposition = "simulate" if mode == "simulation" else "authorized_dry_run"
        elif action_adapter is None:
            disposition = "safe_idle"
            holds.append("live action requires an existing canonical action adapter")
        else:
            result = action_adapter(deepcopy(selected))
            executed = True
            disposition = "attempted"
            if not isinstance(result, dict) or not result.get("evidence_reference"):
                holds.append("action adapter did not return canonical outcome evidence")
                disposition = "verification_failed"
    elif normalized:
        disposition = "escalate" if any(item["permission"] == "protected" for item in normalized) else "safe_idle"

    stage_records = []
    for stage in STAGES:
        stage_records.append({
            "stage": stage,
            "status": "completed",
            "evidence": sorted(references),
            "note": {
                "act": "canonical adapter invoked" if executed else "no side effect performed",
                "verify": "adapter evidence recorded" if result and result.get("evidence_reference") else "no executed outcome to verify",
            }.get(stage, "deterministic cycle stage"),
        })
    record = {
        "schema_version": SCHEMA_VERSION,
        "cycle_id": cycle_id,
        "observed_at": observed_at,
        "mode": mode,
        "input_digest": _digest(copied_inputs),
        "candidate_digest": _digest(sorted(copied_candidates, key=lambda item: (str(item.get("action_id")), str(item.get("idempotency_key"))))),
        "stages": stage_records,
        "disposition": disposition,
        "selected_action": proposed,
        "action_executed": executed,
        "action_result": result,
        "holds": sorted(set(holds)),
        "warnings": sorted(set(warnings)),
        "evidence_references": sorted(references | ({result["evidence_reference"]} if result and result.get("evidence_reference") else set())),
        "deduplication": {"prior_action_keys": prior_keys, "selected_key": proposed.get("idempotency_key") if proposed else None},
        "cooldown": {"seconds": cooldown_seconds, "last_action_at": last_action_at, "active": cooldown_active},
        "safe_idle": disposition == "safe_idle",
        "creates_authority": False,
        "canonical_records_mutated_only_by_adapter": executed,
    }
    record["record_digest"] = _digest(record)
    return record


class ChatGPTReasoningCMEOwner:
    """CME's bounded runtime owner for one ChatGPT mailbox activation.

    CME evaluates and launches one bounded worker; it is not a second queue
    or an unbounded polling scheduler. Comms8 remains lifecycle authority.
    """

    def __init__(self, store, *, state_path: str | Path = DEFAULT_REASONING_STATE,
                 lock_path: str | Path = DEFAULT_REASONING_LOCK,
                 wrapper: str | Path = CANONICAL_WORKER_WRAPPER,
                 launcher: Callable[..., Any] | None = None,
                 read_request: Callable[[str], dict[str, Any]] | None = None,
                 now: Callable[[], float] = time.time,
                 backoff_seconds: int = 30) -> None:
        self.store = store
        self.state_path = Path(state_path)
        self.lock_path = Path(lock_path)
        self.wrapper = Path(wrapper)
        self.launcher = launcher or self._launch
        self.read_request = read_request or self._live_read_request
        self.now = now
        self.backoff_seconds = backoff_seconds
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"state": "IDLE"}
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {"state": "IDLE"}
        except (OSError, json.JSONDecodeError):
            return {"state": "ERROR", "reason": "owner_state_unreadable"}

    def _write_state(self, state: str, **extra: Any) -> dict[str, Any]:
        if state not in REASONING_OWNER_STATES:
            raise ValueError("invalid_reasoning_owner_state")
        value = {"owner": "CME", "state": state, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **extra}
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.state_path)
        return value

    def _acquire_lock(self, activation_id: str) -> bool:
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"activation_id": activation_id, "pid": os.getpid()}))
            return True
        except FileExistsError:
            return False

    def _release_lock(self) -> None:
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    def _launch(self, command: list[str], *, cwd: str, env: dict[str, str], stdout, stderr):
        return subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, text=True)

    @staticmethod
    def _alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (OSError, ValueError):
            return False

    def _eligible(self) -> Any | None:
        candidates = self.store.search(status="awaiting_reasoning")
        return candidates[0] if candidates else None

    def _lock_record(self) -> dict[str, Any] | None:
        if not self.lock_path.exists():
            return None
        try:
            value = json.loads(self.lock_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except (OSError, json.JSONDecodeError):
            return {"invalid": True}

    def reconcile_stale_owner(self) -> dict[str, Any]:
        """Recover only a provably dead CME activation without touching work."""
        state = self._read_state()
        active_states = {"WAKE_PENDING", "STARTING", "PROCESSING", "WAITING_FOR_AUTHORITATIVE_COMPLETION"}
        if state.get("state") not in active_states:
            return {"status": "NOT_STALE", **state}

        owner_pid = state.get("pid")
        lock = self._lock_record()
        lock_pid = lock.get("pid") if lock else None
        recorded_pids = [pid for pid in (owner_pid, lock_pid) if pid]
        if not recorded_pids:
            return {"status": "NOT_PROVABLY_STALE", **state, "lock": lock}
        if any(self._alive(pid) for pid in recorded_pids):
            return {"status": "LIVE_OWNER", **state, "lock": lock}

        logical_id = state.get("logical_consultation_id")
        consultation = self.store.get(logical_id) if logical_id else None
        if consultation is None or consultation.status != "awaiting_reasoning" or not consultation.ec8_request_id:
            return {"status": "NOT_ELIGIBLE", **state}
        authoritative = self._authoritative(consultation) or {}
        if authoritative.get("state") == "resolved" and authoritative.get("response"):
            self._release_lock()
            reconciled = self._write_state(
                "STOPPED",
                activation_id=state.get("activation_id"),
                logical_consultation_id=logical_id,
                result="AUTHORITATIVE_COMPLETE_AFTER_OWNER_EXIT",
                completion_time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            return {"status": "TERMINAL_OWNER_RECONCILED", **reconciled}
        if authoritative.get("state") not in {"queued", "awaiting_reasoning"}:
            return {"status": "ACTIVE_OR_TERMINAL_REQUEST", **state, "request": authoritative}
        claim = authoritative.get("claim") or {}
        if claim.get("lease_expires_at") and authoritative.get("state") not in {"resolved", "expired"}:
            return {"status": "ACTIVE_AUTHORITATIVE_LEASE", **state, "request": authoritative}

        history = list(state.get("activation_history") or [])
        prior = {k: state.get(k) for k in ("activation_id", "logical_consultation_id", "pid", "state", "updated_at") if state.get(k) is not None}
        prior["disposition"] = "OWNER_PROCESS_EXITED_UNEXPECTEDLY"
        prior["reconciled_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if prior and prior not in history:
            history.append(prior)
        self._release_lock()
        recovered = self._write_state(
            "ABANDONED",
            activation_id=state.get("activation_id"),
            logical_consultation_id=logical_id,
            reason="OWNER_PROCESS_EXITED_UNEXPECTEDLY",
            recoverable=True,
            stale_pids=recorded_pids,
            activation_history=history,
        )
        return {"status": "STALE_OWNER_RECOVERED", **recovered}

    def _authoritative(self, consultation) -> dict[str, Any] | None:
        if not self.read_request or not consultation.ec8_request_id:
            return None
        return self.read_request(consultation.ec8_request_id)

    @staticmethod
    def _live_read_request(request_id: str) -> dict[str, Any]:
        from estate.core.grace_consultation_loop import GraceConsultationLoop
        return GraceConsultationLoop().read_request(request_id)

    def tick(self) -> dict[str, Any]:
        """Perform one CME owner tick; repeated calls are idempotent."""
        stale = self.reconcile_stale_owner()
        state = self._read_state()
        lock = self._lock_record()
        # Re-entry by this CME owner is idempotent even when a fake launcher
        # does not expose a child PID.  A direct stale-owner inspection still
        # reports LIVE_OWNER, preserving the safety boundary for other owners.
        if (
            state.get("state") in {"STARTING", "PROCESSING", "WAITING_FOR_AUTHORITATIVE_COMPLETION"}
            and lock and lock.get("pid") == os.getpid()
        ):
            return {"status": "ALREADY_RUNNING", **state}
        if stale.get("status") in {"LIVE_OWNER", "ACTIVE_AUTHORITATIVE_LEASE", "NOT_ELIGIBLE"}:
            return stale
        if float(state.get("backoff_until") or 0) > self.now():
            return {"status": "BACKOFF", **state}
        pid = state.get("pid")
        if state.get("state") in {"STARTING", "PROCESSING", "WAITING_FOR_AUTHORITATIVE_COMPLETION"} and self._alive(pid):
            return {"status": "ALREADY_RUNNING", **state}
        consultation = self._eligible()
        if consultation is None:
            self._release_lock()
            return self._write_state("IDLE", result="EMPTY_QUEUE")
        activation_id = f"cme-chatgpt-{uuid4().hex[:16]}"
        if not self._acquire_lock(activation_id):
            return {"status": "ALREADY_RUNNING", **self._read_state()}
        try:
            authoritative = self._authoritative(consultation)
            claim = (authoritative or {}).get("claim") or {}
            if claim.get("lease_expires_at") and (authoritative or {}).get("state") not in {"resolved", "expired"}:
                # An already leased request is not launched again. The worker
                # owner may be reconstructed on the next tick after expiry.
                result = self._write_state("WAITING_FOR_AUTHORITATIVE_COMPLETION", activation_id=activation_id, logical_consultation_id=consultation.logical_consultation_id, reason="active_comms8_lease")
                self._release_lock()
                return result
            history = state.get("activation_history")
            history_kwargs = {"activation_history": history} if history else {}
            self._write_state("WAKE_PENDING", activation_id=activation_id, logical_consultation_id=consultation.logical_consultation_id, root_consultation_id=consultation.root_logical_id, **history_kwargs)
            log_path = self.state_path.with_name(f"{activation_id}.log")
            log = log_path.open("a", encoding="utf-8")
            command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(self.wrapper), "--once"]
            self._write_state("STARTING", activation_id=activation_id, logical_consultation_id=consultation.logical_consultation_id, launch_time=datetime.now(timezone.utc).isoformat(timespec="seconds"), **history_kwargs)
            process = self.launcher(command, cwd=str(self.wrapper.parent.parent), env=os.environ.copy(), stdout=log, stderr=log)
            self._write_state("PROCESSING", activation_id=activation_id, pid=getattr(process, "pid", None), logical_consultation_id=consultation.logical_consultation_id, **history_kwargs)
            return {"status": "STARTED", "activation_id": activation_id, "pid": getattr(process, "pid", None), "logical_consultation_id": consultation.logical_consultation_id}
        except Exception as exc:
            self._release_lock()
            return self._write_state("ERROR", activation_id=activation_id, reason=type(exc).__name__ + ":" + str(exc), backoff_until=self.now() + self.backoff_seconds)

    def reconcile(self) -> dict[str, Any]:
        state = self._read_state()
        pid = state.get("pid")
        process = state.get("process")
        if state.get("state") in {"STARTING", "PROCESSING"} and self._alive(pid):
            return {"status": "RUNNING", **state}
        logical_id = state.get("logical_consultation_id")
        if not logical_id:
            self._release_lock()
            return self._write_state("IDLE", result="NO_ACTIVE_REASONING")
        consultation = self.store.get(logical_id)
        authoritative = self._authoritative(consultation)
        if authoritative and authoritative.get("state") == "resolved" and authoritative.get("response"):
            self._release_lock()
            self._write_state("STOPPED", activation_id=state.get("activation_id"), logical_consultation_id=logical_id, result="AUTHORITATIVE_COMPLETE", completion_time=datetime.now(timezone.utc).isoformat(timespec="seconds"))
            return {"status": "COMPLETE", "logical_consultation_id": logical_id, "authoritative": True}
        if consultation.status == "steward_decision_required":
            self._release_lock()
            return self._write_state("ESCALATED", activation_id=state.get("activation_id"), logical_consultation_id=logical_id)
        self._release_lock()
        return self._write_state("ERROR", activation_id=state.get("activation_id"), logical_consultation_id=logical_id, reason="worker_exit_without_authoritative_completion", backoff_until=self.now() + self.backoff_seconds)

    def activate_until_settled(self, *, timeout_seconds: int = 660, poll_seconds: float = 1.0) -> dict[str, Any]:
        started = self.tick()
        if started.get("status") in {"EMPTY_QUEUE", "BACKOFF", "ALREADY_RUNNING", "WAITING_FOR_AUTHORITATIVE_COMPLETION"}:
            return started
        deadline = self.now() + timeout_seconds
        while self.now() < deadline:
            result = self.reconcile()
            if result.get("status") in {"COMPLETE", "ERROR", "ESCALATED"}:
                return result
            time.sleep(poll_seconds)
        return self._write_state("ERROR", reason="cme_authoritative_reconciliation_timeout", backoff_until=self.now() + self.backoff_seconds)
