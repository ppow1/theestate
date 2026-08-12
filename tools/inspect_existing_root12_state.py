"""Read-only durable/live inspection of the preserved root 12 lane."""
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
    turns=store.latest_turns("12.00", 20)
    payload={"turns":[],"requests":[],"executions":[],"cme":None}
    for t in turns:
        payload["turns"].append({"logical":t.logical_consultation_id,"parent":t.parent_logical_id,"status":t.status,"request_id":t.ec8_request_id,"response_id":t.response_id,"reason":t.continuation_reason})
        if t.ec8_request_id:
            try: payload["requests"].append({"logical":t.logical_consultation_id,"request_id":t.ec8_request_id,"record":loop.read_request(t.ec8_request_id)})
            except Exception as e: payload["requests"].append({"logical":t.logical_consultation_id,"request_id":t.ec8_request_id,"error":f"{type(e).__name__}: {e}"})
        payload["executions"].extend([x.__dict__ for x in store.execution_requests(t.logical_consultation_id)])
    for p in [DATA/"chatgpt-mailbox-worker"/"cme-owner-state.json",DATA/"chatgpt-mailbox-worker"/"worker-state.json"]:
        payload["cme" if "cme-owner" in p.name else "worker"]=json.loads(p.read_text()) if p.exists() else None
    (out/"root12-state.json").write_text(json.dumps(payload,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,default=str))
if __name__=="__main__": main()
