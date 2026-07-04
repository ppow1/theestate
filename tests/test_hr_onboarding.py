import json
from pathlib import Path

from estate.core.hr_onboarding import run_employee_onboarding


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed(root):
    write(root / "README.md", "estate")
    write(root / "data/registry/personnel.json", json.dumps([
        {"employee_id": 6, "display_name": "Helen", "current_title": "Manager of Human Resources", "current_office": "Human Resources", "mailbox_id": 6, "status": "active"},
        {"employee_id": 7, "display_name": "Alfred", "current_title": "Manager of Administration", "current_office": "Administration", "mailbox_id": 7, "status": "active"},
    ]))
    write(root / "data/registry/mailboxes.json", json.dumps([
        {"mailbox_id": 10004, "mailbox_type": "office", "display_name": "Human Resources Office", "owning_office": "Human Resources", "responsible_employee_id": 6, "status": "active"}
    ]))
    write(root / "data/registry/residents.json", "[]")
    write(root / "docs/operations/Onboarding_Checklist_v1.md", "checklist")
    write(root / "docs/onboarding/Worker_Onboarding_Manifest.md", "manifest")
    write(root / "docs/onboarding/worker_onboarding_manifest.json", "{}")


def test_successful_onboarding_creates_registry_mailbox_packet_index_and_audit(tmp_path):
    seed(tmp_path)
    result = run_employee_onboarding(
        name="Jordan", department="Engineering", office="Implementation", role="Implementation Worker",
        classification="metadata_only", package_type="worker", steward_authorization="AUTH-1", root=tmp_path,
    )
    assert result["ok"] is True
    assert result["employee_id"] == 8
    personnel = json.loads((tmp_path / "data/registry/personnel.json").read_text())
    assert personnel[-1]["display_name"] == "Jordan"
    assert personnel[-1]["status"] == "onboarding"
    assert (tmp_path / "collaboration/mailboxes/0008/inbox").is_dir()
    assert Path(tmp_path / result["artifacts"]["onboarding_packet"]).exists()
    index = json.loads((tmp_path / "collaboration/mailboxes/index.json").read_text())
    assert any(item["destination_mailbox_id"] == 8 for item in index["messages"])
    assert Path(tmp_path / result["artifacts"]["run_result"]).exists()
    assert (tmp_path / "runtime/hr/onboarding_result.json").exists()


def test_missing_required_input_fails_safely(tmp_path):
    seed(tmp_path)
    result = run_employee_onboarding(
        name="", department="Engineering", office="Implementation", role="Worker",
        classification="metadata_only", package_type="worker", steward_authorization="AUTH-1", root=tmp_path,
    )
    assert result["ok"] is False
    assert "missing required" in result["error"]
    assert not (tmp_path / "runtime/hr/onboarding_result.json").exists()


def test_duplicate_employee_protection(tmp_path):
    seed(tmp_path)
    result = run_employee_onboarding(
        name="Helen", department="Human Resources", office="Human Resources", role="Manager",
        classification="metadata_only", package_type="worker", steward_authorization="AUTH-1", root=tmp_path,
    )
    assert result["ok"] is False
    assert "already exists" in result["error"]


def test_authorization_failure_mode(tmp_path):
    seed(tmp_path)
    result = run_employee_onboarding(
        name="Riley", department="Engineering", office="Implementation", role="Worker",
        classification="metadata_only", package_type="worker", steward_authorization="unauthorized", root=tmp_path,
    )
    assert result["ok"] is False
    assert "Steward authorization" in result["error"]
