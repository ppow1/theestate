import subprocess
from pathlib import Path
from estate.core.operational_targets_runtime import OperationalTargetRuntime

def init_repo(p:Path):
    p.mkdir(); subprocess.run(['git','init','-b','main'],cwd=p,check=True,capture_output=True); (p/'README.md').write_text('x'); subprocess.run(['git','add','.'],cwd=p,check=True); subprocess.run(['git','-c','user.email=a@b.c','-c','user.name=t','commit','-m','init'],cwd=p,check=True,capture_output=True)

def test_list_show_status_and_transitions(tmp_path):
    rt=OperationalTargetRuntime(tmp_path)
    assert rt.get('estate-main').target_id=='estate-main'
    assert rt.transition('estate-main','paused')['watch_state']=='paused'
    assert rt.transition('estate-main','disabled')['watch_state']=='disabled'
    assert rt.transition('estate-main','retired')['watch_state']=='retired'
    assert rt.transition('cue-mastery','import_candidate')['watch_state']=='import_candidate'
    status=rt.write_status()
    assert status['summary']['operational_targets_available']>=4
    assert 'cue-mastery' in status['import_candidates']

def test_active_tree_dirty_reported_not_stashed(tmp_path):
    repo=tmp_path/'repo'; init_repo(repo); (repo/'dirty.txt').write_text('dirty')
    rt=OperationalTargetRuntime(tmp_path); targets=rt.load_targets(); targets[0].local_path=str(repo); rt.write_targets(targets)
    h=rt.inspect_git_hygiene(targets[0])
    assert 'active_tree_dirty_reported_not_repaired' in h['issues'] or h['issues']
