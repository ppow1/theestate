import json

from estate.core.validation_observations import (
    append_observation,
    ensure_observation_log,
    load_observations,
    render_markdown_log,
    update_observation_status,
)


def sample_observation(**overrides):
    payload = {
        "observation_id": "VO-TEST-0001",
        "related_work_package": "WP-TEST",
        "observed_behavior": "Observed behavior was recorded without confirming a defect.",
        "expected_behavior": "Expected behavior may be documented when known.",
        "source_of_observation": "unit test",
        "severity": "follow-up",
        "status": "open",
        "recommended_next_action": "Review later.",
        "linked_follow_up_work_package": None,
        "timestamp": "2026-07-04T00:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_missing_observation_files_are_created_safely(tmp_path):
    paths = ensure_observation_log(tmp_path)

    assert paths["jsonl"].exists()
    assert paths["markdown"].exists()
    assert load_observations(tmp_path) == []
    assert "No validation observations recorded" in paths["markdown"].read_text(encoding="utf-8")


def test_observation_creation_writes_parseable_jsonl_and_markdown(tmp_path):
    append_observation(sample_observation(), tmp_path)

    jsonl_path = tmp_path / "validation/observations/validation_observations.jsonl"
    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    parsed = [json.loads(line) for line in lines]

    assert parsed[0]["observation_id"] == "VO-TEST-0001"
    assert parsed[0]["severity"] == "follow-up"
    assert parsed[0]["status"] == "open"

    markdown = (tmp_path / "validation/observations/validation_observations.md").read_text(encoding="utf-8")
    assert "Validation observations preserve findings for review" in markdown
    assert "VO-TEST-0001" in markdown
    assert "not confirmed defects" in markdown


def test_observation_status_changes_preserve_follow_up_link(tmp_path):
    append_observation(sample_observation(), tmp_path)

    updated = update_observation_status("VO-TEST-0001", "converted-to-work-package", tmp_path, linked_follow_up_work_package="WP-9999")

    assert updated["status"] == "converted-to-work-package"
    assert updated["linked_follow_up_work_package"] == "WP-9999"
    assert load_observations(tmp_path)[0]["linked_follow_up_work_package"] == "WP-9999"


def test_markdown_rendering_handles_empty_logs():
    markdown = render_markdown_log([])

    assert "# Validation Observation Log" in markdown
    assert "No validation observations recorded." in markdown
