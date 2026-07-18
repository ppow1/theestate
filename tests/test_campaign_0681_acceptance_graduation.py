from estate.core.readiness_evidence_projection import assess_operational_graduation, draft_campaign_closeout


def capability(**extra):
    evidence = {key: [f"evidence/{key}.json"] for key in ["validation", "operating_procedure", "ownership", "support", "recovery", "observability", "audit", "authority_record"]}
    value = {"capability_id": "momentum-engine", "accepting_authority": "Chief Architect", "evidence": evidence, "residual_risks": [], "accepted_exceptions": [], "deferred_scope": [], "successor_work_packages": []}
    value.update(extra)
    return value


def test_complete_bundle_is_ready_but_not_accepted_or_graduated():
    result = assess_operational_graduation([capability()], campaign_id="CAMPAIGN-0681")
    item = result["capabilities"][0]
    assert item["operational_state"] == "ready_for_protected_acceptance"
    assert item["accepted"] is False
    assert item["graduated"] is False
    assert result["institutional_acceptance_granted"] is False


def test_missing_evidence_and_wrong_acceptance_authority_fail_closed():
    incomplete = capability()
    incomplete["evidence"]["recovery"] = []
    incomplete["protected_acceptance_reference"] = "acceptance/wrong.json"
    incomplete["acceptance_issuer"] = "Steward"
    item = assess_operational_graduation([incomplete], campaign_id="CAMPAIGN-0681")["capabilities"][0]
    assert item["operational_state"] == "evidence_incomplete"
    assert "recovery" in item["missing_evidence"]
    assert item["accepted"] is False


def test_matching_protected_acceptance_can_be_observed_but_not_created():
    accepted = capability(protected_acceptance_reference="acceptance/ca.json", acceptance_issuer="Chief Architect")
    result = assess_operational_graduation([accepted], campaign_id="CAMPAIGN-0681")
    assert result["capabilities"][0]["accepted"] is True
    assert result["ready_for_campaign_acceptance_review"] is True
    assert result["authorizes_action"] is False


def test_conditional_exception_and_deferred_scope_require_authority_and_successor():
    item = capability(accepted_exceptions=[{"risk": "limited observation"}], deferred_scope=["long-term tuning"])
    result = assess_operational_graduation([item], campaign_id="CAMPAIGN-0681")["capabilities"][0]
    assert result["operational_state"] == "evidence_incomplete"
    assert any("exception" in risk for risk in result["residual_risks"])
    assert any("successor" in risk for risk in result["residual_risks"])


def test_closeout_preserves_obligations_and_stays_blocked_without_acceptance():
    item = capability(residual_risks=["monitor retry behavior"], deferred_scope=["future tuning"], successor_work_packages=["WP-NEXT"])
    assessment = assess_operational_graduation([item], campaign_id="CAMPAIGN-0681")
    closeout = draft_campaign_closeout(assessment)
    assert closeout["final_status"] == "awaiting_protected_acceptance"
    assert closeout["closeout_blocked"] is True
    assert closeout["campaign_closed"] is False
    assert {entry["kind"] for entry in closeout["unresolved_obligations"]} == {"residual_risk", "deferred_scope", "protected_acceptance_pending"}


def test_even_observed_steward_acceptance_requires_manual_closeout():
    accepted = capability(protected_acceptance_reference="acceptance/ca.json", acceptance_issuer="Chief Architect")
    assessment = assess_operational_graduation([accepted], campaign_id="CAMPAIGN-0681")
    closeout = draft_campaign_closeout(assessment, campaign_acceptance_reference="acceptance/steward.json", campaign_acceptance_authority="Steward")
    assert closeout["campaign_acceptance_verified"] is True
    assert closeout["final_status"] == "accepted_awaiting_manual_closeout"
    assert closeout["campaign_closed"] is False
    assert closeout["requires_manual_closeout_authority"] is True
