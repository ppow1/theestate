import hashlib, json
from copy import deepcopy
from pathlib import Path
import pytest
from estate.portraits import PortraitValidationError, validate_catalog, validate_full_body_manifest, validate_full_body_sidecar
ROOT=Path(__file__).resolve().parents[1]
REG={r['id']:r for r in json.loads((ROOT/'data/registry/residents.json').read_text()) if r['status']=='Active'}
MAN=json.loads((ROOT/'data/portraits/residents/evelyn/full_body/manifest.json').read_text())
REGIONS=['crown_hair','head','neck','torso','pelvis','left_arm_hand','right_arm_hand','left_leg','right_leg','left_foot_shoe','right_foot_shoe']
def asset(tmp_path):
 p=tmp_path/'a.png';p.write_bytes(b'wp4120-test-image'); digest=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'schema_version':'full_body_asset_metadata_v1','asset_id':'a','resident_id':'evelyn','category':'neutral_front','lifecycle_state':'candidate','access_tier':'Estate Restricted','asset_path':'a.png','sha256':digest,'source_references':['identity','height','wardrobe','face'],'prompts':{'resident_binding':'evelyn'},'generation':{'model':'test','seed':1},'camera':{'focal_length_equivalent_mm':85,'distance_m':4,'height':'mid_torso','floor_plane':'level'},'crop':{'crown_hair_complete':True,'both_feet_and_footwear_complete':True,'visible_major_regions':list(REGIONS)},'pose':{'name':'neutral_front'},'physical_fidelity':{'height_check':'pass','proportion_check':'pass','posture_check':'pass'},'wardrobe':{'source_reference':'wardrobe'},'footwear':{'type':'pump','heel_height_in':3,'source_reference':'wardrobe','posture_effect_documented':True},'scale_reference':{'consistency_check':'pass'},'provenance':{'created_at':'2026-07-21T00:00:00Z','operator':'test'},'validation':{'state':'pass'},'steward_review':{'state':'pending'},'canonical':{'declared':False,'steward_approval':None},'lineage':{}}
def test_all_active_residents_have_ten_honestly_pending_categories():
 validate_catalog(ROOT)
 for resident in REG:
  key=resident.lower().replace('-','_'); m=json.loads((ROOT/f'data/portraits/residents/{key}/full_body/manifest.json').read_text())
  assert len(m['categories'])==10 and all(c['state']=='pending_generation' and c['evidence'] is None for c in m['categories'])
def test_manifest_rejects_cross_resident_binding():
 m=deepcopy(MAN);m['resident_template_binding']='grace'
 with pytest.raises(PortraitValidationError,match='cross-resident'):validate_full_body_manifest(m,root=ROOT,registry_record=REG['evelyn'])
def test_manifest_rejects_missing_review():
 m=deepcopy(MAN);m['steward_review'].pop('state')
 with pytest.raises(PortraitValidationError,match='missing Steward'):validate_full_body_manifest(m,root=ROOT,registry_record=REG['evelyn'])
@pytest.mark.parametrize(('mutation','message'),[
 (lambda a:a['crop'].__setitem__('both_feet_and_footwear_complete',False),'cropped feet'),
 (lambda a:a['crop'].__setitem__('crown_hair_complete',False),'cropped crown'),
 (lambda a:a['crop']['visible_major_regions'].remove('torso'),'missing major'),
 (lambda a:a['footwear'].pop('source_reference'),'footwear'),
 (lambda a:a['footwear'].__setitem__('posture_effect_documented',False),'posture'),
 (lambda a:a['camera'].__setitem__('focal_length_equivalent_mm',24),'perspective distortion'),
 (lambda a:a['provenance'].pop('operator'),'missing provenance'),
 (lambda a:a['prompts'].__setitem__('resident_binding','grace'),'cross-resident'),
])
def test_asset_validation_rejects_objective_failures(tmp_path,mutation,message):
 a=asset(tmp_path);mutation(a)
 with pytest.raises(PortraitValidationError,match=message):validate_full_body_sidecar(a,root=tmp_path,resident_id='evelyn')
def test_scale_flag_blocks_false_canon(tmp_path):
 a=asset(tmp_path); a['lifecycle_state']='canonical';a['canonical']={'declared':True,'steward_approval':'approval.json'};a['scale_reference']['consistency_check']='flag'
 (tmp_path/'approval.json').write_text(json.dumps({'authority':'steward','decision':'approve','asset_id':'a','sha256':a['sha256']}))
 with pytest.raises(PortraitValidationError,match='flagged asset'):validate_full_body_sidecar(a,root=tmp_path,resident_id='evelyn')
def test_candidate_cannot_be_presented_as_canon(tmp_path):
 a=asset(tmp_path);a['canonical']['declared']=True
 with pytest.raises(PortraitValidationError,match='presented as canon'):validate_full_body_sidecar(a,root=tmp_path,resident_id='evelyn')
