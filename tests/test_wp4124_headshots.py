import hashlib,json
from copy import deepcopy
from pathlib import Path
import pytest
from estate.portraits import PortraitValidationError,validate_catalog,validate_headshot_manifest,validate_headshot_sidecar
ROOT=Path(__file__).resolve().parents[1]
REG={x['id']:x for x in json.loads((ROOT/'data/registry/residents.json').read_text()) if x['status']=='Active'}
MAN=json.loads((ROOT/'data/portraits/residents/evelyn/headshots/manifest.json').read_text())
def asset(tmp_path,kind='derivative'):
 p=tmp_path/'a.png';p.write_bytes(b'fixture');h=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'schema_version':'thumbnail_derivative_v1' if kind=='derivative' else 'headshot_master_v1','asset_id':'a','resident_id':'evelyn','asset_kind':kind,'use':'thumbnail' if kind=='derivative' else 'headshot','lifecycle_state':'candidate','scope':'review_only','asset_path':'a.png','sha256':h,'dimensions':{'width':32 if kind=='derivative' else 2048,'height':32 if kind=='derivative' else 2560,'aspect_ratio':'1:1' if kind=='derivative' else '4:5'},'crop':{'x':0,'y':0,'width':1,'height':1,'hair_silhouette_preserved':True,'jawline_preserved':True},'safe_area':{'face_inside':True,'radius_ratio':.42},'identity_fidelity':{x:'pass' for x in ['facial_geometry','eyes','hair','age','expression','recognizable_at_32px']},'provenance':{'source_sha256':'0'*64},'lineage':{'source_asset_id':'master','source_sha256':'0'*64,'recipe_id':'v1'} if kind=='derivative' else {'predecessor_asset_id':None},'steward_review':{'state':'pending'},'canonical':{'declared':False,'steward_approval':None}}
def test_catalog_and_all_resident_pending_coverage():
 validate_catalog(ROOT)
 cat=json.loads((ROOT/'data/portraits/estate_portrait_catalog.json').read_text());assert len(cat['residents'])==8
 for r in cat['residents']:
  m=json.loads((ROOT/r['headshot_manifest_path']).read_text());validate_headshot_manifest(m,root=ROOT,registry_record=REG[r['resident_id']]);assert len(m['master_slots'])==4 and len(m['derivative_plan'])==5;assert not m['assets'];assert all(x['state']=='pending_generation' and x['evidence'] is None for x in m['master_slots'])
def test_sizes_crop_hash_and_lineage_diagnostics(tmp_path):
 a=asset(tmp_path);validate_headshot_sidecar(a,root=tmp_path,resident_id='evelyn')
 for mutate,msg in [(lambda x:x['dimensions'].__setitem__('width',48),'unsupported thumbnail'),(lambda x:x['crop'].__setitem__('hair_silhouette_preserved',False),'invalid crop'),(lambda x:x['lineage'].pop('source_sha256'),'lineage'),(lambda x:x.__setitem__('sha256','0'*64),'stale hash')]:
  b=deepcopy(a);mutate(b)
  with pytest.raises(PortraitValidationError,match=msg):validate_headshot_sidecar(b,root=tmp_path,resident_id='evelyn')
def test_duplicate_derivatives_detected(tmp_path):
 a=asset(tmp_path);b=deepcopy(a);b['asset_id']='b';
 for x in (a,b): (tmp_path/f'{x["asset_id"]}.json').write_text(json.dumps(x))
 m=deepcopy(MAN);m['assets']=[{'metadata_path':'a.json'},{'metadata_path':'b.json'}]
 with pytest.raises(PortraitValidationError,match='duplicate derivative content'):validate_headshot_manifest(m,root=tmp_path,registry_record=REG['evelyn'])
def test_silent_canonical_replacement_rejected(tmp_path):
 a=asset(tmp_path);a['lifecycle_state']='canonical';a['scope']='canonical';a['canonical']['declared']=True
 with pytest.raises(PortraitValidationError,match='approval'):validate_headshot_sidecar(a,root=tmp_path,resident_id='evelyn')
def test_schemas_templates_and_review_records():
 for p in ['data/schemas/visual_bible/headshots/headshot_master_v1.schema.json','data/schemas/visual_bible/headshots/thumbnail_derivative_v1.schema.json','data/schemas/visual_bible/headshots/resident_headshot_manifest_v1.schema.json','data/portraits/templates/thumbnail_derivative_recipe_v1.json']:json.loads((ROOT/p).read_text())
 review=json.loads((ROOT/'data/portraits/residents/evelyn/headshots/reviews/recognizability_review.json').read_text());assert set(review['native_size_results'])=={'32','64','128','256','512'} and review['state']=='pending'
