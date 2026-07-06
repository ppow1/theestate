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


def test_dry_run_is_trustworthy_and_writes_only_non_authoritative_summary(tmp_path):
    seed(tmp_path)
    before_personnel = (tmp_path / "data/registry/personnel.json").read_text()
    result = run_employee_onboarding(
        name="Ingrid", department="Security and Boundary", office="Office of Security and Boundary",
        role="Security Manager / Boundary Guardian", classification="Estate Internal",
        package_type="standard", steward_authorization="Steward authorization dry-run validation for WP-0146",
        root=tmp_path, dry_run=True,
    )
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["source_files_modified"] is False
    assert result["employee_id"] == 8
    assert result["mailbox_id"] == 8
    assert result["input"]["office"] == "Office of Security and Boundary"
    assert result["steward_authorization_reference"] == "Steward authorization dry-run validation for WP-0146"
    assert (tmp_path / "data/registry/personnel.json").read_text() == before_personnel
    assert not (tmp_path / "collaboration/messages/msg_helen_onboarding_employee_0008_ingrid.json").exists()
    assert not (tmp_path / "runtime/hr/onboarding_result.json").exists()
    summary = tmp_path / result["artifacts"]["summary_receipt"]
    assert summary.exists()
    text = summary.read_text()
    assert "Status: dry_run_complete" in text
    assert "Source files modified: False" in text
    missing = {item["path"]: item["classification"] for item in result["support_artifacts"] if not item["exists"]}
    assert missing["runtime/mailboxes/index.json"] == "non-blocking runtime projection"
    assert missing["runtime/mailboxes/synchronization_duty.json"] == "should be generated by an existing command"
    assert missing["data/onboarding/manifest.json"] == "should be a later work package"
    assert missing["runtime/onboarding/status.json"] == "non-blocking runtime projection"
    assert missing["runtime/residents/cards.json"] == "should be generated by an existing command"


def test_real_onboarding_receipt_records_authority_and_visibility(tmp_path):
    seed(tmp_path)
    result = run_employee_onboarding(
        name="Morgan", department="Architecture", office="Office of Chief Architect",
        role="Chief Architect #5", classification="Estate Internal", package_type="chief_architect",
        steward_authorization="Steward authorization fixture AUTH-WP-0146-REAL", root=tmp_path,
    )
    assert result["ok"] is True
    assert result["source_files_modified"] is True
    assert result["receipt_status"] == "onboarded"
    assert result["resolver_confirmation"]["resolved"] is True
    assert result["mailbox_index_visible"] is True
    summary = (tmp_path / result["artifacts"]["summary_receipt"]).read_text()
    assert "Authority reference: Steward authorization fixture AUTH-WP-0146-REAL" in summary
    latest = json.loads((tmp_path / "runtime/hr/onboarding_result.json").read_text())
    assert latest["artifacts"]["summary_receipt"] == result["artifacts"]["summary_receipt"]


def test_staffing_target_dry_runs(tmp_path):
    seed(tmp_path)
    targets = [
        ("Ingrid", "Security and Boundary", "Office of Security and Boundary", "Security Manager / Boundary Guardian", "standard"),
        ("Chief Architect #5", "Architecture", "Office of Chief Architect", "Chief Architect #5", "chief_architect"),
        ("Chief Architect #6", "Architecture", "Office of Chief Architect", "Chief Architect #6", "chief_architect"),
        ("Chief Character / Resident Development Engineer", "Resident Development", "Office of Resident Development", "Chief Character / Resident Development Engineer", "standard"),
    ]
    for name, department, office, role, package_type in targets:
        result = run_employee_onboarding(
            name=name, department=department, office=office, role=role,
            classification="Estate Internal", package_type=package_type,
            steward_authorization="WP-0146 dry-run staffing validation", root=tmp_path, dry_run=True,
        )
        assert result["ok"] is True, result
        assert result["source_files_modified"] is False
        assert result["receipt_status"] == "dry_run_complete"
