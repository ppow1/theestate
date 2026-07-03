import json
import subprocess
import sys
from pathlib import Path

from estate.core.check_updates import generate_check_updates


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed(root: Path):
    write(root / "data/registry/personnel.json", json.dumps([
        {"employee_id": 4, "display_name": "Chief Architect #3", "current_title": "Chief Architect #3", "current_office": "Office of the Chief Architect", "mailbox_id": 4},
        {"employee_id": 5, "display_name": "Chief Architect #4", "current_title": "Chief Architect #4", "current_office": "Office of the Chief Architect", "mailbox_id": 5},
        {"employee_id": 6, "display_name": "Helen", "current_title": "Manager of Human Resources", "current_office": "Human Resources", "mailbox_id": 6, "resident_id": "RES-000003"},
        {"employee_id": 7, "display_name": "Alfred", "current_title": "Manager of Administration", "current_office": "Administration", "mailbox_id": 7, "resident_id": "RES-000001"},
    ]))
    write(root / "data/registry/mailboxes.json", json.dumps([
        {"mailbox_id": 10001, "mailbox_type": "office", "display_name": "Office of the Chief Architect", "owning_office": "Office of the Chief Architect", "responsible_employee_id": 4},
        {"mailbox_id": 10100, "mailbox_type": "queue", "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff", "responsible_employee_id": None},
        {"mailbox_id": 10004, "mailbox_type": "office", "display_name": "Human Resources Office", "owning_office": "Human Resources", "responsible_employee_id": 6},
    ]))
    write(root / "data/registry/residents.json", json.dumps([
        {"id": "RES-000001", "name": "Alfred", "office": "Manager of Administration"},
        {"id": "RES-000003", "name": "Helen", "office": "Manager of Human Resources"},
    ]))
    write(root / "docs/governance/policy.md", "# Governance Change\nClassification: Estate Internal\n")
    write(root / "Architecture/ADR/adr-1.md", "# ADR One\nClassification: Estate Internal\n")
    write(root / "docs/collaboration/Worker_Runtime_Contract_v1.md", "# Worker Runtime Contract v1\nClassification: Estate Internal\n")
    write(root / "docs/collaboration/Instruction_Precedence_v1.md", "# Instruction Precedence v1\nClassification: Estate Internal\n")
    write(root / "docs/operations/public.md", "# Public Operations Note\n")
    write(root / "runtime/dependencies/dependency_graph.json", json.dumps({"title": "Dependency Graph"}))
    write(root / "runtime/validation/operational_validation_report.json", json.dumps({"title": "Operational Validation"}))
    write(root / "collaboration/messages/impl.json", json.dumps({"id": "m1", "destination": "worker.implementation", "subject": "Implement package"}))
    write(root / "collaboration/messages/ca.json", json.dumps({"id": "m2", "destination": "office.chief_architect_2", "subject": "Architecture briefing"}))
    write(root / "collaboration/messages/ca3.json", json.dumps({"id": "m3", "destination_employee_id": 4, "requires_ack": True, "ack_status": "pending", "thread_id": "t-ca3", "payload": {"title": "CA3 mailbox briefing"}}))
    write(root / "collaboration/messages/ca4.json", json.dumps({"id": "m4", "destination": "mailbox.5", "requires_ack": True, "reply_to": "m3", "payload": {"title": "CA4 mailbox briefing"}}))
    write(root / "collaboration/messages/alfred.json", json.dumps({"id": "m5", "destination_mailbox_id": 10100, "payload": {"title": "Alfred routing note"}}))
    write(root / "collaboration/messages/alfred_personal.json", json.dumps({"id": "m7", "destination": "alfred", "payload": {"title": "Alfred personnel note"}}))
    write(root / "collaboration/messages/helen.json", json.dumps({"id": "m6", "destination": "employee.6", "payload": {"title": "Helen personnel note"}}))
    write(root / "runtime/collaboration/events/events.jsonl", '{"id":"e1"}\n')
    write(root / "archive/institutional_memory/memo.md", "# Memory\nClassification: Estate Internal\n")


def test_general_actor_receives_safe_summary(tmp_path):
    seed(tmp_path)
    report = generate_check_updates(root=tmp_path)
    assert report["actor"] == "general"
    assert report["visibility_level"] == "public"
    assert report["updates"]["operations_updates"]
    assert not report["updates"]["governance_updates"]
    assert not report["updates"]["assigned_messages"]


def test_chief_architect_receives_architecture_governance_collaboration(tmp_path):
    seed(tmp_path)
    report = generate_check_updates("office.chief_architect_2", root=tmp_path)
    assert report["actor_category"] == "office.chief_architect"
    assert report["updates"]["architecture_updates"]
    assert report["updates"]["governance_updates"]
    assert report["updates"]["collaboration_updates"]
    assert report["updates"]["assigned_messages"][0]["destination"] == "office.chief_architect_2"


def test_audit_worker_receives_audit_relevant_updates(tmp_path):
    seed(tmp_path)
    report = generate_check_updates("audit", root=tmp_path)
    assert report["actor"] == "worker.audit"
    assert report["updates"]["audit_updates"]


def test_implementation_worker_receives_contract_precedence_dependency_and_message(tmp_path):
    seed(tmp_path)
    report = generate_check_updates("implementation", root=tmp_path)
    titles = [item["title"] for item in report["updates"]["collaboration_updates"]]
    assert "Worker Runtime Contract v1" in titles
    assert "Instruction Precedence v1" in titles
    assert report["updates"]["capability_updates"]
    assert report["updates"]["assigned_messages"][0]["title"] == "Implement package"


def test_assigned_messages_detected_by_destination(tmp_path):
    seed(tmp_path)
    report = generate_check_updates("worker.implementation", root=tmp_path)
    assert len(report["updates"]["assigned_messages"]) == 1


def test_ca3_mailbox_identity_ack_and_thread(tmp_path):
    seed(tmp_path)
    report = generate_check_updates("office.chief_architect_3", root=tmp_path)
    assert report["identity"]["canonical_destination"] == "mailbox.4"
    assert report["mailbox"] == {"canonical_actor": "mailbox.4", "employee_id": 4, "mailbox_id": 4}
    assert report["mailbox_obligations"]["messages_requiring_ack"][0]["thread_id"] == "t-ca3"


def test_ca4_mailbox_resolution_by_mailbox_destination(tmp_path):
    seed(tmp_path)
    report = generate_check_updates("office.chief_architect_4", root=tmp_path)
    assert report["identity"]["employee_id"] == 5
    assert any(message["message_id"] == "m4" and message["reply_to"] == "m3" for message in report["updates"]["assigned_messages"])


def test_alfred_and_helen_mailbox_resolution(tmp_path):
    seed(tmp_path)
    alfred = generate_check_updates("alfred", root=tmp_path)
    helen = generate_check_updates("helen", root=tmp_path)
    assert alfred["identity"]["employee_id"] == 7
    assert alfred["identity"]["mailbox_id"] == 7
    assert alfred["identity"]["resident_id"] == "RES-000001"
    assert any(message["message_id"] == "m7" for message in alfred["updates"]["assigned_messages"])
    assert not any(message["message_id"] == "m5" for message in alfred["updates"]["assigned_messages"])
    queue = generate_check_updates("alfred.queue", root=tmp_path)
    assert queue["identity"]["employee_id"] is None
    assert queue["identity"]["mailbox_id"] == 10100
    assert any(message["message_id"] == "m5" for message in queue["updates"]["assigned_messages"])
    assert helen["identity"]["employee_id"] == 6
    assert any(message["message_id"] == "m6" for message in helen["updates"]["assigned_messages"])


def test_missing_artifacts_become_warnings(tmp_path):
    report = generate_check_updates(root=tmp_path)
    assert report["inputs"]["missing"]
    assert any(w["type"] == "missing_input" for w in report["warnings"])


def test_malformed_json_message_becomes_warning(tmp_path):
    write(tmp_path / "collaboration/messages/bad.json", "{")
    report = generate_check_updates("worker.implementation", root=tmp_path)
    assert any(w["type"] == "malformed_json" and w["path"] == "collaboration/messages/bad.json" for w in report["warnings"])


def test_markdown_output_is_generated(tmp_path):
    seed(tmp_path)
    generate_check_updates("worker.implementation", root=tmp_path)
    assert (tmp_path / "runtime/updates/check_updates_latest.json").exists()
    md = tmp_path / "operations/updates/check_updates_latest.md"
    assert md.exists()
    assert "# Check for Updates" in md.read_text(encoding="utf-8")


def test_cli_registration_and_json_output(tmp_path):
    seed(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "check-updates", "--actor", "worker.implementation", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(repo / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["actor"] == "worker.implementation"
    assert (tmp_path / "operations/updates/check_updates_latest.md").exists()
