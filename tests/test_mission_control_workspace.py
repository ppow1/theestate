import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.mission_control_workspace import build_mission_control_workspace
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_mission_control_writes_read_only_workspace_and_warns_on_missing_sources(tmp_path):
    write_json(tmp_path, "runtime/validation/local_operational_validation_run.json", {"summary": {"ok": True}})

    payload = build_mission_control_workspace(tmp_path)
    data = payload["data"]

    assert payload["available"] is True
    assert data["authority_boundary"] == "read_only_overview"
    assert data["degrades_gracefully"] is True
    assert data["summary"]["state"] == "partial"
    assert data["summary"]["missing_source_count"] > 0
    assert any(source["name"] == "validation" and source["available"] for source in data["sources"])
    assert (tmp_path / "runtime/steward/mission_control_workspace.json").exists()


def test_mission_control_all_sources_ready_when_artifacts_exist(tmp_path):
    for rel in [
        "runtime/work_packages/assignment_queue.json",
        "runtime/workers/worker_runtime_monitor.json",
        "runtime/workers/worker_runtime_heartbeat.json",
        "runtime/validation/local_operational_validation_run.json",
        "runtime/mailboxes/synchronization_duty.json",
        "runtime/audit/recall_audit_log.json",
        "runtime/notifications/notification_center_workspace.json",
    ]:
        write_json(tmp_path, rel, {"summary": {"ok": True}})
    for rel in [
        "runtime/steward/command_center.html",
        "operations/steward/decision_queue.md",
        "operations/boards/roadmap.md",
    ]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Source\n", encoding="utf-8")

    data = build_mission_control_workspace(tmp_path, write=False)["data"]

    assert data["summary"]["state"] == "ready"
    assert data["summary"]["ready_source_count"] == data["summary"]["source_count"]
    assert data["warnings"] == []


def test_command_center_exposes_mission_control_tab(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "mission_control_workspace" in payload["panels"]
    assert any(item["id"] == "mission-control" for item in payload["navigation"]["items"])
    assert "Mission Control Workspace" in html
    assert "read_only_overview" in json.dumps(payload["panels"]["mission_control_workspace"])
