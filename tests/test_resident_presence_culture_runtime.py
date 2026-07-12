import json
from pathlib import Path

from estate.core.resident_presence_culture import (
    build_ambient_activity,
    build_culture_runtime,
    build_occupancy,
    build_presence_api_response,
    generate_passive_interactions,
    validate_presence_culture_runtime,
)


def write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def baseline(root: Path):
    write(root / "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred"},
        {"id": "RES-000003", "name": "Helen"},
    ])
    write(root / "runtime/residents/presence.json", {"residents": [
        {"resident_id": "RES-000001", "name": "Alfred", "presence_state": "working", "location_id": "library", "last_heartbeat": "2026-07-12T10:00:00Z"},
        {"resident_id": "RES-000003", "name": "Helen", "presence_state": "available", "location_id": "library", "last_heartbeat": "2026-07-12T10:00:00Z"},
    ]})
    write(root / "data/culture/estate_culture_runtime.json", {
        "schema_version": "estate_presence_culture.v1",
        "traditions": [{"tradition_id": "t1", "status": "active", "origin_evidence": ["source.md"]}],
        "culture_memories": [{"memory_id": "m1", "sources": ["archive.md"], "disclosure_scope": "public"}],
        "running_jokes": [{"joke_id": "j1", "consent_state": "approved", "status": "active"}],
        "annual_events": [{"event_template_id": "a1", "status": "planned"}],
        "culture_signals": [{"signal_id": "s1", "classification": "verified_practice"}],
        "culture_change_proposals": [{"proposal_id": "p1", "state": "experiment"}],
    })


def test_presence_api_is_read_only_source_lined_and_uncertain(tmp_path):
    baseline(tmp_path)
    payload = build_presence_api_response(tmp_path, as_of="2026-07-12T10:05:00Z")
    assert payload["mutation_allowed"] is False
    assert {a["source_class"] for a in payload["activities"]} == {"inferred"}
    assert all("confidence" in a and "visibility" in a for a in payload["activities"])
    assert payload["occupancy"][0]["freshness"] == "current"


def test_unknown_and_consequential_ambient_claims_fail_closed(tmp_path):
    baseline(tmp_path)
    write(tmp_path / "runtime/residents/ambient_activity.json", {"items": [{
        "resident_id": "RES-000001", "activity_type": "focused_work", "summary": "approved and completed WP-1", "start_time": "2026-07-12T10:00:00Z"
    }]})
    payload = build_ambient_activity(tmp_path, as_of="2026-07-12T10:05:00Z")
    alfred = next(a for a in payload["activities"] if a["resident_id"] == "RES-000001")
    assert alfred["activity_type"] == "unknown"
    assert any(d["code"] == "consequential_ambient_claim" for d in payload["diagnostics"])


def test_occupancy_and_passive_interactions_do_not_create_facts(tmp_path):
    baseline(tmp_path)
    occupancy = build_occupancy(tmp_path, as_of="2026-07-12T10:05:00Z")
    assert occupancy["room_occupancy"][0]["summary_is_canonical"] is False
    interaction = generate_passive_interactions(tmp_path, as_of="2026-07-12T10:05:00Z")
    assert interaction["interactions"][0]["creates_canonical_fact"] is False
    assert "cannot create messages" in interaction["authority_statement"]


def test_culture_runtime_preserves_review_and_authority_boundaries(tmp_path):
    baseline(tmp_path)
    culture = build_culture_runtime(tmp_path)
    assert culture["running_jokes"][0]["eligible_for_callback"] is True
    assert culture["annual_events"][0]["planning_is_attendance_evidence"] is False
    assert culture["culture_change_proposals"][0]["requires_explicit_review"] is True
    assert "cannot alter governance" in culture["authority_statement"]
    assert validate_presence_culture_runtime(tmp_path)["valid"] is True
