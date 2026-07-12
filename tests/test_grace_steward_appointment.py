import json
from pathlib import Path

from estate.core.resident_lifecycle import transition


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def grace_entry(path: str):
    return next(entry for entry in read_json(path) if entry.get("display_name") == "Grace")


def test_wp4033_records_explicit_steward_appointment_and_fixed_ids():
    decision = read_json("runtime/onboarding/grace/steward_appointment_decision.json")
    readiness = read_json("runtime/onboarding/grace/appointment_readiness.json")
    personnel = grace_entry("data/registry/personnel.json")
    mailbox = grace_entry("data/registry/mailboxes.json")

    assert decision["appointing_authority"] == "Steward"
    assert decision["decision"] == "appoint"
    assert decision["resident"] == "Grace"
    assert decision["role"] == "Director of Operations"
    assert decision["office"] == "Office of Operations"
    assert decision["employee_id"] == 12
    assert decision["mailbox_id"] == 12
    assert readiness["appointed"] is True
    assert readiness["activated"] is False
    assert readiness["employee_id"] == 12
    assert readiness["mailbox_id"] == 12
    assert personnel["employee_id"] == 12
    assert personnel["mailbox_id"] == 12
    assert mailbox["mailbox_id"] == 12
    assert mailbox["responsible_employee_id"] == 12


def test_wp4033_reconciles_onboarding_without_premature_activation_or_gateway_exposure():
    readiness = read_json("runtime/onboarding/grace/appointment_readiness.json")
    lifecycle = read_json("runtime/residents/lifecycle/grace.json")
    next_action = read_json("runtime/onboarding/grace/next_action_before_gateway_activation.json")

    assert readiness["status"] == "appointed_onboarding"
    assert readiness["state_boundaries"] == {
        "appointed": True,
        "onboarding": True,
        "activated_for_live_service": False,
        "accepted_for_full_operational_service": False,
    }
    assert lifecycle["status"] == "onboarding"
    assert lifecycle["pending_gate"] == "mark_ready"
    assert next_action["target_surface"] == "estate/grace"
    assert "Do not add estate/grace to resident gateway" in next_action["prohibited_until_complete"]


def test_wp4033_lifecycle_provenance_and_no_self_appointment():
    lifecycle = read_json("runtime/residents/lifecycle/grace.json")
    steward_events = [event for event in lifecycle["history"] if event["actor"] == "Steward"]

    assert [event["event_id"] for event in lifecycle["history"]] == [
        "WP-4033:intake_candidate",
        "WP-4033:begin_review",
        "WP-4033:approve_for_hire",
        "WP-4033:start_onboarding",
    ]
    assert len(steward_events) == 1
    assert steward_events[0]["transition"] == "approve_for_hire"
    assert steward_events[0]["evidence"]["appointment_decision"] == "runtime/onboarding/grace/steward_appointment_decision.json"
    assert all(event["actor"] != "Grace" for event in lifecycle["history"])


def test_wp4033_preserves_helen_ingrid_traffic_controller_and_authority_gates():
    decision = read_json("runtime/onboarding/grace/steward_appointment_decision.json")
    plan = read_json("runtime/onboarding/grace/onboarding_plan.json")

    assert decision["authority_boundaries"]["helen"] == "owns onboarding execution and readiness evidence"
    assert "Ingrid access review completed for any elevated/cross-office access" in plan["remaining_gates_before_activation"]
    assert "Traffic Controller movement constraints satisfied" in plan["remaining_gates_before_activation"]
    assert "No provider execution or parallel queue creation without separate authorization" in plan["probationary_readiness_conditions"]
    assert "not a hiring condition or authority gate" in plan["estate_commissioning_tradition"]


def test_wp4033_lifecycle_rerun_is_idempotent(tmp_path):
    evidence = {"work_package_id": "WP-4033", "appointment_decision": "runtime/onboarding/grace/steward_appointment_decision.json", "employee_id": 12, "mailbox_id": 12}
    first = transition("grace", "intake_candidate", actor="Helen", resident_name="Grace", evidence=evidence, root=tmp_path, resume_token="WP-4033:intake_candidate")
    second = transition("grace", "intake_candidate", actor="Helen", resident_name="Grace", evidence=evidence, root=tmp_path, resume_token="WP-4033:intake_candidate")

    assert second == first
    assert len(second["history"]) == 1
