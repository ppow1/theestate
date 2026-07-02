import json
import subprocess
import sys
from pathlib import Path

from estate.core.mailbox_sync_duty import generate_mailbox_sync_duty


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed(root: Path):
    write(root / "data/registry/personnel.json", json.dumps([
        {"employee_id": 4, "display_name": "Chief Architect #3", "current_title": "Chief Architect #3", "current_office": "Office of the Chief Architect", "mailbox_id": 4},
        {"employee_id": 5, "display_name": "Chief Architect #4", "current_title": "Chief Architect #4", "current_office": "Office of the Chief Architect", "mailbox_id": 5},
    ]))
    write(root / "data/registry/mailboxes.json", json.dumps([
        {"mailbox_id": 10001, "mailbox_type": "office", "display_name": "Office of the Chief Architect", "owning_office": "Office of the Chief Architect", "responsible_employee_id": 4},
    ]))
    write(root / "data/registry/residents.json", "[]")


def test_actor_with_no_obligations(tmp_path):
    seed(tmp_path)
    report = generate_mailbox_sync_duty("office.chief_architect_4", root=tmp_path)
    assert report["summary"]["has_obligations"] is False
    assert report["summary"]["assigned_message_count"] == 0


def test_actor_with_open_messages(tmp_path):
    seed(tmp_path)
    write(tmp_path / "collaboration/messages/open.json", json.dumps({"id": "m-open", "destination_employee_id": 4, "status": "open", "payload": {"title": "Open item"}}))
    report = generate_mailbox_sync_duty("office.chief_architect_3", root=tmp_path)
    assert report["summary"]["has_obligations"] is True
    assert report["summary"]["open_or_unread_message_count"] == 1
    assert report["obligations"]["open_or_unread_messages"][0]["message_id"] == "m-open"


def test_actor_with_acknowledgement_required_messages(tmp_path):
    seed(tmp_path)
    write(tmp_path / "collaboration/messages/ack.json", json.dumps({"id": "m-ack", "destination": "mailbox.4", "requires_ack": True, "ack_status": "pending", "payload": {"title": "Ack item"}}))
    report = generate_mailbox_sync_duty("office.chief_architect_3", root=tmp_path)
    assert report["summary"]["ack_required_message_count"] == 1
    assert report["obligations"]["messages_requiring_ack"][0]["message_id"] == "m-ack"


def test_replies_waiting_for_actor_attention(tmp_path):
    seed(tmp_path)
    write(tmp_path / "collaboration/messages/reply.json", json.dumps({"id": "m-reply", "destination": "employee.4", "reply_to": "m-original", "thread_id": "t-1", "payload": {"title": "Reply item"}}))
    report = generate_mailbox_sync_duty("office.chief_architect_3", root=tmp_path)
    assert report["summary"]["reply_attention_message_count"] == 1
    assert report["obligations"]["replies_waiting_for_attention"][0]["reply_to"] == "m-original"


def test_unresolved_identity_warning(tmp_path):
    report = generate_mailbox_sync_duty("office.unknown_actor", root=tmp_path)
    assert report["summary"]["has_obligations"] is True
    assert any(w["type"] == "unresolved_identity" for w in report["warnings"])


def test_output_generation_and_cli(tmp_path):
    seed(tmp_path)
    write(tmp_path / "collaboration/messages/open.json", json.dumps({"id": "m-open", "destination_employee_id": 4, "status": "open", "payload": {"title": "Open item"}}))
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "mailbox-sync-duty", "--actor", "office.chief_architect_3", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(repo / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["summary"]["open_or_unread_message_count"] == 1
    assert (tmp_path / "runtime/mailboxes/synchronization_duty.json").exists()
    md = tmp_path / "operations/mailboxes/synchronization_duty.md"
    assert md.exists()
    assert "# Mailbox Synchronization Duty" in md.read_text(encoding="utf-8")
