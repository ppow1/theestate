"""Normal CME-owned tick for the preserved 12.01 continuation."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
sys.path.insert(0, r"A:\theestate\src")
from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop
DATA=Path(r"A:\theestate-data")
def main():
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
    store=ConsultationStore(DATA/"consultations"/"consultations.db"); loop=GraceConsultationLoop(store=store)
    owner=ChatGPTReasoningCMEOwner(store,state_path=DATA/"chatgpt-mailbox-worker"/"cme-owner-state.json",lock_path=DATA/"chatgpt-mailbox-worker"/"cme-owner.lock",read_request=loop.read_request)
    started=owner.tick(); payload={"started":started}
    if started.get("status")=="STARTED":
        deadline=time.monotonic()+720
        while time.monotonic()<deadline:
            result=owner.reconcile(); payload["reconciled"]=result
            if result.get("status") in {"COMPLETE","ERROR","ESCALATED"}: break
            time.sleep(2)
    t=store.get("12.01"); request=loop.read_request(t.ec8_request_id)
    payload["final"]={"status":t.status,"request_id":t.ec8_request_id,"request":request,"turns":[{"logical":x.logical_consultation_id,"status":x.status,"response_id":x.response_id} for x in store.latest_turns("12.00",20)],"execution_total":sum(len(store.execution_requests(x.logical_consultation_id)) for x in store.latest_turns("12.00",20)),"cme":json.loads((DATA/"chatgpt-mailbox-worker"/"cme-owner-state.json").read_text())}
    (out/"root12-cme-tick.json").write_text(json.dumps(payload,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,default=str))
if __name__=="__main__": main()
