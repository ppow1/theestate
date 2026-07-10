from estate.core.runtime_recovery import RuntimePersistenceStore
from estate.core.runtime_replay import RuntimeReplayEngine


def test_replay_reconstructs_state_without_repeating_completed_side_effects(tmp_path):
    store = RuntimePersistenceStore(tmp_path)
    store.persist_checkpoint(
        cycle_id="cycle-1",
        cycle_state="running",
        leases={"lease-1": {"status": "active"}},
        claims={"claim-1": {"status": "claimed"}},
        scheduler_state={"pending": ["claim-1"]},
        campaign_state={"phase": "audit"},
        admitted_audit_state={"audit-1": "admitted"},
        last_durable_event_position=0,
        completed_side_effects=["effect-1"],
    )
    store.append_event("lease_released", {"lease_id": "lease-1", "side_effect_id": "effect-1"})
    store.append_event("claim_requeued", {"claim_id": "claim-1", "side_effect_id": "effect-2"})
    store.append_event("scheduler_state_updated", {"scheduler_state": {"pending": ["claim-1"], "recovered": True}})

    replay = RuntimeReplayEngine(tmp_path).replay_from_checkpoint("cycle-1")

    assert replay["skipped_completed_side_effects"] == ["effect-1"]
    assert replay["replayed_events"] == 2
    assert replay["reconstructed_state"]["leases"] == {"lease-1": {"status": "active"}}
    assert replay["reconstructed_state"]["claims"]["claim-1"]["status"] == "retryable"
    assert replay["reconstructed_state"]["scheduler_state"]["recovered"] is True


def test_replay_from_terminal_checkpoint_rebuilds_from_immutable_events(tmp_path):
    store = RuntimePersistenceStore(tmp_path)
    store.persist_checkpoint(cycle_id="cycle-2", cycle_state="completed", last_durable_event_position=-1)
    store.append_event("campaign_state_updated", {"campaign_state": {"campaign": "reconstructed"}})
    store.append_event("audit_state_updated", {"admitted_audit_state": {"audit-2": "completed"}})

    replay = RuntimeReplayEngine(tmp_path).replay_from_checkpoint("cycle-2")

    assert replay["replayed_events"] >= 2
    assert replay["reconstructed_state"]["campaign_state"]["campaign"] == "reconstructed"
    assert replay["reconstructed_state"]["admitted_audit_state"]["audit-2"] == "completed"
