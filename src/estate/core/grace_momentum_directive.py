"""Grace-owned continuation directives for CME-managed operational momentum."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
from uuid import uuid4
from estate.core.execution_provider_adapter import utc_now
from estate.core.paths import ESTATE_ROOT

DIRECTIVES = Path("runtime/operations/grace/momentum_directives")
EVENTS = Path("runtime/operations/grace/momentum_events.jsonl")
ACTIVE = {"active"}; TERMINAL={"stopped","completed","revoked","expired","superseded"}
TRANSITIONS={"proposed":{"active","revoked"},"active":{"paused","stopping","stopped","completed","revoked","expired","escalation_required","superseded"},"paused":{"active","stopped","revoked","expired","superseded"},"stopping":{"stopped","escalation_required"},"escalation_required":{"paused","stopped","revoked"}}
def _root(root=None): return Path(root) if root is not None else ESTATE_ROOT
def _p(root,id): return _root(root)/DIRECTIVES/f"{id}.json"
def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def _event(root,kind,payload):
 p=_root(root)/EVENTS;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("a",encoding="utf-8") as h:h.write(json.dumps({"event_id":f"gmd-event-{uuid4().hex[:12]}","event_kind":kind,"occurred_at":utc_now(),"payload":payload},sort_keys=True)+"\n")
def load(directive_id,root=None):
 p=_p(root,directive_id)
 if not p.exists(): raise ValueError("momentum directive not found")
 return json.loads(p.read_text(encoding="utf-8"))
def create(objective_id, grace_action_id, *, authority_reference, allowed_transition_classes=("engineering_progression",), maximum_retries=0, expires_at=None, idempotency_key=None, root=None):
 key=idempotency_key or f"{objective_id}:{grace_action_id}:momentum"
 d=_root(root)/DIRECTIVES
 for p in d.glob("*.json") if d.exists() else ():
  x=json.loads(p.read_text(encoding="utf-8"))
  if x.get("idempotency_key")==key:return x
 now=utc_now(); x={"directive_id":f"gmd-{uuid4().hex[:12]}","grace_objective_id":objective_id,"grace_action_id":grace_action_id,"operational_owner":"Grace","status":"active","continuation_mode":"event_driven","allowed_automatic_transition_classes":list(allowed_transition_classes),"prohibited_transition_classes":["provider_selection","technical_validation","acceptance"],"maximum_retries":maximum_retries,"expires_at":expires_at,"locality":"local_only","privacy_egress":"no_external_egress","spend":"no_spend","escalation_conditions":["authority_missing","conflicting_evidence"],"pause_conditions":[],"stop_conditions":[],"grace_authority_reference":authority_reference,"created_at":now,"activated_at":now,"updated_at":now,"terminal_at":None,"idempotency_key":key,"version":1,"supersedes_directive_id":None,"audit_correlation_id":f"gmd-audit-{objective_id}"}
 x["content_hash"]=_hash(x);_write(_p(root,x["directive_id"]),x);_event(root,"grace_momentum_directive_activated",x);return x
def transition(directive_id,status,*,root=None,reason=None):
 x=load(directive_id,root); cur=x["status"]
 if status not in TRANSITIONS.get(cur,set()): raise ValueError(f"invalid directive transition {cur} -> {status}")
 x["status"]=status;x["updated_at"]=utc_now();x["terminal_at"]=x["updated_at"] if status in TERMINAL else None
 if reason:x["reason"]=reason
 x["content_hash"]=_hash({k:v for k,v in x.items() if k!="content_hash"});_write(_p(root,directive_id),x);_event(root,f"grace_momentum_directive_{status}",x);return x
def supersede(directive_id,*,grace_action_id,authority_reference,root=None):
 old=transition(directive_id,"superseded",root=root);new=create(old["grace_objective_id"],grace_action_id,authority_reference=authority_reference,idempotency_key=f"{old['directive_id']}:superseded",root=root);new["supersedes_directive_id"]=old["directive_id"];new["content_hash"]=_hash({k:v for k,v in new.items() if k!="content_hash"});_write(_p(root,new["directive_id"]),new);return new
