"""Steward-facing AI Services and model selector data layer."""
import json
from datetime import datetime, timezone
from pathlib import Path
from .control import status as control_status
from .discovery import append_audit, rediscover
from .execution import load_approvals, record_approval_decision

PREFS='runtime/ai_services/model_preferences.json'
ASSIGN='runtime/ai_services/model_assignments.json'
KNOWN_DEFAULTS=['estate_fallback_text_model','estate_preferred_text_model','estate_preferred_vision_model','estate_preferred_embedding_model','estate_preferred_coding_model','estate_preferred_speech_model']
KNOWN_ASSIGNMENTS=['steward','alfred','helen','chief_architect','codex_worker_default']
SECRET_KEYS={'token','secret','password','api_key','authorization','credential'}
MODEL_FILE_SUFFIXES={'.gguf','.bin','.safetensors','.pt','.pth','.onnx','.ckpt'}

def now(): return datetime.now(timezone.utc).isoformat()
def _root(root=None): return Path(root) if root else Path.cwd()
def _read_json(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return default

def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8'); return data

def _sanitize(obj):
    if isinstance(obj, dict): return {k:('[redacted]' if any(s in k.lower() for s in SECRET_KEYS) else _sanitize(v)) for k,v in obj.items()}
    if isinstance(obj, list): return [_sanitize(v) for v in obj]
    if isinstance(obj, str):
        lowered=obj.lower()
        if any(s in lowered for s in ['token=','api_key=','password=','authorization:']): return '[redacted]'
    return obj

def model_id(service_id, name): return f'{service_id}:{name}'

def _classify_model_entry(child):
    if child.is_file() and child.suffix.lower() in MODEL_FILE_SUFFIXES: return 'gguf_file' if child.suffix.lower()=='.gguf' else 'model_file'
    if child.is_dir():
        names={p.name for p in child.iterdir()} if child.exists() else set()
        if {'config.json'} & names or any(p.suffix.lower() in MODEL_FILE_SUFFIXES for p in child.iterdir() if p.is_file()): return 'huggingface_or_model_directory'
        return 'model_repository_directory'
    return None

def _dir_inventory(service):
    out=[]; paths=service.get('paths') or {}; mdir=paths.get('models')
    if not mdir: return out, 'not_declared', mdir
    p=Path(mdir)
    if not p.exists(): return out, 'unavailable', mdir
    for child in sorted(p.iterdir(), key=lambda c: c.name.lower())[:500]:
        kind=_classify_model_entry(child)
        if kind: out.append({'name':child.name,'layout':kind,'path':str(child),'installed':True})
    return out, 'available', mdir

def _loaded_names(service_id, state):
    sv=(state.get('services') or {}).get(service_id,{}) ; proc=(state.get('processes') or {}).get(service_id,{})
    names=[]
    for src in (sv, proc, sv.get('details') or {}, proc.get('details') or {}):
        for key in ('loaded_model','current_model','model','requested_model'):
            if src.get(key): names.append(str(src.get(key)))
    return set(names)

def build_models(registry, state=None):
    state=state or {}; models=[]
    for s in registry.get('services',[]):
        sid=s.get('service_id'); ops=s.get('operations') or {}; paths=s.get('paths') or {}; loaded=_loaded_names(sid,state)
        entries, source_state, mdir = _dir_inventory(s)
        if entries:
            for e in entries:
                name=e['name']; mid=model_id(sid,name)
                models.append({'model_id':mid,'name':name,'backing_service':sid,'source':'manifest_model_directory','source_path':e['path'],'model_location':mdir,'source_status':source_state,'capabilities':['unknown'],'classification_status':e['layout'],'installed':True,'currently_loaded':name in loaded or mid in loaded,'preferred':False,'assigned':False,'default':False,'unavailable':False,'unresolved':False})
        elif sid in {'textgen','ollama'} or paths.get('models'):
            models.append({'model_id':model_id(sid,'unavailable-inventory'),'name':'unavailable-inventory','backing_service':sid,'source':'manifest_model_directory' if paths.get('models') else 'service_inventory','model_location':mdir,'source_status':source_state if paths.get('models') else 'unavailable','capabilities':['unknown'],'classification_status':'unknown','installed':False,'currently_loaded':False,'preferred':False,'assigned':False,'default':False,'unavailable':True,'unresolved':True})
        for key,path in paths.items():
            if key not in {'models','model'} and 'model' in key:
                models.append({'model_id':model_id(sid,key),'name':key,'backing_service':sid,'source':'manifest_path','source_path':path,'source_status':'declared','capabilities':['unknown'],'classification_status':'declared_path','installed':False,'currently_loaded':False,'preferred':False,'assigned':False,'default':False,'unavailable':False,'unresolved':False})
        if 'list_models' in ops or 'inventory_models' in ops:
            models.append({'model_id':model_id(sid,'runtime-api-inventory'),'name':'runtime-api-inventory','backing_service':sid,'source':'runtime_api','source_status':'available_hook_unqueried','capabilities':['unknown'],'classification_status':'runtime_inventory_hook','installed':False,'currently_loaded':False,'preferred':False,'assigned':False,'default':False,'unavailable':False,'unresolved':False})
    return models

def _known_model_ids(models): return {m['model_id'] for m in models if not m.get('unresolved')}
def _annotate_model_roles(models, prefs, assigns):
    pref_ids={v.get('model_id') for v in (prefs.get('preferences') or {}).values()}; assign_ids={v.get('model_id') for v in (assigns.get('assignments') or {}).values()}
    for m in models:
        m['preferred']=m['model_id'] in pref_ids; m['default']=m['preferred']; m['assigned']=m['model_id'] in assign_ids
    return models

def load_preferences(root=None, models=None):
    r=_root(root); models=models or build_models(control_status(r)['registry'], control_status(r)['state']); known=_known_model_ids(models)
    data=_read_json(r/PREFS, {'version':'ai-services-model-preferences-v1','preferences':{}}); prefs=data.setdefault('preferences',{})
    for k in KNOWN_DEFAULTS: prefs.setdefault(k, {'model_id':None,'backing_service':None,'resolution':'unresolved','reason':'Not configured','last_updated':None,'updated_by':None})
    for v in prefs.values():
        mid=v.get('model_id'); v['resolution']='resolved' if mid in known else 'unresolved'
    return data

def set_preference(name, model_id_value, updated_by='steward', reason='', root=None):
    r=_root(root); cp=control_status(r); models=build_models(cp['registry'], cp['state']); svc=model_id_value.split(':',1)[0] if model_id_value and ':' in model_id_value else None
    data=load_preferences(r, models); data['preferences'][name]={'model_id':model_id_value,'backing_service':svc,'resolution':'resolved' if model_id_value in _known_model_ids(models) else 'unresolved','reason':reason,'last_updated':now(),'updated_by':updated_by}
    _write_json(r/PREFS, data); append_audit({'actor':updated_by,'operation':'set_model_preference','service_id':svc,'authority':'steward_approved' if updated_by=='steward' else 'unapproved','policy_result':'allowed' if updated_by=='steward' else 'denied','result':'updated' if updated_by=='steward' else 'denied','details':{'preference':name,'model_id':model_id_value}}, r); return data

def load_assignments(root=None, models=None):
    r=_root(root); models=models or build_models(control_status(r)['registry'], control_status(r)['state']); known=_known_model_ids(models)
    data=_read_json(r/ASSIGN, {'version':'ai-services-model-assignments-v1','assignments':{}}); assigns=data.setdefault('assignments',{})
    for worker in KNOWN_ASSIGNMENTS: assigns.setdefault(worker, {'model_id':None,'fallback_model_id':None,'backing_service':None,'allowed_services':[],'allowed_operations':['status'],'approval_requirement':'steward_required_for_start_stop_load_model','reason':'Not configured','last_updated':None,'updated_by':None,'resolution':'unresolved'})
    for v in assigns.values():
        mid=v.get('model_id'); v['resolution']='resolved' if mid in known else 'unresolved'; v.setdefault('allowed_services', [v.get('backing_service')] if v.get('backing_service') else []); v.setdefault('fallback_model_id', None)
    return data

def set_assignment(worker, model_id_value, updated_by='steward', reason='', allowed_operations=None, root=None):
    if updated_by != 'steward':
        append_audit({'actor':updated_by,'operation':'set_assignment','service_id':None,'authority':'unapproved','policy_result':'denied','result':'denied','details':{'worker':worker}}, _root(root)); return {'error':'steward_approval_required','updated':False}
    r=_root(root); cp=control_status(r); models=build_models(cp['registry'], cp['state']); svc=model_id_value.split(':',1)[0] if model_id_value and ':' in model_id_value else None
    data=load_assignments(r, models); data['assignments'][worker]={'model_id':model_id_value,'fallback_model_id':None,'backing_service':svc,'allowed_services':[svc] if svc else [],'allowed_operations':allowed_operations or ['status'],'approval_requirement':'steward_required_for_start_stop_load_model','reason':reason,'last_updated':now(),'updated_by':updated_by,'resolution':'resolved' if model_id_value in _known_model_ids(models) else 'unresolved'}
    _write_json(r/ASSIGN, data); append_audit({'actor':updated_by,'operation':'set_assignment','service_id':svc,'authority':'steward_approved','policy_result':'allowed','result':'updated','details':{'worker':worker,'model_id':model_id_value}}, r); return data

def audit_tail(root=None, limit=25):
    p=_root(root)/'runtime/ai_services/audit_log.jsonl'; rows=[]
    if p.exists():
        for line in reversed(p.read_text(encoding='utf-8').splitlines()[-limit:]):
            try: rows.append(_sanitize(json.loads(line)))
            except Exception: rows.append({'unparsed':'[redacted]' if any(s in line.lower() for s in SECRET_KEYS) else line[:200]})
    return rows

def approvals(root=None): return load_approvals(_root(root))
def decide_approval(decision, operation, service_id, actor='alfred', model=None, approved_by='steward', reason='', root=None):
    if actor == approved_by: return {'error':'actor_cannot_approve_own_authority_expansion','updated':False}
    return record_approval_decision(operation, service_id, actor=actor, approved_by=approved_by, decision=decision, reason=reason, model=model, root=_root(root))
def refresh_status(root=None):
    r=_root(root); payload=control_status(r); append_audit({'actor':'steward','operation':'status_refresh','service_id':None,'authority':'steward_approved','policy_result':'allowed','result':'success','details':{}}, r); return payload

def build_steward_ai_services_panel(root=None):
    r=_root(root); cp=control_status(r); reg=cp['registry']; state=cp['state']; models=build_models(reg,state); prefs=load_preferences(r,models); assigns=load_assignments(r,models); _annotate_model_roles(models,prefs,assigns); appr=approvals(r); audit=audit_tail(r)
    services=[]
    for s in reg.get('services',[]):
        sid=s.get('service_id'); sv=(state.get('services') or {}).get(sid,{}); proc=(state.get('processes') or {}).get(sid,{})
        services.append({'service_id':sid,'display_name':s.get('display_name'),'service_type':s.get('service_type'),'endpoint':s.get('default_endpoint'),'host_policy':s.get('host_policy'),'ports':s.get('ports',[]),'current_state':sv.get('status','unknown'),'health_status':proc.get('health_status') or sv.get('health_status') or sv.get('status','unknown'),'pid':proc.get('pid'),'last_health_result':proc.get('last_health_result') or sv.get('last_health_result'),'last_startup_time':proc.get('started_at') or sv.get('last_startup_time'),'startup_failures':proc.get('startup_failures') or sv.get('startup_failures',0),'process_exit_code':proc.get('return_code') or proc.get('exit_code'),'last_operation':sv.get('last_operation') or proc.get('operation_id'),'available_operations':sorted((s.get('operations') or {}).keys()),'approval_requirements':s.get('approval',{}),'log_reference':proc.get('log_path') or sv.get('log_path'),'manifest_path':s.get('manifest_path'),'model_locations':{k:v for k,v in (s.get('paths') or {}).items() if 'model' in k},'paths':s.get('paths',{}),'operations':s.get('operations',{}),'launcher':(s.get('launcher') or (s.get('paths') or {}).get('launcher')),'working_directory':(s.get('paths') or {}).get('working_directory') or (s.get('paths') or {}).get('application'),'local_only':s.get('local_only', True)})
    counts={'discovered_services':len(services),'running_services':sum(1 for s in services if s['current_state']=='running'),'unhealthy_services':sum(1 for s in services if s['health_status'] in {'unhealthy','interrupted','health_failed'}),'pending_approvals':sum(1 for a in appr.get('requests',[]) if a.get('state')=='requires_approval'),'known_installed_models':sum(1 for m in models if m.get('installed')),'active_default_assignments':sum(1 for v in (prefs.get('preferences') or {}).values() if v.get('resolution')=='resolved')}
    actions={'rediscover':'ai-services rediscover','refresh_status':'ai-services status','refresh_models':'PYTHONPATH=src python -m estate.cli.main ai-services models --json','view_registry':'cat runtime/ai_services/registry.json','view_state':'cat runtime/ai_services/state.json','view_audit':'tail -n 50 runtime/ai_services/audit_log.jsonl','view_approvals':'cat runtime/ai_services/approvals.json','approve':'PYTHONPATH=src python -m estate.cli.main ai-services approve ...','deny':'PYTHONPATH=src python -m estate.cli.main ai-services deny ...'}
    return {'available':True,'path':'runtime/ai_services/registry.json; runtime/ai_services/state.json; runtime/ai_services/model_preferences.json; runtime/ai_services/model_assignments.json','kind':'steward_ai_services_models','data':{'local_only':True,'control_surface':'Office of the Steward / AI Services / Models','dashboard':counts,'services':services,'models':models,'model_inventory_by_service':{sid:[m for m in models if m.get('backing_service')==sid] for sid in [s['service_id'] for s in services]},'model_preferences':prefs,'model_assignments':assigns,'approvals':appr,'audit_tail':audit,'actions':actions,'rediscovery_refresh_hooks':actions}}
