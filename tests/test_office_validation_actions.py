import json
from pathlib import Path

from estate.core.office_command_surface import controls_for_tab, execute_office_action
from estate.core.office_validation_actions import inspect_validation_control_center
from estate.core.work_package_validation import get_validation_recipe


def test_validation_control_center_inspects_filters_and_opens_artifacts(tmp_path):
    p = tmp_path / "runtime/validation/work_packages/WP-9999_validation.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"work_package_id": "WP-9999", "validation_status": "failed", "owner": "QA"}), encoding="utf-8")
    verdict = tmp_path / "runtime/post_merge_audit/verdicts/audit-1.json"
    verdict.parent.mkdir(parents=True)
    verdict.write_text(json.dumps({"work_package_id": "WP-9999", "verdict": "needs_repair"}), encoding="utf-8")

    payload = inspect_validation_control_center(tmp_path, result="failed", package="WP-9999", owner="QA")
    assert payload["summary"]["row_count"] == 1
    assert payload["rows"][0]["attention_state"] == "attention_required"
    assert "never grants institutional acceptance" in payload["source_of_truth_boundary"]

    result = execute_office_action("validation.open_artifact", root=tmp_path, artifact_path="runtime/post_merge_audit/verdicts/audit-1.json")
    assert result["outcome"] == "completed"
    assert "runtime/post_merge_audit/verdicts/audit-1.json" in result["artifacts_read"]


def test_validation_request_revalidation_ack_status_and_governed_retry(tmp_path):
    assert any(c["action_id"] == "validation.governed_retry" for c in controls_for_tab("validation"))
    assert get_validation_recipe("WP-0518") is not None

    result = execute_office_action("validation.request", root=tmp_path, work_package_id="WP-0518", revalidate=True)
    assert result["outcome"] == "completed"
    assert "institutional acceptance not granted" in result["steward_message"]
    assert (tmp_path / "runtime/validation/office_validation_control_center.json").is_file()

    artifact = result["artifacts_written"][0]
    ack = execute_office_action("validation.acknowledge_failure", root=tmp_path, artifact_id=artifact, acknowledged_by="QA", reason="reviewing")
    assert ack["outcome"] == "completed"
    assert (tmp_path / "runtime/validation/failure_acknowledgements.jsonl").is_file()

    status = execute_office_action("validation.automatic_validator_status", root=tmp_path)
    assert status["outcome"] == "completed"
    assert "Automatic validator" in status["steward_message"]

    retry = execute_office_action("validation.governed_retry", root=tmp_path, max_count=1)
    assert retry["outcome"] == "completed"
    assert "Governed retry processed" in retry["steward_message"]
