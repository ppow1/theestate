import json, os, re, shlex, subprocess, time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
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
    def is_alive(self, pid):
        try:
            os.kill(int(pid), 0); return True
        except Exception:
            return False

class HealthChecker:
    def check(self, endpoint, timeout_seconds=30, interval_seconds=2, runner=None, pid=None):
        deadline=time.monotonic()+max(0.1, float(timeout_seconds)); last_error=None; attempts=0
        while time.monotonic() <= deadline:
            attempts += 1
            if pid is not None and runner is not None and hasattr(runner, 'is_alive') and not runner.is_alive(pid):
                return {'healthy':False,'status':'process_exited','error':'process_exited_before_health','attempts':attempts,'pid_alive':False}
            try:
                req=Request(endpoint, method='GET')
                with urlopen(req, timeout=min(float(interval_seconds), max(0.1, deadline-time.monotonic()))) as resp:
                    code=getattr(resp, 'status', resp.getcode())
                    if 200 <= int(code) < 300:
                        return {'healthy':True,'status':'healthy','http_status':code,'attempts':attempts,'pid_alive':True}
                    last_error=f'http_status_{code}'
            except Exception as e:
                last_error=type(e).__name__.lower()
            if time.monotonic() < deadline:
                time.sleep(max(0.1, float(interval_seconds)))
        return {'healthy':False,'status':'health_failed','error':last_error or 'timeout','attempts':attempts,'pid_alive':None}

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

def _status_health_endpoint(svc):
    status=(svc.get('operations') or {}).get('status', {})
    raw=status.get('api_template') or status.get('status_check')
    if raw:
        parts=raw.split()
        candidate=parts[-1] if parts else raw
        if candidate.startswith('http://') or candidate.startswith('https://'):
            endpoint=candidate
        elif candidate.startswith('/'):
            endpoint=(svc.get('default_endpoint') or '').rstrip('/') + candidate
        else:
            endpoint=None
    else:
        endpoint=None
    if svc.get('service_id') == 'textgen':
        endpoint='http://127.0.0.1:5000/v1/models'
    return endpoint

def _loopback_url(url):
    try:
        host=urlparse(url).hostname
    except Exception:
        return False
    return host in {'127.0.0.1','localhost','::1'}

def _log_tail(path, max_chars=1200):
    try:
        text=Path(path).read_text(encoding='utf-8', errors='replace')
        return text[-max_chars:]
    except Exception:
        return None

def _diagnostics(sid, svc, proc, health, log_abs, command):
    endpoint=(health or {}).get('endpoint') or _status_health_endpoint(svc)
    return {'tracked_pid': proc.get('pid') if proc else None, 'pid_alive': (health or {}).get('pid_alive'), 'expected_endpoint': endpoint, 'expected_port': (svc.get('ports') or [None])[0], 'last_health_error': (health or {}).get('error'), 'log_path': proc.get('log_path') if proc else None, 'log_tail': _log_tail(log_abs), 'command_label': command}

def execute_plan(plan, svc, runner=None, root=None, health_checker=None, health_timeout_seconds=30, health_interval_seconds=2):
    runner=runner or ProcessRunner(); health_checker=health_checker or HealthChecker(); op=plan['operation']; sid=plan['service_id']
    model=plan.get('details',{}).get('model')
    append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_attempted','details':{}}, root)
    try:
        if op=='stop':
            st=load_state(root); proc=st.get('processes',{}).get(sid)
            if not proc or not proc.get('pid'): raise RuntimeError('no_tracked_process')
            res=runner.stop(proc['pid']); proc['status']='stopped'; proc['current_status']='stopped'; proc['stopped_at']=now(); save_state(st, root)
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_succeeded','details':res}, root)
            return {**plan,'approval_state':'executed','result':'executed','execution':res}
        cmd=plan.get('planned_command')
        if not cmd: raise RuntimeError('no_safe_command_template')
        endpoint=_status_health_endpoint(svc)
        if endpoint and not _loopback_url(endpoint): raise RuntimeError('health_endpoint_must_be_loopback')
        log=f'runtime/ai_services/logs/{sid}.log'; log_abs=(Path(root)/log) if root else (STATE.parent/'logs'/f'{sid}.log'); log_abs.parent.mkdir(parents=True, exist_ok=True)
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'process_start_attempted','details':{'command_label':cmd}}, root)
        res=runner.start(cmd, cwd=(svc.get('paths') or {}).get('application'), log_path=str(log_abs))
        pid=res.get('pid')
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'process_started','details':{'pid':pid}}, root)
        st=load_state(root)
        proc={'service_id':sid,'operation_id':op,'pid':pid,'start_time':now(),'command_label':cmd,'endpoint':svc.get('default_endpoint'),'expected_ports':svc.get('ports',[]),'current_status':'process_started','health_status':'pending' if endpoint else 'not_declared','log_path':log}
        st['processes'][sid]=proc; st['services'][sid]={'status':'health_pending' if endpoint else 'process_started','endpoint':svc.get('default_endpoint'),'last_operation':op}; save_state(st, root)
        if endpoint:
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'health_check_started','details':{'endpoint':endpoint,'timeout_seconds':health_timeout_seconds,'interval_seconds':health_interval_seconds}}, root)
            health=health_checker.check(endpoint, timeout_seconds=health_timeout_seconds, interval_seconds=health_interval_seconds, runner=runner, pid=pid)
            health['endpoint']=endpoint
            st=load_state(root); proc=st['processes'][sid]
            proc['health_status']='healthy' if health.get('healthy') else 'failed'; proc['health_result']=health; proc['pid_alive']=health.get('pid_alive')
            if health.get('healthy'):
                proc['current_status']='healthy'; st['services'][sid]={'status':'running','endpoint':svc.get('default_endpoint'),'last_operation':op}
                save_state(st, root)
                append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'health_check_succeeded','details':health}, root)
                append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_succeeded','details':{**res,'health':health}}, root)
                return {**plan,'approval_state':'executed','result':'executed','execution':{**res,'lifecycle_state':'healthy','health':health}}
            event='process_exited_before_health' if health.get('status')=='process_exited' or health.get('error')=='process_exited_before_health' else 'health_check_failed'
            proc['current_status']='process_exited' if event=='process_exited_before_health' else 'exited_or_unhealthy'; proc['health_error']=health.get('error')
            st['services'][sid]={'status':'process_exited' if event=='process_exited_before_health' else 'health_failed','endpoint':svc.get('default_endpoint'),'last_operation':op}
            save_state(st, root)
            diag=_diagnostics(sid, svc, proc, health, log_abs, cmd)
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':event,'details':{**health,'diagnostics':diag}}, root)
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_failed','details':diag}, root)
            return {**plan,'approval_state':'failed','result':'health_failed','execution':{**res,'lifecycle_state':st['services'][sid]['status'],'health':health,'diagnostics':diag}}
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_succeeded','details':res}, root)
        return {**plan,'approval_state':'executed','result':'executed','execution':{**res,'lifecycle_state':'process_started'}}
    except Exception as e:
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'authority':'steward_approved','policy_result':'allowed','result':'execution_failed','details':{'error':str(e)}}, root)
        return {**plan,'approval_state':'failed','result':'failed','error':str(e)}
