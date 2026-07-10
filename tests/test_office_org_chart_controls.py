import json
from estate.core.office_personnel_directory import build_office_personnel_directory, open_employee_detail
from estate.core.steward_command_center import generate_command_center


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_org_chart_nodes_match_employee_detail_and_html_controls(tmp_path):
    write_json(tmp_path, "data/registry/personnel.json", [
        {"employee_id": "E1", "display_name": "Manager", "current_title": "Lead", "current_office": "Ops", "mailbox_id": 1},
        {"employee_id": "E2", "display_name": "Report", "current_title": "Analyst", "current_office": "Ops", "mailbox_id": 2, "manager_employee_id": "E1"},
    ])
    write_json(tmp_path, "data/registry/mailboxes.json", [{"mailbox_id": 1}, {"mailbox_id": 2}])
    write_json(tmp_path, "data/registry/capabilities.json", {"capabilities": []})
    payload = build_office_personnel_directory(tmp_path)
    node = next(n for n in payload["org_chart"]["nodes"] if n.get("employee_id") == "E2")
    assert node["click_action"] == "open_employee_detail"
    assert node["keyboard_action"] == "enter_open_employee_detail"
    assert open_employee_detail(node["employee_id"], tmp_path)["employee"]["employee_id"] == "E2"
    cc = generate_command_center(tmp_path, write=True)
    html = (tmp_path / "runtime/steward/command_center.html").read_text(encoding="utf-8")
    assert "data-org-employee='E2'" in html
    assert "function bindPersonnelDirectory" in html
    assert "Escape" in html
    assert "#personnel?employee_id=" in html
    assert cc["panels"]["office_personnel_directory"]["data"]["summary"]["employee_count"] == 2
