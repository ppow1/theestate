import json

from estate.core.office_command_surface import controls_for_tab, execute_office_action
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def test_operations_control_surface_renders_real_runtime_state_and_controls(tmp_path):
    payload = generate_command_center(root=tmp_path, write=False)
    surface = payload["panels"]["operations_control_surface"]
    assert surface["available"] is True
    assert surface["data"]["constraints"]["does_not_grant_final_acceptance"] is True
    action_ids = {c["action_id"] for c in controls_for_tab("operational-activity")}
    assert "operations_surface.host_control" in action_ids
    assert "operations_surface.scheduler_control" in action_ids
    assert "operations_surface.watch_control" in action_ids
    assert "operations_surface.trigger_cycle" in action_ids
    html = render_command_center_html(payload)
    assert "Operations Control Surface" in html
    assert "data-office-action='operations_surface.scheduler_control'" in html
    assert "data-office-action='operations_surface.watch_control'" in html


def test_scheduler_and_watch_controls_persist_state(tmp_path):
    disable_job = execute_office_action(
        "operations_surface.scheduler_control",
        root=tmp_path,
        scheduler_action="disable",
        job_id="health_refresh",
    )
    assert disable_job["outcome"] == "completed"
    scheduler_state = json.loads((tmp_path / "runtime/operations_scheduler/state.json").read_text())
    assert scheduler_state["jobs"]["health_refresh"]["enabled"] is False

    enable_watch = execute_office_action(
        "operations_surface.watch_control",
        root=tmp_path,
        watch_action="enable",
        watch_id="operations_runtime_health_watch",
    )
    assert enable_watch["outcome"] == "completed"
    watch_state = json.loads((tmp_path / "runtime/background_operations/watch_state.json").read_text())
    assert watch_state["watches"]["operations_runtime_health_watch"]["enabled"] is True


def test_bounded_cycle_and_evidence_inspection_are_truthful(tmp_path):
    cycle = execute_office_action(
        "operations_surface.trigger_cycle",
        root=tmp_path,
        dry_run="true",
        mode="observe-only",
        max_audit_requests="1",
    )
    assert cycle["outcome"] == "completed"
    assert "OperationsRuntimeService.run_once" in cycle["source_handler"]

    evidence = tmp_path / "runtime/operations_runtime/status/latest.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text('{"ok": true}\n')
    inspected = execute_office_action(
        "operations_surface.inspect_evidence",
        root=tmp_path,
        evidence_path="runtime/operations_runtime/status/latest.json",
    )
    assert inspected["outcome"] == "completed"
    assert "readable" in inspected["steward_message"]

    blocked = execute_office_action("operations_surface.inspect_evidence", root=tmp_path, evidence_path="../outside.json")
    assert blocked["outcome"] == "blocked"
