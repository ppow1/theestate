import json

from estate.core.wp4232_acceptance import WP4232AcceptanceHarness


def test_wp4232_harness_uses_real_runtime_and_records_pre_live_gates(tmp_path):
    report = WP4232AcceptanceHarness(tmp_path / "evidence").run()
    assert report["bounded_live_executed"] is False
    assert report["readiness_gate"]["fixture_acceptance"] is True
    assert report["readiness_gate"]["shadow_acceptance"] is True
    assert report["readiness_gate"]["restart_and_replay"] is True
    assert report["readiness_gate"]["emergency_stop"] is True
    assert report["readiness_gate"]["rollback"] is True
    assert report["readiness_gate"]["ready"] is False
    assert report["readiness_gate"]["missing_event_types"]
    assert report["readiness_gate"]["dual_surface_projection_available"] is True
    assert report["readiness_gate"]["dual_surface_complete"] is False
    assert report["blocker_classification"]["progression.changed"]["provider_dependency"] is False
    assert report["blocker_classification"]["reconciliation.completed"]["provider_dependency"] is True
    assert (tmp_path / "evidence" / "acceptance_evidence.json").exists()


def test_wp4232_evidence_is_machine_readable_and_does_not_claim_receipt(tmp_path):
    root = tmp_path / "evidence"
    WP4232AcceptanceHarness(root).run()
    evidence = json.loads((root / "acceptance_evidence.json").read_text(encoding="utf-8"))
    assert evidence["bounded_live_executed"] is False
    assert evidence["readiness_gate"]["complete_lifecycle"] is False
    assert "grace.receipt.recorded" in evidence["readiness_gate"]["missing_event_types"]
    assert evidence["bounded_live_task"]["execution_status"] == "not_executed"
    assert evidence["blocker_classification"]["dispatch.submitted"]["status"] == "declared_but_unreachable_by_current_dispatch_command"
