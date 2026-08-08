"""Canonical transport retry for expired existing continuation 12.01.

This replaces only the expired Comms8 transport attempt.  It does not allocate
a consultation turn, wake a worker, or create an execution request; CME owns
the subsequent activation.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, r"A:\theestate\src")
from estate.core.consultation_store import ConsultationStore
from estate.core.grace_consultation_loop import GraceConsultationLoop

DATA=Path(r"A:\theestate-data")
def main():
    out=Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    store=ConsultationStore(DATA/"consultations"/"consultations.db")
    loop=GraceConsultationLoop(store=store)
    logical="12.01"; consultation=store.get(logical)
    original_id=consultation.ec8_request_id
    original=loop.read_request(original_id)
    if original.get("state")!="expired" or original.get("response"):
        raise RuntimeError("root12_transport_not_expired_without_response")
    attempts=store.transport_attempts(logical)
    if not attempts:
        store.record_transport_attempt(logical, original_id, workflow_id=consultation.workflow_id, status="expired", failure_class="request_expiry_elapsed", worker_id=(original.get("claim") or {}).get("worker_id"))
    elif attempts[-1].request_id==original_id and attempts[-1].status!="expired":
        store.mark_transport_attempt(logical, attempts[-1].attempt_number, status="expired", failure_class="request_expiry_elapsed")
    reservation=store.reserve_transport_retry(logical, original_id, failure_class="request_expiry_elapsed")
    replacement=loop._create_and_attach(store.get(logical), attempt_number=reservation.attempt_number, supersedes_request_id=original_id) if reservation.status=="creating" else store.get(logical)
    payload={"logical_consultation_id":logical,"original_request_id":original_id,"original_state":original,"reservation":reservation.__dict__,"replacement_request_id":replacement.ec8_request_id,"execution_request_count":len(store.execution_requests(logical)),"worker_woken":False}
    (out/"transport-recovery.json").write_text(json.dumps(payload,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,default=str))
if __name__=="__main__": main()
