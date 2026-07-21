import copy, json
from pathlib import Path
import pytest
from estate.visual_bible import (
 ValidationError, TAXONOMY, append_audit_event, canonical_digest, check_reference,
 load_wardrobe_record, scaffold_wardrobe, validate_accessory, validate_content_digest, validate_fit_rule,
 validate_footwear, validate_private_activation, validate_prompt_fragment,
 validate_signature_look, validate_transition, validate_wardrobe_manifest,
)
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/visual_bibles/residents/evelyn/internal/wardrobe'
def load(name): return load_wardrobe_record(BASE/name)

def test_complete_evelyn_provisional_library_and_distinct_records_validate():
 m=load('wardrobe_manifest.yaml'); validate_wardrobe_manifest(m,resident='evelyn',scope='internal')
 assert {x['category'] for x in m['category_coverage']}==set(TAXONOMY)
 validate_fit_rule(load('fit_rules.yaml')); validate_footwear(load('footwear.yaml'))
 validate_accessory(load('accessories.yaml')); validate_prompt_fragment(load('prompt_fragments/pf-evelyn-white-linen-prompt-v1.yaml'))
 validate_signature_look(load('signature_looks.yaml'))

def test_evelyn_is_honestly_provisional_and_cannot_promote_without_assets_or_decision():
 look=load('signature_looks.yaml'); assert look['approval']['canonical_promotion_allowed'] is False
 assert look['evidence']['full_body_asset'] is None
 with pytest.raises(ValidationError,match='WARDROBE-SIGNATURE-INCOMPLETE'): validate_signature_look(look,promotion=True)

def test_missing_scope_fit_and_prompt_fragments_have_required_codes():
 m=load('wardrobe_manifest.yaml'); del m['audience_scope']
 with pytest.raises(ValidationError,match='WARDROBE-MISSING-SCOPE'): validate_wardrobe_manifest(m)
 fit=load('fit_rules.yaml'); del fit['presentation_effects']
 with pytest.raises(ValidationError,match='WARDROBE-MISSING-FIT'): validate_fit_rule(fit)
 for side,field in [('positive','fabric_behavior'),('negative','identity_drift')]:
  p=load('prompt_fragments/pf-evelyn-white-linen-prompt-v1.yaml'); del p[side][field]
  with pytest.raises(ValidationError,match='WARDROBE-MISSING-PROMPT'): validate_prompt_fragment(p)

def test_taxonomy_duplicates_and_path_scope_mismatch_fail():
 m=load('wardrobe_manifest.yaml'); m['category_coverage'][-1]['category']=m['category_coverage'][0]['category']
 with pytest.raises(ValidationError,match='taxonomy'): validate_wardrobe_manifest(m)
 m=load('wardrobe_manifest.yaml')
 with pytest.raises(ValidationError,match='WARDROBE-ID-SCOPE-MISMATCH'): validate_wardrobe_manifest(m,resident='another')

def test_cross_resident_inheritance_and_scope_escalation_fail():
 owner=load('signature_looks.yaml'); target=load('fit_rules.yaml'); target['resident_id']='ingrid'; target['record_id']='fit-ingrid-white-linen-petite-v1'
 with pytest.raises(ValidationError,match='WARDROBE-CROSS-RESIDENT-COLLISION'): check_reference(owner,target)
 target=load('fit_rules.yaml'); target['audience_scope']='private'
 with pytest.raises(ValidationError,match='WARDROBE-AUDIENCE-LEAK'): check_reference(owner,target)

def test_physique_mutation_heel_mutation_and_adapter_identity_override_fail():
 fit=load('fit_rules.yaml'); fit['tailoring_assumptions']='changes canonical measurements'
 with pytest.raises(ValidationError,match='WARDROBE-CANON-CONTRADICTION'): validate_fit_rule(fit)
 shoe=load('footwear.yaml'); shoe['canonical_standing_height_unchanged']=False
 with pytest.raises(ValidationError,match='WARDROBE-HEEL-HEIGHT-MUTATION'): validate_footwear(shoe)
 p=load('prompt_fragments/pf-evelyn-white-linen-prompt-v1.yaml'); p['model_overlays']=[{'model':'x','overrides':{'identity':'generic'}}]
 with pytest.raises(ValidationError,match='WARDROBE-CANON-CONTRADICTION'): validate_prompt_fragment(p)

def test_lifecycle_rejection_approval_retirement_and_revision_rules():
 old=load('signature_looks.yaml'); new=copy.deepcopy(old); new['revision']=2; new['lifecycle_state']='in_review'; validate_transition(old,new)
 bad=copy.deepcopy(new); bad['revision']=3; bad['lifecycle_state']='retired'; bad['canon_class']='retired'
 with pytest.raises(ValidationError,match='WARDROBE-ILLEGAL-TRANSITION'): validate_transition(new,bad)
 rejected=copy.deepcopy(old); rejected['lifecycle_state']='rejected'; rejected['canon_class']='rejected'
 with pytest.raises(ValidationError,match='inactive dependency'): check_reference(old,rejected)

def test_private_is_deny_by_default_and_time_bounded():
 record=load('signature_looks.yaml'); record['audience_scope']='private'
 with pytest.raises(ValidationError,match='WARDROBE-AUDIENCE-LEAK'): validate_private_activation(record,None)
 validate_private_activation(record,{'deny_by_default':True,'expires_at':'2026-07-22T00:00:00Z'})

def test_safe_loader_rejects_duplicate_keys_and_non_json_yaml(tmp_path):
 p=tmp_path/'bad.yaml'; p.write_text('{"record_id":"a","record_id":"b"}')
 with pytest.raises(ValidationError,match='duplicate key'): load_wardrobe_record(p)
 p.write_text('!!python/object:unsafe {}')
 with pytest.raises(ValidationError,match='safe JSON-compatible YAML'): load_wardrobe_record(p)

def test_digest_deterministic_and_audit_chain_append_only():
 record=load('fit_rules.yaml'); assert canonical_digest(record)==canonical_digest(copy.deepcopy(record)); validate_content_digest(record)
 changed=copy.deepcopy(record); changed['fit_class']='relaxed'
 with pytest.raises(ValidationError,match='WARDROBE-HASH-MISMATCH'): validate_content_digest(changed)
 events=[]; one=append_audit_event(events,{'event_type':'submitted','subject_record_id':record['record_id'],'actor_id':'test','timestamp':'2026-07-21T00:00:00Z'})
 two=append_audit_event(events,{'event_type':'revision-requested','subject_record_id':record['record_id'],'actor_id':'test','timestamp':'2026-07-21T01:00:00Z'})
 assert two['previous_hash']==one['event_hash']; assert len(events)==2

def test_scaffold_all_scopes_without_resident_content_inheritance(tmp_path):
 scaffold_wardrobe(tmp_path,'neutral-adult')
 for scope in ('public','internal','restricted','private'):
  base=tmp_path/'neutral-adult'/scope/'wardrobe'; assert (base/'steward_notes.md').exists(); assert (base/'prompt_fragments').is_dir()
 assert not any('evelyn' in p.read_text().lower() for p in tmp_path.rglob('*') if p.is_file())

def test_all_eight_json_schemas_are_valid_and_examples_conform():
 js=pytest.importorskip('jsonschema'); schemas=ROOT/'data/schemas/visual_bible/wardrobe'
 mapping={'wardrobe_manifest_v1.schema.json':'wardrobe_manifest.yaml','signature_looks_v1.schema.json':'signature_looks.yaml','fit_rules_v1.schema.json':'fit_rules.yaml','footwear_v1.schema.json':'footwear.yaml','accessories_v1.schema.json':'accessories.yaml','wardrobe_prompt_fragment_v1.schema.json':'prompt_fragments/pf-evelyn-white-linen-prompt-v1.yaml','wardrobe_review_v1.schema.json':'reviews/wr-evelyn-white-linen-pending-v1.yaml'}
 for schema_path in schemas.glob('*.schema.json'): js.Draft202012Validator.check_schema(json.loads(schema_path.read_text()))
 for schema_name,record_name in mapping.items(): js.validate(load(record_name),json.loads((schemas/schema_name).read_text()))
