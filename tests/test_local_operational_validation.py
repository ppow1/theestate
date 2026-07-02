import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.local_operational_validation import generate_local_operational_validation_run


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def representative_artifacts(root):
    write(root, "estate_ledger/ledger.md", "ledger\n")
    write(root, "development/devlog.md", "devlog\n")
    write(root, "data/registry/personnel.json", json.dumps([{"employee_id": 4, "display_name": "CA3", "mailbox_id": 4}]))
    write(root, "data/registry/mailboxes.json", json.dumps([{"mailbox_id": 10001, "mailbox_type": "office", "display_name": "Office"}]))
    write(root, "data/registry/capabilities.json", json.dumps([{"id": "CAP-1", "name": "Cap", "lifecycle_state": "Implemented", "implementation_refs": ["src/x.py"], "validation_evidence": ["runtime/evidence.json"]}]))
    write(root, "data/registry/services.json", json.dumps([{"id": "SVC-1", "name": "Svc", "dependencies": []}]))
    write(root, "runtime/evidence.json", "{}")
    write(root, "collaboration/messages/msg.json", json.dumps({"id": "m1", "version": 1, "created_at": "2026-07-02T00:00:00", "created_by": "Alfred", "source": "alfred", "destination": "worker.implementation", "classification": "Estate Internal", "message_type": "implementation", "priority": "normal", "status": "open", "payload": {"title": "Implement"}}))
    write(root, "operations/boards/parking_lot.md", "# Parking Lot\n\n## Parking Lot Items\n\n| ID | Idea | Category | Priority | Originator | Date Captured | Status | Target Milestone | Promotion Condition |\n|---|---|---|---|---|---|---|---|---|\n| PL-1 | Stable | Ops | High | A | 2026-07-01 | Captured | Stable | Board is stable |\n")
    write(root, "operations/boards/active_work.md", "# Active Work Board\n\n## Active Work\n\n| ID | Effort | Owner | Status | Current Milestone | Dependency | Next Action |\n|---|---|---|---|---|---|---|\n| AW-1 | Ops | Alfred | Active | v1 | None | Review |\n")
    write(root, "operations/boards/daily_board.md", "# Daily Task Board\n\n## Today\n\n| ID | Task | Owner | Status | Blocker | Review Required | Next Action |\n|---|---|---|---|---|---|---|\n| DT-1 | Task | Alfred | Active | None | Yes | Do it |\n")
    write(root, "collaboration/work_packages/pending/WP-1.md", "# WP-1\n")
    write(root, "collaboration/work_packages/completions/WP-0_codex_done.json", json.dumps({"work_package_id": "WP-0", "ready_for_ca_review": True}))


def test_successful_run_with_representative_artifacts(tmp_path):
    representative_artifacts(tmp_path)
    report = generate_local_operational_validation_run(tmp_path)
    assert report["summary"]["step_count"] >= 9
    assert report["summary"]["failed_steps"] == 0
    assert report["policy"]["ledger_unchanged"] is True
    assert report["policy"]["devlog_unchanged"] is True


def test_missing_optional_artifacts_warn_not_fatal(tmp_path):
    report = generate_local_operational_validation_run(tmp_path, write=False)
    assert report["summary"]["ok"] is True
    assert any(w["type"] == "missing_optional_artifact" for w in report["warnings"])


def test_failed_sub_step_capture(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr("estate.core.local_operational_validation.generate_dependency_graph", boom)
    report = generate_local_operational_validation_run(tmp_path, write=False)
    failed = [s for s in report["steps"] if s["name"] == "dependency_graph"][0]
    assert failed["status"] == "failed"
    assert failed["error"]["message"] == "boom"
    assert any(w.get("step") == "dependency_graph" for w in report["warnings"])


def test_json_and_markdown_output_generation(tmp_path):
    generate_local_operational_validation_run(tmp_path)
    assert (tmp_path / "runtime/validation/local_operational_validation_run.json").exists()
    md = tmp_path / "operations/validation/local_operational_validation_run.md"
    assert md.exists()
    assert md.read_text(encoding="utf-8").startswith("# Local Operational Validation Run")


def test_no_direct_ledger_devlog_writes(tmp_path):
    representative_artifacts(tmp_path)
    ledger = (tmp_path / "estate_ledger/ledger.md").read_text(encoding="utf-8")
    devlog = (tmp_path / "development/devlog.md").read_text(encoding="utf-8")
    generate_local_operational_validation_run(tmp_path)
    assert (tmp_path / "estate_ledger/ledger.md").read_text(encoding="utf-8") == ledger
    assert (tmp_path / "development/devlog.md").read_text(encoding="utf-8") == devlog


def test_estate_validate_local_cli_registration(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "estate-validate-local", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["outputs"]["json"] == "runtime/validation/local_operational_validation_run.json"
