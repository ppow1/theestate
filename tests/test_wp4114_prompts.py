import copy,json
from pathlib import Path
import pytest
from estate.visual_bible import ValidationError, compose, load_prompt_record, validate_adapter, validate_fragment, validate_receipt
ROOT=Path(__file__).resolve().parents[1]
def records(resident):
 b=ROOT/f'data/visual_bibles/residents/{resident}/internal/prompts'
 req=load_prompt_record(b/'example_request.json'); adapter=load_prompt_record(b/'model_adapters/reference_adapter.json')
 fs=[load_prompt_record(p) for p in (b/'fragments').glob('*.json')]; return req,fs,adapter
def test_evelyn_and_contrasting_ingrid_compose_without_identity_collision():
 e=compose(*records('evelyn')); i=compose(*records('ingrid'))
 assert e['positive_prompt']!=i['positive_prompt']; assert '4 ft 10' in e['positive_prompt']; assert 'guarded' in i['positive_prompt']
def test_composition_is_deterministic_and_ordered():
 req,fs,a=records('evelyn'); one=compose(req,fs,a); two=compose(copy.deepcopy(req),list(reversed(fs)),copy.deepcopy(a))
 assert one==two; assert one['ordered_fragment_ids'][0]=='evelyn-identity-v1'; assert one['ordered_fragment_ids'][-1]=='evelyn-exclusion-v1'
def test_identity_required_and_adult_clarity_required():
 req,fs,a=records('evelyn'); req['layers']['identity']=[]
 with pytest.raises(ValidationError,match='PROMPT-MISSING-IDENTITY'):compose(req,fs,a)
 f=next(x for x in fs if x['layer']=='identity');f['text']='ambiguous portrait'
 with pytest.raises(ValidationError,match='PROMPT-AGE-AMBIGUOUS'):validate_fragment(f)
def test_adapter_cannot_override_identity():
 _,_,a=records('evelyn');a['identity_overrides']={'height':'different'}
 with pytest.raises(ValidationError,match='PROMPT-IDENTITY-OVERRIDE'):validate_adapter(a)
def test_cross_resident_and_scope_leaks_fail():
 req,fs,a=records('evelyn');fs[0]['resident_id']='ingrid'
 with pytest.raises(ValidationError,match='PROMPT-CROSS-RESIDENT'):compose(req,fs,a)
 req,fs,a=records('evelyn');fs[0]['audience_scope']='private'
 with pytest.raises(ValidationError,match='PROMPT-AUDIENCE-LEAK'):compose(req,fs,a)
def test_receipt_requires_reproducibility_and_canonical_approval():
 r={'receipt_id':'r','request_id':'q','resident_ids':['evelyn'],'audience_scope':'internal','prompt_version':'1','positive_prompt':'adult Evelyn','negative_prompt':'','fragment_digests':{'x':'0'*64},'model':'m','model_version':'1','workflow_version':'1','seed':1,'dimensions':{'width':1,'height':1},'parameters':{},'reference_ids':[],'adapter_ids':['a'],'generated_at':'2026-07-21T00:00:00Z','review_state':'unreviewed','asset_status':'provisional'}
 validate_receipt(r)
 with pytest.raises(ValidationError,match='PROMPT-CANONICAL-RECEIPT-INVALID'):validate_receipt(r,canonical_asset=True)
def test_schemas_and_examples_validate():
 js=pytest.importorskip('jsonschema');sp=ROOT/'data/schemas/visual_bible/prompts'
 for p in sp.glob('*.schema.json'):js.Draft202012Validator.check_schema(json.loads(p.read_text()))
 mapping={'prompt_request_v1.schema.json':'example_request.json','model_adapter_v1.schema.json':'model_adapters/reference_adapter.json'}
 for resident in ('evelyn','ingrid'):
  b=ROOT/f'data/visual_bibles/residents/{resident}/internal/prompts'
  for sn,rn in mapping.items():js.validate(load_prompt_record(b/rn),json.loads((sp/sn).read_text()))
  schema=json.loads((sp/'prompt_fragment_v1.schema.json').read_text())
  for p in (b/'fragments').glob('*.json'):js.validate(load_prompt_record(p),schema)
def test_turnaround_measurement_group_and_anchor_templates_present():
 b=ROOT/'data/visual_bibles/residents/_template/internal/prompts'
 for n in ('turnaround_template.json','measurement_comparison_template.json','group_scene_template.json','emotional_anchor_template.json'): assert load_prompt_record(b/n)['template_id']
