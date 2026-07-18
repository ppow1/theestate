import json
from pathlib import Path

from estate.core.campaign_0681_pilot import run_pilot


def test_bounded_real_work_pilot_uses_canonical_lanes_and_stops_protected_action(tmp_path):
    source = Path(__file__).resolve().parents[1]
    result = run_pilot(source, tmp_path / "pilot", occurred_at="2026-07-18T14:00:00Z")
    assert result["grace"]["view"]["derived_view_only"] is True
    assert result["alfred"]["recorded"] is True
    assert result["alfred"]["routing_is_execution"] is False
    assert result["helen"]["disposition"]["disposition"] == "deferred"
    assert result["engineering"]["state"] == "Queued"
    assert result["engineering"]["live_provider_execution"] is False
    assert result["interruption_recovery"]["skipped_completed_side_effects"] == ["msg_campaign0681_wp0706_pilot"]
    assert result["interruption_recovery"]["reconstructed_state"]["campaign_state"]["phase"] == "recovered-for-review"
    assert result["protected_escalation"]["cycle"]["disposition"] == "escalate"
    assert result["protected_escalation"]["adapter_calls"] == 0
    assert result["steward_visibility"]["protected_decisions"]
    assert not any(result["protected_actions"].values())


def test_pilot_artifacts_are_durable_in_sandbox_without_duplicate_message(tmp_path):
    source = Path(__file__).resolve().parents[1]
    root = tmp_path / "pilot"
    result = run_pilot(source, root, occurred_at="2026-07-18T14:00:00Z")
    assert (root / result["alfred"]["repository_message_path"]).is_file()
    assert len(list((root / "collaboration/messages").glob("msg_campaign0681_wp0706_pilot.json"))) == 1
    queue = json.loads((root / "runtime/execution_dispatch/queue.json").read_text())
    assert [item["dispatch_id"] for item in queue["items"]] == ["dispatch-campaign0681-wp0706-pilot"]
    assert (root / "audit/autonomy/autonomous_operations_audit.jsonl").is_file()


def test_committed_pilot_result_records_real_run_and_protected_stop():
    root = Path(__file__).resolve().parents[1]
    result = json.loads((root / "collaboration/evidence/CAMPAIGN_0681_WP0706_pilot_result.json").read_text())
    assert result["pilot_id"] == "CAMPAIGN-0681-WP0706-EVIDENCE-INTEGRITY"
    assert result["alfred"]["recorded"] is True
    assert result["helen"]["disposition"]["disposition"] == "deferred"
    assert result["engineering"]["state"] == "Queued"
    assert result["interruption_recovery"]["skipped_completed_side_effects"] == ["msg_campaign0681_wp0706_pilot"]
    assert result["protected_escalation"]["adapter_calls"] == 0
    assert not any(result["protected_actions"].values())
