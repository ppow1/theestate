import json, os, re, shlex, subprocess
from datetime import datetime, timezone
from pathlib import Path
from .discovery import append_audit
from .paths import STATE

APPROVALS='approvals.json'
SAFE_MODEL=re.compile(r'^[A-Za-z0-9._+-]+$')

class ProcessRunner:
    def start(self, command, cwd=None, log_path=None):
        stdout = open(log_path, 'ab') if log_path else subprocess.DEVNULL
        args = command if isinstance(command, list) else shlex.split(command, posix=(os.name != 'nt'))
        proc = subprocess.Popen(args, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT, shell=False)
        return {'pid': proc.pid}
    def stop(self, pid):
        os.kill(int(pid), 15); return {'stopped': True, 'pid': int(pid)}

def now(): return datetime.now(timezone.utc).isoformat()
def _root(root): return Path(root) if root else None
def state_path(root=None): return (Path(root)/'runtime/ai_services/state.json') if root else STATE
def approvals_path(root=None): return (Path(root)/'runtime/ai_services'/APPROVALS) if root else STATE.parent/APPROVALS

def load_state(root=None):
    p=state_path(root)
    if not p.exists(): return {'version':'ai-services-state-v1','services':{},'processes':{}}
    data=json.loads(p.read_text(encoding='utf-8'))
    data.setdefault('services',{}); data.setdefault('processes',{})
    return data

def save_state(data, root=None):
    p=state_path(root); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8'); return p

def _approval_key(operation, service_id, actor, model=None):
    return '|'.join([operation, service_id, actor or '', model or ''])

def load_approvals(root=None):
    p=approvals_path(root)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'version':'ai-services-approvals-v1','requests':[]}

def save_approvals(data, root=None):
    p=approvals_path(root); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8'); return p

def record_approval_request(operation, service_id, actor='alfred', reason=None, model=None, root=None):
    data=load_approvals(root); key=_approval_key(operation, service_id, actor, model)
    existing=next((r for r in data['requests'] if r.get('approval_key')==key and r.get('state')=='requires_approval'), None)
    if existing: return existing
    rec={'approval_key':key,'operation':operation,'service_id':service_id,'actor':actor,'reason':reason,'model':model,'state':'requires_approval','requested_at':now()}
    data['requests'].append(rec); save_approvals(data, root)
    append_audit({'actor':actor,'operation':operation,'service_id':service_id,'requested_model':model,'authority':'unapproved','policy_result':'allowed','result':'approval_requested','details':{'approval_key':key}}, root)
    return rec

def record_approval_decision(operation, service_id, actor='alfred', approved_by=None, decision='approved', reason=None, model=None, root=None):
    if approved_by != 'steward': raise ValueError('only steward may approve or deny AI service execution')
    data=load_approvals(root); key=_approval_key(operation, service_id, actor, model)
    rec=next((r for r in data['requests'] if r.get('approval_key')==key), None)
    if rec is None:
        rec={'approval_key':key,'operation':operation,'service_id':service_id,'actor':actor,'model':model,'requested_at':now()}; data['requests'].append(rec)
    rec.update({'state':'approved' if decision=='approved' else 'denied','decided_by':approved_by,'decided_at':now(),'decision_reason':reason})
    save_approvals(data, root)
    append_audit({'actor':actor,'operation':operation,'service_id':service_id,'requested_model':model,'authority':'steward_approved','policy_result':'allowed' if decision=='approved' else 'denied','result':'approval_granted' if decision=='approved' else 'approval_denied','details':{'approval_key':key}}, root)
    return rec

def has_approval(operation, service_id, actor='alfred', approved_by=None, model=None, root=None):
    if approved_by=='steward':
        record_approval_decision(operation, service_id, actor, approved_by, 'approved', model=model, root=root)
        return True
    key=_approval_key(operation, service_id, actor, model)
    return any(r.get('approval_key')==key and r.get('state')=='approved' for r in load_approvals(root).get('requests',[]))

def validate_model(svc, model, root=None):
    if not model or not SAFE_MODEL.fullmatch(model) or '..' in model or '/' in model or '\\' in model:
        return False, 'invalid_model_name'
    mdir=(svc.get('paths') or {}).get('models')
    if mdir and Path(mdir).exists() and not (Path(mdir)/model).exists():
        return False, 'model_not_found_in_manifest_directory'
    return True, None

def safe_command(svc, operation, model=None):
    tmpl=(svc.get('operations') or {}).get(operation,{}).get('command_template')
    if not tmpl: return None
    if any(bad in tmpl.lower() for bad in ['discover safe launcher','must be confirmed','configured open webui','approved open webui']): return None
    return tmpl.replace('{model}', model or '')

def execute_plan(plan, svc, runner=None, root=None):
    runner=runner or ProcessRunner(); op=plan['operation']; sid=plan['service_id']
    append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':plan.get('details',{}).get('model'),'authority':'steward_approved','policy_result':'allowed','result':'execution_attempted','details':{}}, root)
    try:
        if op=='stop':
            st=load_state(root); proc=st.get('processes',{}).get(sid)
            if not proc or not proc.get('pid'): raise RuntimeError('no_tracked_process')
            res=runner.stop(proc['pid']); proc['status']='stopped'; proc['stopped_at']=now(); save_state(st, root)
        else:
            cmd=plan.get('planned_command')
            if not cmd: raise RuntimeError('no_safe_command_template')
            log=f'runtime/ai_services/logs/{sid}.log'; log_abs=(Path(root)/log) if root else (STATE.parent/'logs'/f'{sid}.log'); log_abs.parent.mkdir(parents=True, exist_ok=True)
            res=runner.start(cmd, cwd=(svc.get('paths') or {}).get('application'), log_path=str(log_abs))
            st=load_state(root); st['processes'][sid]={'service_id':sid,'operation_id':op,'pid':res.get('pid'),'start_time':now(),'command_label':cmd,'endpoint':svc.get('default_endpoint'),'expected_ports':svc.get('ports',[]),'current_status':'running','log_path':log}
            st['services'][sid]={'status':'running','endpoint':svc.get('default_endpoint'),'last_operation':op}; save_state(st, root)
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':plan.get('details',{}).get('model'),'authority':'steward_approved','policy_result':'allowed','result':'execution_succeeded','details':res}, root)
        return {**plan,'approval_state':'executed','result':'executed','execution':res}
    except Exception as e:
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'authority':'steward_approved','policy_result':'allowed','result':'execution_failed','details':{'error':str(e)}}, root)
        return {**plan,'approval_state':'failed','result':'failed','error':str(e)}
