import pytest

from estate.core.resident_lifecycle import transition, status, office_lifecycle_summary
from estate.core.office_personnel_directory import build_office_personnel_directory


def ev(name):
    return {"artifact": name}


def test_lifecycle_deterministic_resume_and_identity_refresh(tmp_path):
    rid = "RES-TEST"
    rec = transition(rid, "intake_candidate", actor="Helen", resident_name="Test", evidence=ev("candidate"), root=tmp_path, resume_token="e1")
    rec2 = transition(rid, "intake_candidate", actor="Helen", resident_name="Test", evidence=ev("candidate"), root=tmp_path, resume_token="e1")
    assert rec2 == rec
    for name, actor in [
        ("begin_review", "Helen"), ("approve_for_hire", "Steward"), ("start_onboarding", "Helen"),
        ("mark_ready", "Helen"), ("activate", "Steward"), ("schedule_reflection", "Helen"),
        ("start_reflection", "Helen"), ("complete_refresh", "Helen"),
    ]:
        rec = transition(rid, name, actor=actor, evidence=ev(name), root=tmp_path)
    assert rec["status"] == "active"
    assert rec["resident_id"] == rid
    assert rec["identity_lineage"]["kind"] == "refreshed_resident"


def test_invalid_and_steward_reserved_transitions(tmp_path):
    with pytest.raises(ValueError):
        transition("RES-X", "activate", actor="Steward", evidence=ev("bad"), root=tmp_path)
    transition("RES-X", "intake_candidate", actor="Helen", resident_name="X", evidence=ev("candidate"), root=tmp_path)
    transition("RES-X", "begin_review", actor="Helen", evidence=ev("review"), root=tmp_path)
    with pytest.raises(PermissionError):
        transition("RES-X", "approve_for_hire", actor="Helen", evidence=ev("approval"), root=tmp_path)


def test_interrupted_resume_and_retirement_successor_distinct(tmp_path):
    rid = "RES-Y"
    for name, actor in [("intake_candidate", "Helen"), ("begin_review", "Helen"), ("approve_for_hire", "Steward"), ("start_onboarding", "Helen"), ("mark_ready", "Helen"), ("activate", "Steward"), ("stand_down", "Steward"), ("review_retirement", "Steward"), ("retire", "Steward")]:
        transition(rid, name, actor=actor, evidence=ev(name), root=tmp_path)
    retired = status(rid, root=tmp_path)
    assert retired["identity_lineage"]["kind"] == "retired_resident"
    successor_gate = transition(rid, "open_successor_review", actor="Steward", evidence=ev("succession"), root=tmp_path)
    assert successor_gate["status"] == "successor_review"
    assert successor_gate["resident_id"] == rid
    assert successor_gate["identity_lineage"].get("successor_resident_id") is None
    assert office_lifecycle_summary(tmp_path)["records"][0]["status"] == "successor_review"


def test_office_directory_lifecycle_source_link(tmp_path):
    (tmp_path / "data/registry").mkdir(parents=True)
    (tmp_path / "data/registry/personnel.json").write_text('[{"employee_id": 9, "display_name": "Test", "resident_id": "RES-T", "mailbox_id": 9}]')
    (tmp_path / "data/registry/mailboxes.json").write_text('[]')
    (tmp_path / "data/registry/residents.json").write_text('[{"id": "RES-T", "name": "Test"}]')
    transition("RES-T", "intake_candidate", actor="Helen", resident_name="Test", evidence=ev("candidate"), root=tmp_path)
    payload = build_office_personnel_directory(tmp_path)
    emp = payload["employees_by_id"]["9"]
    assert emp["resident_lifecycle"]["status"] == "candidate"
    assert payload["resident_lifecycle_status"]["source"] == "runtime/residents/lifecycle"
