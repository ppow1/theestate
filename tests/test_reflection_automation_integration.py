from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PL0030 = ROOT / "operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md"
PROCESS = ROOT / "docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md"
HINTS = ROOT / "AI_REFLECTION_HINTS.md"
TEMPLATE = ROOT / "docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md"


def test_reflection_automation_governing_documents_are_complete_and_linked() -> None:
    documents = (PL0030, PROCESS, HINTS, TEMPLATE)
    for document in documents:
        assert document.is_file(), document
        assert document.read_text(encoding="utf-8").strip(), document

    pl0030 = PL0030.read_text(encoding="utf-8")
    process = PROCESS.read_text(encoding="utf-8")
    hints = HINTS.read_text(encoding="utf-8")

    assert "Approved design; automation not implemented" in pl0030
    assert "manual process is the authority and judgment framework" in pl0030
    assert "Evaluation request" in pl0030
    assert "Direct reflection directive" in pl0030
    assert "Mandatory Helen review" in pl0030
    assert "Manual fallback" in pl0030
    assert "Failure, retry, versioning, and idempotency" in pl0030
    assert "Durable audit trail" in pl0030
    assert "does not establish that an orchestrator" in process
    assert "does not prove that orchestration" in hints


def test_reflection_lifecycle_and_authority_boundaries_are_explicit() -> None:
    pl0030 = PL0030.read_text(encoding="utf-8")
    required_states = (
        "evaluation_requested",
        "assessment_in_progress",
        "reflection_recommended",
        "reflection_authorized",
        "package_building",
        "package_validation_failed",
        "package_ready_for_review",
        "helen_review_required",
        "approved_for_onboarding",
        "onboarding_in_progress",
        "first_assignment_in_progress",
        "renewal_confirmed",
        "previous_implementation_retired",
        "manual_fallback_active",
        "renewal_blocked",
    )
    for state in required_states:
        assert f"`{state}`" in pl0030, state

    assert "Steward | Final institutional authority" in pl0030
    assert "alone approves progression into renewed onboarding" in pl0030
    assert "Grace |" in pl0030 and "cannot warrant reflection" in pl0030
    assert "cannot assess, authorize, approve, accept, or retire" in pl0030
    assert "prior implementation and evidence remain available read-only" in pl0030
