import json
import subprocess
from pathlib import Path

from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.post_merge_audit import PostMergeAuditRequest
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor
from estate.core.operations_runtime import OperationsRuntime
from estate.core.background_operations_runtime import BackgroundOperationsRuntime
from estate.core.steward_command_center import generate_command_center


def _repo(path: Path):
    path.mkdir(); subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "file.txt").write_text("ok", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True); subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def _receipt(repo: Path, wp: str = "WP-X"):
    d = repo / "collaboration/work_packages/completions"; d.mkdir(parents=True, exist_ok=True)
    (d / f"{wp}_codex_done.json").write_text('{"work_package_id":"WP-X","codex_status":"done","completed_at":"now","branch":"main","summary":"done","files_changed":["file.txt"],"tests_run":["test"],"known_limitations":[],"ready_for_ca_review":true,"pull_request_url":"https://example.invalid/pr/1","merge_authority":"test"}', encoding="utf-8")


def _setup(tmp_path):
    repo = tmp_path / "repo"; _repo(repo); _receipt(repo)
    OperationalTargetRuntime(tmp_path).write_targets([OperationalTarget("estate", "Estate", "git_repository", "Estate", local_path=str(repo), base_branch="main", capabilities=["git", "validation", "audit"], watch_state="enabled")])
    req = PostMergeAuditRequest.create("estate", "WP-X", expected_files=["file.txt"])
    d = req.to_dict(); d["state"] = "pending"
    p = tmp_path / "runtime/post_merge_audit/requests" / f"{req.audit_id}.json"; p.parent.mkdir(parents=True); p.write_text(json.dumps(d), encoding="utf-8")
    return req


def test_pending_request_claimed_once_and_state_updated(tmp_path):
    req = _setup(tmp_path)
    processor = PostMergeAuditProcessor(tmp_path, validator=lambda *_: {"validation_status": "passed", "failures": [], "findings": [], "warnings": []})
    first = processor.process_next(); second = processor.process_next()
    assert first["processed"] is True
    assert second["processed"] is False
    saved = json.loads((tmp_path / "runtime/post_merge_audit/requests" / f"{req.audit_id}.json").read_text())
    assert saved["state"] == "ring2_required"
    assert saved["verdict"] == "ring2_required"
    assert saved["workspace"]


def test_runtime_cycle_metrics_and_office_summary(tmp_path, monkeypatch):
    monkeypatch.setattr("estate.core.post_merge_validation_pipeline.PostMergeValidationPipeline._standard_validator", lambda self, wp, workspace: {"validation_status": "passed", "failures": [], "findings": [], "warnings": []})
    _setup(tmp_path)
    BackgroundOperationsRuntime(tmp_path).write_watches([])
    cycle = OperationsRuntime(tmp_path).run_cycle(mode="process-audits")
    assert cycle["audits_claimed"] == 1
    assert cycle["audit_validation_pass"] == 1
    assert cycle["ring2_prompts_generated"] == 1
    payload = generate_command_center(tmp_path, write=False)
    status = payload["status_bar"]
    assert status["automatic_validation_available"] is True
    assert status["latest_verdict"] == "ring2_required"
    assert status["latest_production_ready"] is True
    assert status["validation_evidence_root"]
