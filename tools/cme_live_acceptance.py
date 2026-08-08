"""Detached live CME stale-owner recovery acceptance.

This process is owned by ``cme_owner_isolation.py``.  It is intentionally the
only process that waits for the canonical worker/browser lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(r"A:\theestate")
DATA = Path(r"A:\theestate-data")
sys.path.insert(0, str(ROOT / "src"))

from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop


STATE = DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json"
LOCK = DATA / "chatgpt-mailbox-worker" / "cme-owner.lock"
DB = DATA / "consultations" / "consultations.db"
REQUEST_ID = "ec8-198ea46afd3e4b93"
CONSULTATION_ID = "7.00"
MARKER = "CME_STALE_OWNER_RECOVERY_COMPLETE"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"unreadable": True, "path": str(path)}


def alive(pid) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def process_snapshot() -> list[dict]:
    command = "Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'python|powershell|node|chrome'} | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True, text=True, check=False)
    try:
        parsed = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        parsed = []
    return parsed if isinstance(parsed, list) else ([parsed] if parsed else [])


def lifecycle(request: dict, request_id: str = REQUEST_ID) -> dict:
    events = request.get("events") or []
    return {
        "request_id": request_id,
        "logical_consultation_id": CONSULTATION_ID,
        "state": request.get("state"),
        "worker_id": (request.get("claim") or {}).get("worker_id"),
        "lease_id": (request.get("claim") or {}).get("lease_id"),
        "response_id": (request.get("response") or {}).get("response_id"),
        "event_names": [item.get("event") for item in events if isinstance(item, dict)],
        "timestamps": [{key: item.get(key) for key in ("event", "at")} for item in events if isinstance(item, dict)],
    }


def recover_transport_without_waking_worker(store: ConsultationStore, loop: GraceConsultationLoop) -> dict:
    """Use the accepted transport-recovery record path, leaving ownership to CME."""
    consultation = store.get(CONSULTATION_ID)
    attempts = store.transport_attempts(CONSULTATION_ID)
    if not attempts:
        store.record_transport_attempt(CONSULTATION_ID, REQUEST_ID, workflow_id=consultation.workflow_id, status="expired", failure_class="wrong_worker_lease_expired", worker_id=None)
    elif attempts[-1].request_id == REQUEST_ID and attempts[-1].status != "expired":
        store.mark_transport_attempt(CONSULTATION_ID, attempts[-1].attempt_number, status="expired", failure_class="wrong_worker_lease_expired")
    reservation = store.reserve_transport_retry(CONSULTATION_ID, REQUEST_ID, failure_class="wrong_worker_lease_expired")
    if reservation.status == "creating":
        replacement = loop._create_and_attach(consultation, attempt_number=reservation.attempt_number, supersedes_request_id=REQUEST_ID)
    else:
        replacement = store.get(CONSULTATION_ID)
    return {
        "status": "QUEUED_FOR_CME",
        "logical_consultation_id": CONSULTATION_ID,
        "original_request_id": REQUEST_ID,
        "replacement_request_id": replacement.ec8_request_id,
        "transport_attempt": reservation.attempt_number,
        "worker_woken_by_recovery": False,
    }


def run(run_dir: Path) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
    store = ConsultationStore(DB)
    loop = GraceConsultationLoop(store=store)
    state_before = read_json(STATE)
    lock_before = read_json(LOCK)
    consultation = store.get(CONSULTATION_ID)
    authoritative_before = loop.read_request(REQUEST_ID)
    recorded_pids = [value for value in ((state_before or {}).get("pid"), (lock_before or {}).get("pid")) if value]
    preflight = {
        "recorded_at": now(),
        "consultation": {"logical_consultation_id": consultation.logical_consultation_id, "status": consultation.status, "ec8_request_id": consultation.ec8_request_id},
        "authoritative": lifecycle(authoritative_before, REQUEST_ID),
        "cme_state": state_before,
        "cme_lock": lock_before,
        "recorded_pids": recorded_pids,
        "recorded_pids_alive": {str(pid): alive(pid) for pid in recorded_pids},
        "current_worker_processes": process_snapshot(),
    }
    write(run_dir / "preflight.json", preflight)
    blockers = []
    if consultation is None or consultation.ec8_request_id != REQUEST_ID:
        blockers.append("CONSULTATION_REQUEST_MISMATCH")
    transport_recovery = None
    if authoritative_before.get("state") == "expired" and not authoritative_before.get("response") and not (authoritative_before.get("claim") or {}).get("lease_expires_at"):
        transport_recovery = recover_transport_without_waking_worker(store, loop)
        consultation = store.get(CONSULTATION_ID)
        active_request_id = consultation.ec8_request_id
        authoritative_before = loop.read_request(active_request_id)
        preflight["transport_recovery"] = {"required": True, "original_request_id": REQUEST_ID, "result": transport_recovery, "replacement_request_id": active_request_id}
        preflight["recovered_authoritative"] = lifecycle(authoritative_before, active_request_id)
        write(run_dir / "preflight.json", preflight)
    else:
        active_request_id = REQUEST_ID
    if authoritative_before.get("state") != "queued":
        blockers.append("AUTHORITATIVE_REQUEST_NOT_QUEUED:" + str(authoritative_before.get("state")))
    if any(alive(pid) for pid in recorded_pids):
        blockers.append("LIVE_RECORDED_CME_OWNER")
    claim = authoritative_before.get("claim") or {}
    if claim.get("lease_expires_at") and authoritative_before.get("state") not in {"resolved", "expired"}:
        blockers.append("ACTIVE_AUTHORITATIVE_LEASE")
    if consultation is not None and consultation.status not in {"awaiting_reasoning", "reasoning", "claimed"}:
        blockers.append("CONSULTATION_NOT_REASONING_ELIGIBLE:" + str(consultation.status))
    if blockers:
        write(run_dir / "reconciliation.json", {"status": "BLOCKED", "blockers": blockers, "transport_recovery": transport_recovery, "recorded_at": now()})
        write(run_dir / "final-cme-state.json", {"status": "BLOCKED", "cme_state": read_json(STATE), "lock": read_json(LOCK)})
        (run_dir / "exit-code").write_text("2\n", encoding="utf-8")
        (run_dir / "completion.marker").write_text(MARKER + "\n", encoding="utf-8")
        return 2

    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, read_request=loop.read_request)
    started = owner.tick()
    reconciled_state = read_json(STATE)
    write(run_dir / "reconciliation.json", {"status": "RECOVERED_AND_REACTIVATED", "started": started, "state_after_tick": reconciled_state, "transport_recovery": transport_recovery, "recorded_at": now()})
    write(run_dir / "activation.json", {"activation_id": started.get("activation_id"), "cme_pid": started.get("pid"), "canonical_worker_launched_by_cme": started.get("status") == "STARTED", "worker_command": "canonical wrapper --once", "request_id_selected_by_cme": True, "recorded_at": now()})

    deadline = time.monotonic() + 720
    current = authoritative_before
    while time.monotonic() < deadline:
        current = loop.read_request(active_request_id)
        if current.get("state") == "resolved" and current.get("response"):
            break
        time.sleep(2)
    write(run_dir / "lifecycle.json", lifecycle(current, active_request_id))
    if current.get("state") != "resolved" or not current.get("response"):
        write(run_dir / "final-cme-state.json", {"status": "AUTHORITATIVE_COMPLETION_NOT_PROVEN", "cme_state": read_json(STATE), "lock": read_json(LOCK)})
        (run_dir / "exit-code").write_text("3\n", encoding="utf-8")
        (run_dir / "completion.marker").write_text(MARKER + "\n", encoding="utf-8")
        return 3

    readback = loop.read_request(active_request_id)
    write(run_dir / "grace-readback.json", {"authoritative": readback.get("state") == "resolved" and bool(readback.get("response")), "request_id": active_request_id, "original_request_id": REQUEST_ID, "response_id": (readback.get("response") or {}).get("response_id"), "state": readback.get("state"), "result_metadata": {"response_present": bool(readback.get("response")), "event_count": len(readback.get("events") or [])}})
    terminal = owner.reconcile()
    duplicate = owner.tick()
    final_state = read_json(STATE)
    write(run_dir / "final-cme-state.json", {"terminal_reconcile": terminal, "duplicate_tick": duplicate, "cme_state": final_state, "lock_exists": LOCK.exists(), "prior_activation_preserved": bool((final_state or {}).get("activation_history"))})
    (run_dir / "exit-code").write_text("0\n", encoding="utf-8")
    (run_dir / "completion.marker").write_text(MARKER + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    run_path = Path(sys.argv[1])
    try:
        raise SystemExit(run(run_path))
    except SystemExit:
        raise
    except Exception as exc:
        # Preserve the phase boundary even when a live adapter fails before
        # the normal terminal path.  Do not copy response bodies or secrets.
        write(run_path / "reconciliation.json", {"status": "ERROR", "error_class": type(exc).__name__, "error": str(exc)[:300], "recorded_at": now()})
        write(run_path / "final-cme-state.json", {"status": "ERROR", "cme_state": read_json(STATE), "lock": read_json(LOCK)})
        (run_path / "exit-code").write_text("1\n", encoding="utf-8")
        (run_path / "completion.marker").write_text(MARKER + "\n", encoding="utf-8")
        raise
