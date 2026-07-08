import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.office_command_surface import execute_office_action
from estate.core.office_traffic_controller_panel import load_office_traffic_controller_panel
from estate.core.steward_command_center import generate_command_center, render_command_center_html

NOW = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def latest(**overrides):
    data = {
        "review_id": "opr-1",
        "created_at": "2026-07-08T11:59:00Z",
        "classification": "Estate Internal",
        "source_artifacts": ["runtime/orchestrator/intake/status/queue.json"],
        "blocked_intake_count": 1,
        "assignment_blocked_count": 2,
        "provider_blocked_count": 1,
        "provider_saturated_count": 3,
        "requires_steward_attention": True,
        "requires_boundary_review": True,
        "recommended_actions": [{"action_type": "hold", "target_type": "work_package", "target_id": "WP-0611", "priority": "high", "reason": "Hold blocked work", "safe_summary": "Hold blocked work", "requires_steward_approval": True, "requires_boundary_review": False}],
        "warnings": ["capacity warning"],
        "metadata": {},
    }
    data.update(overrides)
    return data


def test_loader_handles_missing_operations_artifacts(tmp_path):
    panel = load_office_traffic_controller_panel(tmp_path, now=NOW)
    assert panel["available"] is False
    assert "runtime/operations/control/status/latest.json" in panel["expected_status_artifact_paths"]


def test_loader_handles_valid_summary_artifact(tmp_path):
    write_json(tmp_path, "runtime/operations/control/status/summary.json", {"generated_at": "2026-07-08T11:59:00Z", "current_operational_posture": "attention_required", "recommended_next_actions": []})
    panel = load_office_traffic_controller_panel(tmp_path, now=NOW)
    assert panel["summary"]["operational_posture"] == "attention_required"


def test_loader_handles_malformed_summary_without_crashing(tmp_path):
    path = tmp_path / "runtime/operations/control/status/summary.json"
    path.parent.mkdir(parents=True)
    path.write_text("{no", encoding="utf-8")
    panel = load_office_traffic_controller_panel(tmp_path, now=NOW)
    assert panel["summary"]["error_count"] == 1
    assert "Malformed JSON" in panel["errors"][0]["message"]


def test_stale_review_is_marked_stale(tmp_path):
    write_json(tmp_path, "runtime/operations/control/status/latest.json", latest(created_at="2026-07-08T11:00:00Z"))
    panel = load_office_traffic_controller_panel(tmp_path, now=NOW)
    assert panel["freshness"]["state"] == "stale"


def test_recommended_actions_and_attention_render(tmp_path):
    write_json(tmp_path, "runtime/operations/control/status/latest.json", latest())
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Traffic Controller / Operations Manager" in html
    assert "Recommended Actions (1)" in html
    assert "Items requiring Steward attention" in html
    assert "Blocked assignments" in html


def test_provider_capacity_warnings_and_assignment_gaps_render(tmp_path):
    write_json(tmp_path, "runtime/operations/control/status/summary.json", {"generated_at": "2026-07-08T11:59:00Z", "current_operational_posture": "attention_required", "provider_capacity_warnings": 4, "assignment_gaps": 2})
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Provider warnings" in html and "4" in html
    assert "Assignment gaps" in html and "2" in html


def test_sensitive_summaries_redacted_by_default_and_safe_allowed(tmp_path):
    write_json(tmp_path, "runtime/operations/control/status/latest.json", latest(recommended_actions=[
        {"action_type": "hold", "target_type": "work_package", "classification": "Restricted", "reason": "secret", "safe_summary": "secret"},
        {"action_type": "release", "target_type": "work_package", "classification": "Local Only", "reason": "safe shown", "safe_summary": "safe shown", "summary_safe": True},
    ]))
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "<td>secret</td>" not in html
    assert "Sensitive operations summary redacted" in html
    assert "safe shown" in html


def test_real_decision_action_writes_decision_artifact(tmp_path):
    result = execute_office_action("operations_control.record_decision", root=tmp_path, decision_type="hold", target_type="work_package", target_id="WP-0611", decided_by="Steward", reason="Hold safely")
    assert result["outcome"] == "completed"
    assert list((tmp_path / "runtime/operations/control/decisions").glob("*.json"))


def test_unsupported_control_shown_unavailable_and_empty_state_honest(tmp_path):
    write_json(tmp_path, "runtime/operations/control/status/latest.json", latest(recommended_actions=[{"action_type": "execute", "target_type": "system", "reason": "run", "safe_summary": "run"}]))
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Unavailable" in html
    assert "No safe Office handler is registered for execute" in html
    empty = render_command_center_html(generate_command_center(tmp_path / "empty", write=False))
    assert "No operations-control artifacts found" in empty
    assert "No fake healthy status is shown" in empty
