from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wp4023_delegation_runtime.runtime import (  # noqa: E402
    ACCEPTED,
    COMPLETED,
    DECLINED,
    REJECTED,
    REQUESTED,
    STALLED,
    TRANSFERRED,
    AuthorityMetadata,
    EvidenceItem,
    request_delegation,
    transition_delegation,
)


def authority(**overrides):
    values = {
        "source_authority": "assignment:WP-4023:active-runtime",
        "approved_by": "Steward",
        "approval_reference": "approval://wp-4023/local-test",
        "can_request": True,
        "can_accept": True,
        "can_transfer_ownership": True,
        "can_complete": True,
    }
    values.update(overrides)
    return AuthorityMetadata(**values)


def requested_record():
    return request_delegation(
        delegation_id="DEL-4023-001",
        work_item_id="WP-4023",
        requester="Alfred",
        recipient="Helen",
        prerequisites=["active assignment remains visible"],
        completion_criteria=["handoff receipt preserves evidence"],
        authority=authority(),
        evidence=[EvidenceItem("work_package", "collaboration/work_packages/pending/WP-4023_Resident_Work_Delegation_and_Handoff_Runtime.md")],
        idempotency_key="request-1",
    )


def test_request_does_not_transfer_ownership_and_is_visible():
    record = requested_record()
    payload = record.as_dict()
    assert record.state == REQUESTED
    assert record.owner == "Alfred"
    assert payload["visible"] is True
    assert payload["completion_criteria"] == ["handoff receipt preserves evidence"]


def test_accept_then_authorized_transfer_changes_owner_once():
    record = requested_record()
    accepted = transition_delegation(record, target_state=ACCEPTED, actor="Helen", authority=authority(), reason="recipient accepts", idempotency_key="accept-1")
    transferred = transition_delegation(accepted, target_state=TRANSFERRED, actor="Alfred", authority=authority(), reason="approved owner transfer", idempotency_key="transfer-1")
    retry = transition_delegation(transferred, target_state=TRANSFERRED, actor="Alfred", authority=authority(), reason="retry", idempotency_key="transfer-1")
    assert accepted.owner == "Alfred"
    assert transferred.owner == "Helen"
    assert retry is transferred
    assert len(retry.history) == 3


def test_ownership_cannot_change_without_authorized_transition():
    record = requested_record()
    accepted = transition_delegation(record, target_state=ACCEPTED, actor="Helen", authority=authority(), reason="recipient accepts", idempotency_key="accept-1")
    try:
        transition_delegation(accepted, target_state=TRANSFERRED, actor="Alfred", authority=authority(can_transfer_ownership=False), reason="missing approval", idempotency_key="transfer-denied")
    except ValueError as exc:
        assert "ownership transfer is not authorized" in str(exc)
    else:
        raise AssertionError("ownership transfer should require authority")


def test_decline_reject_and_stall_are_deterministic_visible_states():
    declined = transition_delegation(requested_record(), target_state=DECLINED, actor="Helen", authority=authority(), reason="capacity limit", idempotency_key="decline-1")
    assert declined.state == DECLINED
    stalled = transition_delegation(requested_record(), target_state=STALLED, actor="Alfred", authority=authority(), reason="waiting for prerequisite", idempotency_key="stall-1")
    assert stalled.as_dict()["visible"] is True
    rejected = transition_delegation(requested_record(), target_state=REJECTED, actor="Dispatch", authority=authority(), reason="invalid source approval", idempotency_key="reject-1")
    assert rejected.as_dict()["visible"] is True


def test_completion_receipt_preserves_evidence_and_provenance():
    record = requested_record()
    accepted = transition_delegation(record, target_state=ACCEPTED, actor="Helen", authority=authority(), reason="recipient accepts", idempotency_key="accept-1")
    transferred = transition_delegation(accepted, target_state=TRANSFERRED, actor="Alfred", authority=authority(), reason="approved owner transfer", idempotency_key="transfer-1")
    completed = transition_delegation(
        transferred,
        target_state=COMPLETED,
        actor="Helen",
        authority=authority(source_authority="dispatch:handoff-approved"),
        reason="criteria met",
        evidence=[EvidenceItem("audit", "audit://DEL-4023-001", provenance={"mailbox_message": "mail://handoff"})],
        idempotency_key="complete-1",
    )
    assert completed.state == COMPLETED
    assert completed.receipts[0]["provenance"]["delegation_id"] == "DEL-4023-001"
    assert completed.receipts[0]["provenance"]["source_authority"] == "dispatch:handoff-approved"
    assert len(completed.receipts[0]["evidence"]) == 2
