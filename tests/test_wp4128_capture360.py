import hashlib, json, subprocess, sys
from copy import deepcopy
from pathlib import Path
import pytest
from estate.portraits.capture360 import (ANGLES, ANGLE_DEGREES, deterministic_directory,
    deterministic_filename, validate_capture_set)
ROOT=Path(__file__).resolve().parents[1]
def fixture(): return json.loads((ROOT/'tests/fixtures/capture_360/valid_pending_manifest.json').read_text())
def codes(result): return {x['code'] for x in result['diagnostics']}

def test_required_angles_are_clockwise_and_exact():
    assert ANGLES == ('front','front_left_45','left_profile','rear_left_45','rear','rear_right_45','right_profile','front_right_45')
    assert [ANGLE_DEGREES[x] for x in ANGLES] == list(range(0,360,45))

def test_deterministic_storage_and_filename():
    assert str(deterministic_directory('evelyn','canonical_flat','pending')) == 'data/visual_bibles/residents/evelyn/internal/capture_360/review/canonical_flat'
    assert deterministic_filename('evelyn','canonical_flat','front','neutral_flat','review_neutral','candidate',2) == 'evelyn__canonical_flat__front__neutral_flat__review_neutral__candidate__r002.png'
    with pytest.raises(ValueError): deterministic_filename('Evelyn','x','front','flat','look','candidate',1)

def test_complete_enumeration_can_be_honestly_pending():
    result=validate_capture_set(fixture())
    assert result['status']=='pass' and result['coverage']=={'required':8,'represented':8,'materialized':0}
    assert result['complete'] is False and result['comparison_compatible'] is False

def test_missing_duplicate_angle_and_control_drift_fail():
    m=fixture(); m['angles'].pop(); m['angles'].append(deepcopy(m['angles'][0])); m['angles'][0]['controls_fingerprint']='0'*64
    assert {'C360-ANGLE-001','C360-COVERAGE-001','C360-CONSISTENCY-001'} <= codes(validate_capture_set(m))

def test_tolerance_heel_and_pending_asset_fail_closed():
    m=fixture(); m['angles'][0]['observed_degrees']=9; m['angles'][0]['asset']={'path':'invented.png'}
    m['controls']['footwear']={'variant':'heel','id':'heel_without_height'}
    assert {'C360-TOLERANCE-002','C360-PENDING-ASSET-001','C360-FOOTWEAR-002','C360-CONSISTENCY-001'} <= codes(validate_capture_set(m))

def test_materialized_hash_and_accepted_incomplete_are_rejected(tmp_path):
    m=fixture(); m['state']='accepted'; m['angles'][0]['state']='candidate'; m['angles'][0]['asset']={'path':'missing.png','sha256':'sha256:'+'0'*64,'generation_receipt_ref':'receipt'}
    found=codes(validate_capture_set(m,root=tmp_path))
    assert {'C360-FILE-001','C360-ACCEPT-INCOMPLETE-001','C360-APPROVAL-001'} <= found

def test_all_resident_manifests_are_honestly_blocked_and_cli_works(tmp_path):
    manifests=list((ROOT/'data/visual_bibles/residents').glob('*/internal/capture_360/review/canonical_flat/capture_set_manifest.pending.json'))
    assert len(manifests)==8
    for path in manifests:
        m=json.loads(path.read_text()); assert m['state']=='incomplete' and all(x['state']=='pending' and not x['asset'] for x in m['angles'])
        assert 'C360-HEIGHT-001' in codes(validate_capture_set(m))
    out=tmp_path/'result.json'
    run=subprocess.run([sys.executable,'-m','estate.portraits.capture360',str(ROOT/'tests/fixtures/capture_360/valid_pending_manifest.json'),'--root',str(ROOT),'--output',str(out)],cwd=ROOT,env={'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
    assert run.returncode==0 and json.loads(out.read_text())['complete'] is False

def test_json_schemas_templates_queue_and_docs_exist():
    for p in (ROOT/'data/schemas/visual_bible/capture_360').glob('*.json'): json.loads(p.read_text())
    q=json.loads((ROOT/'data/visual_bibles/capture_360/campaign_03_generation_queue.json').read_text())
    assert q['state']=='pending' and len(q['capture_sets'])==8 and all(not x['materialized_angles'] for x in q['capture_sets'])
    assert (ROOT/'docs/visual_bible/wp4128_360_capture_standard_runtime_canon.md').is_file()
