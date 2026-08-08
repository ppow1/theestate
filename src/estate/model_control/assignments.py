import json
from pathlib import Path
from .registry import now, find_model

ASSIGNMENTS_PATH=Path('runtime/model_control/assignments.json')
AUDIT_PATH=Path('runtime/model_control/audit_log.jsonl')
DEFAULTS={'fallback_text_model':None,'preferred_text_model':None,'preferred_code_model':None,'preferred_vision_model':None}

def rootp(root=None): return Path(root) if root is not None else Path.cwd()
def default_assignments():
    return {'version':'estate-model-assignments-v1','updated_at':now(),'estate_defaults':dict(DEFAULTS),'residents':{'alfred':{'text':'estate_default','vision':None,'fallback_text':'estate_default'},'grace':{'text':'estate_default','vision':None,'fallback_text':'estate_default'},'helen':{'text':'estate_default','vision':None,'fallback_text':'estate_default'}},'workers':{},'authority':{'residents':{'alfred':['text','vision'],'grace':['text'],'helen':['text']},'workers':{},'requires_steward_approval':True}}

def load_assignments(root=None):
    p=rootp(root)/ASSIGNMENTS_PATH
    if not p.exists(): return default_assignments()
    data=json.loads(p.read_text(encoding='utf-8'))
    base=default_assignments(); base.update(data); base.setdefault('estate_defaults',{}); base['estate_defaults']={**DEFAULTS, **base['estate_defaults']}; base.setdefault('residents',{}); base.setdefault('workers',{}); base.setdefault('authority', default_assignments()['authority']); return base

def save_assignments(data, root=None):
    data['updated_at']=now(); p=rootp(root)/ASSIGNMENTS_PATH; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n', encoding='utf-8'); return data

def append_audit(record, root=None):
    p=rootp(root)/AUDIT_PATH; p.parent.mkdir(parents=True, exist_ok=True); payload={'timestamp':now(), **record}; p.open('a',encoding='utf-8').write(json.dumps(payload, sort_keys=True)+'\n'); return payload

def _default_key(capability): return {'text':'preferred_text_model','code':'preferred_code_model','vision':'preferred_vision_model'}.get(capability, f'preferred_{capability}_model')
def _fallback_key(capability): return 'fallback_text_model' if capability=='text' else _default_key(capability)

def resolve_assignment(actor, capability, root=None):
    data=load_assignments(root); bucket='residents' if actor in data.get('residents',{}) else 'workers'; entry=(data.get(bucket) or {}).get(actor,{})
    model=entry.get(capability)
    source=f'{bucket}.{actor}.{capability}' if model else None
    if model=='estate_default' or not model:
        model=data['estate_defaults'].get(_default_key(capability)) or data['estate_defaults'].get(_fallback_key(capability)); source='estate_defaults'
    return {'actor':actor,'capability':capability,'model_id':model,'selection_source':'model_control_assignment' if model else 'bootstrap_fallback','assignment_source':source}

def set_default(capability, model_id, approved_by='steward', root=None):
    if approved_by!='steward': return {'updated':False,'error':'steward_approval_required'}
    data=load_assignments(root); key=_default_key(capability); data['estate_defaults'][key]=model_id
    if capability=='text' and not data['estate_defaults'].get('fallback_text_model'): data['estate_defaults']['fallback_text_model']=model_id
    save_assignments(data, root); append_audit({'actor':approved_by,'operation':'set_default','capability':capability,'model_id':model_id,'authority':'steward_approved','policy_result':'allowed'}, root); return data

def assign_actor(actor, capability, model_id, approved_by='steward', actor_type=None, root=None):
    if approved_by!='steward': return {'updated':False,'error':'steward_approval_required'}
    data=load_assignments(root); bucket=actor_type or ('residents' if actor in data.get('residents',{}) or actor in {'alfred','grace','helen','ingrid'} else 'workers')
    data.setdefault(bucket,{}).setdefault(actor,{})[capability]=model_id
    save_assignments(data, root); append_audit({'actor':approved_by,'operation':'assign','target_actor':actor,'actor_type':bucket,'capability':capability,'model_id':model_id,'authority':'steward_approved','policy_result':'allowed'}, root); return data
