import pytest

from estate.core.operational_blocker_classifier import BLOCKER_CLASSES, classify_blockers, declassification_ready


@pytest.mark.parametrize("blocker_class", sorted(BLOCKER_CLASSES))
def test_every_required_blocker_class(blocker_class):
    result = classify_blockers("WP-X", [{
        "blocker_class": blocker_class, "state": "blocked",
        "summary": blocker_class, "evidence_references": [f"canonical/{blocker_class}.json"],
    }])
    assert result["blocker_class"] == blocker_class
    assert result["affected_campaign_or_work_package"] == "WP-X"
    assert result["canonical_evidence_references"]
    assert result["responsible_office_or_authority_lane"]
    assert result["escalation_destination"]
    assert result["acknowledgement_requirement"]
    assert result["reevaluation_trigger"]
    assert result["authorizes_action"] is False
    assert result["mutated_canonical_state"] is False


def test_ambiguous_authority_and_missing_evidence_fail_closed():
    result = classify_blockers("CAMPAIGN-X", [{"condition": "readiness", "authority_ambiguous": True}])
    assert result["blocker_class"] == "unknown_authority_blocker"
    assert "evidence_or_validation_blocker" in result["additional_blocker_classes"]
    assert result["fail_closed_reason"]
    assert result["work_may_continue_in_unaffected_lanes"] is False


@pytest.mark.parametrize("parallel,clear,expected", [(False, False, False), (True, False, False), (False, True, False), (True, True, True)])
def test_unaffected_lane_requires_dependency_and_collision_clearance(parallel, clear, expected):
    result = classify_blockers("WP-X", [{"blocker_class": "dependency_blocker", "evidence_references": ["manifest.json"]}],
                               canonical_dependencies_allow_parallel=parallel, collision_check_clear=clear)
    assert result["work_may_continue_in_unaffected_lanes"] is expected


def test_protected_decision_stops_even_otherwise_clear_parallel_lane():
    result = classify_blockers("WP-X", [{"blocker_class": "protected_steward_decision", "evidence_references": ["decision.json"]}],
                               canonical_dependencies_allow_parallel=True, collision_check_clear=True)
    assert result["work_may_continue_in_unaffected_lanes"] is False
    assert result["escalation_destination"] == "Steward"


def test_reclassification_requires_current_evidence_that_names_cleared_evidence():
    blocked = classify_blockers("WP-X", [{"blocker_class": "service_health_blocker", "evidence_references": ["health/old.json"]}])
    assert not declassification_ready(blocked, [{"state": "healthy", "evidence_references": ["health/new.json"]}])
    assert declassification_ready(blocked, [{"state": "healthy", "evidence_references": ["health/new.json"], "clears_references": ["health/old.json"]}])


def test_input_is_not_mutated_and_order_does_not_change_precedence():
    facts = [{"blocker_class": "dependency_blocker", "evidence_references": ["a"]},
             {"blocker_class": "contradictory_state_blocker", "evidence_references": ["b"]}]
    original = [dict(x) for x in facts]
    assert classify_blockers("WP-X", facts)["blocker_class"] == classify_blockers("WP-X", reversed(facts))["blocker_class"] == "contradictory_state_blocker"
    assert facts == original
