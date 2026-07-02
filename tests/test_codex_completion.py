import json
from pathlib import Path

from estate.core.codex_completion import (
    check_completion_record,
    completion_record_path,
    completion_status,
    format_completion_status,
    list_completion_records,
)


def _record(work_package_id="WP-9999"):
    return {
        "work_package_id": work_package_id,
        "codex_status": "done",
        "completed_at": "2026-07-02T22:10:00Z",
        "branch": "work",
        "pull_request_url": None,
        "summary": "Test completion record.",
        "files_changed": ["docs/example.md"],
        "tests_run": ["pytest tests/test_codex_completion.py"],
        "known_limitations": [],
        "ready_for_ca_review": True,
        "merge_authority": "ca_verified_auto_merge_allowed",
    }


def test_completion_record_path_uses_standard_filename(tmp_path):
    assert completion_record_path("WP-9999", tmp_path) == tmp_path / "WP-9999_codex_done.json"


def test_check_completion_record_accepts_standard_done_record(tmp_path):
    path = tmp_path / "WP-9999_codex_done.json"
    path.write_text(json.dumps(_record()), encoding="utf-8")

    check = check_completion_record(path)

    assert check.is_complete is True
    assert check.ready_for_ca_review is True
    assert check.missing_fields == ()
    assert check.errors == ()


def test_check_completion_record_reports_missing_or_not_ready_fields(tmp_path):
    path = tmp_path / "WP-9999_codex_done.json"
    record = _record()
    record.pop("summary")
    record["ready_for_ca_review"] = False
    path.write_text(json.dumps(record), encoding="utf-8")

    check = check_completion_record(path)

    assert check.is_complete is False
    assert check.missing_fields == ("summary",)
    assert "ready_for_ca_review is not true" in check.errors


def test_completion_status_and_list_completion_records(tmp_path):
    path = tmp_path / "WP-9999_codex_done.json"
    path.write_text(json.dumps(_record()), encoding="utf-8")

    assert completion_status("WP-9999", tmp_path).is_complete is True
    assert [record.work_package_id for record in list_completion_records(tmp_path)] == ["WP-9999"]


def test_format_completion_status_includes_actionable_summary(tmp_path):
    missing = check_completion_record(tmp_path / "missing.json")

    formatted = format_completion_status(missing)

    assert "Complete: False" in formatted
    assert "record not found" in formatted
