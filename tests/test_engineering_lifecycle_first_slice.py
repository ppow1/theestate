import json

from estate.core.alfred_runtime import correlate_operational_response
from estate.core.engineering_lifecycle_slice import EngineeringLifecycleSlice
from estate.core.execution_dispatch import load_dispatch_queue
from estate.core.helen_workforce import HelenWorkforceStore


NOW = "2026-07-26T12:00:00+00:00"


def _registries(root):
    path = root / "data/registry"
    path.mkdir(parents=True)
    (path / "personnel.json").write_text(json.dumps([
        {"employee_id": 1, "mailbox_id": 1, "display_name": "Steward", "current_title": "Steward", "current_office": "Stewardship"},
        {"employee_id": 12, "mailbox_id": 12, "display_name": "Grace", "current_title": "Director of Operations", "current_office": "Office of Operations"},
    ]), encoding="utf-8")
    (path / "mailboxes.json").write_text("[]", encoding="utf-8")


def test_authorized_evelyn_image_iteration_first_vertical_slice(tmp_path):
    _registries(tmp_path)
    lifecycle = EngineeringLifecycleSlice(tmp_path, "evelyn-image-iteration-001")

    intake = lifecycle.intake(occurred_at=NOW)
    assert intake["campaign_id"] == "CAMPAIGN-0670"
    assert intake["work_package_id"] == "WP-0675"
    assert intake["engineering_association_required"] is True
    assert lifecycle.advance()["state"] == "blocked"  # Helen is a required gate.
    assert load_dispatch_queue(tmp_path) == []  # Grace cannot bypass Engineering/readiness.

    disposition, _ = HelenWorkforceStore(tmp_path).record_operational_disposition(
        lifecycle.request_id, disposition="fulfilled", decided_by="Helen",
        evidence_references=["fixture://helen/image-capability-assessment.json"],
        fulfilled_capabilities=["image_iteration"], reason="Deterministic fixture worker is ready.",
        authority_evidence=["STEWARD AUTHORIZATION: first vertical slice"],
    )
    first = lifecycle.advance()
    replay = lifecycle.advance()
    momentum = lifecycle.momentum()
    assert len(load_dispatch_queue(tmp_path)) == 1
    assert first["dispatch_id"] == replay["dispatch_id"] == lifecycle.dispatch_id
    assert first["adapter_request_id"] == replay["adapter_request_id"]
    assert first["helen_disposition_id"] == disposition["disposition_id"]
    assert momentum["deterministic_replay"] is True

    routine = lifecycle.notify("progress", occurred_at=NOW)
    blocker = lifecycle.notify("blocker", occurred_at=NOW)
    blocker_replay = lifecycle.notify("blocker", occurred_at=NOW)
    assert routine == {"recorded": False, "suppressed": True, "reason": "routine Engineering event"}
    assert blocker["recorded"] is True and blocker["routing_is_execution"] is False
    assert blocker_replay["duplicate"] is True

    result = lifecycle.reconcile_fixture("completed")
    reconciliation = result["reconciliation"]
    assert reconciliation["dispatch_state"] == "Validation"  # completion is not acceptance
    assert "provider_result_received" in reconciliation["activity_events_emitted"]
    assert result["grace_reaction"] == "advance_to_validation"
    assert result["retry_authority"] == {"maximum_attempts": 1, "attempts_used": 0}
    assert result["acceptance_granted"] is False
    assert result["real_image_generated"] is False

    original_message = json.loads((tmp_path / blocker["repository_message_path"]).read_text())
    ack = correlate_operational_response(
        original_message,
        {"id": "ack", "message_type": "acknowledgement", "acknowledges": blocker["message_id"],
         "thread_id": original_message["thread_id"]},
    )
    assert ack["acknowledged"] is True
    assert ack["underlying_work_complete"] is False
    assert ack["acceptance_granted"] is False

    evidence = json.loads(lifecycle.evidence_path.read_text())
    assert {evidence[k] for k in ("correlation_id", "campaign_id", "work_package_id", "objective_id",
                                  "workforce_request_id", "dispatch_id")}
    assert evidence["chief_architect_acceptance_required"] is True
