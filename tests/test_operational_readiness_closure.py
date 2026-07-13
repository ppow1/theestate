import json, subprocess, sys
from pathlib import Path

from estate.core.operational_readiness_closure import OperationalReadinessClosureController


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)

def make_root(tmp_path, dirty=False, checks=2):
    root=tmp_path/'estate'; root.mkdir(parents=True); (root/'src/estate/core').mkdir(parents=True); (root/'src/estate/core/operational_readiness_closure.py').write_text('x=1\n'); (root/'.gitignore').write_text('runtime/\n')
    run(['git','init','-b','main'], root); run(['git','config','user.email','t@example.com'], root); run(['git','config','user.name','Tester'], root)
    run(['git','add','.'], root); run(['git','commit','-m','init'], root); sha=run(['git','rev-parse','HEAD'], root).stdout.strip()
    if dirty: (root/'dirty.txt').write_text('dirty')
    reg=root/'runtime/operational_targets/registry.json'; reg.parent.mkdir(parents=True)
    reg.write_text(json.dumps({'targets':[{'target_id':'estate-main','display_name':'Estate Main','target_type':'git_repository','owner_department':'Estate','repository_full_name':'ppow1/theestate','local_path':str(root),'aliases':['estate-main'],'environment_names':['estate-main'],'base_branch':'main','validation_root':None,'workspace_root':None,'watch_enabled':True,'watch_state':'enabled','capabilities':['git','validation','audit'],'acceptance_authority':'Chief Architect / Steward','office_surface':True,'classification':'Estate Internal','metadata':{'runtime_directories':['runtime/demo-required'],'allowed_remediations':['create_declared_runtime_directories','update_activation_ledger'],'activation_requirements':{'ledger':True},'observation_policy':{'checks_required':checks},'validation_recipe':[[sys.executable,'-c','print("ok")']]}}]}), encoding='utf-8')
    return root, sha

def test_full_flow_creates_prereq_activates_validates_observes_and_keeps_acceptance_false(tmp_path):
    root, sha=make_root(tmp_path, checks=2); ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-0650-DEMO', merge_commit=sha)
    first=ctl.process_one(c.case_id); assert first['state']=='observation_in_progress'; assert (root/'runtime/demo-required').exists()
    assert 'WP-0650' in (root/'operations/steward/estate_feature_activation_ledger.md').read_text()
    assert run(['git','status','--porcelain'], root).stdout == ''
    ledger_commit=run(['git','log','-1','--pretty=%B'], root).stdout
    assert 'Record activation ledger evidence for WP-0650-DEMO' in ledger_commit
    assert c.case_id in ledger_commit
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
    target=reg['targets'][0].copy(); target['target_id']='clean'; target['aliases']=['clean']; target['local_path']=str(clean_root); target['metadata']=target['metadata'].copy(); target['metadata']['activation_requirements']={'ledger':False}; reg['targets'].append(target)
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
    assert out['state'] in {'observation_in_progress','operationally_ready'}
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


def test_activation_ledger_retry_is_idempotent_and_clean(tmp_path):
    root, sha=make_root(tmp_path, checks=1); ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-IDEMP-LEDGER', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['state']=='operationally_ready'
    head_before=run(['git','rev-parse','HEAD'], root).stdout.strip()
    case=ctl.show(c.case_id)
    case['state']='assessment_required'
    (root/'runtime/operational_readiness/cases'/f"{c.case_id}.json").write_text(json.dumps(case))
    out=ctl.process_one(c.case_id)
    assert out['state']=='operationally_ready'
    assert run(['git','rev-parse','HEAD'], root).stdout.strip()==head_before
    assert run(['git','status','--porcelain'], root).stdout == ''


def test_activation_ledger_safe_failure_rolls_back_when_commit_cannot_be_created(tmp_path):
    root, sha=make_root(tmp_path, checks=1); ctl=OperationalReadinessClosureController(root)
    hooks=root/'.git'/'failing-hooks'; hooks.mkdir(); hook=hooks/'pre-commit'; hook.write_text('#!/bin/sh\nexit 1\n'); hook.chmod(0o755); run(['git','config','core.hooksPath',str(hooks)], root)
    c=ctl.create_or_resume(work_package_id='WP-NO-COMMITTER', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['state']=='blocked_manual_intervention'
    ledger=root/'operations/steward/estate_feature_activation_ledger.md'
    assert (not ledger.exists()) or 'WP-NO-COMMITTER' not in ledger.read_text()
    assert run(['git','status','--porcelain'], root).stdout == ''


def add_bare_origin(root):
    origin=root.parent/'origin.git'
    origin.mkdir(parents=True)
    run(['git','init','--bare'], origin)
    run(['git','remote','add','origin',str(origin)], root)
    run(['git','push','-u','origin','main'], root)
    return origin


def enable_publication_policy(root, *, authorized=True, production=False):
    reg=json.loads((root/'runtime/operational_targets/registry.json').read_text())
    md=reg['targets'][0]['metadata']
    md['upstream']='origin'; md['publication_required']=True; md['publication_authorized']=authorized
    md['allowed_remediations']=['create_declared_runtime_directories','update_activation_ledger','publish_controller_mutation']
    if production:
        md['production_target']=True
        md['live_target_path']=str(root)
        md['readiness_policy']={'production':True,'environment':'production','min_runtime_cycles':2,'compile_only_sufficient':False,'policy_version':'WP-0654-estate-main-production-readiness-v1'}
        md['observation_policy']={'checks_required':2,'min_elapsed_seconds':1,'health_checks':[[sys.executable,'-c','print("healthy")']], 'health_checks_not_applicable_rationale': None}
        md['validation_recipe']=[[sys.executable,'-c','print("live validation")']]
    (root/'runtime/operational_targets/registry.json').write_text(json.dumps(reg))


def test_authorized_publication_pushes_controller_commit_and_verifies_upstream(tmp_path):
    root, sha=make_root(tmp_path, checks=1); add_bare_origin(root); enable_publication_policy(root)
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-PUBLISH', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['publication']['status']=='verified'
    published=run(['git','merge-base','--is-ancestor',out['publication']['pre_local_head'],'origin/main'], root)
    assert published.returncode == 0
    assert run(['git','status','--porcelain'], root).stdout == ''
    assert run(['git','rev-list','--left-right','--count','main...origin/main'], root).stdout.strip() == '0\t0'


def test_publication_unauthorized_blocks_local_only_commit_from_readiness(tmp_path):
    root, sha=make_root(tmp_path, checks=1); add_bare_origin(root); enable_publication_policy(root, authorized=False)
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-NO-PUBLISH', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['state']=='blocked_manual_intervention'
    assert out['publication'] == {}
    assert run(['git','rev-list','--left-right','--count','main...origin/main'], root).stdout.split()[0] == '1'


def test_missing_production_policy_and_compile_only_zero_observation_blocks(tmp_path):
    root, sha=make_root(tmp_path, checks=1)
    reg=json.loads((root/'runtime/operational_targets/registry.json').read_text())
    md=reg['targets'][0]['metadata']; md['production_target']=True; md['activation_requirements']={'ledger':False}; md['runtime_directories']=[]; md['validation_recipe']=[[sys.executable,'-m','compileall','src/estate/core/operational_readiness_closure.py']]; md['observation_policy']={'checks_required':1,'min_elapsed_seconds':0}
    (root/'runtime/operational_targets/registry.json').write_text(json.dumps(reg))
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-PROD-POLICY', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['state']=='blocked_manual_intervention'
    assert any('production' in b['class'] for b in out['blockers'])


def test_explicit_policy_can_declare_gates_not_applicable(tmp_path):
    root, sha=make_root(tmp_path, checks=1)
    reg=json.loads((root/'runtime/operational_targets/registry.json').read_text())
    md=reg['targets'][0]['metadata']; md['production_target']=True; md['activation_requirements']={'ledger':False}; md['runtime_directories']=[]
    md['live_target_path']=str(root); md['readiness_policy']={'production':True,'environment':'production','min_runtime_cycles':1,'compile_only_sufficient':True,'compile_only_rationale':'repository-only target'}
    md['observation_policy']={'checks_required':1,'min_elapsed_seconds':0,'elapsed_time_not_applicable_rationale':'repository-only target','health_checks_not_applicable_rationale':'no service'}
    (root/'runtime/operational_targets/registry.json').write_text(json.dumps(reg))
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-PROD-EXPLICIT', merge_commit=sha)
    out=ctl.process_one(c.case_id)
    assert out['state']=='operationally_ready'
    verdict=json.loads((root/'runtime/operational_readiness/verdicts'/f"{c.case_id}.json").read_text())
    assert verdict['publication_required'] is False
    assert verdict['institutional_acceptance_granted'] is False


def test_recovery_publishes_safe_attributable_ahead_commit(tmp_path):
    root, sha=make_root(tmp_path, checks=1); add_bare_origin(root); enable_publication_policy(root)
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-RECOVER', merge_commit=sha)
    # Simulate residue: controller-authored local commit already exists, case resumes before publication.
    ctl.remediate(c,'update_activation_ledger')
    ahead=run(['git','rev-list','--left-right','--count','main...origin/main'], root).stdout.split()[0]
    assert ahead == '1'
    out=ctl.process_one(c.case_id)
    assert out['publication']['status']=='verified'
    assert run(['git','rev-list','--left-right','--count','main...origin/main'], root).stdout.strip() == '0\t0'


def test_manual_intake_cannot_weaken_canonical_production_policy(tmp_path):
    root, sha=make_root(tmp_path, checks=2); add_bare_origin(root); enable_publication_policy(root, production=True)
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-WEAKEN', merge_commit=sha, allowed_remediations=[], observation_policy={'checks_required':1}, validation_recipe=[[sys.executable,'-m','compileall','src/estate/core/operational_readiness_closure.py']])
    assert 'publish_controller_mutation' in c.allowed_remediations
    assert c.observation_policy['checks_required'] == 2
    assert 'compileall' not in ' '.join(' '.join(cmd) for cmd in c.validation_recipe)
    assert c.readiness_policy['policy_version'] == 'WP-0654-estate-main-production-readiness-v1'
    assert c.readiness_policy['policy_hash']


def test_legacy_case_rehydrates_canonical_policy_and_merge_discovery_matches(tmp_path):
    root, sha=make_root(tmp_path, checks=2); add_bare_origin(root); enable_publication_policy(root, production=True)
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-LEGACY', merge_commit=sha)
    path=root/'runtime/operational_readiness/cases'/f'{c.case_id}.json'
    data=json.loads(path.read_text()); data['readiness_policy']={}; data['allowed_remediations']=[]; data['observation_policy']={'checks_required':1}; path.write_text(json.dumps(data))
    shown=ctl.create_or_resume(work_package_id='WP-LEGACY', merge_commit=sha)
    assert shown.readiness_policy['policy_version'] == 'WP-0654-estate-main-production-readiness-v1'
    assert 'publish_controller_mutation' in shown.allowed_remediations
    discovery_dir = root / 'runtime/merge_discovery/discoveries'; discovery_dir.mkdir(parents=True)
    discovery_dir.joinpath('md-policy.json').write_text(json.dumps({'target_id':'estate-main','state':'discovered','work_package_id':'WP-MD-POLICY','source_commit':sha,'metadata':{}}))
    made=ctl.intake_from_merge_discovery()
    md_case=next(x for x in made if x['work_package_id']=='WP-MD-POLICY')
    assert md_case['readiness_policy']['policy_hash'] == shown.readiness_policy['policy_hash']


def test_false_ready_verdict_is_preserved_and_superseded_under_current_policy(tmp_path):
    root, sha=make_root(tmp_path, checks=1)
    reg=json.loads((root/'runtime/operational_targets/registry.json').read_text())
    md=reg['targets'][0]['metadata']; md['production_target']=True; md['activation_requirements']={'ledger':False}; md['runtime_directories']=[]
    md['live_target_path']=str(root); md['readiness_policy']={'production':True,'environment':'production','min_runtime_cycles':2,'compile_only_sufficient':False,'policy_version':'WP-0654-estate-main-production-readiness-v1'}
    md['validation_recipe']=[[sys.executable,'-m','compileall','src/estate/core/operational_readiness_closure.py']]
    md['observation_policy']={'checks_required':1,'min_elapsed_seconds':0}
    (root/'runtime/operational_targets/registry.json').write_text(json.dumps(reg))
    ctl=OperationalReadinessClosureController(root)
    c=ctl.create_or_resume(work_package_id='WP-FALSE-READY', merge_commit=sha)
    c.state='operationally_ready'; c.latest_validation={'status':'passed'}; c.observation={'status':'passed','checks_passed':1,'elapsed_seconds':0}; ctl.save(c)
    verdict_dir=root/'runtime/operational_readiness/verdicts'; verdict_dir.mkdir(parents=True)
    (verdict_dir/f'{c.case_id}.json').write_text(json.dumps({'readiness_case_id':c.case_id,'operationally_ready':True,'legacy_evidence':['kept']}))
    out=ctl.process_one(c.case_id)
    assert out['state'] == 'blocked_manual_intervention'
    verdict=json.loads((verdict_dir/f'{c.case_id}.json').read_text())
    assert verdict['superseded'] is True
    assert verdict['superseded_prior_verdict']['legacy_evidence'] == ['kept']
    assert (root/verdict['supersession_evidence']).is_file()
