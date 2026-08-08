"""Detached continuation of consultation 8.00 through evidence and execution."""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(r"A:\theestate"); DATA=Path(r"A:\theestate-data"); sys.path.insert(0,str(ROOT/"src"))
from estate.core.autonomous_reason_execute_loop import AutonomousReasonExecuteLoop, classify_reasoning_response
from estate.core.chatgpt_execution_runtime import build_live_execution_router
from estate.core.consultation_execution import ConsultationExecutionRouter
from estate.core.consultation_store import ConsultationStore
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.grace_consultation_loop import GraceConsultationLoop

DB=DATA/"consultations"/"consultations.db"; STATE=DATA/"chatgpt-mailbox-worker"/"cme-owner-state.json"; LOCK=DATA/"chatgpt-mailbox-worker"/"cme-owner.lock"
ROOT_ID="8.00"

def now(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
def write(p,v): p.write_text(json.dumps(v,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
def read(p):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return None

def launcher(command, **kwargs):
    env=dict(kwargs.get("env") or os.environ); env["ESTATE_STRUCTURED_EXECUTION_HANDOFF"]="0"
    return subprocess.Popen(command,cwd=kwargs.get("cwd"),env=env,stdout=kwargs.get("stdout"),stderr=kwargs.get("stderr"),text=True)

def wait_resolved(loop, rid, timeout=720):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            x=loop.read_request(rid)
            if x.get("state")=="resolved" and x.get("response"): return x
        except Exception: pass
        time.sleep(2)
    raise TimeoutError("authoritative_timeout:"+rid)

def wait_dead(timeout=45):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        x=read(STATE); pid=(x or {}).get("pid")
        if not pid: return x
        try: os.kill(int(pid),0)
        except (OSError,ValueError): return x
        time.sleep(1)
    return read(STATE)

def wake(owner, loop, consultation, evidence, label):
    started=owner.tick(); write(evidence/f"cme-{label}.json",{"tick":started,"state":read(STATE),"logical_consultation_id":consultation.logical_consultation_id,"request_id":consultation.ec8_request_id,"recorded_at":now()})
    authoritative=wait_resolved(loop,consultation.ec8_request_id); wait_dead()
    record=store.get(consultation.logical_consultation_id); response=record.response or {}; decision=classify_reasoning_response(response)
    write(evidence/f"reasoning-{label}.json",{"logical_consultation_id":consultation.logical_consultation_id,"request_id":consultation.ec8_request_id,"response_id":record.response_id,"classification":decision.classification,"structured_decision":response.get("structured_decision"),"events":authoritative.get("events",[])})
    return record, decision, authoritative

def run(evidence:Path):
    global store
    evidence.mkdir(parents=True,exist_ok=True); store=ConsultationStore(DB); loop=GraceConsultationLoop(store=store)
    root=store.get(ROOT_ID)
    if not root or not root.response: raise RuntimeError("existing_root_response_missing")
    decision=classify_reasoning_response(root.response)
    if decision.classification!="MORE_REASONING_REQUIRED" or not decision.evidence_request: raise RuntimeError("existing_decision_not_bounded_evidence_request")
    req=decision.evidence_request; correlation=req.get("consultation_correlation") or {}
    if correlation.get("consultation_id")!=ROOT_ID: raise RuntimeError("evidence_correlation_mismatch")
    # Do not count the current MORE_REASONING_REQUIRED envelope itself as
    # evidence.  Local-history-first considers only prior durable evidence and
    # validation fields.
    history="\n".join(str({"evidence":t.validation_evidence,"current":t.current_evidence}) for t in store.latest_turns(ROOT_ID,5) if t.validation_evidence or t.current_evidence)
    local_available=bool(req.get("target") and req.get("target") in history and all(str(x) in history for x in req.get("evidence_requirements",[])))
    write(evidence/"evidence-request-validation.json",{"classification":decision.classification,"objective":req.get("objective"),"required_capability":req.get("required_capability"),"allowed_scope":req.get("allowed_scope"),"prohibited_scope":req.get("prohibited_scope"),"evidence_requirements":req.get("evidence_requirements"),"correlation":correlation,"local_history_available":local_available})
    if local_available: raise RuntimeError("LOCAL_EVIDENCE_PATH_REQUIRES_EXISTING_ACCEPTANCE_NOT_PRESENT")

    router=build_live_execution_router(store,runtime_root=ROOT)
    canonical_capability="repository_read"
    all_execution_requests=store.execution_requests(ROOT_ID)
    existing_continuation_ids={t.current_evidence.get("execution_request_id") for t in store.latest_turns(ROOT_ID,10) if t.logical_consultation_id != ROOT_ID and t.current_evidence}
    request_records={x.execution_request_id: read(ROOT/"runtime"/"execution_adapters"/"requests"/(x.execution_request_id+".json")) or {} for x in all_execution_requests}
    prior_evidence_requests=[x for x in all_execution_requests if request_records[x.execution_request_id].get("metadata",{}).get("purpose")=="EVIDENCE_ACQUISITION"]
    continuation_evidence=next((x for x in prior_evidence_requests if x.execution_request_id in existing_continuation_ids),None)
    completed_prior=continuation_evidence or next((x for x in prior_evidence_requests if x.status in {"completed","dry_run_completed"}),None)
    if len(prior_evidence_requests)>=2 and not completed_prior:
        raise RuntimeError("evidence_acquisition_retry_limit_exhausted")
    if completed_prior:
        execution_id=completed_prior.execution_request_id
        execution=type("ExistingRequest", (), {"adapter_request_id": execution_id})()
        result_json=completed_prior.result_json or {}
        result=type("ExistingResult", (), {"provider_id": completed_prior.provider_id, "status": completed_prior.status, "validation_status": completed_prior.validation_status, "summary": str(result_json.get("summary") or "")})()
        link=completed_prior
    else:
        retry_number=len(prior_evidence_requests)+1
        execution=router.create_request(ROOT_ID,required_capability=canonical_capability,dispatch_id=f"dispatch-8-00-evidence-{retry_number}",prompt_source="docs/prompts/cme_consultation_8_pytest_evidence_20260807.md",classification="Estate Internal",read_scope_paths=["docs/prompts","pytest.ini","tests"],write_scope_paths=[],blocked_scope_paths=["production","runtime/live"],expected_outputs=req["evidence_requirements"],validation_required=True,decision_reference="consultation-bounded-evidence-request",metadata={"purpose":"EVIDENCE_ACQUISITION","consultation_id":ROOT_ID,"requested_capability":req.get("required_capability"),"scope":"read-only","retry_of":prior_evidence_requests[-1].execution_request_id if prior_evidence_requests else None})
        result=router.execute(execution.adapter_request_id); link=store.execution_request(execution.adapter_request_id)
    write(evidence/"evidence-acquisition-1.json",{"execution_request_id":execution.adapter_request_id,"requested_capability":req.get("required_capability"),"selected_capability":canonical_capability,"provider_id":result.provider_id,"status":result.status,"validation_status":result.validation_status,"summary":result.summary[:4000],"result_reference":link.result_reference,"attempts":[a.__dict__ for a in store.execution_attempts(execution.adapter_request_id)]})
    if result.status not in {"completed","dry_run_completed"}: raise RuntimeError("evidence_provider_failed:"+result.status)
    store.append_validation(ROOT_ID,observed_result="EVIDENCE_ACQUIRED",evidence={"execution_request_id":execution.adapter_request_id,"result_reference":link.result_reference,"provider_id":result.provider_id,"summary":result.summary[:4000]},status="continuation_required")
    existing_continuations=[t for t in store.latest_turns(ROOT_ID,10) if t.logical_consultation_id != ROOT_ID and t.current_evidence and t.current_evidence.get("execution_request_id")==execution.adapter_request_id]
    if existing_continuations:
        continuation=existing_continuations[-1]
    else:
        continuation=router.continue_from_execution(ROOT_ID,execution.adapter_request_id,question="Reevaluate the pytest-root assumption using the acquired effective configuration evidence.",continuation_reason="bounded_pre_execution_evidence_acquired")
        continuation=loop._create_and_attach(continuation); store.set_status(continuation.logical_consultation_id,"awaiting_reasoning")
        write(evidence/"continuation-1.json",{"logical_consultation_id":continuation.logical_consultation_id,"parent_logical_id":continuation.parent_logical_id,"request_id":continuation.ec8_request_id,"reason":continuation.continuation_reason})

    owner=ChatGPTReasoningCMEOwner(store,state_path=STATE,lock_path=LOCK,launcher=launcher,read_request=loop.read_request)
    authoritative=loop.read_request(continuation.ec8_request_id)
    if authoritative.get("state")=="resolved" and authoritative.get("response") and not store.get(continuation.logical_consultation_id).response:
        response=authoritative["response"]
        stored_response={"content":response.get("content"),"structured_decision":response.get("structured_decision")} if isinstance(response,dict) else {"content":str(response)}
        store.append_response(continuation.logical_consultation_id,stored_response,response_id=response.get("response_id") if isinstance(response,dict) else None,recommendation=stored_response.get("content"))
        store.set_status(continuation.logical_consultation_id,"response_received")
    record, second, auth=wake(owner,loop,continuation,evidence,"second") if not store.get(continuation.logical_consultation_id).response else (store.get(continuation.logical_consultation_id), classify_reasoning_response(store.get(continuation.logical_consultation_id).response), authoritative)
    if not (evidence/"reasoning-second.json").exists():
        write(evidence/"reasoning-second.json",{"logical_consultation_id":continuation.logical_consultation_id,"request_id":continuation.ec8_request_id,"response_id":record.response_id,"classification":second.classification,"structured_decision":(record.response or {}).get("structured_decision"),"events":auth.get("events",[])})
    current=continuation; turns=2; execution_ids=[execution.adapter_request_id]
    if second.classification=="EXECUTION_RECOMMENDED":
        handoff=AutonomousReasonExecuteLoop(store,router).accept_reasoning(current.logical_consultation_id,record.response)
        eid=handoff["execution_request_id"]; execution_ids.append(eid); result=router.execute(eid); link=store.execution_request(eid)
        write(evidence/"execution-1.json",{"execution_request_id":eid,"provider_id":result.provider_id,"status":result.status,"validation_status":result.validation_status,"summary":result.summary[:4000],"result_reference":link.result_reference,"attempts":[a.__dict__ for a in store.execution_attempts(eid)]})
        if result.status not in {"completed","dry_run_completed"}: raise RuntimeError("execution_provider_failed:"+result.status)
        store.append_validation(current.logical_consultation_id,observed_result="EXECUTION_EVIDENCE_RETURNED",evidence={"execution_request_id":eid,"result_reference":link.result_reference,"provider_id":result.provider_id,"summary":result.summary[:4000]},status="continuation_required")
        next_turn=router.continue_from_execution(current.logical_consultation_id,eid,question="Reevaluate the recommendation using the actual execution evidence and state the bounded outcome.",continuation_reason="execution_evidence_requires_reevaluation")
        next_turn=loop._create_and_attach(next_turn); store.set_status(next_turn.logical_consultation_id,"awaiting_reasoning")
        write(evidence/"continuation-2.json",{"logical_consultation_id":next_turn.logical_consultation_id,"parent_logical_id":next_turn.parent_logical_id,"request_id":next_turn.ec8_request_id,"reason":next_turn.continuation_reason})
        record, final_decision, auth=wake(owner,loop,next_turn,evidence,"final"); current=next_turn; turns=3
    elif second.classification not in {"INFORMATION_ONLY","MORE_REASONING_REQUIRED","STEWARD_DECISION_REQUIRED"}:
        raise RuntimeError("unexpected_second_classification:"+second.classification)

    owner.reconcile(); duplicate=owner.tick(); final=read(STATE)
    write(evidence/"final-cme-state.json",{"cme_state":final,"lock_exists":LOCK.exists(),"duplicate_tick":duplicate,"root_status":store.get(ROOT_ID).status,"turns":turns,"execution_request_ids":execution_ids,"final_classification":(final_decision.classification if 'final_decision' in locals() else second.classification)})
    (evidence/"exit-code").write_text("0\n",encoding="utf-8"); (evidence/"completion.marker").write_text("CME_8_EVIDENCE_CONTINUATION_COMPLETE\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    p=Path(sys.argv[1])
    try: raise SystemExit(run(p))
    except SystemExit: raise
    except Exception as exc:
        write(p/"failure.json",{"error_class":type(exc).__name__,"error":str(exc)[:500],"cme_state":read(STATE),"lock":read(LOCK),"recorded_at":now()}); (p/"exit-code").write_text("1\n",encoding="utf-8"); (p/"completion.marker").write_text("CME_8_EVIDENCE_CONTINUATION_COMPLETE\n",encoding="utf-8"); raise
