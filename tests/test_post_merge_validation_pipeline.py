import subprocess
from pathlib import Path

from estate.core.operational_targets import OperationalTarget
from estate.core.post_merge_validation_pipeline import PipelineConfig, PostMergeValidationPipeline


def _git_repo(path: Path):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "file.txt").write_text("ok", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, check=True, text=True, capture_output=True).stdout.strip()


def _receipt(repo: Path, wp: str = "WP-X"):
    d = repo / "collaboration/work_packages/completions"; d.mkdir(parents=True, exist_ok=True)
    (d / f"{wp}_codex_done.json").write_text('{"work_package_id":"WP-X","codex_status":"done","completed_at":"now","branch":"main","summary":"done","files_changed":["file.txt"],"tests_run":["test"],"known_limitations":[],"ready_for_ca_review":true,"pull_request_url":"https://example.invalid/pr/1","merge_authority":"test"}', encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "receipt"], cwd=repo, check=True, capture_output=True)


def _target(repo: Path):
    return OperationalTarget("estate", "Estate", "git_repository", "Estate", local_path=str(repo), base_branch="main", capabilities=["git", "validation", "audit"], watch_state="enabled")


def test_clean_workspace_validator_prompt_and_ring2_required(tmp_path):
    repo = tmp_path / "repo"; _git_repo(repo); _receipt(repo); rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, capture_output=True).stdout.strip()
    calls = []
    def validator(wp, workspace):
        calls.append((wp, workspace)); assert workspace != repo; assert (workspace / "file.txt").exists()
        return {"validation_status": "passed", "failures": [], "findings": [], "warnings": []}
    req = {"audit_id": "a1", "target_id": "estate", "work_package_id": "WP-X", "source_reference": rev, "expected_files": ["file.txt"], "metadata": {"expected_revision": rev}}
    result = PostMergeValidationPipeline(PipelineConfig(tmp_path, tmp_path / "ws", tmp_path / "evidence"), validator=validator).run(req, _target(repo))
    assert result["verdict"] == "ring2_required"
    assert result["production_ready"] is True
    assert calls and not Path(result["workspace"]).exists()
    assert (tmp_path / result["artifacts"]["ring2_prompt"]).exists()
    assert result["provider_execution_performed"] is False
    assert result["dispatch_execution_performed"] is False


def test_active_tree_dirtiness_reported_not_stashed_and_wrong_revision_blocks(tmp_path):
    repo = tmp_path / "repo"; _git_repo(repo); _receipt(repo)
    (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
    req = {"audit_id": "a2", "target_id": "estate", "work_package_id": "WP-X", "source_reference": "badrev", "expected_files": ["missing.txt"], "metadata": {"expected_revision": "badrev"}}
    result = PostMergeValidationPipeline(PipelineConfig(tmp_path, tmp_path / "ws", tmp_path / "evidence"), validator=lambda *_: (_ for _ in ()).throw(AssertionError("validator should not run"))).run(req, _target(repo))
    assert result["verdict"] == "blocked"
    assert "active_tree_dirty_reported_not_repaired" in result["warnings"]
    assert "dirty.txt" in {p.name for p in repo.iterdir()}
    assert any("expected_revision_mismatch" in b for b in result["blocking_reasons"])
    assert any("expected_files_missing" in b for b in result["blocking_reasons"])


def test_validation_failure_and_production_readiness_false_blocks_acceptance(tmp_path):
    repo = tmp_path / "repo"; rev = _git_repo(repo); _receipt(repo)
    req = {"audit_id": "a3", "target_id": "estate", "work_package_id": "WP-X", "source_reference": rev, "expected_files": [], "metadata": {}}
    result = PostMergeValidationPipeline(PipelineConfig(tmp_path, tmp_path / "ws", tmp_path / "evidence"), validator=lambda *_: {"validation_status": "failed", "failures": ["no"], "findings": [], "warnings": []}).run(req, _target(repo))
    assert result["verdict"] == "validation_failed"
    assert result["production_ready"] is False
    assert result["ring2_status"] == "prompt_generated"
