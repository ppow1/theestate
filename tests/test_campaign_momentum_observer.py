import json
from copy import deepcopy

from estate.core.campaign_momentum_observer import observe_campaign, render_momentum_markdown

NOW = "2026-07-17T12:00:00Z"


def campaign(tmp_path, packages, status="launch_authorized"):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "campaign_id": "CAMPAIGN-TEST", "status": status,
        "authoritative_campaign_path": "campaign.md", "packages": packages,
    }))
    (tmp_path / "campaign.md").write_text("canonical")
    return path


def package(pid, deps=(), parallel=None, gate="G1"):
    return {"id": pid, "path": f"packages/{pid}.md", "receipt_path": f"receipts/{pid}.md",
            "depends_on": list(deps), "parallel_group": parallel, "gate": gate}


def ev(pid, state, reference=None, source="canonical_artifact", **extra):
    value = {"package_id": pid, "state": state, "source_kind": source,
             "reference": reference or f"evidence/{pid}-{state}.json", "effective_at": NOW}
    value.update(extra)
    return value


def states(result):
    return {item["package_id"]: item["observed_state"] for item in result["packages"]}


def test_sequential_campaign_and_remaining_eligible_work(tmp_path):
    path = campaign(tmp_path, [package("A"), package("B", ["A"]), package("C", ["B"])])
    result = observe_campaign(tmp_path, path, evidence=[ev("A", "accepted")], observed_at=NOW)
    assert states(result) == {"A": "accepted_closed", "B": "eligible", "C": "waiting"}
    assert result["eligible_packages"] == ["B"]
    assert result["observation_only"] is True


def test_parallel_group_does_not_invent_serial_edges(tmp_path):
    path = campaign(tmp_path, [package("A", parallel="PG-1"), package("B", parallel="PG-1")])
    result = observe_campaign(tmp_path, path, observed_at=NOW)
    assert result["eligible_packages"] == ["A", "B"]
    assert all(item["parallel_group"] == "PG-1" for item in result["packages"])


def test_unmet_dependency_overrides_optimistic_progress(tmp_path):
    path = campaign(tmp_path, [package("A"), package("B", ["A"])])
    result = observe_campaign(tmp_path, path, evidence=[ev("B", "active")], observed_at=NOW)
    assert states(result)["B"] == "indeterminate"
    assert "conflicts" in " ".join(result["packages"][1]["warnings"])


def test_completion_is_not_acceptance_and_receipt_discovery_is_bounded(tmp_path):
    path = campaign(tmp_path, [package("A")])
    (tmp_path / "receipts").mkdir()
    (tmp_path / "receipts/A.md").write_text("completion receipt")
    result = observe_campaign(tmp_path, path, observed_at=NOW)
    assert states(result)["A"] == "complete_pending_acceptance"
    assert result["protected_decisions"] == ["A"]


def test_failed_validation_outranks_optimistic_runtime_progress(tmp_path):
    path = campaign(tmp_path, [package("A")])
    evidence = [ev("A", "active", source="runtime_claim"),
                ev("A", "failed", source="schema_valid_receipt", reason="Validation failed")]
    result = observe_campaign(tmp_path, path, evidence=evidence, observed_at=NOW)
    assert states(result)["A"] == "failed"
    assert result["campaign_momentum_state"] == "failed"


def test_protected_gate_halts_continuation(tmp_path):
    path = campaign(tmp_path, [package("A"), package("B", ["A"])])
    result = observe_campaign(tmp_path, path, evidence=[ev("A", "protected")], observed_at=NOW)
    assert states(result) == {"A": "protected_gated", "B": "waiting"}
    assert result["protected_decisions"] == ["A"]


def test_stale_and_contradictory_evidence_fail_closed(tmp_path):
    path = campaign(tmp_path, [package("A"), package("B")])
    evidence = [ev("A", "active", expires_at="2026-07-17T11:00:00Z"),
                ev("B", "active", reference="one"), ev("B", "failed", reference="two")]
    result = observe_campaign(tmp_path, path, evidence=evidence, observed_at=NOW)
    assert states(result) == {"A": "indeterminate", "B": "indeterminate"}
    assert len(result["warnings"]) == 2


def test_paused_campaign_is_stable_and_normalized_output_is_deterministic(tmp_path):
    path = campaign(tmp_path, [package("A")])
    evidence = [ev("A", "paused")]
    before = deepcopy(evidence)
    first = observe_campaign(tmp_path, path, evidence=evidence, observed_at=NOW)
    second = observe_campaign(tmp_path, path, evidence=evidence, observed_at=NOW)
    assert first == second
    assert first["campaign_momentum_state"] == "paused"
    assert evidence == before


def test_review_degraded_blocked_and_human_view(tmp_path):
    path = campaign(tmp_path, [package("A"), package("B"), package("C")])
    evidence = [ev("A", "review_required"), ev("B", "degraded"),
                ev("C", "blocked", blocker_type="staffing", follow_up_destination="Helen")]
    result = observe_campaign(tmp_path, path, evidence=evidence, observed_at=NOW)
    assert states(result) == {"A": "review_gated", "B": "degraded", "C": "blocked"}
    assert result["packages"][2]["recommended_follow_up_destination"] == "Helen"
    rendered = render_momentum_markdown(result)
    assert "| A | review_gated |" in rendered
    assert "does not dispatch" in rendered


def test_unknown_dependency_and_missing_reference_are_indeterminate(tmp_path):
    path = campaign(tmp_path, [package("A", ["MISSING"]), package("B")])
    missing_ref = ev("B", "active")
    missing_ref["reference"] = ""
    result = observe_campaign(tmp_path, path, evidence=[missing_ref], observed_at=NOW)
    assert states(result) == {"A": "indeterminate", "B": "indeterminate"}
    assert result["recommended_follow_up_destination"] == "Chief Architect"
