from pathlib import Path

import pytest

from evelyn_relationship_runtime import ContinuityRecord, EvelynRelationshipRuntime, RelationshipTurn


def runtime(tmp_path: Path) -> EvelynRelationshipRuntime:
    return EvelynRelationshipRuntime(tmp_path, now="2026-07-12T00:00:00+00:00")


def test_sensitive_continuity_requires_steward_approval_before_private_context(tmp_path: Path):
    rt = runtime(tmp_path)
    row = rt.propose_record(ContinuityRecord("rec-1", "sensitive_item", "Pat's private concern", evidence_refs=("conversation:1",)))
    assert row["retention_state"] == "pending_steward_review"
    assert "Pat's private concern" not in row["summary"]
    assert rt.build_context(audience="pat")["records"] == []

    approved = rt.approve_record("rec-1", authority="Steward-approved")
    assert approved["retention_state"] == "approved"
    assert rt.build_context(audience="pat")["records"][0]["record_id"] == "rec-1"


def test_relationship_layer_is_denied_to_office_residents_and_global_search(tmp_path: Path):
    rt = runtime(tmp_path)
    rt.propose_record(ContinuityRecord("rec-2", "relationship_norm", "Quiet evenings matter.", approved_by="Steward-approved"))
    rt.approve_record("rec-2", authority="Steward-approved")

    for audience in ("alfred", "helen", "grace", "office", "global_search"):
        context = rt.build_context(audience=audience)
        assert context["records"] == []
        assert context["private_content_exposed"] is False
        assert context["denied_reason"] == "audience is outside the Steward Relationship Layer"

    audit_context = rt.build_context(audience="ingrid_audit")
    assert audit_context["records"][0]["content_digest"].startswith("sha256:")
    assert "summary" not in audit_context["records"][0]


def test_forget_removes_active_memory_but_preserves_audit(tmp_path: Path):
    rt = runtime(tmp_path)
    rt.propose_record(ContinuityRecord("rec-3", "relationship_norm", "Retain only if asked.", approved_by="Steward-approved"))
    rt.approve_record("rec-3", authority="Steward-approved")
    forgotten = rt.forget_record("rec-3", authority="Pat", reason="no longer wanted")

    assert forgotten["retention_state"] == "forgotten"
    assert forgotten["evidence_refs"] == []
    assert rt.build_context(audience="pat")["records"] == []
    assert rt.diagnostics()["audit_events"] == 3


def test_turn_evaluation_modes_retention_review_and_authority_boundary(tmp_path: Path):
    rt = runtime(tmp_path)
    counsel = rt.evaluate_turn(RelationshipTurn("Be honest and challenge me on this", requested_action="approve"))
    assert counsel["active_mode"] == "candid_counsel"
    assert counsel["authority"]["blocked"] is True
    assert counsel["authority"]["can_execute_institutional_action"] is False

    recovery = rt.evaluate_turn(RelationshipTurn("I'm exhausted. Remember this is private."))
    assert recovery["active_mode"] == "recovery"
    assert recovery["retention_review"]["retention_allowed_now"] is False
    assert recovery["retention_review"]["requires_steward_approval"] is True


def test_invalid_approval_authority_is_rejected(tmp_path: Path):
    rt = runtime(tmp_path)
    rt.propose_record(ContinuityRecord("rec-4", "sensitive_item", "private"))
    with pytest.raises(PermissionError):
        rt.approve_record("rec-4", authority="Helen-approved")
    with pytest.raises(PermissionError):
        rt.forget_record("rec-4", authority="Alfred", reason="wrong audience")
