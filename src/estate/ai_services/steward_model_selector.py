"""Steward-facing AI Services and model selector data layer."""
import json
from datetime import datetime, timezone
from pathlib import Path
from .control import status as control_status
from .discovery import append_audit, rediscover
from .execution import load_approvals, record_approval_decision

PREFS='runtime/ai_services/model_preferences.json'
ASSIGN='runtime/ai_services/model_assignments.json'
KNOWN_DEFAULTS=['estate_fallback_text_model','estate_preferred_text_model','estate_preferred_vision_model']
KNOWN_ASSIGNMENTS=['alfred','helen','chief_architect','codex_worker_default']
SECRET_KEYS={'token','secret','password','api_key','authorization'}

def now(): return datetime.now(timezone.utc).isoformat()
def _root(root=None): return Path(root) if root else Path.cwd()
def _read_json(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return default

def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8'); return data

def _sanitize(obj):
    if isinstance(obj, dict): return {k:('[redacted]' if k.lower() in SECRET_KEYS else _sanitize(v)) for k,v in obj.items()}
    if isinstance(obj, list): return [_sanitize(v) for v in obj]
    return obj

def model_id(service_id, name): return f'{service_id}:{name}'

def _dir_inventory(service):
    out=[]; paths=service.get('paths') or {}; mdir=paths.get('models')
    if not mdir: return out, 'not_declared'
    p=Path(mdir)
    if not p.exists(): return out, 'unavailable'
    for child in sorted(p.iterdir())[:250]:
        if child.is_file() or child.is_dir(): out.append(child.name)
    return out, 'available'

def build_models(registry):
    models=[]
    for s in registry.get('services',[]):
        sid=s.get('service_id'); ops=s.get('operations') or {}; paths=s.get('paths') or {}
        names, source_state = _dir_inventory(s)
        if names:
            for n in names: models.append({'model_id':model_id(sid,n),'name':n,'backing_service':sid,'source':'manifest_model_directory','source_status':source_state,'capabilities':['unknown'],'classification_status':'unknown'})
        elif sid in {'textgen','ollama'} or paths.get('models'):
            models.append({'model_id':model_id(sid,'unavailable-inventory'),'name':'unavailable-inventory','backing_service':sid,'source':'manifest_model_directory' if paths.get('models') else 'service_inventory','source_status':source_state if paths.get('models') else 'unavailable','capabilities':['unknown'],'classification_status':'unknown','unresolved':True})
        for key,path in paths.items():
            if key not in {'models','model'} and 'model' in key:
                models.append({'model_id':model_id(sid,key),'name':key,'backing_service':sid,'source':'manifest_path','source_path':path,'source_status':'declared','capabilities':['unknown'],'classification_status':'unknown'})
        if 'list_models' in ops or 'inventory_models' in ops:
            models.append({'model_id':model_id(sid,'runtime-api-inventory'),'name':'runtime-api-inventory','backing_service':sid,'source':'runtime_api','source_status':'available_hook_unqueried','capabilities':['unknown'],'classification_status':'unknown'})
    return models

def _known_model_ids(models): return {m['model_id'] for m in models if not m.get('unresolved')}

def load_preferences(root=None, models=None):
    r=_root(root); models=models or build_models(control_status(r)['registry']); known=_known_model_ids(models)
    data=_read_json(r/PREFS, {'version':'ai-services-model-preferences-v1','preferences':{}})
    prefs=data.setdefault('preferences',{})
    for k in KNOWN_DEFAULTS: prefs.setdefault(k, {'model_id':None,'backing_service':None,'resolution':'unresolved','reason':'Not configured','last_updated':None,'updated_by':None})
    for k,v in prefs.items():
        mid=v.get('model_id'); v['resolution']='resolved' if mid in known else 'unresolved'
    return data

def set_preference(name, model_id_value, updated_by='steward', reason='', root=None):
    r=_root(root); models=build_models(control_status(r)['registry']); svc=model_id_value.split(':',1)[0] if model_id_value and ':' in model_id_value else None
    data=load_preferences(r, models); data['preferences'][name]={'model_id':model_id_value,'backing_service':svc,'resolution':'resolved' if model_id_value in _known_model_ids(models) else 'unresolved','reason':reason,'last_updated':now(),'updated_by':updated_by}
    _write_json(r/PREFS, data); append_audit({'actor':updated_by,'operation':'set_model_preference','service_id':svc,'authority':'steward_approved' if updated_by=='steward' else 'unapproved','policy_result':'allowed' if updated_by=='steward' else 'denied','result':'updated' if updated_by=='steward' else 'denied','details':{'preference':name,'model_id':model_id_value}}, r)
    return data

def load_assignments(root=None, models=None):
    r=_root(root); models=models or build_models(control_status(r)['registry']); known=_known_model_ids(models)
    data=_read_json(r/ASSIGN, {'version':'ai-services-model-assignments-v1','assignments':{}}); assigns=data.setdefault('assignments',{})
    for worker in KNOWN_ASSIGNMENTS: assigns.setdefault(worker, {'model_id':None,'backing_service':None,'allowed_operations':['status'],'approval_requirement':'steward_required_for_start_stop_load_model','reason':'Not configured','last_updated':None,'updated_by':None,'resolution':'unresolved'})
    for _,v in assigns.items():
        mid=v.get('model_id'); v['resolution']='resolved' if mid in known else 'unresolved'
    return data

def set_assignment(worker, model_id_value, updated_by='steward', reason='', allowed_operations=None, root=None):
    if updated_by != 'steward':
        append_audit({'actor':updated_by,'operation':'set_assignment','service_id':None,'authority':'unapproved','policy_result':'denied','result':'denied','details':{'worker':worker}}, _root(root)); return {'error':'steward_approval_required','updated':False}
    r=_root(root); models=build_models(control_status(r)['registry']); svc=model_id_value.split(':',1)[0] if model_id_value and ':' in model_id_value else None
    data=load_assignments(r, models); data['assignments'][worker]={'model_id':model_id_value,'backing_service':svc,'allowed_operations':allowed_operations or ['status'],'approval_requirement':'steward_required_for_start_stop_load_model','reason':reason,'last_updated':now(),'updated_by':updated_by,'resolution':'resolved' if model_id_value in _known_model_ids(models) else 'unresolved'}
    _write_json(r/ASSIGN, data); append_audit({'actor':updated_by,'operation':'set_assignment','service_id':svc,'authority':'steward_approved','policy_result':'allowed','result':'updated','details':{'worker':worker,'model_id':model_id_value}}, r); return data

def audit_tail(root=None, limit=25):
    p=_root(root)/'runtime/ai_services/audit_log.jsonl'; rows=[]
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines()[-limit:]:
            try: rows.append(_sanitize(json.loads(line)))
            except Exception: rows.append({'unparsed':line[:200]})
    return rows

def approvals(root=None): return load_approvals(_root(root))

def decide_approval(decision, operation, service_id, actor='alfred', model=None, approved_by='steward', reason='', root=None):
    if actor == approved_by: return {'error':'actor_cannot_approve_own_authority_expansion','updated':False}
    return record_approval_decision(operation, service_id, actor=actor, approved_by=approved_by, decision=decision, reason=reason, model=model, root=_root(root))

def refresh_status(root=None):
    r=_root(root); payload=control_status(r); append_audit({'actor':'steward','operation':'status_refresh','service_id':None,'authority':'steward_approved','policy_result':'allowed','result':'success','details':{}}, r); return payload

def build_steward_ai_services_panel(root=None):
    r=_root(root); cp=control_status(r); reg=cp['registry']; state=cp['state']; models=build_models(reg)
    services=[]
    for s in reg.get('services',[]):
        sid=s.get('service_id'); sv_state=(state.get('services') or {}).get(sid,{}); proc=(state.get('processes') or {}).get(sid,{})
        services.append({'service_id':sid,'display_name':s.get('display_name'),'service_type':s.get('service_type'),'endpoint':s.get('default_endpoint'),'host_policy':s.get('host_policy'),'ports':s.get('ports',[]),'current_state':sv_state.get('status','unknown'),'health_status':proc.get('health_status') or sv_state.get('status','unknown'),'last_operation':sv_state.get('last_operation') or proc.get('operation_id'),'available_operations':sorted((s.get('operations') or {}).keys()),'approval_requirements':s.get('approval',{}),'log_reference':proc.get('log_path'),'manifest_path':s.get('manifest_path'),'model_locations':{k:v for k,v in (s.get('paths') or {}).items() if 'model' in k}})
    return {'available':True,'path':'runtime/ai_services/registry.json; runtime/ai_services/state.json; runtime/ai_services/model_preferences.json; runtime/ai_services/model_assignments.json','kind':'steward_ai_services_models','data':{'local_only':True,'control_surface':'Office of the Steward / AI Services / Models','services':services,'models':models,'model_preferences':load_preferences(r, models),'model_assignments':load_assignments(r, models),'approvals':approvals(r),'audit_tail':audit_tail(r),'actions':{'rediscover':'ai-services rediscover','refresh_status':'ai-services status','approve':'ai-services approve','deny':'ai-services deny'}}}
