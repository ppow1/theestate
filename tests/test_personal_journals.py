import json
import pytest
from estate.core.personal_journals import PersonalJournalStore, JournalAccessError
from estate.core.resident_task_visibility import build_resident_task_board

PERSONNEL = [{"employee_id": 6, "display_name": "Helen", "resident_id": "RES-000003", "mailbox_id": 6}, {"employee_id": 10, "display_name": "Ingrid", "resident_id": "RES-000002", "mailbox_id": 10}, {"employee_id": 12, "display_name": "Grace", "mailbox_id": 12}]

def seed(root):
    (root/"data/registry").mkdir(parents=True)
    (root/"data/registry/personnel.json").write_text(json.dumps(PERSONNEL), encoding="utf-8")
    (root/"data/registry/residents.json").write_text(json.dumps([{"id":"RES-000003","name":"Helen","role":"HR"}]), encoding="utf-8")

def test_private_by_default_and_deterministic_path(tmp_path):
    seed(tmp_path); store=PersonalJournalStore(tmp_path)
    created=store.create_entry("Helen", "Helen", "private reflection body", entry_type="cheat_sheet")
    assert created["path"].startswith("runtime/protected_journals/employee-6/entries/")
    with pytest.raises(JournalAccessError): store.read_entry("Helen", created["entry"]["entry_id"], "Grace")
    assert store.read_entry("Helen", created["entry"]["entry_id"], "Helen")["body"] == "private reflection body"

def test_redaction_archive_summary_export_and_audit(tmp_path):
    seed(tmp_path); store=PersonalJournalStore(tmp_path)
    eid=store.create_entry("Helen", "Helen", "sensitive body")["entry"]["entry_id"]
    summary=store.approve_summary("Helen", eid, "Ingrid", "Governed summary only.")
    assert summary["raw_entry_included"] is False
    exported=store.export_entries("Helen", "Helen", scope="summaries")
    assert exported["items"][0]["summary"] == "Governed summary only."
    redacted=store.redact_entry("Helen", eid, "Ingrid", "privacy request")
    assert redacted["body"] == "[redacted]"
    archived=store.archive_entry("Helen", eid, "Ingrid", "no longer active")
    assert archived["status"] == "archived"
    audit=(tmp_path/"runtime/protected_journals/audit.jsonl").read_text(encoding="utf-8")
    for action in ["write", "read", "summary_approval", "export", "redact", "archive"]:
        assert f'"action": "{action}"' in audit

def test_helen_cannot_export_grace_raw_body_without_authorization(tmp_path):
    seed(tmp_path); store=PersonalJournalStore(tmp_path)
    eid=store.create_entry("Grace", "Grace", "grace private body")["entry"]["entry_id"]
    with pytest.raises(JournalAccessError):
        store.export_entries("Grace", "Helen", scope="evidence", entry_ids=[eid], include_body=True)

def test_public_surface_status_has_no_body(tmp_path):
    seed(tmp_path); store=PersonalJournalStore(tmp_path)
    store.create_entry("Helen", "Helen", "do not leak this")
    status=json.dumps(store.privacy_safe_status())
    board=json.dumps(build_resident_task_board(tmp_path))
    assert "do not leak this" not in status
    assert "do not leak this" not in board
    assert "body_included" in status
