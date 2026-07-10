import json
from pathlib import Path

from estate.core.office_personnel_directory import build_office_personnel_directory, open_employee_detail, route_personnel_mailbox, route_personnel_conversation, refresh_personnel_directory
from estate.core.office_command_surface import execute_office_action


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(root):
    write_json(root, "data/registry/personnel.json", [
        {"employee_id": 1, "display_name": "Ada", "current_title": "Architect", "current_office": "Architecture", "mailbox_id": 10, "status": "active", "capabilities": ["design"]},
        {"employee_id": 2, "display_name": "Ben", "current_title": "Engineer", "current_office": "Engineering", "mailbox_id": 20, "status": "active", "manager_employee_id": 1, "resident_id": "RES-2"},
    ])
    write_json(root, "data/registry/mailboxes.json", [{"mailbox_id": 10}, {"mailbox_id": 20}])
    write_json(root, "data/registry/residents.json", [{"id": "RES-2", "name": "Ben"}])
    write_json(root, "data/registry/capabilities.json", {"capabilities": [{"id": "design", "name": "Design", "dependencies": []}]})
    (root / "collaboration/work_packages/pending").mkdir(parents=True)
    (root / "collaboration/work_packages/pending/WP-9999_Ada.md").write_text("# WP-9999 Ada\nOwner: Ada\n", encoding="utf-8")


def test_personnel_directory_aggregates_records_and_routes(tmp_path):
    seed(tmp_path)
    payload = build_office_personnel_directory(tmp_path, write=True)
    assert payload["summary"]["valid_record_count"] == 2
    assert payload["new_personnel_registry_introduced"] is False
    assert payload["new_mailbox_system_introduced"] is False
    ids = [e["employee_id"] for e in payload["employees"]]
    assert sorted(ids) == ["1", "2"]
    ben = open_employee_detail("2", tmp_path)["employee"]
    assert ben["manager_employee_id"] == "1"
    assert ben["manager"] == "Ada"
    assert payload["employees_by_id"]["1"]["direct_reports"][0]["employee_id"] == "2"
    assert route_personnel_mailbox("2", tmp_path)["route"]["mailbox_id"] == "20"
    assert route_personnel_conversation("2", tmp_path)["route"]["selected"] == "RES-2"
    assert route_personnel_conversation("1", tmp_path)["outcome"] == "blocked"
    assert (tmp_path / "runtime/steward/office_personnel_directory.json").is_file()


def test_personnel_directory_detects_duplicate_orphan_cycle_and_malformed(tmp_path):
    write_json(tmp_path, "data/registry/personnel.json", [
        {"employee_id": 1, "display_name": "A", "manager_employee_id": 2},
        {"employee_id": 2, "display_name": "B", "manager_employee_id": 1},
        {"employee_id": 2, "display_name": "B duplicate"},
        {"employee_id": 3, "display_name": "C", "manager_employee_id": 99},
        {"employee_id": 4, "display_name": "D", "manager_employee_id": 5},
        {"employee_id": 5, "display_name": "E", "manager_employee_id": 4},
        {"display_name": "Bad"},
    ])
    write_json(tmp_path, "data/registry/mailboxes.json", [])
    write_json(tmp_path, "data/registry/capabilities.json", {"capabilities": []})
    payload = build_office_personnel_directory(tmp_path)
    types = {w["type"] for w in payload["warnings"]}
    assert "duplicate_employee_id" in types
    assert "orphaned_manager" in types
    assert "manager_cycle" in types
    assert "malformed_personnel_record" in types


def test_refresh_action_preserves_selected_employee_and_reports_counts(tmp_path):
    seed(tmp_path)
    payload = refresh_personnel_directory(tmp_path, selected_employee_id="2", filters={"office": "Engineering"})
    assert payload["selected_employee_id"] == "2"
    assert payload["filters"]["office"] == "Engineering"
    result = execute_office_action("personnel.refresh", root=tmp_path, selected_employee_id="2")
    assert result["outcome"] == "completed"
    assert "duplicates=" in result["steward_message"]
