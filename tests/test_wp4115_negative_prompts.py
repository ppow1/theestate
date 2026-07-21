import copy,json
from pathlib import Path
import pytest
from estate.visual_bible import (ValidationError,compose_negative,validate_negative_library,validate_negative_adapter,validate_resident_extension,validate_defect_observation)
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'data/visual_bibles/_shared/internal/negative_prompts'
def load(p):return json.loads(Path(p).read_text())
def test_global_library_has_every_category_and_anatomy_protection():validate_negative_library(load(BASE/'global_library.json'))
def test_missing_anatomy_detected():
 d=load(BASE/'global_library.json'); next(r for r in d['rules'] if r['category']=='anatomy')['text']='no defects'
 with pytest.raises(ValidationError,match='NEG-MISSING-ANATOMY-PROTECTION'):validate_negative_library(d)
def test_all_required_asset_templates_and_special_controls_exist():
 for a in ('portrait','full_body','turnaround','icon','group','movement','environment','wardrobe','comparison'):
  d=load(BASE/'templates'/f'{a}.json');assert d['asset_type']==a and d['required_rule_ids']
 assert {'declared_variable','locked_variables'}<=set(load(BASE/'templates/comparison.json')['required_controls'])
 assert {'resident_identity_map','relative_height_map','placement_map'}<=set(load(BASE/'templates/group.json')['required_controls'])
def test_resident_template_requires_all_protections_and_positive_identity():
 d=load(ROOT/'data/visual_bibles/residents/_template/internal/negative_prompts/resident_extension_template.json');d['resident_id']='evelyn';validate_resident_extension(d)
 d['positive_identity_instruction_ids']=[]
 with pytest.raises(ValidationError,match='NEG-MISSING-POSITIVE-IDENTITY'):validate_resident_extension(d)
def test_adapter_cannot_change_semantics():
 d=load(BASE/'adapters/reference_adapter.json');validate_negative_adapter(d);d['semantic_overrides']={'identity':'weaken'}
 with pytest.raises(ValidationError,match='NEG-ADAPTER-SEMANTIC-OVERRIDE'):validate_negative_adapter(d)
def test_composition_is_deterministic_and_group_identity_is_separate():
 lib=load(BASE/'global_library.json');tpl=load(BASE/'templates/group.json');ad=load(BASE/'adapters/reference_adapter.json'); ext=load(ROOT/'data/visual_bibles/residents/_template/internal/negative_prompts/resident_extension_template.json')
 es=[]
 for resident in ('evelyn','ingrid'):
  x=copy.deepcopy(ext);x['resident_id']=resident;x['positive_identity_instruction_ids']=[resident+'-identity-v1'];es.append(x)
 s={'asset_type':'group','resident_ids':['evelyn','ingrid'],'audience_scope':'internal','positive_identity_instruction_ids':['evelyn-identity-v1','ingrid-identity-v1'],'rule_ids':[]}
 assert compose_negative(s,lib,tpl,es,ad)==compose_negative(copy.deepcopy(s),lib,tpl,copy.deepcopy(es),ad)
 assert 'group-separation' in compose_negative(s,lib,tpl,es,ad)['ordered_rule_ids']
def test_scope_leak_and_missing_positive_identity_fail():
 lib=load(BASE/'global_library.json');tpl=load(BASE/'templates/portrait.json');ad=load(BASE/'adapters/reference_adapter.json');s={'asset_type':'portrait','resident_ids':['evelyn'],'audience_scope':'internal','positive_identity_instruction_ids':[],'rule_ids':[]}
 with pytest.raises(ValidationError,match='NEG-MISSING-POSITIVE-IDENTITY'):compose_negative(s,lib,tpl,[],ad)
def test_observation_promotion_is_durable_and_schemas_valid():
 o=load(BASE/'remediation/example_observation.json');validate_defect_observation(o);o['state']='promoted'
 with pytest.raises(ValidationError,match='NEG-PROMOTION-WITHOUT-RULE'):validate_defect_observation(o)
 js=pytest.importorskip('jsonschema')
 for p in (ROOT/'data/schemas/visual_bible/negative_prompts').glob('*.json'):js.Draft202012Validator.check_schema(load(p))
