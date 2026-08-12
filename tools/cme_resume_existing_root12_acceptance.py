"""Continue the already-created ordinary Grace root 12 through CME."""
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

DB = DATA / "consultations" / "consultations.db"
STATE = DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json"
LOCK = DATA / "chatgpt-mailbox-worker" / "cme-owner.lock"


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def run(run_dir: Path) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
    store = ConsultationStore(DB)
    loop = GraceConsultationLoop(store=store)
    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, read_request=loop.read_request)
    activations = []
    for _ in range(12):
        turns = store.latest_turns("12.00", 20)
        current = turns[-1]
        if current.status not in {"awaiting_reasoning", "open", "claimed", "reasoning"}:
            pending = [item for item in turns if item.status == "awaiting_reasoning"]
            if not pending:
                break
        started = owner.tick()
        item = {"started": started, "state": json.loads(STATE.read_text()) if STATE.exists() else None}
        if started.get("status") == "STARTED":
            deadline = time.monotonic() + 720
            while time.monotonic() < deadline:
                result = owner.reconcile()
                item["reconcile"] = result
                if result.get("status") in {"COMPLETE", "ERROR", "ESCALATED"}:
                    break
                time.sleep(2)
        elif started.get("status") == "ALREADY_RUNNING":
            # Reconcile an existing activation instead of spinning on its
            # lock.  A dead owner with a terminal authoritative request is
            # released by the governed stale-owner path.
            item["reconcile"] = owner.reconcile()
        activations.append(item)
        if item.get("reconcile", {}).get("status") == "ERROR":
            break
        time.sleep(1)
    turns = store.latest_turns("12.00", 20)
    links = []
    for turn in turns:
        links.extend(store.execution_requests(turn.logical_consultation_id))
    final = turns[-1]
    request = loop.read_request(final.ec8_request_id) if final.ec8_request_id else {}
    payload = {
        "logical_root": "12.00",
        "activations": activations,
        "turns": [{
            "logical_consultation_id": t.logical_consultation_id,
            "parent_logical_id": t.parent_logical_id,
            "status": t.status,
            "request_id": t.ec8_request_id,
            "response_id": t.response_id,
            "continuation_reason": t.continuation_reason,
            "current_evidence": t.current_evidence,
        } for t in turns],
        "execution_requests": [link.__dict__ for link in links],
        "execution_attempts": {link.execution_request_id: [a.__dict__ for a in store.execution_attempts(link.execution_request_id)] for link in links},
        "final_request": request,
        "cme_state": json.loads(STATE.read_text()) if STATE.exists() else None,
        "lock_exists": LOCK.exists(),
    }
    write(run_dir / "root12-resume.json", payload)
    ok = bool(links) and links[-1].status in {"completed", "dry_run_completed"} and bool((request.get("response") or {}))
    (run_dir / "exit-code").write_text(("0" if ok else "2") + "\n", encoding="utf-8")
    (run_dir / "completion.marker").write_text("ROOT12_CME_RESUME_COMPLETE\n", encoding="utf-8")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(run(Path(sys.argv[1])))
