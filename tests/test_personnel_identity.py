import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.personnel_identity import resolve_personnel_identity


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def registry_root(tmp_path):
    write_json(tmp_path / "data/registry/personnel.json", [
        {"employee_id": 4, "display_name": "Chief Architect #3", "current_title": "Chief Architect #3", "current_office": "Office of the Chief Architect", "mailbox_id": 4},
        {"employee_id": 5, "display_name": "Chief Architect #4", "current_title": "Chief Architect #4", "current_office": "Office of the Chief Architect", "mailbox_id": 5},
        {"employee_id": 6, "display_name": "Helen", "current_title": "Manager of Human Resources", "current_office": "Human Resources", "mailbox_id": 6, "resident_id": "RES-000003"},
        {"employee_id": 7, "display_name": "Alfred", "current_title": "Manager of Administration", "current_office": "Administration", "mailbox_id": 7, "resident_id": "RES-000001"},
    ])
    write_json(tmp_path / "data/registry/mailboxes.json", [
        {"mailbox_id": 10100, "mailbox_type": "queue", "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff", "responsible_employee_id": None},
        {"mailbox_id": 10004, "mailbox_type": "office", "display_name": "Human Resources Office", "owning_office": "Human Resources", "responsible_employee_id": 6},
    ])
    write_json(tmp_path / "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "office": "Manager of Administration"},
        {"id": "RES-000003", "name": "Helen", "office": "Manager of Human Resources"},
    ])
    return tmp_path


def test_employee_mailbox_and_office_resolution(tmp_path):
    root = registry_root(tmp_path)
    assert resolve_personnel_identity("employee.4", root)["canonical_destination"] == "mailbox.4"
    assert resolve_personnel_identity("mailbox.5", root)["employee_id"] == 5
    ca3 = resolve_personnel_identity("office.chief_architect_3", root)
    ca4 = resolve_personnel_identity("office.chief_architect_4", root)
    assert (ca3["employee_id"], ca3["mailbox_id"], ca3["warnings"]) == (4, 4, [])
    assert (ca4["employee_id"], ca4["mailbox_id"], ca4["warnings"]) == (5, 5, [])


def test_resident_and_worker_resolution(tmp_path):
    root = registry_root(tmp_path)
    alfred = resolve_personnel_identity("alfred", root)
    helen = resolve_personnel_identity("helen", root)
    worker = resolve_personnel_identity("worker.implementation", root)
    assert (alfred["resident_id"], alfred["canonical_destination"], alfred["employee_id"], alfred["mailbox_id"]) == ("RES-000001", "mailbox.7", 7, 7)
    queue = resolve_personnel_identity("alfred.queue", root)
    routing = resolve_personnel_identity("alfred.routing", root)
    mailbox = resolve_personnel_identity("mailbox.10100", root)
    assert (queue["destination_type"], queue["employee_id"], queue["mailbox_id"]) == ("mailbox", None, 10100)
    assert routing["mailbox_id"] == 10100
    assert mailbox["mailbox_id"] == 10100
    assert (helen["resident_id"], helen["canonical_destination"], helen["employee_id"]) == ("RES-000003", "mailbox.6", 6)
    assert (worker["destination_type"], worker["canonical_destination"], worker["warnings"]) == ("worker", "worker.implementation", [])


def test_missing_and_ambiguous_mappings_warn_without_fabrication(tmp_path):
    root = registry_root(tmp_path)
    missing = resolve_personnel_identity("employee.999", root)
    unknown_worker = resolve_personnel_identity("worker.unknown", root)
    assert missing["resolved"] is False
    assert missing["mailbox_id"] is None
    assert missing["warnings"]
    assert unknown_worker["resolved"] is True
    assert unknown_worker["warnings"] == ["worker is not in known routing rules: worker.unknown"]


def test_personnel_resolve_cli_json():
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "personnel-resolve", "--actor", "office.chief_architect_4", "--json"],
        cwd=repo,
        env={"PYTHONPATH": str(repo / "src")},
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["canonical_destination"] == "mailbox.5"
    assert payload["employee_id"] == 5
