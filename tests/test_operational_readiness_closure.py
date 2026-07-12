import json, subprocess, sys
from pathlib import Path

from estate.core.operational_readiness_closure import OperationalReadinessClosureController


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)

def make_root(tmp_path, dirty=False, checks=2):
    root=tmp_path/'estate'; root.mkdir(parents=True); (root/'src/estate/core').mkdir(parents=True); (root/'src/estate/core/operational_readiness_closure.py').write_text('x=1\n'); (root/'.gitignore').write_text('runtime/\noperations/\n')
    run(['git','init','-b','main'], root); run(['git','config','user.email','t@example.com'], root); run(['git','config','user.name','Tester'], root)
    run(['git','add','.'], root); run(['git','commit','-m','init'], root); sha=run(['git','rev-parse','HEAD'], root).stdout.strip()
    if dirty: (root/'dirty.txt').write_text('dirty')
    reg=root/'runtime/operational_targets/registry.json'; reg.parent.mkdir(parents=True)
    reg.write_text(json.dumps({'targets':[{'target_id':'estate-main','display_name':'Estate Main','target_type':'git_repository','owner_department':'Estate','repository_full_name':'ppow1/theestate','local_path':str(root),'aliases':['estate-main'],'environment_names':['estate-main'],'base_branch':'main','validation_root':None,'workspace_root':None,'watch_enabled':True,'watch_state':'enabled','capabilities':['git','validation','audit'],'acceptance_authority':'Chief Architect / Steward','office_surface':True,'classification':'Estate Internal','metadata':{'runtime_directories':['runtime/demo-required'],'allowed_remediations':['create_declared_runtime_directories','update_activation_ledger'],'activation_requirements':{'ledger':True},'observation_policy':{'checks_required':checks},'validation_recipe':[[sys.executable,'-c','print("ok")']]}}]}), encoding='utf-8')
    return root, sha

def test_full_flow_creates_prereq_activates_validates_observes_and_keeps_acceptance_false(tmp_path):
    root, sha=make_root(tmp_path, checks=2); ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-0650-DEMO', merge_commit=sha)
    first=ctl.process_one(c.case_id); assert first['state']=='assessment_required'; assert (root/'runtime/demo-required').exists()
    second=ctl.process_one(c.case_id); assert second['state']=='assessment_required'; assert 'WP-0650' in (root/'operations/steward/estate_feature_activation_ledger.md').read_text()
    third=ctl.process_one(c.case_id); assert third['state']=='observation_in_progress'
    fourth=ctl.process_one(c.case_id); assert fourth['state']=='operationally_ready'
    verdict=json.loads((root/'runtime/operational_readiness/verdicts'/f"{c.case_id}.json").read_text())
    assert verdict['operationally_ready'] is True
    assert verdict['institutional_acceptance_granted'] is False

def test_dirty_checkout_blocks_without_modification(tmp_path):
    root, sha=make_root(tmp_path, dirty=True); ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-DIRTY', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['state']=='blocked_manual_intervention'
    assert 'dirty.txt' in run(['git','status','--porcelain'], root).stdout

def test_idempotent_case_and_pause_resume_acknowledge(tmp_path):
    root, sha=make_root(tmp_path); ctl=OperationalReadinessClosureController(root)
    a=ctl.create_or_resume(work_package_id='WP-IDEMP', merge_commit=sha); b=ctl.create_or_resume(work_package_id='WP-IDEMP', merge_commit=sha)
    assert a.case_id==b.case_id
    assert ctl.pause(a.case_id)['paused'] is True
    assert ctl.resume(a.case_id)['paused'] is False
    ctl.acknowledge(a.case_id, 'cleared')
    assert ctl.show(a.case_id)['state']=='assessment_required'

def test_blocked_case_does_not_starve_other_case(tmp_path):
    root, sha=make_root(tmp_path, dirty=True); ctl=OperationalReadinessClosureController(root)
    blocked=ctl.create_or_resume(work_package_id='WP-BLOCK', merge_commit=sha)
    clean_root, clean_sha=make_root(tmp_path/'clean')
    # Use same controller root: make second target clean in registry.
    reg=json.loads((root/'runtime/operational_targets/registry.json').read_text())
    target=reg['targets'][0].copy(); target['target_id']='clean'; target['local_path']=str(clean_root); reg['targets'].append(target)
    (root/'runtime/operational_targets/registry.json').write_text(json.dumps(reg))
    ready=ctl.create_or_resume(work_package_id='WP-CLEAN', merge_commit=clean_sha, target_id='clean')
    cycle=ctl.run_cycle(limit=2)
    states={r['work_package_id']:r['state'] for r in cycle['results']}
    assert states['WP-BLOCK']=='blocked_manual_intervention'
    assert states['WP-CLEAN'] in {'assessment_required','observation_required','observation_in_progress','operationally_ready'}

def test_merge_discovery_intake_and_descendant_ancestry_validation(tmp_path):
    root, sha = make_root(tmp_path)
    (root / 'live.txt').write_text('live')
    run(['git','add','live.txt'], root); run(['git','commit','-m','descendant'], root)
    discovery_dir = root / 'runtime/merge_discovery/discoveries'; discovery_dir.mkdir(parents=True)
    discovery_dir.joinpath('md.json').write_text(json.dumps({
        'target_id':'estate-main','state':'discovered','work_package_id':'WP-0651',
        'source_commit':sha,'completion_receipt_path':'collaboration/work_packages/completions/WP-0651.json',
        'metadata':{'changed_paths':['src/estate/core/operational_readiness_closure.py']}
    }))
    ctl=OperationalReadinessClosureController(root)
    made=ctl.intake_from_merge_discovery()
    assert made[0]['work_package_id']=='WP-0651'
    out=ctl.process_one(made[0]['case_id'])
    assert out['state']=='assessment_required'
    assessment=json.loads(next((root/'runtime/operational_readiness/evidence'/made[0]['case_id']).glob('assessment_*.json')).read_text())
    assert assessment['required_merge_commit_present'] is True


def test_validation_runs_against_declared_live_target_not_controller_root(tmp_path):
    root, sha=make_root(tmp_path)
    live=tmp_path/'live-target'; live.mkdir()
    run(['git','init','-b','main'], live); run(['git','config','user.email','t@example.com'], live); run(['git','config','user.name','Tester'], live)
    (live/'target_only.txt').write_text('ok')
    run(['git','add','.'], live); run(['git','commit','-m','target'], live); live_sha=run(['git','rev-parse','HEAD'], live).stdout.strip()
    reg=json.loads((root/'runtime/operational_targets/registry.json').read_text())
    reg['targets'][0]['local_path']=str(live)
    reg['targets'][0]['metadata']['runtime_directories']=[]
    reg['targets'][0]['metadata']['activation_requirements']={'ledger':False}
    reg['targets'][0]['metadata']['validation_recipe']=[[sys.executable,'-c','from pathlib import Path; assert Path("target_only.txt").exists()']]
    (root/'runtime/operational_targets/registry.json').write_text(json.dumps(reg))
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-LIVE', merge_commit=live_sha)
    out=ctl.process_one(c.case_id)
    if out['latest_validation'] is None:
        out=ctl.process_one(c.case_id)
    assert out['latest_validation']['status']=='passed'
    assert out['latest_validation']['live_target_path']==str(live)
    assert out['latest_validation']['repository_local_simulation'] is False
