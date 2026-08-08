"""Detached truthful CME state reconciliation for a terminal existing turn."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(r"A:\theestate") / "src"))
from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop

DB = Path(r"A:\theestate-data\consultations\consultations.db")
STATE = Path(r"A:\theestate-data\chatgpt-mailbox-worker\cme-owner-state.json")
LOCK = Path(r"A:\theestate-data\chatgpt-mailbox-worker\cme-owner.lock")

def run(logical_id: str, evidence: Path) -> int:
    store = ConsultationStore(DB)
    loop = GraceConsultationLoop(store=store)
    consultation = store.get(logical_id)
    if not consultation or not consultation.ec8_request_id:
        raise RuntimeError("consultation_or_transport_missing")
    authoritative = loop.read_request(consultation.ec8_request_id)
    if authoritative.get("state") != "resolved" or not authoritative.get("response"):
        raise RuntimeError("authoritative_completion_missing")
    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, read_request=loop.read_request)
    terminal = owner.reconcile()
    duplicate = owner.tick()
    payload = {"logical_consultation_id": logical_id, "request_id": consultation.ec8_request_id, "authoritative": True, "terminal_reconcile": terminal, "duplicate_tick": duplicate, "cme_state": json.loads(STATE.read_text()) if STATE.exists() else None, "lock_exists": LOCK.exists(), "consultation_status": store.get(logical_id).status}
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "cme-terminal-reconciliation.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], Path(sys.argv[2])))
