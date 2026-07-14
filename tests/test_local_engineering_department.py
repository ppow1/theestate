from estate.core.local_engineering_department import LocalEngineeringDepartment


def test_closed_loop_creates_externalized_evidence_and_governance(tmp_path):
    result = LocalEngineeringDepartment(root=tmp_path).run_closed_loop()
    assert result.work_packages == ["WP-0548", "WP-0549", "WP-0550", "WP-0551", "WP-0552"]
    assert result.result == "completed"
    assert result.runtime_root == r"A:\AI\Tools\EngineeringWorkerRuntime"
    assert result.evidence["external_worktree"].startswith(r"A:\AI\EngineeringWorktrees")
    assert result.evidence["external_evidence"].startswith(r"A:\AI\EngineeringRuns")
    assert (tmp_path / result.governance_record).exists()
    assert (tmp_path / "runtime/workforce_development/status/latest.json").exists()
    assert (tmp_path / "runtime/operations/grace/status/latest.json").exists()
    assert (tmp_path / "runtime/execution_dispatch/queue.json").exists()
    assert result.evidence["sha256"]["worker_result.json"]
