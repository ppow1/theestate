import json

import pytest

from estate.core.grace_operations_runtime import (
    build_operational_coordination_view,
    create_coordination_request,
    record_coordination_request,
)


def momentum(*packages, observation_only=True):
    return {
        "campaign_id": "CAMPAIGN-0681",
        "observation_timestamp": "2026-07-18T14:00:00+00:00",
        "campaign_momentum_state": "active",
        "packages": list(packages),
        "warnings": [],
        "observation_only": observation_only,
    }


def package(package_id, state, *, evidence=True, warnings=None):
    return {
        "package_id": package_id,
        "observed_state": state,
        "dependency_satisfaction": {"satisfied": [], "unmet": []},
        "evidence_references": [f"evidence/{package_id}.json"] if evidence else [],
        "warnings": warnings or [],
        "explanation": f"{package_id} is {state}.",
        "recommended_follow_up_destination": "Office of the Chief Architect",
    }


def test_grace_view_prioritizes_truth_and_preserves_authority_boundaries():
    source = momentum(
        package("WP-0694", "eligible"),
        package("WP-0707", "complete_pending_acceptance"),
        package("WP-0695", "degraded"),
    )
    view = build_operational_coordination_view(source)

    by_id = {item["package_id"]: item for item in view["items"]}
    assert by_id["WP-0694"]["coordination_permitted"] is True
    assert by_id["WP-0694"]["action_class"] == "coordinate"
    assert by_id["WP-0707"]["protected_stop"] is True
    assert by_id["WP-0707"]["action_class"] == "protected_decision"
    assert view["derived_view_only"] is True
    assert view["authorizes_action"] is False
    assert "merge" in view["authority_boundaries"]["may_not"]
    assert source["packages"][0]["observed_state"] == "eligible"


def test_stale_or_ambiguous_evidence_fails_closed():
    view = build_operational_coordination_view(
        momentum(package("WP-0694", "eligible", warnings=["evidence is stale"]))
    )
    item = view["items"][0]
    assert item["coordination_permitted"] is False
    assert item["action_class"] == "recommend"
    assert item["evidence_freshness_warnings"] == ["evidence is stale"]

    untrusted = build_operational_coordination_view(
        momentum(package("WP-0694", "eligible"), observation_only=False)
    )
    assert untrusted["items"][0]["coordination_permitted"] is False
    assert "fails closed" in untrusted["warnings"][0]


def test_classifier_routes_blocker_without_transferring_decision_authority():
    classification = {
        "affected_campaign_or_work_package": "WP-0695",
        "canonical_evidence_references": ["evidence/staffing.json"],
        "blocker_class": "staffing_or_capability_blocker",
        "severity": "error",
        "recommended_next_action": "Submit the need through Helen's workforce lane.",
        "escalation_destination": "Helen",
        "protected_decision": False,
        "fail_closed_reason": None,
        "authorizes_action": False,
    }
    view = build_operational_coordination_view(
        momentum(package("WP-0695", "blocked")), [classification]
    )
    item = view["items"][0]
    assert item["proper_office_or_lane"] == "Helen"
    assert item["coordination_permitted"] is False
    assert item["acknowledgement_required"] is True
    assert item["authorizes_action"] is False


def test_permitted_request_records_canonical_message_without_dispatch(tmp_path):
    view = build_operational_coordination_view(momentum(package("WP-0694", "eligible")))
    request = create_coordination_request(
        view,
        "WP-0694",
        destination="Office of the Chief Architect",
        destination_id=9,
        mailbox_id=9,
        created_at="2026-07-18T14:05:00+00:00",
        message_id="msg_grace_20260718_wp0694_coordination",
    )
    relative = record_coordination_request(tmp_path, request)
    recorded = json.loads((tmp_path / relative).read_text(encoding="utf-8"))

    assert relative.startswith("collaboration/messages/")
    assert recorded["source_employee_id"] == 12
    assert recorded["destination_employee_id"] == 9
    assert recorded["destination_mailbox_id"] == 9
    assert recorded["requires_ack"] is True
    assert recorded["operational_context"]["authorizes_action"] is False
    assert not (tmp_path / "runtime" / "execution_dispatch" / "queue.json").exists()


def test_protected_or_unsupported_request_is_refused(tmp_path):
    view = build_operational_coordination_view(
        momentum(package("WP-0707", "complete_pending_acceptance"))
    )
    with pytest.raises(PermissionError):
        create_coordination_request(
            view,
            "WP-0707",
            destination="Steward",
            destination_id=1,
            mailbox_id=1,
            created_at="2026-07-18T14:05:00+00:00",
        )

    permitted = build_operational_coordination_view(momentum(package("WP-0694", "eligible")))
    request = create_coordination_request(
        permitted,
        "WP-0694",
        destination="Office of the Chief Architect",
        destination_id=9,
        mailbox_id=9,
        created_at="2026-07-18T14:05:00+00:00",
        message_id="msg_grace_boundary_test",
    )
    request["operational_context"]["authorizes_action"] = True
    with pytest.raises(ValueError):
        record_coordination_request(tmp_path, request)
