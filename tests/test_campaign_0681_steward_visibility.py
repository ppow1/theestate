from estate.core.steward_dashboard import build_operational_visibility

NOW = "2026-07-18T12:00:00Z"


def viewer(role="steward", classes=None):
    return {"role": role, "identity_evidence": ["data/registry/personnel.json"], "allowed_classifications": classes or ["Estate Internal"]}


def signal(signal_id, state, **extra):
    value = {"signal_id": signal_id, "domain": "campaign", "title": signal_id, "summary": f"{state} summary", "state": state, "freshness": "current", "confidence": "high", "observed_at": NOW, "owner": "Operations", "classification": "Estate Internal", "evidence_references": [f"evidence/{signal_id}.json"], "warnings": []}
    value.update(extra)
    return value


def test_highest_priority_constraints_and_all_required_states_are_visible():
    states = ["ready", "active", "blocked", "degraded", "failed", "protected", "stale"]
    signals = [signal(state, state, protected_decision=state == "protected", requested_authority="Steward" if state == "protected" else None, decision_question="Release?" if state == "protected" else None) for state in states]
    result = build_operational_visibility(signals, viewer=viewer(), generated_at=NOW)
    assert result["signals"][0]["state"] == "failed"
    assert set(result["summary"]["by_state"]) >= set(states)
    assert result["protected_decisions"][0]["protected_decision"]["requested_authority"] == "Steward"


def test_every_status_has_drill_through_and_stale_conflicting_missing_is_explicit():
    result = build_operational_visibility([signal("stale", "stale", warnings=["expired"]), signal("conflict", "indeterminate", warnings=["conflicting evidence"]), signal("missing", "ready", evidence_references=[])], viewer=viewer(), generated_at=NOW)
    assert all(item["state"] in {"stale", "indeterminate"} for item in result["signals"])
    assert result["warnings"]
    assert result["authorizes_action"] is False


def test_role_aware_redaction_preserves_reference_without_details():
    result = build_operational_visibility([signal("private", "blocked", classification="Restricted", title="Secret", summary="Private detail")], viewer=viewer(), generated_at=NOW)
    item = result["signals"][0]
    assert item["redacted"] is True
    assert item["title"] == "Restricted operational item"
    assert item["evidence_references"] == ["evidence/private.json"]


def test_controls_require_explicit_viewer_role_and_authorization():
    controls = [
        {"label": "Review", "action_class": "recommendation", "authorized": True, "allowed_roles": ["steward"], "authority_reference": "authority/steward.md"},
        {"label": "Deploy", "action_class": "deployment", "authorized": False, "allowed_roles": ["steward"], "authority_reference": None},
    ]
    steward = build_operational_visibility([signal("one", "ready", controls=controls)], viewer=viewer(), generated_at=NOW)
    office = build_operational_visibility([signal("one", "ready", controls=controls)], viewer=viewer("grace"), generated_at=NOW)
    assert [item["label"] for item in steward["signals"][0]["controls"]] == ["Review"]
    assert office["signals"][0]["controls"] == []


def test_protected_decision_requires_question_and_authority():
    result = build_operational_visibility([signal("decision", "protected", protected_decision=True)], viewer=viewer(), generated_at=NOW)
    assert result["signals"][0]["state"] == "indeterminate"
    assert "lacks requested authority" in " ".join(result["warnings"])


def test_bounded_view_is_deterministic_accessible_and_reports_truncation():
    signals = [signal(f"item-{index:03}", "ready") for index in range(20)]
    result = build_operational_visibility(reversed(signals), viewer=viewer(), generated_at=NOW, max_items=5)
    assert [item["signal_id"] for item in result["signals"]] == [f"item-{index:03}" for index in range(5)]
    assert result["summary"]["truncated"] is True
    assert result["accessibility"]["status_not_color_only"] is True
