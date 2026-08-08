"""Detached live proof of one CME-owned reason/execute/observe/reason loop."""
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

from estate.core.autonomous_reason_execute_loop import AutonomousReasonExecuteLoop, classify_reasoning_response
from estate.core.consultation_execution import ConsultationExecutionRouter
from estate.core.consultation_projection import ConsultationProjection
from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop, _normalize_reasoning_response

DB = DATA / "consultations" / "consultations.db"
STATE = DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json"
LOCK = DATA / "chatgpt-mailbox-worker" / "cme-owner.lock"
WORKER_WRAPPER = ROOT / "tools" / "start_chatgpt_mailbox_worker_canonical.ps1"
MARKER = "FULL_CME_AUTONOMOUS_REASON_EXECUTE_OBSERVE_REASON_COMPLETE"
INTENT = (
    "Determine whether the bounded Estate fixture inspection assumption is correct: "
    "the repository's pytest configuration should expose the tests directory as the test root. "
    "If direct inspection is needed, use the Estate's normal read-only execution path and do not modify production. "
    "Return a structured recommendation and preserve enough evidence for a second reasoning pass."
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def read(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"unreadable": True}


def browser_readiness() -> dict:
    result = subprocess.run(["node", str(ROOT / "tools" / "chatgpt_mailbox_worker_browser.cjs"), "--readiness-only"], capture_output=True, text=True, timeout=90, check=False)
    lines = result.stdout.strip().splitlines()
    payload = json.loads(lines[-1]) if lines else {"marker": "READINESS_FAILED", "reason": "no_readiness_output"}
    if result.returncode != 0 or payload.get("marker") != "READINESS_READY":
        raise RuntimeError("browser_readiness_failed:" + str(payload.get("reason") or payload.get("marker")))
    readiness = payload.get("readiness") or {}
    title = str((payload.get("trace") or [{}])[0].get("title") or "")
    if any(token in title.lower() for token in ("processing limitation", "rate limit", "usage limit", "authentication", "unavailable", "challenge", "error")):
        raise RuntimeError("CHATGPT_PROCESSING_CAPACITY_UNAVAILABLE")
    return {"marker": payload.get("marker"), "readiness": readiness, "trace": payload.get("trace")}


def make_launcher():
    """CME launcher: canonical worker, with handoff deferred to this loop."""
    def launch(command, **kwargs):
        env = dict(kwargs.get("env") or os.environ)
        # The worker still owns generic Comms8 lifecycle.  The structured
        # decision is persisted first; this acceptance then uses the existing
        # neutral execution/continuation seam before the next CME wake.
        env["ESTATE_STRUCTURED_EXECUTION_HANDOFF"] = "0"
        return subprocess.Popen(command, cwd=kwargs.get("cwd"), env=env, stdout=kwargs.get("stdout"), stderr=kwargs.get("stderr"), text=True)
    return launch


def wait_authoritative(loop: GraceConsultationLoop, request_id: str, timeout: float = 720) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = loop.read_request(request_id)
        if record.get("state") == "resolved" and record.get("response"):
            return record
        time.sleep(2)
    raise TimeoutError("authoritative_request_timeout:" + request_id)


def wait_child_dead(state_path: Path, timeout: float = 30) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = read(state_path) or {}
        pid = state.get("pid")
        if not pid:
            return state
        try:
            os.kill(int(pid), 0)
        except (OSError, ValueError):
            return state
        time.sleep(1)
    return read(state_path) or {}


def create_root(store: ConsultationStore, loop: GraceConsultationLoop):
    consultation = loop._allocate(INTENT, parent=None, session_id="cme-full-loop-20260807", ptm_project_id=None, ptm_work_item_id=None, tags=("cme-full-loop", "read-only-acceptance"))
    return loop._create_and_attach(consultation)


def run(evidence: Path) -> int:
    evidence.mkdir(parents=True, exist_ok=True)
    store = ConsultationStore(DB)
    loop = GraceConsultationLoop(store=store)
    write(evidence / "preflight.json", {"recorded_at": now(), "cme_state": read(STATE), "lock": read(LOCK), "browser": browser_readiness(), "existing_full_loop_candidates": [{"id": x.logical_consultation_id, "status": x.status} for x in store.search(tag="cme-full-loop")]})
    if (read(LOCK) or {}).get("pid"):
        raise RuntimeError("ACTIVE_CME_OWNER_BEFORE_ROOT")

    root = create_root(store, loop)
    write(evidence / "consultation-root.json", {"logical_consultation_id": root.logical_consultation_id, "root_logical_id": root.root_logical_id, "ec8_request_id": root.ec8_request_id, "workflow_id": root.workflow_id, "intent": INTENT})
    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, launcher=make_launcher(), read_request=loop.read_request)

    first_started = owner.tick()
    write(evidence / "cme-activation-first.json", {"tick": first_started, "state": read(STATE), "recorded_at": now()})
    first_authoritative = wait_authoritative(loop, root.ec8_request_id)
    wait_child_dead(STATE)
    first_record = store.get(root.logical_consultation_id)
    first_response = first_record.response or {}
    first_decision = classify_reasoning_response(first_response)
    write(evidence / "first-reasoning.json", {"request_id": root.ec8_request_id, "logical_consultation_id": root.logical_consultation_id, "authoritative": True, "response_id": first_record.response_id, "classification": first_decision.classification, "structured_decision": first_response.get("structured_decision"), "comms8_events": first_authoritative.get("events", [])})
    if first_decision.classification != "EXECUTION_RECOMMENDED":
        raise RuntimeError("FIRST_REASONING_NOT_EXECUTION_RECOMMENDED:" + first_decision.classification)

    owner.reconcile()
    router = ConsultationExecutionRouter(
        store,
        __import__("estate.core.chatgpt_execution_runtime", fromlist=["build_live_execution_router"]).build_live_execution_router(store).bindings,
        runtime_root=ROOT,
    )
    reason_loop = AutonomousReasonExecuteLoop(store, router)
    accepted = reason_loop.accept_reasoning(root.logical_consultation_id, first_response)
    write(evidence / "execution-request.json", {"handoff": accepted, "recorded_at": now()})
    if accepted.get("status") != "execution_requested":
        raise RuntimeError("EXECUTION_HANDOFF_NOT_CREATED")
    execution_id = accepted["execution_request_id"]
    result = router.execute(execution_id)
    link = store.execution_request(execution_id)
    attempts = store.execution_attempts(execution_id)
    write(evidence / "execution-attempt.json", {"execution_request_id": execution_id, "provider_id": result.provider_id, "status": result.status, "validation_status": result.validation_status, "summary": result.summary[:4000], "result_reference": link.result_reference, "attempts": [a.__dict__ for a in attempts]})
    if result.status not in {"completed", "dry_run_completed"}:
        raise RuntimeError("EXECUTION_PROVIDER_FAILED:" + result.status)

    store.append_validation(root.logical_consultation_id, observed_result="EVIDENCE_RETURNED", evidence={"execution_request_id": execution_id, "result_reference": link.result_reference, "provider_id": result.provider_id, "validation_status": result.validation_status}, status="continuation_required")
    continuation = router.continue_from_execution(root.logical_consultation_id, execution_id, question="Reevaluate the original assumption using the actual bounded execution evidence and state the current outcome.", continuation_reason="execution_evidence_requires_second_reasoning")
    continuation = loop._create_and_attach(continuation)
    store.set_status(continuation.logical_consultation_id, "awaiting_reasoning")
    write(evidence / "continuation.json", {"logical_consultation_id": continuation.logical_consultation_id, "parent_logical_id": continuation.parent_logical_id, "ec8_request_id": continuation.ec8_request_id, "reason": continuation.continuation_reason})

    second_started = owner.tick()
    write(evidence / "cme-activation-second.json", {"tick": second_started, "state": read(STATE), "recorded_at": now()})
    second_authoritative = wait_authoritative(loop, continuation.ec8_request_id)
    wait_child_dead(STATE)
    second_record = store.get(continuation.logical_consultation_id)
    second_response = second_record.response or {}
    second_decision = classify_reasoning_response(second_response)
    write(evidence / "second-reasoning.json", {"request_id": continuation.ec8_request_id, "logical_consultation_id": continuation.logical_consultation_id, "authoritative": True, "response_id": second_record.response_id, "classification": second_decision.classification, "structured_decision": second_response.get("structured_decision"), "comms8_events": second_authoritative.get("events", [])})

    owner.reconcile()
    duplicate = owner.tick()
    projection = ConsultationProjection(store, directory=evidence / "projection").project(root.root_logical_id)
    write(evidence / "grace-readback.json", {"authoritative": True, "root_request_id": root.ec8_request_id, "continuation_request_id": continuation.ec8_request_id, "first_response_id": first_record.response_id, "second_response_id": second_record.response_id, "second_classification": second_decision.classification})
    write(evidence / "final-cme-state.json", {"cme_state": read(STATE), "lock_exists": LOCK.exists(), "duplicate_tick": duplicate, "projection": projection, "root_status": store.get(root.logical_consultation_id).status, "continuation_status": store.get(continuation.logical_consultation_id).status})
    (evidence / "exit-code").write_text("0\n", encoding="utf-8")
    (evidence / "completion.marker").write_text(MARKER + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    path = Path(sys.argv[1])
    try:
        raise SystemExit(run(path))
    except SystemExit:
        raise
    except Exception as exc:
        write(path / "failure.json", {"error_class": type(exc).__name__, "error": str(exc)[:500], "cme_state": read(STATE), "lock": read(LOCK), "recorded_at": now()})
        (path / "exit-code").write_text("1\n", encoding="utf-8")
        (path / "completion.marker").write_text(MARKER + "\n", encoding="utf-8")
        raise
