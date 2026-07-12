import json
from pathlib import Path


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_grace_hiring_package_separates_review_recommendation_appointment_and_activation():
    assessment = read_json("runtime/onboarding/grace/hiring_assessment.json")
    readiness = read_json("runtime/onboarding/grace/appointment_readiness.json")

    assert assessment["hr_actor"]["name"] == "Helen"
    assert assessment["state_decisions"] == {
        "candidate_reviewed": True,
        "hiring_recommended": True,
        "onboarding_ready": True,
        "appointment_ready": True,
        "appointed": False,
        "activated": False,
    }
    assert readiness["appointment_authority"] == "Steward"
    assert readiness["appointed"] is True
    assert readiness["activated"] is False


def test_grace_identity_and_mailbox_are_reconciled_for_appointed_onboarding_not_active_service():
    personnel = read_json("data/registry/personnel.json")
    mailboxes = read_json("data/registry/mailboxes.json")
    residents = read_json("data/registry/residents.json")

    grace_personnel = next(entry for entry in personnel if entry.get("display_name") == "Grace")
    grace_mailbox = next(entry for entry in mailboxes if entry.get("display_name") == "Grace")

    assert grace_personnel["status"] == "appointed_onboarding"
    assert grace_personnel["employee_id"] == 12
    assert grace_personnel["mailbox_id"] == 12
    assert grace_personnel.get("resident_id") == "grace"
    assert grace_mailbox["status"] == "onboarding"
    assert grace_mailbox["mailbox_type"] == "personnel"
    assert all(entry.get("name") != "Grace" for entry in residents)


def test_grace_onboarding_boundaries_and_message_preserve_reserved_actions():
    plan = read_json("runtime/onboarding/grace/onboarding_plan.json")
    message = read_json("collaboration/messages/msg_helen_20260710_0001_grace_hiring_recommendation.json")

    assert "Steward appointment recorded" in plan["must_not_start_until"]
    assert "No provider execution or parallel queue creation" in plan["probationary_readiness_conditions"]
    assert message["created_by"] == "Helen"
    assert message["destination_mailbox_id"] == 1
    assert "does not appoint" in message["payload"]["authority_boundary"]
