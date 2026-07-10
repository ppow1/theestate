import json

from estate.core.office_command_surface import controls_for_tab, execute_office_action
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def seed_dashboard_artifacts(root):
    write_json(root, "runtime/operations_runtime/status/latest.json", {"state": "running", "scheduler": {"state": "enabled"}})
    write_json(root, "runtime/background_operations/status/latest.json", {"state": "watching", "watch_state": "enabled"})
    write_json(root, "runtime/operations/status/active.json", [{
        "activity_id": "act-critical",
        "current_state": "Blocked",
        "requires_attention": True,
        "last_message": "Needs Steward attention",
        "severity": "critical",
        "work_package_id": "WP-0635",
        "artifact_paths": ["runtime/evidence/act-critical.json"],
        "metadata": {"summary_safe": True},
    }])
    write_json(root, "runtime/evidence/act-critical.json", {"evidence": "safe"})
    write_json(root, "runtime/post_merge_audit/status/latest.json", {"ring_2_queue": [{"id": "audit-1"}], "active_audits": [{"id": "audit-active"}]})
    write_json(root, "runtime/merge_discovery/status/latest.json", {"repository_targets": [{"repository": "estate-main", "state": "ready", "path": "runtime/merge_discovery/status/latest.json"}]})
    write_json(root, "data/registry/personnel.json", [{"employee_id": "E1", "display_name": "Helen", "office": "Workforce"}])


def test_operational_command_dashboard_aggregates_runtime_artifacts(tmp_path):
    seed_dashboard_artifacts(tmp_path)

    payload = generate_command_center(tmp_path, write=False)
    dashboard = payload["panels"]["office_operational_command_dashboard"]

    assert dashboard["available"] is True
    assert dashboard["data"]["summary"]["runtime_host"] == "running"
    assert dashboard["data"]["summary"]["exceptions_requiring_attention"] >= 1
    assert dashboard["data"]["repositories"][0]["repository"] == "estate-main"
    assert "Workforce" in dashboard["data"]["department_commitments"]
    assert "institutional acceptance remain distinct" in dashboard["data"]["authority_boundaries"]


def test_operational_command_dashboard_renders_filters_drilldown_and_controls(tmp_path):
    seed_dashboard_artifacts(tmp_path)

    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "Office Operational Command Dashboard" in html
    assert "data-dashboard-filter='repository'" in html
    assert "act-critical" in html
    assert "operations_dashboard.inspect_evidence" in html
    assert "runtime/evidence/act-critical.json" in html
    assert "institutional acceptance" in html


def test_operational_dashboard_actions_are_real_and_safe(tmp_path):
    seed_dashboard_artifacts(tmp_path)
    actions = controls_for_tab("operational-dashboard")
    assert {a["action_id"] for a in actions} == {"operations_dashboard.refresh", "operations_dashboard.inspect_evidence"}
    assert all(a["availability"] == "available" for a in actions)

    result = execute_office_action("operations_dashboard.inspect_evidence", root=tmp_path, evidence_path="runtime/evidence/act-critical.json")
    assert result["outcome"] == "completed"
    assert result["target_tab"] == "operational-dashboard"
    assert "provider" not in " ".join(result.get("runtime_state_changed") or []).lower()
