import json
from pathlib import Path

import pytest

from estate.core.character_continuity import (
    artifact_path,
    create_continuity,
    create_cycle,
    prepare_reflection,
    start_next_cycle,
    status,
)


def test_continuity_cycle_preserves_identity_and_filters_private(tmp_path):
    record = create_cycle("RES-ALFRED", "Alfred", root=tmp_path)
    assert record["cycle"]["state"] == "active"

    evidence = {
        "working_journal_summary": [
            {"text": "Public-safe operating summary.", "classification": "Estate Internal"},
            {"text": "Do not leak this", "classification": "Steward Only"},
        ],
        "lessons_retained": [{"text": "Carry concise lessons only.", "classification": "Estate Internal"}],
        "contradictions_unresolved_drift": [{"text": "Resolve autonomy boundaries.", "classification": "Estate Internal"}],
    }
    prepared = prepare_reflection("RES-ALFRED", evidence, root=tmp_path)
    assert prepared["cycle"]["state"] == "in_reflection"
    assert prepared["working_journal_summary"] == ["Public-safe operating summary."]

    artifact = create_continuity("RES-ALFRED", {"decision": "continue", "private_notes": "hidden"}, root=tmp_path)
    assert artifact["classification"]["private_content_excluded"] is True
    assert "private_notes" not in artifact["reflection_outcome"]
    assert artifact_path("RES-ALFRED", "cycle-0001", tmp_path).exists()

    next_record = start_next_cycle("RES-ALFRED", root=tmp_path)
    assert next_record["resident_identity"]["resident_id"] == "RES-ALFRED"
    assert next_record["cycle"]["predecessor_cycle_id"] == "cycle-0001"
    assert next_record["next_cycle_initialization"]["carry_full_transcript"] is False
    assert status("RES-ALFRED", root=tmp_path)["cycle"]["cycle_id"] == "cycle-0002"


def test_requires_reflection_before_artifact(tmp_path):
    create_cycle("RES-HELEN", "Helen", root=tmp_path)
    with pytest.raises(ValueError):
        create_continuity("RES-HELEN", {"decision": "continue"}, root=tmp_path)
