import hashlib, json
from copy import deepcopy
from pathlib import Path
import pytest
from estate.portraits import PortraitValidationError, validate_catalog, validate_three_quarter_manifest, validate_three_quarter_sidecar
ROOT=Path(__file__).resolve().parents[1]
REG={x['id']:x for x in json.loads((ROOT/'data/registry/residents.json').read_text()) if x['status']=='Active'}
MAN=json.loads((ROOT/'data/portraits/residents/evelyn/three_quarter/manifest.json').read_text())

def asset(tmp_path):
 p=tmp_path/'a.png'; p.write_bytes(b'wp4122 fixture'); h=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'schema_version':'three_quarter_asset_metadata_v1','asset_id':'a','resident_id':'evelyn','angle':'front_left_three_quarter','set_type':'technical','lifecycle_state':'candidate','asset_path':'a.png','sha256':h,
 'source_references':['hero','face','scale','wardrobe'],'cross_angle_links':{'frontal':'front','left_profile':'lp','right_profile':'rp','rear':'rear'},
 'prompts':{'resident_binding':'evelyn','positive_template_revision':1,'negative_template_revision':1},'generation':{'model':'test','version':'1','seed':1,'settings':{}},
 'camera':{'focal_length_equivalent_mm':85,'distance_m':2.5,'height_m':1.4,'pitch_degrees':0,'roll_degrees':0},'crop':{'type':'portrait','required_regions_complete':True},
 'pose':{'classification':'neutral','weight_distribution':'balanced'},'orientation':{'body_yaw_degrees':-45,'head_yaw_degrees':-35,'eye_direction':'camera','facing':'front','visible_side':'left'},
 'identity_fidelity':{'face':'pass','visual_fingerprint':'pass','recognizable':'pass'},'geometry':{x:'documented' for x in ['face','visual_fingerprint','hair','ears','jaw','neck','shoulders','back','waist','hips','limbs','posture','silhouette']},
 'physical_fidelity':{'height':'pass','scale':'pass','proportion':'pass','weight_distribution':'pass'},'wardrobe_grooming':{'continuity_checks':{'wardrobe':'pass','accessories':'pass','hair':'pass'}},
 'provenance':{'created_at':'2026-07-21T00:00:00Z','operator':'test'},'validation':{'state':'pass','diagnostics':[]},'hidden_caption_test':{'state':'pass'},'steward_review':{'state':'pending'},'canonical':{'declared':False,'steward_approval':None},'lineage':{'predecessor':None,'successor':None}}

def test_catalog_and_active_resident_pending_coverage():
 validate_catalog(ROOT)
 cat=json.loads((ROOT/'data/portraits/estate_portrait_catalog.json').read_text())
 assert len(cat['residents'])==8
 for r in cat['residents']:
  m=json.loads((ROOT/r['three_quarter_manifest_path']).read_text())
  assert len(m['required_slots'])==4 and all(s['state']=='pending_generation' and s['evidence'] is None for s in m['required_slots'])
  assert not m['candidates'] and not any(m['canonical'].values())
  validate_three_quarter_manifest(m,root=ROOT,registry_record=REG[r['resident_id']])

def test_manifest_rejects_missing_angle_and_cross_resident():
 m=deepcopy(MAN); m['required_slots'].pop()
 with pytest.raises(PortraitValidationError,match='missing required'): validate_three_quarter_manifest(m,root=ROOT,registry_record=REG['evelyn'])
 m=deepcopy(MAN); m['resident_template_binding']='grace'
 with pytest.raises(PortraitValidationError,match='cross-resident'): validate_three_quarter_manifest(m,root=ROOT,registry_record=REG['evelyn'])

@pytest.mark.parametrize('change,message',[
 (lambda a:a['orientation'].__setitem__('body_yaw_degrees',-30),'angle tolerance'),
 (lambda a:a['orientation'].__setitem__('visible_side','right'),'angle tolerance'),
 (lambda a:a['camera'].__setitem__('focal_length_equivalent_mm',24),'camera normalization'),
 (lambda a:a['cross_angle_links'].__setitem__('rear',None),'cross-angle'),
 (lambda a:a['geometry'].pop('ears'),'missing geometry'),
 (lambda a:a['prompts'].__setitem__('resident_binding','grace'),'cross-resident'),
])
def test_sidecar_diagnostics(tmp_path,change,message):
 a=asset(tmp_path); change(a)
 with pytest.raises(PortraitValidationError,match=message): validate_three_quarter_sidecar(a,root=tmp_path,resident_id='evelyn')

def test_terminal_and_flagged_assets_cannot_be_canonical(tmp_path):
 a=asset(tmp_path); a['lifecycle_state']='rejected'; a['canonical']['declared']=True
 with pytest.raises(PortraitValidationError,match='terminal'): validate_three_quarter_sidecar(a,root=tmp_path,resident_id='evelyn')
 a=asset(tmp_path); a['lifecycle_state']='canonical'; a['canonical']={'declared':True,'steward_approval':'ok.json'}; a['identity_fidelity']['face']='flag'
 with pytest.raises(PortraitValidationError,match='flagged'): validate_three_quarter_sidecar(a,root=tmp_path,resident_id='evelyn')

def test_hash_and_angle_bound_steward_promotion(tmp_path):
 a=asset(tmp_path); a['lifecycle_state']='canonical'; a['canonical']={'declared':True,'steward_approval':'ok.json'}
 (tmp_path/'ok.json').write_text(json.dumps({'authority':'steward','decision':'approve','asset_id':'a','angle':a['angle'],'sha256':a['sha256']}))
 validate_three_quarter_sidecar(a,root=tmp_path,resident_id='evelyn')
 approval=json.loads((tmp_path/'ok.json').read_text()); approval['angle']='rear_left_three_quarter'; (tmp_path/'ok.json').write_text(json.dumps(approval))
 with pytest.raises(PortraitValidationError,match='approval does not match'): validate_three_quarter_sidecar(a,root=tmp_path,resident_id='evelyn')

def test_schemas_templates_and_lifecycle_directories_exist():
 for p in ['data/schemas/visual_bible/three_quarter/three_quarter_asset_metadata_v1.schema.json','data/schemas/visual_bible/three_quarter/resident_three_quarter_manifest_v1.schema.json','data/portraits/templates/three_quarter_positive_prompt_template.json','data/portraits/templates/three_quarter_negative_prompt_template.json']:
  json.loads((ROOT/p).read_text())
 base=ROOT/'data/portraits/residents/evelyn/three_quarter'
 assert all((base/x).is_dir() for x in ['candidates','canonical','rejected','superseded','pending','reviews','comparison_sheets','generation_queue','validation'])
