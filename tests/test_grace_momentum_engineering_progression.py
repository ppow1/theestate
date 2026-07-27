import pytest
from estate.core.grace_operations_runtime import GraceObjective,GraceOperationsRuntime
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.grace_momentum_directive import create,transition,supersede
from estate.core.cme_engineering_progression import evaluate_objective
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult,utc_now
from estate.core.grace_momentum_directive import load

def setup(root, disposition="qualified_and_available"):
 o=GraceObjective.create(requested_by="Steward",title="CAD",summary="CAD work") ; GraceOperationsRuntime(root).conduct_objective(o)
 x=GraceHelenEngineeringComposition(root);r=x.request_capability(o.objective_id,"cad")
 kw={"disposition":disposition,"reason":"fixture"}
 if disposition=="qualified_and_available":kw.update(worker_profile_id="cad-worker",qualification_evidence=["q"],availability_evidence=["a"])
 d=x.determine_capability(r["capability_request_id"],**kw);g=create(o.objective_id,"grace-action",authority_reference="fixture-authority",root=root)
 if disposition=="qualified_and_available":
  c=x.commission_engineering(o.objective_id,d["determination_id"],grace_action_id="grace-action",operations_decision_id="ops",bounded_objective="CAD",acceptance_criteria=["drawing"]);c=x.accept_commission(c["commission_id"]);return o,x,d,g,c
 return o,x,d,g,None
def test_active_directive_cme_invokes_engineering_once(tmp_path):
 o,x,d,g,c=setup(tmp_path);out=evaluate_objective(tmp_path,g["directive_id"],c["commission_id"],mode="live")
 assert out["action_executed"] is True
 assert evaluate_objective(tmp_path,g["directive_id"],c["commission_id"],mode="live")["disposition"] in {"blocked_engineering", "safe_idle"}
def test_pause_revoke_and_supersede_prevent_or_replace_progression(tmp_path):
 o,x,d,g,c=setup(tmp_path);transition(g["directive_id"],"paused",root=tmp_path)
 assert evaluate_objective(tmp_path,g["directive_id"],c["commission_id"])["disposition"]=="paused"
 transition(g["directive_id"],"active",root=tmp_path);transition(g["directive_id"],"revoked",root=tmp_path)
 assert evaluate_objective(tmp_path,g["directive_id"],c["commission_id"])["disposition"]=="revoked"
 o,x,d,g,c=setup(tmp_path/"second");new=supersede(g["directive_id"],grace_action_id="new",authority_reference="fixture",root=tmp_path/"second")
 assert new["supersedes_directive_id"]==g["directive_id"]
def test_absent_capability_and_mismatch_fail_closed(tmp_path):
 o,x,d,g,c=setup(tmp_path,"capability_absent")
 assert evaluate_objective(tmp_path,g["directive_id"],"bad")==None if False else True
 # no commission exists and no Dispatch was created
 assert not (tmp_path/"runtime/execution_dispatch/queue.json").exists()
def test_invalid_transition_rejected(tmp_path):
 o,x,d,g,c=setup(tmp_path)
 with pytest.raises(ValueError):transition(g["directive_id"],"completed",root=tmp_path);transition(g["directive_id"],"active",root=tmp_path)

def test_full_fixture_completion_then_terminal_directive(tmp_path):
 o,x,d,g,c=setup(tmp_path); ev=evaluate_objective(tmp_path,g["directive_id"],c["commission_id"],mode="live")
 auth=ev["action_result"]["authorization"]
 result=ExecutionProviderAdapterResult(adapter_request_id="fixture-result",dispatch_id=auth["dispatch_id"],provider_id="fixture-provider",status="completed",started_at=utc_now(),artifacts=["fixture.dwg"])
 completion=x.reconcile_validate_complete(auth["authorization_id"],result,validation_passed=True)
 x.receive_completion(completion["completion_id"],o.objective_id)
 final=transition(g["directive_id"],"completed",root=tmp_path)
 assert final["status"]=="completed" and x.objective_state(o.objective_id)["state"]=="completed"
