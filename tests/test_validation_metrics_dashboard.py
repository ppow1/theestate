import json

from estate.core.validation_metrics_dashboard import generate_validation_metrics_dashboard, format_validation_metrics_dashboard


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_validation_metrics_aggregates_completions_and_observations(tmp_path):
    write_json(tmp_path, "collaboration/work_packages/completions/WP-1_codex_done.json", {"work_package_id": "WP-1", "codex_status": "done", "completed_at": "2026-07-01T00:00:00+00:00"})
    write_json(tmp_path, "collaboration/work_packages/completions/WP-2_codex_done.json", {"work_package_id": "WP-2", "codex_status": "done", "completed_at": "2026-07-02T00:00:00+00:00", "validation_result": "conditional pass"})
    write_json(tmp_path, "collaboration/work_packages/completions/WP-3_codex_done.json", {"work_package_id": "WP-3", "codex_status": "done", "completed_at": "2026-07-02T00:00:00+00:00", "validation_result": "fail"})
    obs = tmp_path / "validation/observations/validation_observations.jsonl"
    obs.parent.mkdir(parents=True)
    obs.write_text('\n'.join([
        json.dumps({"observation_id":"VO-1","status":"open","severity":"follow-up","observed_behavior":"x"}),
        json.dumps({"observation_id":"VO-2","status":"deferred","severity":"follow-up","observed_behavior":"y"}),
        json.dumps({"observation_id":"VO-3","status":"open","severity":"confirmed-defect","observed_behavior":"z"}),
    ]) + '\n', encoding="utf-8")

    payload = generate_validation_metrics_dashboard(tmp_path, write=True)

    assert payload["summary"]["total_validated_work_packages"] == 3
    assert payload["summary"]["pass_count"] == 1
    assert payload["summary"]["conditional_pass_count"] == 1
    assert payload["summary"]["fail_count"] == 1
    assert payload["summary"]["open_observation_count"] == 2
    assert payload["summary"]["confirmed_defect_count"] == 1
    assert payload["summary"]["deferred_observation_count"] == 1
    assert payload["validation_trend_over_time"] == [
        {"date": "2026-07-01", "validated_work_packages": 1},
        {"date": "2026-07-02", "validated_work_packages": 2},
    ]
    assert (tmp_path / "runtime/validation/validation_metrics_dashboard.json").exists()
    assert (tmp_path / "operations/validation/validation_metrics_dashboard.md").exists()


def test_validation_metrics_empty_state_degrades_gracefully(tmp_path):
    payload = generate_validation_metrics_dashboard(tmp_path, write=False)
    markdown = format_validation_metrics_dashboard(payload)

    assert payload["summary"]["total_validated_work_packages"] == 0
    assert payload["summary"]["open_observation_count"] == 0
    assert payload["warnings"][0]["type"] == "missing_artifact"
    assert "No validation trend data available yet" in markdown
