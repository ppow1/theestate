"""Projection from durable Grace/Helen/Engineering records into the existing CME."""
from __future__ import annotations
from estate.core.continuous_momentum_engine import run_momentum_cycle
from estate.core.grace_momentum_directive import load as load_directive
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition, _load, COMMISSIONS, DETERMINATIONS
from estate.core.engineering_commission_progression import EngineeringCommissionProgressionHandler
from estate.core.runtime_recovery import RuntimePersistenceStore
from pathlib import Path
import json
EVALUATIONS=Path("runtime/operations/grace/momentum_evaluations")
def evaluate_objective(root, directive_id, commission_id, *, mode="dry_run"):
 d=load_directive(directive_id,root); comp=GraceHelenEngineeringComposition(root);c=_load(comp._path(COMMISSIONS,commission_id));det=_load(comp._path(DETERMINATIONS,c["helen_determination_id"]))
 state="ready" if d["status"]=="active" and det["disposition"]=="qualified_and_available" and c["status"]=="accepted" else "blocked"
 candidate={"action_id":f"engineering-progress-{commission_id}","permission":"delegated","priority":10,"idempotency_key":f"{directive_id}:{commission_id}:dispatch","source_refs":[directive_id,commission_id,det["determination_id"]],"canonical_mechanism":"engineering_commission_progression","authority_refs":[d["grace_authority_reference"]]}
 if d["status"]!="active": result={"disposition":d["status"],"directive_id":directive_id,"commission_id":commission_id,"action_executed":False}
 elif state!="ready": result={"disposition":"blocked_pending_capability" if det["disposition"]!="qualified_and_available" else "blocked_engineering","directive_id":directive_id,"commission_id":commission_id,"action_executed":False}
 else:
  handler=EngineeringCommissionProgressionHandler(root)
  result=run_momentum_cycle(cycle_id=f"cme-{directive_id}-{commission_id}",observed_at=d["updated_at"],inputs={"directive":{"state":"ready","authorizes_action":False,"evidence_references":[directive_id]},"helen":{"state":"ready","authorizes_action":False,"evidence_references":[det["determination_id"]]}},candidates=[candidate],mode=mode,action_adapter=lambda _:handler.progress(directive_id,commission_id))
 result.update({"evaluation_id":f"cme-eval-{directive_id}-{commission_id}","objective_id":d["grace_objective_id"],"selected_adapter":"EngineeringCommissionProgressionHandler","input_evidence_ids":[directive_id,commission_id,det["determination_id"]]})
 path=Path(root)/EVALUATIONS/f"{result['evaluation_id']}.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 store=RuntimePersistenceStore(Path(root));store.persist_checkpoint(cycle_id=result["evaluation_id"],cycle_state="completed" if result.get("action_executed") else "blocked",campaign_state={"directive_id":directive_id,"commission_id":commission_id,"disposition":result["disposition"]},completed_side_effects=[candidate["idempotency_key"]] if result.get("action_executed") else [],metadata={"evaluation_path":str(path.relative_to(root))})
 result["checkpoint_reference"]=str(store.checkpoint_path(result["evaluation_id"]).relative_to(root));return result
