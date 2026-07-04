import json

from estate.core.validation_handoff_artifact_workflow import (
    generate_validation_handoff_artifact_workflow,
    format_validation_handoff_artifact_workflow,
)


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_validation_handoff_aggregates_existing_artifacts_without_reclassifying_observations(tmp_path):
    write_json(tmp_path, "runtime/validation/validation_metrics_dashboard.json", {"summary": {"total_validated_work_packages": 3, "pass_count": 1, "conditional_pass_count": 1, "fail_count": 1}})
    write_json(tmp_path, "collaboration/work_packages/completions/WP-9_codex_done.json", {"work_package_id": "WP-9", "completed_at": "2026-07-04T00:00:00+00:00", "ready_for_ca_review": True})
    obs = tmp_path / "validation/observations/validation_observations.jsonl"
    obs.parent.mkdir(parents=True)
    obs.write_text("\n".join([
        json.dumps({"observation_id": "VO-1", "status": "open", "severity": "follow-up", "observed_behavior": "Needs review"}),
        json.dumps({"observation_id": "VO-2", "status": "open", "severity": "confirmed-defect", "observed_behavior": "Broken path"}),
    ]) + "\n", encoding="utf-8")

    payload = generate_validation_handoff_artifact_workflow(tmp_path, write=True)

    assert payload["summary"]["total_validated_work_packages"] == 3
    assert payload["summary"]["open_observation_count"] == 2
    assert payload["summary"]["confirmed_defect_count"] == 1
    assert payload["observations"]["open"][0]["observation_id"] == "VO-1"
    assert payload["observations"]["confirmed_defects"][0]["observation_id"] == "VO-2"
    assert any(source["path"] == "runtime/validation/validation_metrics_dashboard.json" for source in payload["sources"])
    assert (tmp_path / "runtime/validation/validation_handoff_artifact_workflow.json").exists()
    assert (tmp_path / "operations/validation/validation_handoff_artifact_workflow.md").exists()


def test_validation_handoff_reports_missing_sources_as_unavailable(tmp_path):
    payload = generate_validation_handoff_artifact_workflow(tmp_path, write=False)
    markdown = format_validation_handoff_artifact_workflow(payload)

    assert payload["summary"]["state"] == "partial"
    assert payload["summary"]["missing_source_count"] > 0
    assert payload["warnings"]
    assert "missing" in markdown
