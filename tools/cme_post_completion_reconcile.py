"""Detached reconciliation after late authoritative Comms8 completion."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(r"A:\theestate")
DATA = Path(r"A:\theestate-data")
sys.path.insert(0, str(ROOT / "src"))

from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop, _normalize_reasoning_response

DB = DATA / "consultations" / "consultations.db"
STATE = DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json"
LOCK = DATA / "chatgpt-mailbox-worker" / "cme-owner.lock"
CONSULTATION = "7.00"
REQUEST = "ec8-4ce9c5dc3e8a4c74"


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def run(evidence: Path) -> int:
    store = ConsultationStore(DB)
    grace = GraceConsultationLoop(store=store)
    authoritative = grace.read_request(REQUEST)
    write(evidence / "late-authoritative-reconciliation.json", {
        "classification": "LATE_AUTHORITATIVE_COMPLETION",
        "request_id": REQUEST,
        "state": authoritative.get("state"),
        "events": authoritative.get("events", []),
        "response_id": (authoritative.get("response") or {}).get("response_id"),
        "receipt_path": (authoritative.get("response") or {}).get("receipt_path"),
        "response_present": bool(authoritative.get("response")),
    })
    if authoritative.get("state") != "resolved" or not authoritative.get("response"):
        raise RuntimeError("authoritative_completion_not_present")

    consultation = store.get(CONSULTATION)
    if consultation.response is None:
        response = _normalize_reasoning_response(authoritative["response"])
        store.append_response(CONSULTATION, response, response_id=authoritative["response"].get("response_id"), recommendation=response.get("content"))
    store.set_status(CONSULTATION, "resolved")
    for attempt in store.transport_attempts(CONSULTATION):
        if attempt.request_id == REQUEST and attempt.status != "resolved":
            store.mark_transport_attempt(CONSULTATION, attempt.attempt_number, status="resolved", worker_id="chatgpt")

    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, read_request=grace.read_request)
    terminal = owner.reconcile()
    readback = grace.read_request(REQUEST)
    write(evidence / "grace-readback.json", {
        "authoritative": readback.get("state") == "resolved" and bool(readback.get("response")),
        "request_id": REQUEST,
        "response_id": (readback.get("response") or {}).get("response_id"),
        "state": readback.get("state"),
        "response_present": bool(readback.get("response")),
    })
    duplicate = owner.tick()
    write(evidence / "final-cme-state.json", {
        "terminal_reconcile": terminal,
        "duplicate_tick": duplicate,
        "cme_state": json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None,
        "lock_exists": LOCK.exists(),
        "consultation_status": store.get(CONSULTATION).status,
        "response_id": store.get(CONSULTATION).response_id,
    })
    (evidence / "post-reconcile-exit-code").write_text("0\n", encoding="utf-8")
    (evidence / "post-reconcile-completion.marker").write_text("CME_LATE_COMPLETION_RECONCILIATION_COMPLETE\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(Path(sys.argv[1])))
