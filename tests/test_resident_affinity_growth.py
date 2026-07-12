import json
from pathlib import Path

from estate.core.resident_affinity_growth import (
    append_experience,
    adjust_confidence,
    evaluate_friendship_mentorship,
    list_experiences,
    migrate_affinity_graph,
    present_affinity,
    propose_milestone,
    propose_skill_growth,
    propose_support_response,
    record_trust_evidence,
    refine_preference,
    set_affinity_dimension,
    save_affinity_graph,
    validate_affinity_growth_runtime,
)


def write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_affinity_migration_is_directional_private_and_authority_neutral(tmp_path):
    write(tmp_path / "data/relationships/resident_relationships.json", {"relationships": [{"source": "RES-A", "target": "RES-B", "familiarity": 50}]})
    graph = migrate_affinity_graph(tmp_path)
    set_affinity_dimension(graph, "RES-A", "RES-B", "respect", 0.7, confidence=0.8, evidence_refs=["review.md"])
    set_affinity_dimension(graph, "RES-B", "RES-A", "warmth", 0.1, confidence=0.8, evidence_refs=["review.md"])
    set_affinity_dimension(graph, "RES-A", "STEWARD", "attraction", 0.2, confidence=0.6, evidence_refs=["private.md"], privacy_class="private")
    save_affinity_graph(tmp_path, graph)
    public = present_affinity(tmp_path, "RES-A", "STEWARD", caller_clearance="public")
    assert public["dimensions"]["attraction"]["redacted"] is True
    assert public["authority_effect"] == "none"
    assert present_affinity(tmp_path, "RES-A", "RES-B")["single_score_available"] is False


def test_trust_evolves_gradually_and_disputed_evidence_does_not_apply(tmp_path):
    applied = record_trust_evidence(tmp_path, "RES-A", "RES-B", "promise_kept", magnitude=0.9, evidence_refs=["exp1"])
    assert applied["state"]["change_rate_limited"] is True
    disputed = record_trust_evidence(tmp_path, "RES-A", "RES-B", "confidentiality", disputed=True)
    assert disputed == {"applied": False, "reason": "disputed_evidence", "event_type": "confidentiality"}


def test_friendship_mentorship_and_support_preserve_boundaries():
    state = evaluate_friendship_mentorship([
        {"event_type": "shared_humor", "reciprocal": True},
        {"event_type": "reciprocal_support", "reciprocal": True},
        {"event_type": "guidance_request", "boundary_respected": True},
        {"event_type": "teaching_event", "boundary_respected": True, "privacy_class": "private", "event_id": "m1"},
    ])
    assert state["friendship_state"] == "emerging"
    assert state["mentorship_state"] == "active_professional"
    assert state["authority_effect"] == "none"
    assert propose_support_response({"signal_type": "workload_pressure"})["requires_consent_before_intervention"] is True
    assert propose_support_response({"signal_type": "explicit_request", "declined": True})["repeat_pressure_allowed"] is False
    assert propose_support_response({"signal_type": "urgent_risk", "institution": "Ingrid"})["institution"] == "Ingrid"


def test_experience_ledger_is_append_only_idempotent_private_and_superseding(tmp_path):
    event = {"resident_id": "RES-A", "occurred_at": "2026-07-12T12:00:00Z", "source_refs": ["ops.md"], "domains": ["engineering"], "significance": "reviewed_outcome", "privacy_class": "private", "confidence": 0.9, "idempotency_key": "same"}
    first = append_experience(tmp_path, event)
    second = append_experience(tmp_path, event)
    correction = append_experience(tmp_path, {**event, "idempotency_key": "correction", "supersedes": first["event"]["event_id"], "privacy_class": "staff-only"})
    assert first["appended"] is True and second["appended"] is False
    assert correction["event"]["supersedes"] == first["event"]["event_id"]
    assert list_experiences(tmp_path, caller_clearance="public") == [correction["event"]]
    assert len((tmp_path / "runtime/resident_growth/experience_ledger.jsonl").read_text().splitlines()) == 2


def test_skill_confidence_preference_and_milestone_are_evidence_reviewed(tmp_path):
    for i, significance in enumerate(["reviewed_outcome", "deliberate_practice"]):
        append_experience(tmp_path, {"resident_id": "RES-A", "occurred_at": f"2026-07-12T12:0{i}:00Z", "source_refs": [f"e{i}.md"], "domains": ["engineering"], "significance": significance, "privacy_class": "staff-only", "confidence": 0.9})
    proposal = propose_skill_growth(tmp_path, "RES-A", "engineering:testing")
    assert proposal["proposed_level"] == 1 and proposal["review_required"] is True
    conf = adjust_confidence(tmp_path, "RES-A", "engineering", proposal["evidence_refs"][0], "success")
    assert conf["competence_authority_effect"] == "none" and conf["current"] > 0
    assert refine_preference(tmp_path, "RES-A", "tea", context="late work", evidence_refs=proposal["evidence_refs"], protected_trait=True)["applied"] is False
    pref = refine_preference(tmp_path, "RES-A", "tea", context="late work", evidence_refs=proposal["evidence_refs"])
    assert pref["preference"]["provenance"] == proposal["evidence_refs"]
    milestone = propose_milestone(tmp_path, "RES-A", "mastery", proposal["evidence_refs"], "Recognized testing growth")
    assert milestone["milestone"]["approval_state"] == "candidate"


def test_validation_reports_persistence_and_migration(tmp_path):
    payload = validate_affinity_growth_runtime(tmp_path)
    assert payload["valid"] is True
    assert "runtime/resident_affinity/affinity_graph.json" in payload["persistence_paths"]
    assert (tmp_path / "runtime/resident_affinity/affinity_graph.json").is_file()
