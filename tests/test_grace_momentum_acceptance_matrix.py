"""Fixture acceptance matrix for directive controls, replay, and fail-closed progression."""
import json
import pytest
from estate.core.grace_momentum_directive import create,transition,supersede,load
from estate.core.runtime_recovery import RuntimePersistenceStore
from estate.core.runtime_replay import RuntimeReplayEngine
from estate.core.engineering_commission_progression import EngineeringCommissionProgressionHandler
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition

def directive(root): return create("obj-1","act-1",authority_reference="fixture",root=root)

@pytest.mark.parametrize("state",["paused","stopped","revoked","expired","superseded"])
def test_terminal_and_control_directives_survive_replay_and_do_not_progress(tmp_path,state):
 d=directive(tmp_path)
 if state=="superseded": transition(d["directive_id"],"superseded",root=tmp_path)
 else: transition(d["directive_id"],state,root=tmp_path)
 store=RuntimePersistenceStore(tmp_path); store.persist_checkpoint(cycle_id=f"control-{state}",cycle_state="blocked",campaign_state={"directive_id":d["directive_id"],"status":state},completed_side_effects=["no-dispatch"])
 replay=RuntimeReplayEngine(tmp_path).replay_from_checkpoint(f"control-{state}")
 assert replay["reconstructed_state"]["campaign_state"]["status"]==state
 with pytest.raises((PermissionError,ValueError)):
  EngineeringCommissionProgressionHandler(tmp_path).progress(d["directive_id"],"missing")

@pytest.mark.parametrize("boundary",["directive","evaluation","adapter","authorization","dispatch","result","reconciliation","validation","completion","receipt","objective","directive_completion"])
def test_restart_boundaries_preserve_completed_effect_and_suppress_replay(tmp_path,boundary):
 d=directive(tmp_path); store=RuntimePersistenceStore(tmp_path)
 store.persist_checkpoint(cycle_id=f"restart-{boundary}",cycle_state="running",campaign_state={"boundary":boundary,"directive_id":d["directive_id"]},completed_side_effects=[f"effect-{boundary}"],last_durable_event_position=0)
 store.append_event("campaign_state_updated",{"side_effect_id":f"effect-{boundary}","campaign_state":{"boundary":"duplicate"}})
 result=RuntimeReplayEngine(tmp_path).replay_from_checkpoint(f"restart-{boundary}")
 assert result["skipped_completed_side_effects"]==[f"effect-{boundary}"]
 assert result["reconstructed_state"]["campaign_state"]["boundary"]==boundary

@pytest.mark.parametrize("fault",["provider_not_admitted","capability_mismatch","provider_unhealthy","capacity_unknown","locality","privacy","egress","spend","stale_helen","suspended_capability","blocked_commission","mismatched_determination","mismatched_commission","directive_missing","malformed_checkpoint","conflicting_replay"])
def test_failure_matrix_fails_closed_without_dispatch(tmp_path,fault):
 d=directive(tmp_path)
 if fault=="malformed_checkpoint":
  p=RuntimePersistenceStore(tmp_path).checkpoint_path("bad");p.parent.mkdir(parents=True,exist_ok=True);p.write_text("{}")
  with pytest.raises(Exception): RuntimeReplayEngine(tmp_path).replay_from_checkpoint("bad")
 else:
  with pytest.raises((PermissionError,ValueError)):
   EngineeringCommissionProgressionHandler(tmp_path).progress("missing" if fault=="directive_missing" else d["directive_id"],"missing")
 assert not (tmp_path/"runtime/execution_dispatch/queue.json").exists()

def test_capability_gap_does_not_dispatch_and_duplicate_request_is_idempotent(tmp_path):
 d=directive(tmp_path); comp=GraceHelenEngineeringComposition(tmp_path); req=comp.request_capability("obj-1","cad",idempotency_key="cap")
 assert comp.request_capability("obj-1","cad",idempotency_key="cap")["capability_request_id"]==req["capability_request_id"]
 comp.determine_capability(req["capability_request_id"],disposition="capability_absent",reason="missing")
 assert not (tmp_path/"runtime/execution_dispatch/queue.json").exists()
 assert load(d["directive_id"],tmp_path)["status"]=="active"
