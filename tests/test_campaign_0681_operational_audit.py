import json

import pytest

from estate.core.autonomous_operations_audit import (
    append_operational_audit_event, explain_operational_history,
    query_operational_audit, read_audit_records, reconstruct_operational_history,
)


def event(event_id, kind="recommendation", **extra):
    value = {
        "event_id": event_id, "event_kind": kind, "occurred_at": "2026-07-18T12:00:00Z",
        "correlations": {"campaign_id": "CAMPAIGN-0681", "work_package_id": "WP-0702", "cycle_id": "cycle-1"},
        "source_evidence": ["collaboration/evidence/state.json"], "freshness": "current",
        "confidence": "high", "policy_disposition": "allow", "authority": {"required": False, "references": []},
        "outcome": "recommended", "uncertainty": [],
    }
    value.update(extra)
    return value


def test_append_query_and_correlation_reconstruct_complete_history(tmp_path):
    append_operational_audit_event(event("observed", "observed_fact", outcome="observed"), root=tmp_path)
    append_operational_audit_event(event("recommendation"), root=tmp_path)
    records = query_operational_audit(root=tmp_path, campaign_id="CAMPAIGN-0681")
    assert [record["event_id"] for record in records] == ["observed", "recommendation"]
    history = reconstruct_operational_history(root=tmp_path, cycle_id="cycle-1")
    assert len(history["events"]) == 2
    assert history["generated_explanation_is_authoritative"] is False


def test_correction_is_append_only_and_preserves_original(tmp_path):
    append_operational_audit_event(event("original", outcome="deferred", uncertainty=["missing validation"]), root=tmp_path)
    append_operational_audit_event(event("correction", "correction", outcome="validation supplied", corrects_event_id="original", supersedes_event_id="original"), root=tmp_path)
    records = read_audit_records(tmp_path)
    assert len(records) == 2
    assert records[0]["event_id"] == "original"
    history = reconstruct_operational_history(root=tmp_path, campaign_id="CAMPAIGN-0681")
    assert history["corrected_event_ids"] == ["original"]
    assert "later corrected" in explain_operational_history(history)


def test_partial_and_conflicting_history_keeps_uncertainty_visible(tmp_path):
    append_operational_audit_event(event("partial", freshness="unknown", confidence="low", policy_disposition="escalate", outcome="held", uncertainty=["conflicting authority"]), root=tmp_path)
    history = reconstruct_operational_history(root=tmp_path, work_package_id="WP-0702")
    assert history["missing_evidence_visible"] is True
    assert "conflicting authority" in explain_operational_history(history)


def test_authorized_action_identifies_policy_authority_and_outcome(tmp_path):
    record = append_operational_audit_event(event("action", "action", policy_disposition="allow", authority={"required": True, "references": ["authority/delegation.json"]}, outcome="completed", source_evidence=["cycle.json", "dispatch/result.json"]), root=tmp_path)
    assert record["authority"]["references"] == ["authority/delegation.json"]
    assert record["generated_explanation_is_authoritative"] is False


def test_duplicate_missing_correction_target_and_restricted_payload_refused(tmp_path):
    append_operational_audit_event(event("one"), root=tmp_path)
    with pytest.raises(ValueError, match="already exists"):
        append_operational_audit_event(event("one"), root=tmp_path)
    with pytest.raises(ValueError, match="existing event_id"):
        append_operational_audit_event(event("bad-correction", "correction", corrects_event_id="missing"), root=tmp_path)
    with pytest.raises(ValueError, match="restricted or personal"):
        append_operational_audit_event(event("private", personal_data={"name": "redacted"}), root=tmp_path)


def test_jsonl_remains_machine_readable_and_empty_explanation_is_truthful(tmp_path):
    append_operational_audit_event(event("one"), root=tmp_path)
    lines = (tmp_path / "audit/autonomy/autonomous_operations_audit.jsonl").read_text().splitlines()
    assert json.loads(lines[0])["record_type"] == "operational_audit_event"
    empty = reconstruct_operational_history(root=tmp_path, campaign_id="OTHER")
    assert "cannot be reconstructed" in explain_operational_history(empty)
