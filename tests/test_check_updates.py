import json
import subprocess
import sys
from pathlib import Path

from estate.core.check_updates import generate_check_updates


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed(root: Path):
    write(root / "docs/governance/policy.md", "# Governance Change\nClassification: Estate Internal\n")
    write(root / "Architecture/ADR/adr-1.md", "# ADR One\nClassification: Estate Internal\n")
    write(root / "docs/collaboration/Worker_Runtime_Contract_v1.md", "# Worker Runtime Contract v1\nClassification: Estate Internal\n")
    write(root / "docs/collaboration/Instruction_Precedence_v1.md", "# Instruction Precedence v1\nClassification: Estate Internal\n")
    write(root / "docs/operations/public.md", "# Public Operations Note\n")
    write(root / "runtime/dependencies/dependency_graph.json", json.dumps({"title": "Dependency Graph"}))
    write(root / "runtime/validation/operational_validation_report.json", json.dumps({"title": "Operational Validation"}))
    write(root / "collaboration/messages/impl.json", json.dumps({"id": "m1", "destination": "worker.implementation", "subject": "Implement package"}))
    write(root / "collaboration/messages/ca.json", json.dumps({"id": "m2", "destination": "office.chief_architect_2", "subject": "Architecture briefing"}))
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
