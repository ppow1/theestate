import hashlib, json
from copy import deepcopy
from pathlib import Path
import pytest
from estate.portraits import PortraitValidationError, validate_catalog, validate_expression_manifest, validate_expression_sidecar
ROOT=Path(__file__).resolve().parents[1]
REG={x['id']:x for x in json.loads((ROOT/'data/registry/residents.json').read_text()) if x['status']=='Active'}
MAN=json.loads((ROOT/'data/portraits/residents/evelyn/expressions/manifest.json').read_text())

def asset(tmp_path):
 p=tmp_path/'a.png'; p.write_bytes(b'wp4123 fixture'); h=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'schema_version':'expression_asset_metadata_v1','asset_id':'a','resident_id':'evelyn','expression_id':'warm_greeting','category':'core','lifecycle_state':'candidate','asset_path':'a.png','sha256':h,'identity_source':{'resident_id':'evelyn','references':['hero']},'facial_action':{x:'documented' for x in ['eyes','brows','mouth','cheeks','jaw','head_angle','posture']},'micro_expression':{'intensity':'subtle','name':'eyes_softening'},'emotional_claim':{'label':'warm_greeting','approved_vocabulary':True,'supported_by':['character_bible']},'normalization':{'focal_length_equivalent_mm':85,**{x:True for x in ['camera_locked','crop_locked','lighting_locked','grooming_locked','wardrobe_locked','background_locked']}},'prompts':{'resident_binding':'evelyn','positive_revision':1,'negative_revision':1},'generation':{'model':'test','version':'1','seed':1,'settings':{}},'provenance':{'created_at':'2026-07-21T00:00:00Z','operator':'test','source_hashes':{}},'identity_fidelity':{x:'pass' for x in ['eye_geometry','nose_geometry','mouth_geometry','jaw_geometry','cheek_geometry','age','skin','hair','visual_fingerprint','personality']},'hidden_caption_test':{'state':'pass'},'validation':{'state':'pass','diagnostics':[]},'steward_review':{'state':'pending','notes':[]},'canonical':{'declared':False,'steward_approval':None},'lineage':{'predecessor':None,'successor':None}}

def test_catalog_and_truthful_expression_coverage():
 validate_catalog(ROOT)
 cat=json.loads((ROOT/'data/portraits/estate_portrait_catalog.json').read_text())
 assert len(cat['residents'])==8
 for r in cat['residents']:
  m=json.loads((ROOT/r['expression_manifest_path']).read_text()); validate_expression_manifest(m,root=ROOT,registry_record=REG[r['resident_id']])
  assert len([s for s in m['required_expression_slots'] if s['category']=='core'])==12
  assert all(s['state']=='pending_generation' and s['evidence'] is None for s in m['required_expression_slots'])
  assert not m['candidates'] and m['emotional_anchor']['approval_state']=='pending_steward'

def test_missing_expression_and_cross_resident_rejected():
 m=deepcopy(MAN); m['required_expression_slots']=m['required_expression_slots'][1:]
 with pytest.raises(PortraitValidationError,match='missing required'): validate_expression_manifest(m,root=ROOT,registry_record=REG['evelyn'])
 m=deepcopy(MAN); m['resident_template_binding']='grace'
 with pytest.raises(PortraitValidationError,match='cross-resident'): validate_expression_manifest(m,root=ROOT,registry_record=REG['evelyn'])

@pytest.mark.parametrize('change,message',[(lambda a:a['micro_expression'].__setitem__('intensity','extreme'),'exaggerated'),(lambda a:a['emotional_claim'].__setitem__('supported_by',[]),'unsupported emotional'),(lambda a:a['normalization'].__setitem__('camera_locked',False),'normalization'),(lambda a:a['identity_fidelity'].pop('age'),'identity drift'),(lambda a:a['prompts'].__setitem__('resident_binding','grace'),'cross-resident')])
def test_expression_diagnostics(tmp_path,change,message):
 a=asset(tmp_path); change(a)
 with pytest.raises(PortraitValidationError,match=message): validate_expression_sidecar(a,root=tmp_path,resident_id='evelyn')

def test_unapproved_or_drifted_canonical_promotion_rejected(tmp_path):
 a=asset(tmp_path); a['lifecycle_state']='canonical'; a['canonical']['declared']=True
 with pytest.raises(PortraitValidationError,match='approval'): validate_expression_sidecar(a,root=tmp_path,resident_id='evelyn')
 a=asset(tmp_path); a['lifecycle_state']='canonical'; a['canonical']={'declared':True,'steward_approval':'ok.json'}; a['identity_fidelity']['age']='flag'
 with pytest.raises(PortraitValidationError,match='identity drift'): validate_expression_sidecar(a,root=tmp_path,resident_id='evelyn')

def test_hash_bound_steward_approval(tmp_path):
 a=asset(tmp_path); a['lifecycle_state']='canonical'; a['canonical']={'declared':True,'steward_approval':'ok.json'}
 (tmp_path/'ok.json').write_text(json.dumps({'authority':'steward','decision':'approve','asset_id':'a','expression_id':'warm_greeting','sha256':a['sha256']}))
 validate_expression_sidecar(a,root=tmp_path,resident_id='evelyn')
 approval=json.loads((tmp_path/'ok.json').read_text()); approval['expression_id']='concern'; (tmp_path/'ok.json').write_text(json.dumps(approval))
 with pytest.raises(PortraitValidationError,match='approval does not match'): validate_expression_sidecar(a,root=tmp_path,resident_id='evelyn')

def test_schemas_templates_and_lifecycle_layout_exist():
 for p in ['data/schemas/visual_bible/expressions/resident_expression_manifest_v1.schema.json','data/schemas/visual_bible/expressions/expression_asset_metadata_v1.schema.json','data/portraits/templates/expression_positive_prompt_template.json','data/portraits/templates/expression_negative_prompt_template.json']:
  json.loads((ROOT/p).read_text())
 base=ROOT/'data/portraits/residents/evelyn/expressions'
 assert all((base/x).is_dir() for x in ['candidates','canonical','rejected','superseded','pending','reviews','comparison_sheets','generation_queue','validation'])
