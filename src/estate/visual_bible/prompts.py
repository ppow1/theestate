"""WP-4114 deterministic, model-neutral visual prompt composition."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from .validator import ValidationError

LAYERS=("identity","presence","wardrobe","pose","environment","camera","rendering","exclusion")
SCOPES=("public","internal","restricted","private")

def _fail(code, message): raise ValidationError(f"{code}: {message}")
def canonical_json(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def digest(value): return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def load_prompt_record(path):
    path=Path(path); raw=path.read_text(encoding='utf-8')
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:_fail('PROMPT-DUPLICATE-KEY',k)
            out[k]=v
        return out
    try:return json.loads(raw,object_pairs_hook=pairs)
    except json.JSONDecodeError as e:_fail('PROMPT-UNSAFE-FORMAT',f'{path}: JSON-compatible YAML required ({e.msg})')
def validate_fragment(f, expected_resident=None, expected_scope=None):
    required={'schema_version','fragment_id','resident_id','audience_scope','layer','version','status','text','provenance'}
    if missing:=required-set(f):_fail('PROMPT-MISSING-METADATA',','.join(sorted(missing)))
    if f['layer'] not in LAYERS:_fail('PROMPT-UNKNOWN-LAYER',str(f['layer']))
    if f['audience_scope'] not in SCOPES:_fail('PROMPT-MISSING-SCOPE','invalid scope')
    if not f['text'].strip():_fail('PROMPT-EMPTY-FRAGMENT',f['fragment_id'])
    if expected_resident and f['resident_id'] not in (expected_resident,'_shared'):_fail('PROMPT-CROSS-RESIDENT',f['fragment_id'])
    if expected_scope and SCOPES.index(f['audience_scope'])>SCOPES.index(expected_scope):_fail('PROMPT-AUDIENCE-LEAK',f['fragment_id'])
    if f['layer']=='identity' and 'adult' not in f['text'].lower():_fail('PROMPT-AGE-AMBIGUOUS',f['fragment_id'])
    return f
def validate_adapter(a, scope='internal'):
    for k in ('adapter_id','audience_scope','model','model_version','parameters','identity_overrides'):
        if k not in a:_fail('PROMPT-ADAPTER-INCOMPLETE',k)
    if a['identity_overrides']:_fail('PROMPT-IDENTITY-OVERRIDE',a['adapter_id'])
    if SCOPES.index(a['audience_scope'])>SCOPES.index(scope):_fail('PROMPT-AUDIENCE-LEAK',a['adapter_id'])
    return a
def compose(request, fragments, adapter):
    """Compose in fixed order; input order never affects output."""
    for k in ('request_id','audience_scope','purpose','residents','layers','adapter'):
        if k not in request:_fail('PROMPT-REQUEST-INCOMPLETE',k)
    if not request['residents']:_fail('PROMPT-MISSING-IDENTITY','resident roster empty')
    validate_adapter(adapter,request['audience_scope'])
    if request['adapter']!=adapter['adapter_id']:_fail('PROMPT-ADAPTER-MISMATCH',request['adapter'])
    by_id={f['fragment_id']:validate_fragment(f) for f in fragments}
    positive=[]; negative=[]; used=[]
    for layer in LAYERS:
        ids=request['layers'].get(layer,[])
        if layer=='identity' and not ids:_fail('PROMPT-MISSING-IDENTITY','identity layer empty')
        for fid in sorted(ids):
            if fid not in by_id:_fail('PROMPT-MISSING-FRAGMENT',fid)
            f=by_id[fid]
            if f['layer']!=layer:_fail('PROMPT-LAYER-MISMATCH',fid)
            if f['resident_id'] not in (*request['residents'],'_shared'):_fail('PROMPT-CROSS-RESIDENT',fid)
            if SCOPES.index(f['audience_scope'])>SCOPES.index(request['audience_scope']):_fail('PROMPT-AUDIENCE-LEAK',fid)
            (negative if layer=='exclusion' else positive).append(f['text'].strip()); used.append(f)
    return {'positive_prompt':'; '.join(positive),'negative_prompt':'; '.join(negative),'ordered_fragment_ids':[f['fragment_id'] for f in used],'fragment_digests':{f['fragment_id']:digest(f) for f in used},'composition_digest':digest({'request':request,'fragments':used,'adapter':adapter})}
def validate_receipt(r, canonical_asset=False):
    required={'receipt_id','request_id','resident_ids','audience_scope','prompt_version','positive_prompt','negative_prompt','fragment_digests','model','model_version','workflow_version','seed','dimensions','parameters','reference_ids','adapter_ids','generated_at','review_state','asset_status'}
    if missing:=required-set(r):_fail('PROMPT-RECEIPT-INCOMPLETE',','.join(sorted(missing)))
    if not r['resident_ids']:_fail('PROMPT-MISSING-IDENTITY','receipt roster')
    if canonical_asset and (r['asset_status']!='canonical' or r['review_state']!='approved'):_fail('PROMPT-CANONICAL-RECEIPT-INVALID','approval/status')
    return r
