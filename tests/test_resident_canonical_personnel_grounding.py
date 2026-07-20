from pathlib import Path

import pytest

from estate.core.office_personnel_directory import canonical_resident_personnel_record
from estate.core.resident_authority import ALLOWED, check_authority
from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.resident_interaction import _canonical_self_personnel_response, _clean_resident_visible_response


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("resident,employee,mailbox,status", [
    ("Alfred", 7, 7, "active"),
    ("Helen", 6, 6, "active"),
    ("Ingrid", 10, 10, "onboarding"),
    ("Grace", 12, 12, "active"),
])
def test_canonical_gateway_resident_personnel(resident, employee, mailbox, status):
    record = canonical_resident_personnel_record(resident, ROOT)
    assert (record["employee_id"], record["mailbox_id"], record["personnel_status"]) == (employee, mailbox, status)
    assert record["source_lineage"][0] == "data/registry/personnel.json"


@pytest.mark.parametrize("resident", ["Evelyn", "Eleanor", "Marie", "Judy"])
def test_missing_residents_never_receive_identifiers(resident):
    record = canonical_resident_personnel_record(resident, ROOT)
    assert record["record_found"] is False
    assert record["employee_id"] is record["mailbox_id"] is None
    assert record["identifier_assigned"] is False


@pytest.mark.parametrize("resident", ["alfred", "helen", "ingrid", "grace", "evelyn", "eleanor", "marie", "judy"])
def test_conversation_is_allowed_for_every_gateway_resident(resident, tmp_path):
    decision = check_authority(resident, "conversation", root=tmp_path, audit=False)
    assert decision["decision"] == ALLOWED
    assert decision["authority_classification"] == "conversation_only"


def test_composition_propagates_steward_and_canonical_personnel():
    composition = compose_resident_identity("ingrid", surface_id="conference-room-gateway", root=ROOT)
    layers = {item["layer"]: item["content"] for item in composition["included_context_layers"]}
    assert layers["participant_identity_context"]["participant_role"] == "Steward"
    assert layers["participant_identity_context"]["privileged_execution_implied"] is False
    assert layers["canonical_self_personnel_facts"]["employee_id"] == 10
    assert layers["canonical_self_personnel_facts"]["personnel_status"] == "onboarding"


def test_missing_record_answer_is_epistemically_disciplined():
    composition = compose_resident_identity("judy", surface_id="single-resident-gateway", root=ROOT)
    answer = _canonical_self_personnel_response("What is your employee ID and onboarding status?", composition)
    assert "not present" in answer
    assert "no verified employee ID" in answer
    assert all(word not in answer.lower() for word in ("privacy", "security", "legal restriction", "protocol"))


def test_raw_classifier_diagnostics_are_removed_from_prose():
    visible = _clean_resident_visible_response(
        "Request blocked due to an unknown category: unknown action category 'conversation'; unknown resident authority.",
        "judy", {"intent": "conversation"},
    ).lower()
    assert "unknown action category" not in visible
    assert "unknown resident authority" not in visible
    assert "blocked due to an unknown category" not in visible
