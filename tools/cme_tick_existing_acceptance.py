"""CME-owned tick over existing durable work; creates no roots or requests."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop

DATA = Path(r'A:\theestate-data')
ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    store = ConsultationStore(DATA / 'consultations' / 'consultations.db')
    loop = GraceConsultationLoop(store=store)
    owner = ChatGPTReasoningCMEOwner(
        store,
        state_path=DATA / 'chatgpt-mailbox-worker' / 'cme-owner-state.json',
        lock_path=DATA / 'chatgpt-mailbox-worker' / 'cme-owner.lock',
        wrapper=ROOT / 'tools' / 'start_chatgpt_mailbox_worker_acceptance.ps1',
        read_request=loop.read_request,
    )
    result = owner.activate_until_settled(timeout_seconds=660, poll_seconds=2.0)
    print(json.dumps(result, indent=2, default=str))

if __name__ == '__main__':
    main()
