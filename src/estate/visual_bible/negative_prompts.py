"""WP-4115 model-neutral negative-prompt validation and composition."""
from __future__ import annotations
from .prompts import SCOPES, digest
from .validator import ValidationError

ASSETS=("portrait","full_body","turnaround","icon","group","movement","environment","wardrobe","comparison")
REQUIRED_CATEGORIES={"anatomy","identity","age","scale","proportion","appearance","rendering","artifact","framing"}
RESIDENT_PROTECTIONS={"face_shape","adult_age_range","height","build_and_measurements","visual_fingerprint","posture","signature_expression","hair_length_texture_color","eye_shape_color","distinguishing_features","forbidden_resident_resemblances"}
def _fail(code,msg): raise ValidationError(f"{code}: {msg}")
def rules_by_id(library):
 out={}
 for rule in library.get('rules',[]):
  rid=rule.get('rule_id')
  if not rid or rid in out:_fail('NEG-DUPLICATE-RULE',str(rid))
  out[rid]=rule
 return out
def validate_library(library):
 rules=rules_by_id(library); cats={r.get('category') for r in rules.values() if 'all' in r.get('asset_types',[])}
 if missing:=REQUIRED_CATEGORIES-cats:_fail('NEG-MISSING-GLOBAL-CATEGORY',','.join(sorted(missing)))
 anatomy=' '.join(r['text'].lower() for r in rules.values() if r.get('category')=='anatomy')
 for term in ('limbs','hands','fingers','feet','toes','joints','heads','faces','teeth','ears','eyes','hairlines'):
  if term not in anatomy:_fail('NEG-MISSING-ANATOMY-PROTECTION',term)
 for a in ASSETS:
  if not any(a in r.get('asset_types',[]) or 'all' in r.get('asset_types',[]) for r in rules.values()):_fail('NEG-MISSING-ASSET-COVERAGE',a)
 return library
def validate_resident_extension(ext):
 if not ext.get('positive_identity_instruction_ids'):_fail('NEG-MISSING-POSITIVE-IDENTITY','negative prompts supplement rather than replace positive identity instructions')
 if missing:=RESIDENT_PROTECTIONS-set(ext.get('protections',{})):_fail('NEG-MISSING-RESIDENT-PROTECTION',','.join(sorted(missing)))
 if ext.get('resident_id') in (None,'','REQUIRED'):_fail('NEG-MISSING-RESIDENT','resident_id')
 return ext
def validate_adapter(adapter):
 required={'adapter_id','audience_scope','engine_family','negative_channel','serialization','semantic_overrides','provenance'}
 if missing:=required-set(adapter):_fail('NEG-ADAPTER-INCOMPLETE',','.join(sorted(missing)))
 if adapter['semantic_overrides']:_fail('NEG-ADAPTER-SEMANTIC-OVERRIDE',adapter['adapter_id'])
 return adapter
def compose_negative(prompt_set,library,template,extensions,adapter):
 validate_library(library);validate_adapter(adapter); rules=rules_by_id(library)
 if prompt_set.get('asset_type')!=template.get('asset_type'):_fail('NEG-ASSET-MISMATCH',str(prompt_set.get('asset_type')))
 if not prompt_set.get('positive_identity_instruction_ids'):_fail('NEG-MISSING-POSITIVE-IDENTITY','prompt set')
 if SCOPES.index(prompt_set['audience_scope'])>SCOPES.index(adapter['audience_scope']):_fail('NEG-AUDIENCE-LEAK',adapter['adapter_id'])
 for e in extensions:
  validate_resident_extension(e)
  if e['resident_id'] not in prompt_set.get('resident_ids',[]):_fail('NEG-CROSS-RESIDENT',e['resident_id'])
  if SCOPES.index(e['audience_scope'])>SCOPES.index(prompt_set['audience_scope']):_fail('NEG-AUDIENCE-LEAK',e['resident_id'])
 ids=list(dict.fromkeys(template.get('required_rule_ids',[])+prompt_set.get('rule_ids',[])+sum((e.get('rule_ids',[]) for e in extensions),[])))
 if missing:=[x for x in ids if x not in rules]:_fail('NEG-MISSING-RULE',','.join(missing))
 if prompt_set['asset_type']=='group' and (len(prompt_set.get('resident_ids',[]))<2 or not extensions):_fail('NEG-GROUP-SEPARATION-INCOMPLETE','identity map/extensions')
 selected=[rules[x] for x in ids]
 return {'negative_prompt':adapter['serialization']['separator'].join(r['text'] for r in selected),'ordered_rule_ids':ids,'rule_digests':{r['rule_id']:digest(r) for r in selected},'composition_digest':digest({'set':prompt_set,'rules':selected,'template':template,'extensions':extensions,'adapter':adapter}),'review_state':'review_required' if any(r['severity']=='review_required' for r in selected) else 'valid'}
def validate_observation(o):
 required={'observation_id','receipt_id','category','rule_ids','observed_at','observer','audience_scope','state','evidence_ref','remediation'}
 if missing:=required-set(o):_fail('NEG-OBSERVATION-INCOMPLETE',','.join(sorted(missing)))
 if o['state']=='promoted' and not o['remediation'].get('candidate_rule_id'):_fail('NEG-PROMOTION-WITHOUT-RULE','candidate_rule_id')
 return o
