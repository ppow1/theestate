import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from estate.core.institutional_learning import InstitutionalLearningStore, InstitutionalLesson


def test_intake_routes_and_integrates_workforce(tmp_path: Path):
    store = InstitutionalLearningStore(tmp_path)
    lesson = InstitutionalLesson.create(lesson_type="retrieval_gap", source_type="worker", source_office="Engineering", submitted_by="worker-1", summary="Repeatedly missed validation report location.", evidence_artifacts=["operations/validation/reports/x.md"])
    store.intake(lesson)
    assert lesson.status == "accepted"
    assert lesson.recommended_owner == "Engineering"
    assert lesson.workforce_request_id
    assert (tmp_path / "runtime/workforce_development/requests" / f"{lesson.workforce_request_id}.json").is_file()
    assert (tmp_path / "runtime/office/institutional_learning_summary.json").is_file()


def test_duplicate_pattern_detection(tmp_path: Path):
    store = InstitutionalLearningStore(tmp_path)
    first = InstitutionalLesson.create(lesson_type="documentation_gap", summary="Workers cannot find the close command documentation.")
    second = InstitutionalLesson.create(lesson_type="documentation_gap", summary="Workers cannot find the close command documentation.")
    store.intake(first)
    store.intake(second)
    assert second.status == "duplicate"
    assert second.duplicate_of == first.lesson_id
    assert first.lesson_id in second.related_lessons


def test_privacy_and_office_summary_redaction(tmp_path: Path):
    lesson = InstitutionalLesson.create(lesson_type="onboarding_gap", summary="Worker Alex Smith exposed private personnel notes during onboarding.", contains_private_personnel_detail=True, classification="Restricted")
    InstitutionalLearningStore(tmp_path).intake(lesson)
    assert "Alex Smith" not in lesson.office_summary
    status = InstitutionalLearningStore(tmp_path).write_status()
    assert status["private_personnel_detail_exposed"] is False
    assert status["summary"]["privacy_restricted_count"] == 1
    with pytest.raises(ValueError, match="private personnel detail cannot be Public"):
        InstitutionalLesson.create(lesson_type="onboarding_gap", summary="bad", contains_private_personnel_detail=True, classification="Public").to_dict()


def test_policy_governance_requires_existing_approval_path(tmp_path: Path):
    lesson = InstitutionalLesson.create(lesson_type="governance_ambiguity", summary="Approval threshold is ambiguous.")
    InstitutionalLearningStore(tmp_path).intake(lesson)
    assert lesson.recommended_owner == "Chief Architect"
    assert lesson.approval_required_for_policy_or_governance_change is True
    assert InstitutionalLearningStore(tmp_path).write_status()["policy_or_governance_auto_rewritten"] is False


def test_closure_requires_and_records_summary(tmp_path: Path):
    store = InstitutionalLearningStore(tmp_path)
    lesson = InstitutionalLesson.create(lesson_type="worker_suggestion", summary="Add a shorter onboarding checklist.")
    store.intake(lesson)
    closed = store.close(lesson.lesson_id, "Owner reviewed and added checklist task to existing Engineering path.")
    assert closed.status == "closed"
    assert store.write_status()["summary"]["closed_count"] == 1


def test_main_cli_institutional_learning(tmp_path: Path):
    data = {"lesson_type":"retrieval_gap", "summary":"Workers repeatedly searched the wrong folder.", "source_type":"worker"}
    f = tmp_path / "lesson.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "institutional-learning", "intake", "--root", str(tmp_path), "--file", str(f), "--json"], text=True, capture_output=True, check=True, env=env)
    payload = json.loads(result.stdout)
    assert payload["lesson"]["status"] == "accepted"
