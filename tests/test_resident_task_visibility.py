import json
from pathlib import Path

from estate.core.resident_task_visibility import (
    build_resident_task_board,
    create_resident_message,
    alfred_attention_summary,
    helen_availability_constraints,
)


def write_json(root, rel, data):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def seed(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-1", "name": "Alfred", "role": "Coordinate"},
        {"id": "RES-3", "name": "Helen", "role": "Assign"},
    ])
    write_json(root, "data/registry/personnel.json", [
        {"employee_id": 7, "display_name": "Alfred", "mailbox_id": 7, "resident_id": "RES-1", "current_office": "Administration"},
        {"employee_id": 6, "display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-3", "current_office": "Human Resources"},
    ])


def test_stale_state_and_escalation_are_reported(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/task_status.json", {"residents": [
        {"resident_id": "RES-1", "name": "Alfred", "goal": "Coordinate", "current_task": "Review", "last_meaningful_movement": "2000-01-01T00:00:00+00:00", "availability_state": "working", "escalation_state": "none"}
    ]})
    row = build_resident_task_board(tmp_path)["participants"][0]
    assert row["stale_status"] is True
    assert row["blocker"] == "status stale or missing"
    assert row["escalation_state"] == "attention_needed"


def test_mailbox_identity_and_unread_count(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "collaboration/messages/msg.json", {"id": "msg", "destination": "mailbox.7", "status": "open", "ack_status": "pending"})
    row = build_resident_task_board(tmp_path)["participants"][0]
    assert row["employee_id"] == 7
    assert row["mailbox_id"] == 7
    assert row["unread_message_count"] == 1


def test_privacy_fields_are_not_exposed_to_participant_board_or_helen(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/task_status.json", {"residents": [
        {"resident_id": "RES-3", "name": "Helen", "goal": "Assign", "current_task": "Plan", "last_meaningful_movement": "2026-07-10T00:00:00+00:00", "availability_state": "working", "escalation_state": "none", "private_journal": "secret", "detailed_workforce_assessment": "secret"}
    ]})
    text = json.dumps(build_resident_task_board(tmp_path)) + json.dumps(helen_availability_constraints(tmp_path))
    assert "private_journal" not in text
    assert "detailed_workforce_assessment" not in text
    assert "secret" not in text


def test_governed_resident_message_uses_existing_mailbox_identities(tmp_path):
    seed(tmp_path)
    result = create_resident_message("Alfred", "Helen", "Please review availability constraints.", tmp_path)
    message = result["message"]
    assert message["source"] == "mailbox.7"
    assert message["destination"] == "mailbox.6"
    assert message["message_type"] == "resident_operational_message"
    assert (tmp_path / result["path"]).exists()


def test_alfred_summary_surfaces_escalation(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/presence.json", {"residents": [{"resident_id": "RES-1", "name": "Alfred", "needs_steward": True, "last_heartbeat": "2026-07-10T00:00:00+00:00"}]})
    assert alfred_attention_summary(tmp_path)["attention_count"] >= 1
