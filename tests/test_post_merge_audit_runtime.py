import subprocess
from pathlib import Path
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.post_merge_audit_runtime import PostMergeAuditRuntime

def init_repo(p:Path):
    p.mkdir(); subprocess.run(['git','init','-b','main'],cwd=p,check=True,capture_output=True); (p/'README.md').write_text('x'); subprocess.run(['git','add','.'],cwd=p,check=True); subprocess.run(['git','-c','user.email=a@b.c','-c','user.name=t','commit','-m','init'],cwd=p,check=True,capture_output=True)

def test_dirty_workspace_blocks_audit_and_prompt_without_ollama(tmp_path):
    repo=tmp_path/'repo'; init_repo(repo); (repo/'dirty.txt').write_text('dirty')
    otr=OperationalTargetRuntime(tmp_path); targets=otr.load_targets(); targets[0].local_path=str(repo); targets[0].workspace_root=str(repo); otr.write_targets(targets)
    rt=PostMergeAuditRuntime(tmp_path); req=rt.create_request('estate-main','WP-0618',expected_files=[]); v=rt.run_audit(req)
    assert v.verdict=='needs_repair'
    assert v.provider_execution_performed is False and v.dispatch_execution_performed is False
    assert (tmp_path/v.artifacts['ring2_prompt']).exists()

def test_expected_files_missing_blocks_audit(tmp_path):
    repo=tmp_path/'repo'; init_repo(repo)
    otr=OperationalTargetRuntime(tmp_path); targets=otr.load_targets(); targets[0].local_path=str(repo); targets[0].workspace_root=str(repo); otr.write_targets(targets)
    rt=PostMergeAuditRuntime(tmp_path); req=rt.create_request('estate-main','WP-0618',expected_files=['missing.txt']); v=rt.run_audit(req)
    assert 'expected_files_missing: missing.txt' in v.blocking_reasons

def test_background_watch_creates_post_merge_request(tmp_path):
    from estate.core.background_operations_runtime import BackgroundOperationsRuntime
    status=BackgroundOperationsRuntime(tmp_path).run_cycle(write=True)
    assert status['provider_execution_performed'] is False
    assert (tmp_path/'runtime/post_merge_audit/requests').exists()
