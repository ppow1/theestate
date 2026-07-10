import json
import subprocess
from pathlib import Path

from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.post_merge_audit import PostMergeAuditRequest
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor
from estate.core.operations_runtime import OperationsRuntime


def git(cwd: Path, *args: str):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)


def make_repo(path: Path, wp="WP-X"):
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    (path / "file.txt").write_text("ok", encoding="utf-8")
    d = path / "collaboration/work_packages/completions"; d.mkdir(parents=True)
    (d / f"{wp}_codex_done.json").write_text(json.dumps({"work_package_id": wp, "codex_status": "done", "completed_at": "now", "branch": "main", "summary": "done", "files_changed": ["file.txt"], "tests_run": ["test"], "known_limitations": [], "ready_for_ca_review": True, "pull_request_url": "https://example.invalid/pr/1", "merge_authority": "test"}), encoding="utf-8")
    git(path, "add", "."); git(path, "commit", "-m", "init")
    return git(path, "rev-parse", "HEAD").stdout.strip()


def write_req(root: Path, audit_id: str, rev: str, wp="WP-X"):
    d = PostMergeAuditRequest(audit_id, "estate", wp, "merge_commit", rev, [], metadata={"expected_revision": rev}).to_dict()
    p = root / "runtime/post_merge_audit/requests" / f"{audit_id}.json"
    d["state"] = "pending"
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d), encoding="utf-8")


def setup_target(root: Path, repo: Path, retain=True):
    OperationalTargetRuntime(root).write_targets([OperationalTarget("estate", "Estate", "git_repository", "Estate", local_path=str(repo), base_branch="main", validation_root=str(root / "outside_validation"), workspace_root=str(root / "outside_workspaces"), capabilities=["git", "validation", "audit"], watch_state="enabled", metadata={"fetch_enabled": False, "retain_failed_audit_workspaces": retain})])


def test_validation_runs_in_isolated_workspace_and_external_evidence(tmp_path):
    r = tmp_path / "repo"; rev = make_repo(r); setup_target(tmp_path, r)
    (r / "dirty.txt").write_text("dirty", encoding="utf-8")
    write_req(tmp_path, "a1", rev)
    seen = []
    out = PostMergeAuditProcessor(tmp_path, validator=lambda wp, ws: seen.append(ws) or {"validation_status": "passed", "failures": [], "findings": [], "warnings": []}).process_all(max_count=1)
    verdict = out["results"][0]["verdict"]
    assert seen and seen[0] != r
    assert verdict["active_checkout_dirty"] is True
    assert verdict["external_evidence_root"] == str(tmp_path / "outside_validation")
    assert verdict["workspace_record"]["cleanup_status"] == "removed"
    assert not Path(verdict["workspace"]).exists()
    assert verdict["provider_execution_performed"] is False
    assert verdict["dispatch_execution_performed"] is False


def test_failed_audit_does_not_stop_batch_and_limit_five(tmp_path, monkeypatch):
    r = tmp_path / "repo"; rev = make_repo(r); setup_target(tmp_path, r, retain=True)
    for i in range(6):
        write_req(tmp_path, f"a{i}", "badrev" if i == 0 else rev)
    monkeypatch.setattr("estate.core.post_merge_validation_pipeline.PostMergeValidationPipeline._standard_validator", lambda self, wp, ws: {"validation_status": "passed", "failures": [], "findings": [], "warnings": []})
    cycle = OperationsRuntime(tmp_path).run_cycle(mode="process-audits", max_audit_requests=5)
    assert cycle["audits_started"] == 5
    assert cycle["audits_blocked"] >= 1
    assert cycle["provider_execution_performed"] is False
    assert cycle["dispatch_execution_performed"] is False
