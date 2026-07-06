import json, os, re, shlex, subprocess, time, uuid
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from pathlib import Path
from .discovery import append_audit
from .paths import STATE

APPROVALS='approvals.json'
SAFE_MODEL=re.compile(r'^[A-Za-z0-9._+-]+$')

class ProcessRunner:
    def __init__(self):
        self._processes={}
        self._streams={}
    def start(self, command, cwd=None, log_path=None):
        stdout = open(log_path, 'ab') if log_path else subprocess.DEVNULL
        args = command_to_subprocess_args(command)
        proc = subprocess.Popen(args, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT, shell=False)
        self._processes[proc.pid]=proc
        if log_path:
            self._streams[proc.pid]=stdout
        return {'pid': proc.pid, 'return_code': proc.poll()}
    def stop(self, pid):
        os.kill(int(pid), 15); return {'stopped': True, 'pid': int(pid)}
    def is_alive(self, pid):
        proc=self._processes.get(int(pid)) if pid is not None else None
        if proc is not None:
            return proc.poll() is None
        try:
            os.kill(int(pid), 0); return True
        except Exception:
            return False
    def return_code(self, pid):
        proc=self._processes.get(int(pid)) if pid is not None else None
        return proc.poll() if proc is not None else None

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


def _safe_substitution(value):
    if value is None:
        return ''
    text=str(value)
    if not SAFE_MODEL.fullmatch(text) or '..' in text or '/' in text or '\\' in text:
        raise ValueError('invalid_model_name')
    return text

def _operation(svc, operation):
    return (svc.get('operations') or {}).get(operation,{})

def command_to_subprocess_args(command):
    if isinstance(command, dict):
        args=command.get('subprocess_args') or command.get('arguments')
        if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
            raise ValueError('structured_command_requires_string_argument_list')
        return args
    if isinstance(command, list):
        return command
    return shlex.split(command, posix=(os.name != 'nt'))

def _render_arguments(arguments, model=None):
    rendered=[]
    for arg in arguments or []:
        if not isinstance(arg, str):
            raise ValueError('command_arguments_must_be_strings')
        rendered.append(arg.replace('{model}', _safe_substitution(model)))
    return rendered

def _windows_batch_command(op, model=None):
    launcher=op.get('launcher')
    if not launcher or not isinstance(launcher, str):
        raise ValueError('windows_batch_launcher_required')
    if any(sep in launcher for sep in ['/', '\\']) or launcher.lower() != Path(launcher).name.lower():
        raise ValueError('windows_batch_launcher_must_be_local_filename')
    if not launcher.lower().endswith(('.bat', '.cmd')):
        raise ValueError('windows_batch_launcher_must_be_batch_file')
    rendered=_render_arguments(op.get('arguments', []), model=model)
    subprocess_args=['cmd.exe','/d','/c',launcher,*rendered]
    return {
        'command_type':'windows_batch',
        'working_directory':op.get('working_directory'),
        'launcher':launcher,
        'arguments':rendered,
        'subprocess_args':subprocess_args,
        'shell':False,
    }

def planned_command_for(svc, operation, model=None):
    op=_operation(svc, operation)
    ctype=op.get('command_type')
    if ctype == 'windows_batch':
        return _windows_batch_command(op, model=model)
    return safe_command(svc, operation, model=model)

def command_working_directory(svc, operation):
    op=_operation(svc, operation)
    return op.get('working_directory') or (svc.get('paths') or {}).get('application')

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
    return tmpl.replace('{model}', _safe_substitution(model) if model is not None else '')

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

def _attempt_log_path(sid, root=None):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    name=f'{sid}-{stamp}-{uuid.uuid4().hex[:8]}.log'
    rel=f'runtime/ai_services/logs/{name}'
    return rel, (Path(root)/rel) if root else (STATE.parent/'logs'/name)

def _runner_return_code(runner, pid):
    if pid is None or not hasattr(runner, 'return_code'):
        return None
    try:
        return runner.return_code(pid)
    except Exception:
        return None

def _runner_alive(runner, pid):
    if pid is None or not hasattr(runner, 'is_alive'):
        return None
    try:
        return runner.is_alive(pid)
    except Exception:
        return None

def _diagnostics(sid, svc, proc, health, log_abs, command, runner=None):
    endpoint=(health or {}).get('endpoint') or _status_health_endpoint(svc)
    pid=proc.get('pid') if proc else None
    pid_alive=(health or {}).get('pid_alive')
    if pid_alive is None:
        pid_alive=_runner_alive(runner, pid)
    return_code=(health or {}).get('return_code')
    if return_code is None:
        return_code=_runner_return_code(runner, pid)
    return {'service_id': sid, 'operation': proc.get('operation_id') if proc else None, 'tracked_pid': pid, 'pid': pid, 'working_directory': proc.get('working_directory') if proc else None, 'pid_alive': pid_alive, 'process_alive': pid_alive, 'process_exit_code': return_code, 'return_code': return_code, 'expected_endpoint': endpoint, 'health_endpoint': endpoint, 'expected_port': (svc.get('ports') or [None])[0], 'health_status': (health or {}).get('status'), 'last_health_error': (health or {}).get('error'), 'log_path': proc.get('log_path') if proc else None, 'log_tail': _log_tail(log_abs), 'command_label': command}



def _interruption_name(exc):
    return type(exc).__name__

def _record_health_interrupted(plan, svc, sid, op, model, res, pid, endpoint, log_abs, cmd, root, exc):
    interrupted={
        'healthy': False,
        'status': 'interrupted',
        'error': _interruption_name(exc),
        'endpoint': endpoint,
        'pid_alive': None,
    }
    st=load_state(root)
    proc=st.setdefault('processes', {}).setdefault(sid, {
        'service_id': sid,
        'operation_id': op,
        'pid': pid,
        'start_time': now(),
        'command_label': cmd,
        'endpoint': svc.get('default_endpoint'),
        'expected_ports': svc.get('ports', []),
        'log_path': res.get('log_path') if isinstance(res, dict) else None,
    })
    proc.update({
        'current_status': 'interrupted',
        'health_status': 'interrupted',
        'health_error': _interruption_name(exc),
        'health_result': interrupted,
        'pid_alive': None,
        'interrupted_at': now(),
        'interruption': {'type': _interruption_name(exc), 'message': str(exc)},
    })
    st.setdefault('services', {})[sid]={
        'status': 'interrupted',
        'endpoint': svc.get('default_endpoint'),
        'last_operation': op,
    }
    save_state(st, root)
    diag=_diagnostics(sid, svc, proc, interrupted, log_abs, cmd, runner=None)
    diag['interruption']={'type': _interruption_name(exc), 'message': str(exc)}
    append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'health_check_interrupted','details':{**interrupted,'diagnostics':diag}}, root)
    append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_interrupted','details':diag}, root)
    return {**plan,'approval_state':'interrupted','result':'interrupted','execution':{**(res or {}),'lifecycle_state':'interrupted','health':interrupted,'diagnostics':diag}}

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
        log, log_abs=_attempt_log_path(sid, root); log_abs.parent.mkdir(parents=True, exist_ok=True); log_abs.write_text(f'[{now()}] ai_services attempt log created service={sid} operation={op}\n', encoding='utf-8')
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'process_start_attempted','details':{'command_label':cmd,'log_path':log,'working_directory':command_working_directory(svc, op)}}, root)
        res=runner.start(cmd, cwd=command_working_directory(svc, op), log_path=str(log_abs))
        res={**(res or {}), 'log_path': log, 'working_directory': command_working_directory(svc, op)}
        pid=res.get('pid')
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'process_started','details':{'pid':pid,'log_path':log,'working_directory':command_working_directory(svc, op),'return_code':res.get('return_code')}}, root)
        st=load_state(root)
        proc={'service_id':sid,'operation_id':op,'pid':pid,'start_time':now(),'command_label':cmd,'endpoint':svc.get('default_endpoint'),'expected_ports':svc.get('ports',[]),'current_status':'process_started','health_status':'pending' if endpoint else 'not_declared','log_path':log,'working_directory':command_working_directory(svc, op),'return_code':res.get('return_code')}
        st['processes'][sid]=proc; st['services'][sid]={'status':'health_pending' if endpoint else 'process_started','endpoint':svc.get('default_endpoint'),'last_operation':op}; save_state(st, root)
        if endpoint:
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'health_check_started','details':{'endpoint':endpoint,'timeout_seconds':health_timeout_seconds,'interval_seconds':health_interval_seconds}}, root)
            try:
                health=health_checker.check(endpoint, timeout_seconds=health_timeout_seconds, interval_seconds=health_interval_seconds, runner=runner, pid=pid)
            except (KeyboardInterrupt, InterruptedError) as e:
                return _record_health_interrupted(plan, svc, sid, op, model, res, pid, endpoint, log_abs, cmd, root, e)
            health['endpoint']=endpoint
            st=load_state(root); proc=st['processes'][sid]
            proc['health_status']='healthy' if health.get('healthy') else 'failed'; proc['health_result']=health; proc['pid_alive']=health.get('pid_alive'); proc['return_code']=_runner_return_code(runner, pid)
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
            diag=_diagnostics(sid, svc, proc, health, log_abs, cmd, runner=runner)
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':event,'details':{**health,'diagnostics':diag}}, root)
            append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_failed','details':diag}, root)
            return {**plan,'approval_state':'failed','result':'health_failed','execution':{**res,'lifecycle_state':st['services'][sid]['status'],'health':health,'diagnostics':diag}}
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'requested_model':model,'authority':'steward_approved','policy_result':'allowed','result':'execution_succeeded','details':res}, root)
        return {**plan,'approval_state':'executed','result':'executed','execution':{**res,'lifecycle_state':'process_started'}}
    except Exception as e:
        append_audit({'actor':plan.get('actor'),'operation':op,'service_id':sid,'authority':'steward_approved','policy_result':'allowed','result':'execution_failed','details':{'error':str(e)}}, root)
        return {**plan,'approval_state':'failed','result':'failed','error':str(e)}
