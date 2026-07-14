import json
import shutil
from pathlib import Path

import pytest

from estate.core.local_engineering_department import (
    DEFAULT_RUNTIME_ROOT,
    LocalEngineeringDepartment,
    external_path,
)

SOURCE_RUNTIME = Path("external/engineering_worker_runtime")


def materialize_runtime(root: Path, *, version: str = "1.0.0") -> Path:
    runtime = external_path(DEFAULT_RUNTIME_ROOT, estate_root=root)
    shutil.copytree(SOURCE_RUNTIME, runtime, dirs_exist_ok=True)
    manifest_path = runtime / "runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = version
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return runtime


def test_closed_loop_creates_externalized_evidence_and_governance(tmp_path):
    materialize_runtime(tmp_path)
    result = LocalEngineeringDepartment(root=tmp_path).run_closed_loop()
    assert result.work_packages == ["WP-0548", "WP-0549", "WP-0550", "WP-0551", "WP-0552"]
    assert result.result == "completed"
    assert result.runtime_root == r"A:\AI\Tools\EngineeringWorkerRuntime"
    assert result.evidence["external_worktree"].startswith(r"A:\AI\EngineeringWorktrees")
    assert result.evidence["external_evidence"].startswith(r"A:\AI\EngineeringRuns")
    assert "host_worktree" not in result.evidence
    assert "host_evidence" not in result.evidence
    record = tmp_path / result.governance_record
    assert record.exists()
    assert (tmp_path / "runtime/workforce_development/status/latest.json").exists()
    assert (tmp_path / "runtime/operations/grace/status/latest.json").exists()
    assert (tmp_path / "runtime/execution_dispatch/queue.json").exists()
    assert result.evidence["sha256"]["worker_result.json"]
    assert not (tmp_path / "runtime/local_engineering_department" / "worker_result.json").exists()


def test_estate_adapter_no_longer_installs_embedded_worker(tmp_path):
    department = LocalEngineeringDepartment(root=tmp_path)
    with pytest.raises(RuntimeError, match="Embedded runtime installation has been removed"):
        department.install_runtime()
    source = Path("src/estate/core/local_engineering_department.py").read_text(encoding="utf-8")
    assert "worker.write_text" not in source
    assert "Invoke-EngineeringWorker.ps1\")\n        worker.write_text" not in source


def test_external_runtime_manifest_is_validated(tmp_path):
    materialize_runtime(tmp_path)
    manifest = LocalEngineeringDepartment(root=tmp_path).adapter.validate_manifest()
    assert manifest["runtime_id"] == "engineering-worker-runtime"
    assert manifest["version"] == "1.0.0"
    assert manifest["canonical_runtime_root"] == r"A:\AI\Tools\EngineeringWorkerRuntime"


def test_missing_or_mismatched_runtime_fails_closed(tmp_path):
    with pytest.raises(RuntimeError, match="manifest is missing"):
        LocalEngineeringDepartment(root=tmp_path).run_closed_loop()
    materialize_runtime(tmp_path, version="0.0.0")
    with pytest.raises(RuntimeError, match="version mismatch"):
        LocalEngineeringDepartment(root=tmp_path).run_closed_loop()


def test_bounded_package_paths_are_enforced(tmp_path):
    materialize_runtime(tmp_path)
    adapter = LocalEngineeringDepartment(root=tmp_path).adapter
    package = tmp_path / "unbounded.json"
    package.write_text("{}", encoding="utf-8")
    worktree = external_path(r"A:\AI\EngineeringWorktrees", estate_root=tmp_path) / "run"
    evidence = external_path(r"A:\AI\EngineeringRuns", estate_root=tmp_path) / "run"
    worktree.mkdir(parents=True)
    evidence.mkdir(parents=True)
    with pytest.raises(ValueError):
        adapter.invoke(package_path=package, worktree_path=worktree, evidence_path=evidence)


def test_helen_grace_and_dispatch_boundaries_remain_unchanged(tmp_path):
    materialize_runtime(tmp_path)
    result = LocalEngineeringDepartment(root=tmp_path).run_closed_loop()
    assessment = json.loads(next((tmp_path / "runtime/workforce_development/assessments").glob("*.json")).read_text(encoding="utf-8"))
    assert "Dispatch remains the handoff authority" in assessment["institutional_factors"]
    objective = json.loads(next((tmp_path / "runtime/operations/grace/objectives").glob("*.json")).read_text(encoding="utf-8"))
    assert objective["owner"] == "local-engineering-worker-001"
    queue = json.loads((tmp_path / "runtime/execution_dispatch/queue.json").read_text(encoding="utf-8"))
    item = next(item for item in queue["items"] if item["dispatch_id"] == result.dispatch_id)
    assert item["requested_by"] == "Grace"
    assert item["result_reference"].startswith(r"A:\AI\EngineeringRuns")


def test_estate_records_references_and_hashes_not_raw_execution_artifacts(tmp_path):
    materialize_runtime(tmp_path)
    result = LocalEngineeringDepartment(root=tmp_path).run_closed_loop()
    record = json.loads((tmp_path / result.governance_record).read_text(encoding="utf-8"))
    evidence = record["evidence"]
    assert evidence["external_evidence"].startswith(r"A:\AI\EngineeringRuns")
    assert evidence["sha256"]["worker_result.json"]
    assert "External runtime received" not in json.dumps(record)
