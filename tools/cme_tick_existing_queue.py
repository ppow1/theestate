"""Detached normal CME tick for the next eligible reasoning consultation."""

from __future__ import annotations

import json
import time
from pathlib import Path
import sys

ROOT = Path(r"A:\theestate")
DATA = Path(r"A:\theestate-data")
sys.path.insert(0, str(ROOT / "src"))

from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop


def main() -> int:
    run_dir = Path(sys.argv[1])
    run_dir.mkdir(parents=True, exist_ok=True)
    store = ConsultationStore(DATA / "consultations" / "consultations.db")
    loop = GraceConsultationLoop(store=store)
    owner = ChatGPTReasoningCMEOwner(
        store,
        state_path=DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json",
        lock_path=DATA / "chatgpt-mailbox-worker" / "cme-owner.lock",
        read_request=loop.read_request,
    )
    started = owner.tick()
    payload = {"started": started}
    if started.get("status") == "STARTED":
        deadline = time.monotonic() + 720
        while time.monotonic() < deadline:
            result = owner.reconcile()
            payload["reconciled"] = result
            if result.get("status") in {"COMPLETE", "ERROR", "ESCALATED"}:
                break
            time.sleep(2)
    consultation = store.get("11.00")
    request = loop.read_request(consultation.ec8_request_id)
    payload["final"] = {
        "consultation_status": consultation.status,
        "request_id": consultation.ec8_request_id,
        "request": request,
        "execution_request_count": len(store.execution_requests("11.00")),
        "cme_state": json.loads((DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json").read_text()),
        "lock_exists": (DATA / "chatgpt-mailbox-worker" / "cme-owner.lock").exists(),
    }
    (run_dir / "cme-tick.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    ok = request.get("state") == "resolved" and bool(request.get("response")) and payload["final"]["execution_request_count"] == 0
    (run_dir / "exit-code").write_text(("0" if ok else "3") + "\n", encoding="utf-8")
    (run_dir / "completion.marker").write_text("CME_EXISTING_QUEUE_TICK_COMPLETE\n", encoding="utf-8")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
