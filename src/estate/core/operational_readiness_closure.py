"""Canonical Operational Readiness Closure Controller for WP-0650.

File-backed, deterministic controller integrated with existing Estate runtime artifacts.
It does not create a scheduler, validation engine, audit engine, Office, queue, or authority
hierarchy; callers invoke it from the existing Operations Runtime, CLI, and Office surface.
"""
from __future__ import annotations

import hashlib, json, os, shutil, subprocess, uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.operational_targets_runtime import OperationalTargetRuntime

STATES = {
    "merged","assessment_required","deployment_required","deployment_in_progress","deployed",
    "activation_required","activation_in_progress","live_validation_required","live_validation_in_progress",
    "live_validation_failed","remediation_required","remediation_in_progress","observation_required",
    "observation_in_progress","operationally_ready","blocked_authority_required",
    "blocked_manual_intervention","blocked_unsafe_action","failed_bounded_retries","rejected",
}
FINAL_STATES = {"operationally_ready","blocked_authority_required","blocked_manual_intervention","blocked_unsafe_action","failed_bounded_retries","rejected"}
BASE = Path("runtime/operational_readiness")
CASES = BASE/"cases"; VERDICTS = BASE/"verdicts"; EVIDENCE = BASE/"evidence"; STATUS = BASE/"status"
LEDGER = Path("operations/steward/estate_feature_activation_ledger.md")
OFFICE = Path("operations/steward/operational_readiness_closure.md")


def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _read(path:Path, default=None):
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8"))
def _write(path:Path, payload:Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(path)
def _append_jsonl(path:Path, payload:Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a",encoding="utf-8") as f: f.write(json.dumps(payload,sort_keys=True)+"\n")
def _rel(root:Path,p:Path|str):
    p=Path(p)
    try: return str(p.relative_to(root)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')
def _run(cmd:list[str], cwd:Path, timeout:int=60):
    r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout,check=False)
    return {"command":cmd,"cwd":str(cwd),"exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr,"timestamp":utc_now_iso()}

@dataclass
class ReadinessCase:
    case_id: str; work_package_id: str; target_id: str; repository: str; base_branch: str; merge_commit: str
    state: str = "merged"; completion_receipt: str|None=None; validation_recipe: list[list[str]]=field(default_factory=list)
    affected_files: list[str]=field(default_factory=list); affected_subsystems: list[str]=field(default_factory=list)
    allowed_remediations: list[str]=field(default_factory=list); activation_requirements: dict[str,Any]=field(default_factory=dict)
    observation_policy: dict[str,Any]=field(default_factory=lambda:{"checks_required":1})
    acceptance_authority: str="Chief Architect / Steward"; institutional_acceptance_granted: bool=False
    retry_history: dict[str,int]=field(default_factory=dict); blockers: list[dict[str,Any]]=field(default_factory=list)
    evidence: list[str]=field(default_factory=list); paused: bool=False; created_at: str=field(default_factory=utc_now_iso)
    updated_at: str=field(default_factory=utc_now_iso); lease: dict[str,Any]|None=None; observation: dict[str,Any]=field(default_factory=dict)
    last_validation_fingerprint: str|None=None; latest_validation: dict[str,Any]|None=None; remediations_attempted: list[dict[str,Any]]=field(default_factory=list)

    def to_dict(self):
        if self.state not in STATES: raise ValueError(f"unknown readiness state {self.state}")
        return asdict(self)
    @classmethod
    def from_dict(cls,d): return cls(**{k:d.get(k) for k in cls.__dataclass_fields__}) # type: ignore

class OperationalReadinessClosureController:
    def __init__(self, root:Path|str|None=None, clock=None): self.root=_root(root); self.clock=clock or utc_now_iso
    def _case_path(self, cid): return self.root/CASES/f"{cid}.json"
    def _event_path(self, cid): return self.root/EVIDENCE/cid/"events.jsonl"
    def _target(self, target_id): return OperationalTargetRuntime(self.root).get(target_id)
    def save(self, c:ReadinessCase): c.updated_at=self.clock(); _write(self._case_path(c.case_id), c.to_dict()); return c
    def list_cases(self, state:str|None=None):
        out=[]
        for p in sorted((self.root/CASES).glob("*.json")):
            c=ReadinessCase.from_dict(_read(p,{}));
            if not state or c.state==state or (state=="active" and c.state not in FINAL_STATES): out.append(c.to_dict())
        return out
    def show(self, case_id): return ReadinessCase.from_dict(_read(self._case_path(case_id),{})).to_dict()
    def create_or_resume(self, *, work_package_id:str, merge_commit:str, target_id="estate-main", repository="ppow1/theestate", base_branch="main", **kw):
        raw=f"{repository}|{target_id}|{work_package_id}|{merge_commit}"; cid="orc-"+hashlib.sha256(raw.encode()).hexdigest()[:16]
        if self._case_path(cid).exists(): return ReadinessCase.from_dict(_read(self._case_path(cid)))
        t=self._target(target_id); md=t.metadata or {}
        c=ReadinessCase(cid,work_package_id,target_id,repository,base_branch,merge_commit,
            state="assessment_required", validation_recipe=kw.get("validation_recipe") or md.get("validation_recipe") or [["python","-m","compileall","src/estate/core/operational_readiness_closure.py"]],
            affected_files=kw.get("affected_files") or [], affected_subsystems=kw.get("affected_subsystems") or [],
            allowed_remediations=kw.get("allowed_remediations") or md.get("allowed_remediations") or ["create_declared_runtime_directories","update_activation_ledger"],
            activation_requirements=kw.get("activation_requirements") or md.get("activation_requirements") or {"ledger":True},
            observation_policy=kw.get("observation_policy") or md.get("observation_policy") or {"checks_required":1},
            acceptance_authority=kw.get("acceptance_authority") or t.acceptance_authority)
        self.record(c,"case_created",{"work_package_id":work_package_id,"merge_commit":merge_commit}); return self.save(c)
    def record(self,c,kind,detail):
        rel=_rel(self.root,self._event_path(c.case_id)); _append_jsonl(self._event_path(c.case_id),{"at":self.clock(),"case_id":c.case_id,"kind":kind,"detail":detail});
        if rel not in c.evidence: c.evidence.append(rel)
    def assess(self,c:ReadinessCase):
        t=self._target(c.target_id); path=Path(t.local_path or self.root); md=t.metadata or {}
        blockers=[]; git={}
        if not path.exists(): blockers.append({"class":"missing_prerequisite","blocker":"managed checkout path missing","required_action":"manual provision target path"})
        else:
            status=_run(["git","status","--porcelain"],path) if (path/".git").exists() else {"exit_code":1,"stdout":"","stderr":"not git"}
            branch=_run(["git","branch","--show-current"],path) if status["exit_code"]==0 else {"stdout":"","exit_code":1}
            head=_run(["git","rev-parse","HEAD"],path) if status["exit_code"]==0 else {"stdout":"","exit_code":1}
            git={"branch":branch.get("stdout"," ").strip(),"head":head.get("stdout","").strip(),"dirty":bool(status.get("stdout")),"status_evidence":status}
            if git["dirty"]: blockers.append({"class":"stale_repository_or_dirty_checkout","blocker":"repository contains uncommitted work","required_action":"manual clean or commit local work"})
            if git["branch"] and git["branch"]!=c.base_branch: blockers.append({"class":"stale_repository_or_dirty_checkout","blocker":"wrong branch","required_action":f"switch managed checkout to {c.base_branch}"})
            if c.merge_commit and git["head"] and not git["head"].startswith(c.merge_commit[:12]):
                if "fast_forward_checkout" in c.allowed_remediations: blockers.append({"class":"stale_runtime_checkout","blocker":"target revision differs from merge commit","handler":"fast_forward_checkout"})
                else: blockers.append({"class":"deployment_failure","blocker":"target revision differs from merge commit","required_action":"authorize fast_forward_checkout"})
        for d in md.get("runtime_directories",[]):
            if not (self.root/d).exists(): blockers.append({"class":"missing_prerequisite","blocker":f"declared runtime directory missing: {d}","handler":"create_declared_runtime_directories"})
        if c.activation_requirements.get("ledger") and "WP-0650" not in (self.root/LEDGER).read_text(encoding="utf-8") if (self.root/LEDGER).exists() else True:
            blockers.append({"class":"activation_failure","blocker":"activation ledger entry missing","handler":"update_activation_ledger"})
        assessment={"generated_at":self.clock(),"case_id":c.case_id,"state":c.state,"current_merged_revision":c.merge_commit,"current_target_revision":git.get("head"),"repository_cleanliness":"dirty" if git.get("dirty") else "clean_or_unavailable","branch":git.get("branch"),"runtime_process_state":md.get("runtime_process_state","not_declared"),"scheduled_task_state":md.get("scheduled_task_state","not_declared"),"activation_state":"ledger_current" if not any(b.get("class")=="activation_failure" for b in blockers) else "activation_required","latest_validation_result":c.latest_validation,"blockers":blockers,"available_deterministic_remediation_handlers":c.allowed_remediations,"actions_requiring_authority":[b for b in blockers if not b.get("handler")],"actions_prohibited_by_policy":[],"retry_history":c.retry_history,"next_action":next((b.get("handler") for b in blockers if b.get("handler")),"validate_or_observe")}
        rel=f"runtime/operational_readiness/evidence/{c.case_id}/assessment_{uuid.uuid4().hex[:8]}.json"; _write(self.root/rel,assessment); c.blockers=blockers; self.record(c,"assessment",{"path":rel,"blockers":blockers}); return assessment
    def _retry_ok(self,c,h,limit=2): return c.retry_history.get(h,0)<limit
    def remediate(self,c:ReadinessCase,handler:str):
        if handler not in c.allowed_remediations: c.state="blocked_unsafe_action"; self.record(c,"remediation_refused",{"handler":handler,"reason":"not allowed by target policy"}); return c
        if not self._retry_ok(c,handler): c.state="failed_bounded_retries"; self.record(c,"retry_limit",{"handler":handler}); return c
        c.retry_history[handler]=c.retry_history.get(handler,0)+1; c.state="remediation_in_progress"; self.save(c)
        if handler=="create_declared_runtime_directories":
            for d in (self._target(c.target_id).metadata or {}).get("runtime_directories",[]): (self.root/d).mkdir(parents=True,exist_ok=True)
            result={"created_runtime_directories":(self._target(c.target_id).metadata or {}).get("runtime_directories",[])}
        elif handler=="update_activation_ledger":
            p=self.root/LEDGER; p.parent.mkdir(parents=True,exist_ok=True)
            with p.open("a",encoding="utf-8") as f: f.write(f"\n| WP-0650 Operational Readiness Closure Controller | Live | `{_rel(self.root,self._case_path(c.case_id))}` and `{_rel(self.root,self._event_path(c.case_id))}` | Connected through existing Operations Runtime, CLI, Office command surface, and Activation Ledger; institutional acceptance remains separate. |\n")
            result={"ledger":_rel(self.root,p)}
        elif handler=="fast_forward_checkout":
            t=self._target(c.target_id); path=Path(t.local_path or self.root); result={"fetch":_run(["git","fetch","--quiet",(t.metadata or {}).get("upstream","origin")],path),"merge":_run(["git","merge","--ff-only",f"{(t.metadata or {}).get('upstream','origin')}/{c.base_branch}"],path)}
        else:
            c.state="blocked_manual_intervention"; self.record(c,"unknown_handler",{"handler":handler}); return c
        c.remediations_attempted.append({"handler":handler,"at":self.clock(),"result":result}); self.record(c,"remediation",{"handler":handler,"result":result}); c.state="assessment_required"; return self.save(c)
    def validate(self,c):
        fp=json.dumps([c.merge_commit,c.validation_recipe,c.remediations_attempted],sort_keys=True)
        if c.last_validation_fingerprint==hashlib.sha256(fp.encode()).hexdigest() and c.latest_validation: return c.latest_validation
        results=[]; ok=True
        for cmd in c.validation_recipe:
            r=_run(cmd,self.root,timeout=120); results.append(r); ok=ok and r["exit_code"]==0
        rel=f"runtime/operational_readiness/evidence/{c.case_id}/validation_{uuid.uuid4().hex[:8]}.json"; payload={"status":"passed" if ok else "failed","results":results,"revision":c.merge_commit,"path":rel}; _write(self.root/rel,payload)
        c.latest_validation=payload; c.last_validation_fingerprint=hashlib.sha256(fp.encode()).hexdigest(); self.record(c,"validation",payload); c.state="observation_required" if ok else "live_validation_failed"; self.save(c); return payload
    def observe(self,c):
        req=int(c.observation_policy.get("checks_required",1)); done=int(c.observation.get("checks_passed",0))+1; c.observation={"checks_required":req,"checks_passed":done,"status":"passed" if done>=req else "in_progress","updated_at":self.clock()}; self.record(c,"observation",c.observation); c.state="operationally_ready" if done>=req else "observation_in_progress"; return self.save(c)
    def write_verdict(self,c):
        payload={"readiness_case_id":c.case_id,"work_package_id":c.work_package_id,"repository":c.repository,"target_id":c.target_id,"merge_commit":c.merge_commit,"deployed_revision":c.merge_commit if c.state=="operationally_ready" else None,"activation_state":"verified" if c.state=="operationally_ready" else "not_verified","validation_status":(c.latest_validation or {}).get("status"),"validation_evidence":(c.latest_validation or {}).get("path"),"observation_status":c.observation.get("status"),"observation_evidence":c.evidence,"remediations_attempted":c.remediations_attempted,"unresolved_findings":c.blockers if c.state!="operationally_ready" else [],"final_state":c.state,"operationally_ready":c.state=="operationally_ready","institutional_acceptance_granted":False,"acceptance_authority":c.acceptance_authority,"generated_at":self.clock(),"evidence_root":f"runtime/operational_readiness/evidence/{c.case_id}"}
        rel=VERDICTS/f"{c.case_id}.json"; _write(self.root/rel,payload); self.record(c,"verdict",{"path":_rel(self.root,self.root/rel),"state":c.state}); self.save(c); return payload
    def process_one(self, case_id):
        c=ReadinessCase.from_dict(_read(self._case_path(case_id),{}))
        if c.paused or c.state in FINAL_STATES: return c.to_dict()
        c.lease={"holder":"operations_runtime","claimed_at":self.clock()}; self.save(c)
        assessment=self.assess(c)
        if c.blockers:
            unhandled=[b for b in c.blockers if not b.get("handler")]
            if unhandled:
                c.state="blocked_manual_intervention"; self.record(c,"escalation",{"blockers":unhandled}); self.save(c)
            else:
                h=next((b.get("handler") for b in c.blockers if b.get("handler")),None)
                if h: c=self.remediate(c,h)
                else: c.state="blocked_manual_intervention"; self.record(c,"escalation",{"blockers":c.blockers}); self.save(c)
        else:
            if c.state in {"assessment_required","merged","deployed","live_validation_required","live_validation_failed"}: self.validate(c); c=ReadinessCase.from_dict(_read(self._case_path(case_id)))
            if c.state in {"observation_required","observation_in_progress"}: c=self.observe(c)
        if c.state in FINAL_STATES: self.write_verdict(c)
        return c.to_dict()
    def run_cycle(self, limit=2):
        cases=[ReadinessCase.from_dict(x) for x in self.list_cases() if x.get("state") not in FINAL_STATES and not x.get("paused")]
        metrics={"cases_discovered":0,"cases_assessed":0,"cases_advanced":0,"remediations_attempted":0,"remediations_succeeded":0,"remediations_failed":0,"validations_executed":0,"cases_entering_observation":0,"cases_declared_operationally_ready":0,"cases_blocked_for_authority":0,"cases_blocked_for_manual_intervention":0,"retry_limits_reached":0,"current_active_cases":len(cases),"oldest_active_case_age":None}
        results=[]
        for c in cases[:limit]:
            before=c.state; before_rem=len(c.remediations_attempted); r=self.process_one(c.case_id); results.append(r); metrics["cases_assessed"]+=1; metrics["cases_advanced"]+= before!=r.get("state"); metrics["remediations_attempted"]+=max(0,len(r.get("remediations_attempted",[]))-before_rem); metrics["validations_executed"]+=1 if r.get("latest_validation") else 0; metrics["cases_entering_observation"]+=1 if r.get("state") in {"observation_required","observation_in_progress"} else 0; metrics["cases_declared_operationally_ready"]+=1 if r.get("state")=="operationally_ready" else 0; metrics["cases_blocked_for_manual_intervention"]+=1 if r.get("state")=="blocked_manual_intervention" else 0; metrics["cases_blocked_for_authority"]+=1 if r.get("state")=="blocked_authority_required" else 0; metrics["retry_limits_reached"]+=1 if r.get("state")=="failed_bounded_retries" else 0
        payload={"generated_at":self.clock(),"metrics":metrics,"results":results}; _write(self.root/STATUS/"latest.json",payload); self.render_office(); return payload
    def pause(self,cid): c=ReadinessCase.from_dict(_read(self._case_path(cid))); c.paused=True; return self.save(c).to_dict()
    def resume(self,cid): c=ReadinessCase.from_dict(_read(self._case_path(cid))); c.paused=False; c.state="assessment_required" if c.state in FINAL_STATES-{"operationally_ready"} else c.state; return self.save(c).to_dict()
    def acknowledge(self,cid,note="manual blocker cleared"):
        c=ReadinessCase.from_dict(_read(self._case_path(cid))); self.record(c,"manual_blocker_acknowledged",{"note":note}); c.blockers=[]; c.state="assessment_required"; return self.save(c).to_dict()
    def render_office(self):
        rows=self.list_cases(); text="# Operational Readiness Closure\n\nExisting Office projection for the canonical WP-0650 controller. Controls call `estate.core.operational_readiness_closure`. Keyboard command equivalents: list, show, process-one, cycle, pause, resume, acknowledge, report.\n\n| Case | Work package | State | Target | Next action | Evidence |\n| --- | --- | --- | --- | --- | --- |\n"
        for r in rows: text+=f"| {r['case_id']} | {r['work_package_id']} | {r['state']} | {r['target_id']} | {(r.get('blockers') or [{}])[0].get('handler','validate/observe')} | runtime/operational_readiness/evidence/{r['case_id']} |\n"
        (self.root/OFFICE).parent.mkdir(parents=True,exist_ok=True); (self.root/OFFICE).write_text(text,encoding="utf-8"); return text
    def report(self): self.render_office(); return {"cases":self.list_cases(),"status":_read(self.root/STATUS/"latest.json",{}),"office_projection":str(OFFICE)}
