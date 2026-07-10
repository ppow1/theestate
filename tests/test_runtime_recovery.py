import json

import pytest

from estate.core.runtime_recovery import RuntimePersistenceStore, RuntimeRecoveryManager, load_recovery_status


def test_startup_classifies_interrupted_cycle_leases_and_claims(tmp_path):
    store = RuntimePersistenceStore(tmp_path)
    store.persist_checkpoint(
        cycle_id="cycle-1",
        cycle_state="running",
        leases={"lease-1": {"status": "active"}},
        claims={"claim-1": {"status": "claimed"}},
        scheduler_state={"queue": ["cycle-1"]},
        campaign_state={"campaign": "active"},
        admitted_audit_state={"audit-1": "admitted"},
        last_durable_event_position=0,
    )

    plan = RuntimeRecoveryManager(tmp_path).inspect_startup()

    assert plan["recovery_posture"] == "recoverable"
    assert plan["destructive_repair_required"] is False
    classifications = {item["artifact"]: item["classification"] for item in plan["classifications"]}
    assert classifications["cycle_checkpoint"] == "resumable"
    assert classifications["lease:lease-1"] == "retryable"
    assert classifications["claim:claim-1"] == "retryable"
    assert "replay_after_last_durable_event_position" in plan["pending_actions"]
    assert load_recovery_status(tmp_path)["plan_id"] == plan["plan_id"]


def test_corrupt_checkpoint_is_reported_without_destructive_execution(tmp_path):
    store = RuntimePersistenceStore(tmp_path)
    envelope = store.persist_checkpoint(cycle_id="cycle-2", cycle_state="running")
    path = store.checkpoint_path("cycle-2")
    envelope["state"]["scheduler_state"] = {"tampered": True}
    path.write_text(json.dumps(envelope), encoding="utf-8")

    plan = RuntimeRecoveryManager(tmp_path).inspect_startup()

    assert plan["recovery_posture"] == "safe-state"
    assert plan["destructive_repair_required"] is True
    assert plan["safe_state_fallback"] is True
    assert plan["execute_destructive_repairs"] is False
    with pytest.raises(ValueError, match="explicit operator review"):
        RuntimeRecoveryManager(tmp_path).execute_non_destructive_plan(plan)


def test_backup_rotation_and_corrupt_isolation(tmp_path):
    store = RuntimePersistenceStore(tmp_path, backup_limit=2)
    for index in range(4):
        store.persist_checkpoint(cycle_id="cycle-3", cycle_state="running", metadata={"index": index})
    assert len(list((tmp_path / "runtime/operations_runtime/persistence/backups").glob("*.json"))) <= 2

    manager = RuntimeRecoveryManager(tmp_path)
    result = manager.isolate_corrupt_checkpoint("runtime/operations_runtime/persistence/checkpoints/cycle-3.json", reason="test corruption")
    assert (tmp_path / result["isolated"]).exists()
    assert result["safe_state_plan"]["checkpoint"] is None
