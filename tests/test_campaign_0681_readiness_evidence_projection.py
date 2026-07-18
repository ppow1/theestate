from copy import deepcopy

from estate.core.readiness_evidence_projection import project_readiness_evidence

NOW = "2026-07-18T12:00:00Z"


def ev(subject, state, kind="validation_result", evidence_id=None, **extra):
    value = {
        "subject_id": subject, "state": state, "source_kind": kind,
        "evidence_id": evidence_id or f"{subject}-{state}-{kind}",
        "reference": f"evidence/{subject}-{state}.json", "issued_at": NOW,
    }
    value.update(extra)
    return value


def states(result):
    return {item["subject_id"]: item["readiness_state"] for item in result["subjects"]}


def test_shared_vocabulary_and_protected_acceptance_attribution():
    result = project_readiness_evidence([
        ev("A", "validating"), ev("B", "ready"),
        ev("C", "accepted", "protected_acceptance", authority="Chief Architect"),
        ev("D", "rejected", "protected_rejection", authority="Chief Architect"),
    ], subjects=["E"], observed_at=NOW)
    assert states(result) == {"A": "validating", "B": "ready", "C": "accepted", "D": "rejected", "E": "unverified"}
    assert result["subjects"][2]["acceptance_authority"] == "Chief Architect"
    assert result["authorizes_action"] is False


def test_optimistic_acceptance_claim_is_only_ready():
    result = project_readiness_evidence([ev("A", "accepted", "approval_record", authority="Reviewer")], observed_at=NOW)
    assert states(result)["A"] == "ready"
    assert result["subjects"][0]["acceptance_authority"] is None


def test_partial_dependencies_cannot_become_ready_or_accepted():
    evidence = [
        ev("A", "accepted", "protected_acceptance", authority="Chief Architect"),
        ev("B", "ready"),
    ]
    result = project_readiness_evidence(evidence, dependencies={"B": ["A", "C"]}, observed_at=NOW)
    assert states(result)["B"] == "partially_evidenced"
    assert result["aggregate_readiness"] == "partially_evidenced"


def test_stale_conflicting_inaccessible_and_missing_evidence_fail_closed():
    missing_identity = ev("D", "ready")
    missing_identity["evidence_id"] = ""
    result = project_readiness_evidence([
        ev("A", "ready", issued_at="2026-07-16T00:00:00Z"),
        ev("B", "ready", evidence_id="b1"), ev("B", "rejected", evidence_id="b2"),
        ev("C", "ready", inaccessible=True),
        missing_identity,
    ], observed_at=NOW)
    assert states(result) == {"A": "stale", "B": "indeterminate", "C": "indeterminate", "D": "indeterminate"}
    assert result["aggregate_readiness"] == "indeterminate"


def test_supersession_retains_lineage_and_uses_current_record():
    old = ev("A", "rejected", evidence_id="old")
    new = ev("A", "ready", evidence_id="new", supersedes="old")
    result = project_readiness_evidence([old, new], observed_at=NOW)
    item = result["subjects"][0]
    assert item["readiness_state"] == "ready"
    assert len(item["evidence_lineage"]) == 2
    assert next(x for x in item["evidence_lineage"] if x["evidence_id"] == "old")["superseded"] is True


def test_conflicting_evidence_identity_and_input_mutation_are_refused():
    evidence = [ev("A", "ready", evidence_id="same"), ev("A", "rejected", evidence_id="same")]
    before = deepcopy(evidence)
    result = project_readiness_evidence(evidence, observed_at=NOW)
    assert states(result)["A"] == "indeterminate"
    assert "conflicting content" in " ".join(result["warnings"])
    assert evidence == before
