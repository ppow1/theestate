import pytest

from estate.core import (
    create_reflection_workflow,
    load_reflection_workflow,
    reflection_workflow_status,
    transition_reflection_workflow,
    workflow_path,
)


def _create_direct(tmp_path):
    return create_reflection_workflow(
        run_id="REF-2026-0001",
        office="Chief Architect",
        officeholder="Chief Architect",
        current_implementation="Chief Architect 5",
        mailbox_id="5",
        initiation_type="direct_reflection",
        authority_reference="Steward directive 2026-07-18",
        actor="Steward",
        reason="Operational degradation",
        repository="A:/theestate",
        branch="main",
        root=tmp_path,
    )


def test_direct_creation_is_persisted_and_idempotent(tmp_path):
    first = _create_direct(tmp_path)
    second = _create_direct(tmp_path)
    assert first == second
    assert first["state"] == "reflection_authorized"
    assert workflow_path("REF-2026-0001", tmp_path).exists()
    assert load_reflection_workflow("REF-2026-0001", tmp_path) == first
    assert reflection_workflow_status("REF-2026-0001", tmp_path) == first


def test_direct_creation_requires_steward(tmp_path):
    with pytest.raises(PermissionError):
        create_reflection_workflow(
            run_id="REF-2", office="Architect", officeholder="Architect",
            current_implementation="Architect 1", mailbox_id="1",
            initiation_type="direct_reflection", authority_reference="memo",
            actor="Worker", root=tmp_path,
        )


def test_transition_updates_evidence_and_is_idempotent(tmp_path):
    _create_direct(tmp_path)
    first = transition_reflection_workflow(
        "REF-2026-0001", "package_building", actor="Chief Architect",
        evidence={"work_package": "WP-0711"}, event_id="package-started",
        next_action="build_continuity_package", artifacts={"request": "request.json"},
        root=tmp_path,
    )
    second = transition_reflection_workflow(
        "REF-2026-0001", "package_building", actor="Chief Architect",
        evidence={"work_package": "WP-0711"}, event_id="package-started",
        next_action="ignored_on_replay", root=tmp_path,
    )
    assert first == second
    assert first["state"] == "package_building"
    assert first["artifacts"]["request"] == "request.json"
    assert len(first["history"]) == 2


def test_conflicting_event_id_is_rejected(tmp_path):
    _create_direct(tmp_path)
    transition_reflection_workflow(
        "REF-2026-0001", "package_building", actor="Chief Architect",
        evidence={"work_package": "WP-0711"}, event_id="same-id",
        next_action="build", root=tmp_path,
    )
    with pytest.raises(ValueError, match="conflicting event_id reuse"):
        transition_reflection_workflow(
            "REF-2026-0001", "package_ready_for_review", actor="Chief Architect",
            evidence={"validation": "passed"}, event_id="same-id",
            next_action="request_review", root=tmp_path,
        )


def test_invalid_transition_and_protected_state_are_rejected(tmp_path):
    _create_direct(tmp_path)
    with pytest.raises(ValueError, match="invalid reflection transition"):
        transition_reflection_workflow(
            "REF-2026-0001", "renewal_confirmed", actor="Helen",
            evidence={"receipt": "x"}, event_id="skip", next_action="retire",
            root=tmp_path,
        )

    evaluation = create_reflection_workflow(
        run_id="REF-3", office="Architect", officeholder="Architect",
        current_implementation="Architect 1", mailbox_id="1",
        initiation_type="evaluation", authority_reference="request",
        actor="Helen", root=tmp_path,
    )
    assert evaluation["state"] == "evaluation_requested"
    transition_reflection_workflow(
        "REF-3", "assessment_in_progress", actor="Worker",
        evidence={"request": "accepted"}, event_id="assessment",
        next_action="assess", root=tmp_path,
    )
    transition_reflection_workflow(
        "REF-3", "reflection_recommended", actor="Worker",
        evidence={"result": "recommend"}, event_id="recommend",
        next_action="authorize", root=tmp_path,
    )
    with pytest.raises(PermissionError):
        transition_reflection_workflow(
            "REF-3", "reflection_authorized", actor="Worker",
            evidence={"approval": "claimed"}, event_id="authorize",
            next_action="build", root=tmp_path,
        )


def test_conflicting_create_is_rejected(tmp_path):
    _create_direct(tmp_path)
    with pytest.raises(ValueError, match="conflicting workflow already exists"):
        create_reflection_workflow(
            run_id="REF-2026-0001", office="Different Office",
            officeholder="Chief Architect", current_implementation="Chief Architect 5",
            mailbox_id="5", initiation_type="direct_reflection",
            authority_reference="Steward directive 2026-07-18", actor="Steward",
            root=tmp_path,
        )
