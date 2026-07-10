import json
from pathlib import Path

from estate.core.resident_task_visibility import build_resident_task_board
from estate.core.office_command_surface import execute_office_action
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, data):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def seed(root):
    write_json(root, "data/registry/residents.json", [{"id": "RES-1", "name": "Alfred", "role": "Coordinate"}, {"id": "RES-2", "name": "Helen", "role": "Assign"}])
    write_json(root, "data/registry/personnel.json", [{"employee_id": 1, "display_name": "Alfred", "resident_id": "RES-1", "mailbox_id": 1, "current_office": "Operations"}, {"employee_id": 2, "display_name": "Helen", "resident_id": "RES-2", "mailbox_id": 2, "current_office": "Human Resources"}])


def test_board_fields_filtering_source_and_privacy(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/task_status.json", {"residents": [{"resident_id": "RES-1", "current_goal": "Ship board", "current_task": "Aggregate status", "task_owner": "Alfred", "last_meaningful_movement": "2026-07-10T00:00:00+00:00", "waiting_on": "Steward", "next_action": "Refresh", "next_checkpoint": "Noon", "availability_state": "waiting", "project": "WP-4017", "source_artifact": "runtime/residents/task_status.json", "source_last_updated": "2026-07-10T00:00:00+00:00", "private_journal": "do not leak"}]})
    board = build_resident_task_board(tmp_path, resident="Alfred", project="WP-4017", status="waiting")
    row = board["participants"][0]
    assert row["current_goal"] == "Ship board"
    assert row["task_owner"] == "Alfred"
    assert row["status"] == "waiting"
    assert row["related_work_package_or_project"] == "WP-4017"
    assert row["source_artifact"] == "runtime/residents/task_status.json"
    assert "do not leak" not in json.dumps(board)


def test_navigation_actions_and_office_ui(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/task_status.json", {"residents": [{"resident_id": "RES-1", "current_task": "Review", "last_meaningful_movement": "2026-07-10T00:00:00+00:00", "availability_state": "working"}]})
    refreshed = execute_office_action("resident_task_board.refresh", root=tmp_path, resident="Alfred")
    detail = execute_office_action("resident_task_board.open_detail", root=tmp_path, resident_id="RES-1")
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)
    assert refreshed["outcome"] == "completed"
    assert detail["outcome"] == "completed"
    assert "Resident Task Board" in html
    assert "resident_task_board.refresh" in html
