import json

import pytest

from estate.core.helen_workforce import HelenWorkforceStore


def blocker(blocker_class="staffing_or_capability_blocker", *, protected=False, evidence=True):
    return {
        "blocker_class": blocker_class,
        "canonical_evidence_references": ["evidence/WP-0695-blocker.json"] if evidence else [],
        "protected_decision": protected,
        "authorizes_action": False,
    }


def create_request(store, **overrides):
    values = {
        "campaign_id": "CAMPAIGN-0681",
        "package_id": "WP-0695",
        "need_kind": "capability",
        "required_role": "bounded Engineering validator",
        "required_capabilities": ["python-testing", "powershell-validation"],
        "urgency": "high",
        "duration": "one bounded package",
        "constraints": ["workspace-write"],
    }
    values.update(overrides)
    return store.create_operational_request(blocker(), **values)


def test_operational_blocker_enters_existing_helen_workforce_lane(tmp_path):
    store = HelenWorkforceStore(tmp_path)
    request, path = create_request(store)
    recorded = json.loads(path.read_text(encoding="utf-8"))

    assert path.parent.name == "requests"
    assert request.request_type == "staffing_request"
    assert recorded["metadata"]["need_kind"] == "capability"
    assert recorded["metadata"]["request_is_fulfillment"] is False
    assert recorded["metadata"]["engineering_priority_authority_granted"] is False
    assert recorded["metadata"]["acceptance_authority_granted"] is False
    assert (tmp_path / "runtime/workforce_development/status/latest.json").exists()


def test_fulfilled_and_partial_dispositions_require_helen_and_authority(tmp_path):
    store = HelenWorkforceStore(tmp_path)
    request, _ = create_request(store)

    with pytest.raises(ValueError, match="only Helen"):
        store.record_operational_disposition(
            request.request_id,
            disposition="fulfilled",
            decided_by="Grace",
            evidence_references=["evidence/candidate.json"],
            fulfilled_capabilities=["python-testing"],
            authority_evidence=["authority/helen-workforce-lane.md"],
            reason="Grace cannot fulfill staffing.",
        )

    payload, path = store.record_operational_disposition(
        request.request_id,
        disposition="partially_fulfilled",
        decided_by="Helen",
        evidence_references=["evidence/candidate.json"],
        fulfilled_capabilities=["python-testing"],
        authority_evidence=["authority/helen-workforce-lane.md"],
        reason="One capability is evidenced; PowerShell validation remains open.",
    )
    assert path.parent.name == "operational_dispositions"
    assert payload["remaining_need"] == ["powershell-validation"]
    assert payload["staff_assignment_performed"] is False
    assert store.load_request(request.request_id).status == "ready_for_action"


@pytest.mark.parametrize(
    ("disposition", "expected_status", "expires_at"),
    [
        ("refused", "declined", None),
        ("deferred", "blocked", None),
        ("expired", "blocked", "2026-07-19T00:00:00+00:00"),
    ],
)
def test_nonfulfillment_dispositions_remain_truthful(tmp_path, disposition, expected_status, expires_at):
    store = HelenWorkforceStore(tmp_path)
    request, _ = create_request(store)
    payload, _ = store.record_operational_disposition(
        request.request_id,
        disposition=disposition,
        decided_by="Helen",
        evidence_references=[f"evidence/{disposition}.json"],
        reason=f"Request was {disposition}.",
        expires_at=expires_at,
    )
    assert payload["remaining_need"] == ["powershell-validation", "python-testing"]
    assert payload["provider_execution_performed"] is False
    assert store.load_request(request.request_id).status == expected_status


def test_protected_constraints_block_fulfillment_and_require_review(tmp_path):
    store = HelenWorkforceStore(tmp_path)
    request, _ = create_request(store, constraints=["budget", "privacy"])
    assert request.status == "blocked"
    assert request.requires_steward_attention is True
    assert request.requires_boundary_review is True

    with pytest.raises(ValueError, match="protected constraints"):
        store.record_operational_disposition(
            request.request_id,
            disposition="fulfilled",
            decided_by="Helen",
            evidence_references=["evidence/candidate.json"],
            fulfilled_capabilities=["python-testing", "powershell-validation"],
            authority_evidence=["authority/helen-workforce-lane.md"],
            reason="Protected constraints are unresolved.",
        )
    payload, _ = store.record_operational_disposition(
        request.request_id,
        disposition="protected_review_required",
        decided_by="Helen",
        evidence_references=["evidence/protected-constraints.json"],
        reason="Budget and privacy decisions remain protected.",
    )
    assert payload["requires_protected_review"] is True
    assert payload["staff_assignment_performed"] is False


def test_unqualified_or_unevidenced_blockers_fail_closed(tmp_path):
    store = HelenWorkforceStore(tmp_path)
    with pytest.raises(ValueError, match="not a staffing"):
        store.create_operational_request(
            blocker("dependency_blocker"),
            campaign_id="CAMPAIGN-0681",
            package_id="WP-0695",
            need_kind="staffing",
            required_role="Engineer",
            required_capabilities=["python"],
            urgency="normal",
            duration="bounded",
        )
    with pytest.raises(ValueError, match="canonical blocker evidence"):
        store.create_operational_request(
            blocker(evidence=False),
            campaign_id="CAMPAIGN-0681",
            package_id="WP-0695",
            need_kind="staffing",
            required_role="Engineer",
            required_capabilities=["python"],
            urgency="normal",
            duration="bounded",
        )
