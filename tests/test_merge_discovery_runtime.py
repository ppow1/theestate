import json, subprocess
from pathlib import Path
from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.background_operations_runtime import BackgroundOperationsRuntime
from estate.core.merge_discovery_runtime import MergeDiscoveryRuntime
from estate.core.operations_runtime import OperationsRuntime
from estate.core.steward_command_center import generate_command_center

def git(r,*a): return subprocess.run(["git",*a],cwd=r,text=True,capture_output=True,check=True).stdout.strip()
def setup(tmp):
    r=tmp/"repo"; r.mkdir(parents=True); git(r,"init","-b","main"); git(r,"config","user.email","t@example.com"); git(r,"config","user.name","T")
    (r/"README.md").write_text("ok"); git(r,"add","."); git(r,"commit","-m","init")
    d=r/"collaboration/work_packages/completions"; d.mkdir(parents=True)
    (d/"WP-0623_codex_done.json").write_text(json.dumps({"work_package_id":"WP-0623","files_changed":["README.md"],"ready_for_ca_review":True}))
    git(r,"add","."); git(r,"commit","-m","Complete WP-0623")
    OperationalTargetRuntime(tmp).write_targets([OperationalTarget("estate-main","Estate Main","git_repository","Estate",local_path=str(r),aliases=["estate"],base_branch="main",capabilities=["git","validation","audit"],watch_state="enabled")])
    BackgroundOperationsRuntime(tmp).write_watches([]); return r

def test_request_compatible_and_runtime_discovers_then_processes(tmp_path, monkeypatch):
    setup(tmp_path)
    monkeypatch.setattr("estate.core.post_merge_validation_pipeline.PostMergeValidationPipeline._standard_validator", lambda self, wp, workspace: {"validation_status":"passed","failures":[],"findings":[],"warnings":[]})
    cycle=OperationsRuntime(tmp_path).run_cycle(mode="discover-merges-and-process-audits")
    assert cycle["audit_requests_created_from_merges"]==1
    assert cycle["audits_claimed"]==1
    assert cycle["provider_execution_performed"] is False and cycle["dispatch_execution_performed"] is False
    req=json.loads(next((tmp_path/"runtime/post_merge_audit/requests").glob("*.json")).read_text())
    assert {"audit_id","target_id","work_package_id","source_kind","source_reference","expected_files","metadata","state"}.issubset(req)

def test_cli_runtime_status_candidates_and_office_summary(tmp_path):
    setup(tmp_path)
    out=MergeDiscoveryRuntime(tmp_path).scan("estate-main")
    assert MergeDiscoveryRuntime(tmp_path).status("estate-main")["summary"]["merge_discovery_available"] is True
    assert "candidates" in MergeDiscoveryRuntime(tmp_path).candidates("estate-main")
    office=generate_command_center(tmp_path, write=False)["status_bar"]
    assert office["merge_discovery_available"] is True
    assert office["latest_discovered_work_package"]=="WP-0623"
    assert out["provider_execution_performed"] is False and out["dispatch_execution_performed"] is False
