import json
from pathlib import Path

from estate.core.mailbox_index import (
    generate_mailbox_index,
    load_functional_mailbox_registry,
    load_personnel_registry,
    resolve_destination,
)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(tmp_path):
    write_json(tmp_path / "data/registry/personnel.json", [
        {"employee_id": 3, "display_name": "Chief Architect #2", "mailbox_id": 3},
        {"employee_id": 4, "display_name": "Chief Architect #3", "mailbox_id": 4},
    ])
    write_json(tmp_path / "data/registry/mailboxes.json", [
        {"mailbox_id": 10001, "mailbox_type": "office", "display_name": "Office of the Chief Architect"},
        {"mailbox_id": 10100, "mailbox_type": "queue", "display_name": "Alfred Routing Intake"},
    ])


def test_personnel_id_mapping(tmp_path):
    seed(tmp_path)
    personnel = load_personnel_registry(tmp_path)
    assert {entry["employee_id"]: entry["mailbox_id"] for entry in personnel} == {3: 3, 4: 4}


def test_functional_mailbox_registry_parsing(tmp_path):
    seed(tmp_path)
    mailboxes = load_functional_mailbox_registry(tmp_path)
    assert [entry["mailbox_id"] for entry in mailboxes] == [10001, 10100]


def test_legacy_destination_mapping(tmp_path):
    seed(tmp_path)
    personnel = load_personnel_registry(tmp_path)
    employee_id, mailbox_id, warning = resolve_destination({"destination": "office.chief_architect_2"}, personnel, [])
    assert (employee_id, mailbox_id, warning) == (3, 3, None)


def test_destination_employee_id_precedence(tmp_path):
    seed(tmp_path)
    personnel = load_personnel_registry(tmp_path)
    employee_id, mailbox_id, warning = resolve_destination(
        {"destination": "office.chief_architect_2", "destination_employee_id": 4}, personnel, []
    )
    assert (employee_id, mailbox_id, warning) == (4, 4, None)


def test_mailbox_index_generation_and_warnings(tmp_path):
    seed(tmp_path)
    write_json(tmp_path / "collaboration/messages/ca2.json", {
        "id": "ca2", "created_at": "2026-07-01T00:00:00", "source": "office.chief_architect_3",
        "destination": "office.chief_architect_2", "message_type": "work_package", "priority": "normal",
        "status": "open", "payload": {"title": "CA2 work"}
    })
    write_json(tmp_path / "collaboration/messages/ca3.json", {
        "id": "ca3", "created_at": "2026-07-01T00:00:00", "source": "office.chief_architect_2",
        "destination": "office.chief_architect_3", "message_type": "work_package", "priority": "normal",
        "status": "open", "payload": {"title": "CA3 work"}
    })
    write_json(tmp_path / "collaboration/messages/unknown.json", {"id": "unknown", "destination": "office.unknown"})
    (tmp_path / "collaboration/messages/bad.json").write_text("{bad", encoding="utf-8")

    index = generate_mailbox_index(tmp_path)

    assert (tmp_path / "collaboration/mailboxes/index.json").exists()
    assert (tmp_path / "collaboration/mailboxes/0003/inbox").is_dir()
    assert (tmp_path / "collaboration/mailboxes/0004/inbox").is_dir()
    assert (tmp_path / "collaboration/mailboxes/10001/inbox").is_dir()
    assert any(m["destination_employee_id"] == 3 for m in index["messages"])
    assert any(m["destination_employee_id"] == 4 for m in index["messages"])
    assert any("malformed message" in m.get("warning", "") for m in index["messages"])
    assert any("unresolved destination" in m.get("warning", "") for m in index["messages"])


def test_cli_registration():
    from estate.cli.main import main
    assert callable(main)
