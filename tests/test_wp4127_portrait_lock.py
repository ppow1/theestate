import hashlib, json, subprocess, sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from estate.portraits.lock import REQUIRED_SLOTS, CHECKS, record_hash, resolve_canonical, validate_lock
ROOT=Path(__file__).resolve().parents[1]
FILES=sorted((ROOT/'tests/fixtures/portrait_consistency').glob('*.bin'))

def provisional():
    return json.loads((ROOT/'data/visual_bibles/locks/evelyn_portrait_lock.provisional.example.json').read_text())
def rehash(r): r['lock_hash']=record_hash(r); return r
def canonical():
    r=provisional(); r['state']='canonical'; r['blocking_findings']=[]
    r['steward_decision']={'explicit_approval':True,'authority_role':'Steward','decision_id':'synthetic-test-decision','steward_id':'test-steward','decided_at':'2026-07-21T00:00:00Z','signed_record_sha256':'sha256:'+'a'*64}
    for slot,path in zip(r['slots'],FILES):
        rel=str(path.relative_to(ROOT)); digest='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
        slot['state']='canonical'; slot['asset']={'asset_id':'test-'+slot['category'],'path':rel,'sha256':digest,'catalog_ref':'fixture-only'}
        slot['acceptance_evidence']={x:{'result':'pass','evidence_ref':'synthetic-test:'+x} for x in CHECKS}
    return rehash(r)

def codes(result): return {x['code'] for x in result['diagnostics']}
def test_provisional_example_is_valid_but_not_canonical():
    result=validate_lock(provisional(),root=ROOT)
    assert result['status']=='pass' and not result['canonical'] and result['may_grant_steward_approval'] is False
    assert result['coverage']=={'required':10,'represented':10,'canonical':0}
def test_fully_evidenced_synthetic_record_resolves_only_for_tests():
    r=canonical(); assert validate_lock(r,root=ROOT)['canonical']
    result=resolve_canonical([r],'evelyn','hero_portrait',root=ROOT)
    assert result['status']=='resolved' and result['lock_hash']==r['lock_hash']
def test_hash_tamper_missing_file_and_incomplete_evidence_fail():
    r=canonical(); r['slots'][0]['asset']['path']='missing.png'; r['slots'][1]['acceptance_evidence'].pop('crop'); rehash(r)
    assert {'PCL-FILE-MISSING-001','PCL-EVIDENCE-001'} <= codes(validate_lock(r,root=ROOT))
    r['lock_hash']='sha256:'+'0'*64
    assert 'PCL-LOCK-HASH-001' in codes(validate_lock(r,root=ROOT))
def test_missing_duplicate_and_reused_asset_are_blocking():
    r=canonical(); r['slots'].pop(); r['slots'].append(deepcopy(r['slots'][0])); rehash(r)
    assert {'PCL-COVERAGE-001','PCL-UNIQUE-001','PCL-ASSET-REUSE-001'} <= codes(validate_lock(r,root=ROOT))
def test_stale_downstream_and_approval_conflict():
    r=canonical(); r['reviewed_at']='2020-01-01T00:00:00Z'; r['downstream_references']=[{'consumer':'x','lock_hash':'sha256:'+'0'*64}]; rehash(r)
    assert {'PCL-STALE-001','PCL-DOWNSTREAM-STALE-001'} <= codes(validate_lock(r,root=ROOT,now=datetime(2026,7,21,tzinfo=timezone.utc)))
    p=provisional(); p['steward_decision']={'explicit_approval':True}; rehash(p)
    assert 'PCL-APPROVAL-CONFLICT-001' in codes(validate_lock(p,root=ROOT))
def test_noncanonical_missing_and_ambiguous_resolution_fail_closed():
    assert resolve_canonical([provisional()],'evelyn','hero_portrait',root=ROOT)['status']=='unavailable'
    r=canonical(); assert resolve_canonical([r,deepcopy(r)],'evelyn','hero_portrait',root=ROOT)['code']=='PCL-RESOLVE-AMBIGUOUS-001'
def test_cli_schemas_templates_and_reports(tmp_path):
    out=tmp_path/'report.json'; run=subprocess.run([sys.executable,'-m','estate.portraits.lock',str(ROOT/'data/visual_bibles/locks/evelyn_portrait_lock.provisional.example.json'),'--root',str(ROOT),'--output',str(out)],cwd=ROOT,env={'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
    assert run.returncode==0 and not json.loads(out.read_text())['canonical']
    for p in (ROOT/'data/schemas/visual_bible/locks').glob('*.json'): json.loads(p.read_text())
    for name in ['WP-4127_CAMPAIGN_02_COMPLETION_REPORT.md','WP-4127_TRACEABILITY_MATRIX.md','WP-4127_COVERAGE_REPORT.md','WP-4127_UNRESOLVED_RESIDENT_DATA.md','WP-4127_LOCAL_GENERATION_READINESS.md']: assert (ROOT/'reports/visual_campaign_02'/name).is_file()
