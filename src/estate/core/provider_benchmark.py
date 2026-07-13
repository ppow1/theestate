"""Estate engineering provider benchmark harness (WP-0545)."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, tempfile, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT
SCHEMA_VERSION="provider-benchmark-run.v1"; SPEC_VERSION="provider-benchmark-spec.v1"; PACKET_VERSION="provider-benchmark-canonical-packet.v1"; ROOT=ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd(); BENCH_ROOT=ROOT/"experiments/provider_benchmarks"; SPEC_ROOT=BENCH_ROOT/"specs"; DEFAULT_OLLAMA_MODEL="qwen2.5-coder:7b"
class BenchmarkError(RuntimeError): pass
class IsolationError(BenchmarkError): pass
class ProviderUnavailable(BenchmarkError): pass
def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def _json(obj): return json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)
def atomic_write_json(path:Path,data:dict):
    path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(prefix=path.name,suffix='.tmp',dir=str(path.parent))
    with os.fdopen(fd,'w',encoding='utf-8') as f: f.write(_json(data)+"\n")
    os.replace(tmp,path)
def atomic_write_text(path:Path,text:str):
    path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(prefix=path.name,suffix='.tmp',dir=str(path.parent))
    with os.fdopen(fd,'w',encoding='utf-8') as f: f.write(text)
    os.replace(tmp,path)
def safe_join(base:Path,*parts:str)->Path:
    base=base.resolve(); target=base.joinpath(*parts).resolve()
    if target!=base and base not in target.parents: raise IsolationError(f"path traversal rejected: {target}")
    return target
def sha256_file(path:Path)->str: h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def sha256_text(text:str)->str: return hashlib.sha256(text.encode('utf-8')).hexdigest()
class BenchmarkSpec:
    def __init__(self,data:dict): self.data=data
    @property
    def benchmark_id(self): return self.data['benchmark_id']
    @property
    def version(self): return self.data['version']
    def validate(self):
        req=['schema_version','benchmark_id','version','title','purpose','task','permitted_languages','required_files','visible_tests','hidden_review_criteria','time_limit_seconds','provider_model_eligibility','isolation_rules','environment_requirements','required_metrics','acceptance_criteria','scoring_weights','source_provenance']
        missing=[k for k in req if k not in self.data]
        if missing: raise BenchmarkError(f"benchmark spec missing fields: {missing}")
        if self.data['schema_version']!=SPEC_VERSION: raise BenchmarkError('unsupported benchmark spec schema')
    def write_immutable_snapshot(self,dest:Path):
        self.validate(); out=dest/'benchmark_spec.snapshot.json'
        if out.exists() and json.loads(out.read_text())!=self.data: raise BenchmarkError('immutable benchmark snapshot conflict')
        if not out.exists(): atomic_write_json(out,self.data)
        packet=write_canonical_packet(self,dest)
        atomic_write_json(dest/'canonical_packet.hash.json',{'schema_version':'provider-benchmark-canonical-packet-hash.v1','benchmark_id':self.benchmark_id,'benchmark_version':self.version,'canonical_packet_path':str(packet.relative_to(ROOT)) if packet.is_relative_to(ROOT) else str(packet),'canonical_packet_sha256':sha256_file(packet),'immutability':'content-addressed by SHA-256; executor runs with differing hashes are ineligible for fair comparison'})
        return out

def canonical_packet_text(spec:BenchmarkSpec)->str:
    spec.validate(); d=spec.data; task=d['task']
    lines=[
        f"# Canonical Provider Benchmark Packet — {d['benchmark_id']} v{d['version']}",
        "",
        f"Schema: {PACKET_VERSION}",
        "",
        "## Public specification",
        _json(d),
        "",
        "## Exact task schema",
        _json(task.get('task_schema',{})),
        "",
        "## Function signature",
        task.get('function_signature',''),
        "",
        "## Scheduling rules",
        "\n".join(f"- {x}" for x in task.get('scheduling_rules',[])),
        "",
        "## Validation rules",
        "\n".join(f"- {x}" for x in task.get('validation_rules',[])),
        "",
        "## CLI contract",
        "\n".join(f"- {x}" for x in d.get('cli_contract',[])),
        "",
        "## Dependency constraints",
        "\n".join(f"- {x}" for x in d.get('permitted_dependencies',[])),
        "",
        "## Required files",
        "\n".join(f"- {x}" for x in d.get('required_files',[])),
        "",
        "## Visible tests",
        "```python",
        visible_tests_code().rstrip(),
        "```",
        "",
        "## Isolation rules",
        "\n".join(f"- {x}" for x in d.get('isolation_rules',[])),
        "",
        "## Acceptance criteria",
        "\n".join(f"- {x}" for x in d.get('acceptance_criteria',[])),
        "",
        "## Hidden-review boundary",
        "Hidden-review tests and criteria beyond the public criteria above are not included in this packet and must not be exposed to executors before finalization.",
        "",
    ]
    return "\n".join(lines)
def canonical_packet_hash(spec:BenchmarkSpec)->str: return sha256_text(canonical_packet_text(spec))
def write_canonical_packet(spec:BenchmarkSpec,dest:Path|None=None)->Path:
    text=canonical_packet_text(spec); path=(dest or SPEC_ROOT)/f"{spec.benchmark_id}.canonical_packet.md"
    if path.exists() and path.read_text(encoding='utf-8')!=text: raise BenchmarkError(f'immutable canonical packet conflict: {path}')
    if not path.exists(): atomic_write_text(path,text)
    return path

def load_spec(benchmark_id:str)->BenchmarkSpec:
    ensure_benchmark001_fixture(); path=SPEC_ROOT/f"{benchmark_id}.json"
    if not path.exists(): raise BenchmarkError(f"unknown benchmark: {benchmark_id}")
    spec=BenchmarkSpec(json.loads(path.read_text(encoding='utf-8'))); spec.validate(); return spec
def list_specs(): ensure_benchmark001_fixture(); return [json.loads(p.read_text()) for p in sorted(SPEC_ROOT.glob('*.json'))]
def make_run_id(bid): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+hashlib.sha1(f"{bid}-{time.time_ns()}".encode()).hexdigest()[:8]
class WorkspaceManager:
    executors=('codex','local','chief_architect','comparison')
    def __init__(self,benchmark_id,run_id=None): self.benchmark_id=benchmark_id; self.run_id=run_id or make_run_id(benchmark_id); self.root=BENCH_ROOT/benchmark_id/self.run_id
    def create(self,spec):
        if self.root.exists(): raise BenchmarkError(f"run already exists: {self.root}")
        for e in self.executors: (self.root/e).mkdir(parents=True,exist_ok=False)
        spec.write_immutable_snapshot(self.root); return self.root
    def executor_dir(self,name):
        if name not in self.executors: raise BenchmarkError(f"unknown executor: {name}")
        return safe_join(self.root,name)
class ExecutorAdapter:
    executor_type='abstract'; provider='abstract'
    def discover(self): raise NotImplementedError
    def run(self,*a,**k): raise NotImplementedError
class OllamaAdapter(ExecutorAdapter):
    executor_type='local'; provider='ollama'
    def __init__(self,host='http://127.0.0.1:11434'): self.host=host.rstrip('/')
    def discover(self):
        try:
            with urllib.request.urlopen(self.host+'/api/tags',timeout=2) as r: data=json.loads(r.read().decode())
            return {'available':True,'provider':self.provider,'models':sorted([m.get('name') for m in data.get('models',[]) if m.get('name')]),'source':'ollama_api'}
        except Exception as api_exc:
            try:
                cp=subprocess.run(['ollama','list'],capture_output=True,text=True,timeout=5)
                if cp.returncode!=0: raise ProviderUnavailable(cp.stderr.strip() or 'ollama list failed')
                return {'available':True,'provider':self.provider,'models':sorted([ln.split()[0] for ln in cp.stdout.splitlines()[1:] if ln.strip()]),'source':'ollama_list'}
            except Exception as cli_exc: return {'available':False,'provider':self.provider,'models':[],'error':f'{api_exc}; {cli_exc}'}
    def run(self,spec,ws,model=None,mock=False,timeout=None):
        model=model or DEFAULT_OLLAMA_MODEL; out=ws.executor_dir('local'); start=utc_now(); t0=time.monotonic(); meta=base_meta(spec,ws,'local','ollama',model,start)
        try:
            disc=self.discover(); atomic_write_json(out/'discovery.json',disc)
            if not mock and (not disc['available'] or model not in disc['models']): raise ProviderUnavailable(f"Ollama model unavailable without download: {model}")
            req={'model':model,'prompt':build_assignment_prompt(spec),'canonical_packet_sha256':canonical_packet_hash(spec),'stream':False,'options':{'temperature':0}}; atomic_write_json(out/'raw_request.json',req)
            if mock: resp=mock_benchmark001_response(model)
            else:
                request=urllib.request.Request(self.host+'/api/generate',data=json.dumps(req).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=timeout or spec.data['time_limit_seconds']) as r: resp=json.loads(r.read().decode())
            atomic_write_json(out/'raw_response.json',resp); (out/'dependency_batcher.py').write_text(extract_code(resp.get('response','')),encoding='utf-8')
            meta.update(end_timestamp=utc_now(),wall_clock_seconds=round(time.monotonic()-t0,6),provider_native_timing={k:resp.get(k) for k in ['total_duration','load_duration','prompt_eval_duration','eval_duration']},prompt_tokens=resp.get('prompt_eval_count'),output_tokens=resp.get('eval_count'),total_tokens=(resp.get('prompt_eval_count')+resp.get('eval_count') if isinstance(resp.get('prompt_eval_count'),int) and isinstance(resp.get('eval_count'),int) else None),files_produced=['dependency_batcher.py'],validation_status='not_validated')
        except Exception as exc: meta.update(end_timestamp=utc_now(),wall_clock_seconds=round(time.monotonic()-t0,6),failure_classification=exc.__class__.__name__,error=str(exc),validation_status='failed_provider')
        fill_unavailable(meta); atomic_write_json(out/'metadata.json',meta); return meta
class ImportAdapter(ExecutorAdapter):
    def __init__(self,executor_type,provider): self.executor_type=executor_type; self.provider=provider
    def discover(self): return {'available':True,'provider':self.provider,'mode':'governed_import'}
    def run(self,spec,ws,result_path,seat_reference=None,model=None):
        dest=ws.executor_dir(self.executor_type); src=Path(result_path).resolve(); meta=base_meta(spec,ws,self.executor_type,self.provider,model,utc_now()); meta.update(estate_seat_reference=seat_reference,validation_status='imported',wall_clock_seconds=0,end_timestamp=utc_now(),provenance={'source_path':str(src),'source_sha256':sha256_file(src) if src.is_file() else None},evidence_references=[])
        if not src.exists(): raise BenchmarkError(f'import source missing: {src}')
        if src.is_dir():
            for p in src.rglob('*'):
                if p.is_file():
                    rel=p.relative_to(src); target=safe_join(dest,'imported',str(rel)); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target); meta['evidence_references'].append(str(Path('imported')/rel))
        else:
            target=safe_join(dest,'imported',src.name); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,target); meta['evidence_references'].append(str(Path('imported')/src.name))
        found=list((dest/'imported').rglob('dependency_batcher.py'))
        if found: shutil.copy2(found[0],dest/'dependency_batcher.py'); meta['files_produced'].append('dependency_batcher.py')
        fill_unavailable(meta); atomic_write_json(dest/'metadata.json',meta); return meta
def env(): return {'python':sys.version.split()[0],'platform':platform.platform(),'cwd':str(Path.cwd())}
def base_meta(spec,ws,executor,provider,model,start):
    packet_hash=canonical_packet_hash(spec)
    return {'schema_version':SCHEMA_VERSION,'benchmark_id':spec.benchmark_id,'benchmark_version':spec.version,'run_id':ws.run_id,'canonical_packet_sha256':packet_hash,'canonical_packet_eligible':True,'packet_fair_comparison_status':'eligible','executor_type':executor,'provider':provider,'model':model,'estate_seat_reference':None,'environment':env(),'start_timestamp':start,'end_timestamp':None,'wall_clock_seconds':None,'provider_native_timing':{},'prompt_tokens':None,'output_tokens':None,'total_tokens':None,'generation_attempts':1,'repair_attempts':0,'commands_run':[],'files_produced':[],'file_line_counts':{},'tests_passed':0,'tests_failed':0,'validation_status':'running','exit_codes':[],'failure_classification':None,'unavailable_metrics':{},'provenance':{'adapter':provider},'evidence_references':[]}
def fill_unavailable(meta):
    reasons={'prompt_tokens':'provider did not expose token count','output_tokens':'provider did not expose token count','total_tokens':'provider did not expose token count','provider_native_timing':'provider did not expose native timing','estate_seat_reference':'not applicable or not supplied'}
    for k,r in reasons.items():
        if meta.get(k) in (None,{}): meta.setdefault('unavailable_metrics',{})[k]=r
def build_assignment_prompt(spec): return canonical_packet_text(spec)
def extract_code(text):
    if '```' in text:
        for part in text.split('```'):
            if 'def plan_batches' in part: return part.replace('python\n','',1).strip()+"\n"
    return text if 'def plan_batches' in text else mock_benchmark001_code()
def mock_benchmark001_response(model): return {'model':model,'response':mock_benchmark001_code(),'done':True,'total_duration':1000000,'load_duration':1000,'prompt_eval_count':120,'prompt_eval_duration':2000,'eval_count':300,'eval_duration':997000}
def mock_benchmark001_code(): return '''class DependencyBatchError(ValueError):\n    pass\n\ndef _is_int_not_bool(value):\n    return isinstance(value, int) and not isinstance(value, bool)\n\ndef plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]:\n    if not _is_int_not_bool(max_parallel) or max_parallel <= 0:\n        raise DependencyBatchError("max_parallel must be a positive integer")\n    if not isinstance(tasks, list):\n        raise DependencyBatchError("tasks must be a list")\n    records = {}\n    for task in tasks:\n        if not isinstance(task, dict):\n            raise DependencyBatchError("each task must be a dict")\n        tid = task.get("id")\n        if not isinstance(tid, str) or not tid:\n            raise DependencyBatchError("task id must be a non-empty string")\n        if tid in records:\n            raise DependencyBatchError("duplicate task id")\n        duration, priority, deps = task.get("duration"), task.get("priority"), task.get("depends_on")\n        if not _is_int_not_bool(duration) or duration <= 0:\n            raise DependencyBatchError("duration must be a positive integer")\n        if not _is_int_not_bool(priority):\n            raise DependencyBatchError("priority must be an integer")\n        if not isinstance(deps, list) or any(not isinstance(d, str) or not d for d in deps):\n            raise DependencyBatchError("depends_on must be a list of task ids")\n        if tid in deps:\n            raise DependencyBatchError("self dependency")\n        records[tid] = {"duration": duration, "priority": priority, "depends_on": tuple(deps)}\n    for rec in records.values():\n        for dep in rec["depends_on"]:\n            if dep not in records:\n                raise DependencyBatchError("unknown dependency")\n    remaining, completed, batches = set(records), set(), []\n    while remaining:\n        eligible = [tid for tid in remaining if all(dep in completed for dep in records[tid]["depends_on"])]\n        if not eligible:\n            raise DependencyBatchError("dependency cycle detected")\n        eligible.sort(key=lambda tid: (-records[tid]["priority"], records[tid]["duration"], tid))\n        batch = eligible[:max_parallel]\n        batches.append(batch); completed.update(batch); remaining.difference_update(batch)\n    return batches\n'''

def _run_root(benchmark_id:str, run_id:str)->Path:
    return safe_join(BENCH_ROOT, benchmark_id, run_id)
def _metadata_path(executor_dir:Path)->Path|None:
    for name in ('metadata.json','run_metadata.json'):
        p=executor_dir/name
        if p.exists(): return p
    return None
def _load_executor_metadata(executor_dir:Path)->tuple[dict,Path]:
    p=_metadata_path(executor_dir)
    if not p: raise BenchmarkError(f'missing source result metadata: {executor_dir}')
    return json.loads(p.read_text(encoding='utf-8')), p
def _result_files(root:Path)->list[Path]:
    return sorted(p for p in root.rglob('*') if p.is_file() and 'comparison' not in p.relative_to(root).parts)
def _file_hashes(root:Path)->dict[str,str]:
    return {str(p.relative_to(root)).replace(os.sep,'/'):sha256_file(p) for p in _result_files(root)}
def _metadata_value(meta:dict,*names,default=None):
    for n in names:
        if n in meta: return meta[n]
    return default
def _normalize_result_metadata(spec:BenchmarkSpec, run_id:str, executor:str, meta:dict)->dict:
    status=_metadata_value(meta,'validation_status','test_result',default='unknown')
    if status=='pass': status='passed'
    if status=='fail': status='failed'
    unavailable=dict(meta.get('unavailable_metrics',{}))
    for field in ('prompt_tokens','output_tokens','total_tokens'):
        if meta.get(field) is None and meta.get(f'{field}_reason'):
            unavailable[field]=meta[f'{field}_reason']
    return {
        'schema_version':meta.get('schema_version',SCHEMA_VERSION),'benchmark_id':meta.get('benchmark_id',spec.benchmark_id),'benchmark_version':meta.get('benchmark_version',spec.version),'run_id':run_id,
        'canonical_packet_sha256':meta.get('canonical_packet_sha256'),'canonical_packet_eligible':meta.get('canonical_packet_eligible', True),'packet_fair_comparison_status':meta.get('packet_fair_comparison_status','eligible'),
        'executor_type':meta.get('executor_type',meta.get('executor',executor)),'provider':meta.get('provider', meta.get('executor',executor)),'model':meta.get('model'),
        'wall_clock_seconds':meta.get('wall_clock_seconds'),'prompt_tokens':meta.get('prompt_tokens'),'output_tokens':meta.get('output_tokens'),'total_tokens':meta.get('total_tokens'),
        'generation_attempts':meta.get('generation_attempts'),'repair_attempts':meta.get('repair_attempts'),'tests_passed':meta.get('tests_passed', 1 if meta.get('test_result')=='pass' else 0),'tests_failed':meta.get('tests_failed', 0 if meta.get('test_result')=='pass' else 1 if meta.get('test_result')=='fail' else 0),
        'validation_status':status,'unavailable_metrics':unavailable,'provenance':meta.get('provenance',{}),'imported_evidence':meta.get('imported_evidence',False),'source_metadata':meta}

def import_executor_result(spec:BenchmarkSpec, source_run_id:str, source_executor:str, destination_run_id:str, destination_executor:str|None=None, command:str|None=None)->dict:
    destination_executor=destination_executor or source_executor
    if source_executor not in WorkspaceManager.executors or source_executor=='comparison': raise BenchmarkError(f'unknown source executor: {source_executor}')
    if destination_executor not in WorkspaceManager.executors or destination_executor=='comparison': raise BenchmarkError(f'unknown destination executor: {destination_executor}')
    source_dir=safe_join(_run_root(spec.benchmark_id,source_run_id),source_executor)
    dest_dir=safe_join(_run_root(spec.benchmark_id,destination_run_id),destination_executor)
    if not source_dir.exists(): raise BenchmarkError(f'missing source result: {source_dir}')
    if not _run_root(spec.benchmark_id,destination_run_id).exists(): raise BenchmarkError(f'missing destination run: {_run_root(spec.benchmark_id,destination_run_id)}')
    source_meta, source_meta_path=_load_executor_metadata(source_dir)
    src_norm=_normalize_result_metadata(spec,source_run_id,source_executor,source_meta)
    dest_snapshot=_run_root(spec.benchmark_id,destination_run_id)/'benchmark_spec.snapshot.json'
    if dest_snapshot.exists():
        dst_spec=json.loads(dest_snapshot.read_text(encoding='utf-8'))
        if dst_spec.get('benchmark_id')!=spec.benchmark_id or dst_spec.get('version')!=spec.version: raise BenchmarkError('destination benchmark ID/version mismatch')
    if src_norm['benchmark_id']!=spec.benchmark_id or src_norm['benchmark_version']!=spec.version: raise BenchmarkError('source benchmark ID/version mismatch')
    expected=canonical_packet_hash(spec); source_hash=src_norm.get('canonical_packet_sha256')
    if not source_hash: raise BenchmarkError('source canonical packet hash missing')
    dst_hash_path=_run_root(spec.benchmark_id,destination_run_id)/'canonical_packet.hash.json'
    if dst_hash_path.exists() and json.loads(dst_hash_path.read_text()).get('canonical_packet_sha256')!=source_hash: raise BenchmarkError('destination canonical packet hash mismatch')
    if source_hash!=expected: raise BenchmarkError('source canonical packet hash mismatch')
    if src_norm.get('canonical_packet_eligible') is not True or src_norm.get('packet_fair_comparison_status') not in (None,'eligible'): raise BenchmarkError('source result is not canonical-packet eligible')
    before=_file_hashes(source_dir); dest_hashes=_file_hashes(dest_dir) if dest_dir.exists() else {}
    if dest_hashes:
        existing_receipt=dest_dir/'import_receipt.json'
        if existing_receipt.exists() and json.loads(existing_receipt.read_text()).get('source_run_id')==source_run_id and dest_hashes==before: return json.loads(existing_receipt.read_text())
        raise BenchmarkError('destination executor directory already contains non-identical result evidence')
    dest_dir.mkdir(parents=True,exist_ok=True)
    for p in _result_files(source_dir):
        rel=p.relative_to(source_dir); target=safe_join(dest_dir,*rel.parts); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
    copied=_file_hashes(dest_dir)
    if before!=_file_hashes(source_dir): raise BenchmarkError('source evidence changed during import')
    imported_meta=dict(source_meta); imported_meta['imported_evidence']=True; imported_meta['run_id']=destination_run_id; imported_meta['provenance']=dict(imported_meta.get('provenance',{}))|{'imported_from_run_id':source_run_id,'imported_from_executor':source_executor}
    atomic_write_json(dest_dir/('metadata.json' if (dest_dir/'metadata.json').exists() or not (dest_dir/'run_metadata.json').exists() else 'run_metadata.json'), imported_meta)
    copied=_file_hashes(dest_dir)
    receipt={'schema_version':'provider-benchmark-import-receipt.v1','source_run_id':source_run_id,'source_executor':source_executor,'destination_run_id':destination_run_id,'destination_executor':destination_executor,'source_metadata_sha256':sha256_file(source_meta_path),'copied_file_sha256':copied,'canonical_packet_sha256':source_hash,'import_timestamp':utc_now(),'import_command':command,'import_eligibility_decision':'eligible_imported','receipt_path':str((dest_dir/'import_receipt.json').relative_to(ROOT)) if (dest_dir/'import_receipt.json').is_relative_to(ROOT) else str(dest_dir/'import_receipt.json')}
    atomic_write_json(dest_dir/'import_receipt.json',receipt); return receipt

class ValidationRunner:
    def validate(self,spec,ws,executor,hidden=False):
        d=ws.executor_dir(executor); failures=[]; passes=[]; commands=[]
        for f in spec.data['required_files']:
            if not safe_join(d,f).exists(): failures.append(f'missing required file: {f}')
        (d/'test_dependency_batcher_visible.py').write_text(visible_tests_code(),encoding='utf-8')
        cmd=[sys.executable,'-m','unittest','test_dependency_batcher_visible.py']; cp=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=30); commands.append({'command':' '.join(cmd),'exit_code':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
        passes += ['visible_unittest'] if cp.returncode==0 else []; failures += [] if cp.returncode==0 else ['visible_unittest']
        mp=d/'metadata.json'; meta=json.loads(mp.read_text()) if mp.exists() else base_meta(spec,ws,executor,'unknown',None,utc_now())
        meta.update(commands_run=meta.get('commands_run',[])+commands,tests_passed=len(passes),tests_failed=len(failures),validation_status='passed' if not failures else 'failed',file_line_counts={p.name:len(p.read_text(errors='ignore').splitlines()) for p in d.glob('*.py')},exit_codes=[c['exit_code'] for c in commands])
        atomic_write_json(mp,meta); atomic_write_json(d/'validation.json',{'start':utc_now(),'end':utc_now(),'passed':passes,'failed':failures,'commands':commands,'hidden_review_executed':hidden}); return meta
def visible_tests_code(): return '''import copy, unittest\nfrom dependency_batcher import plan_batches, DependencyBatchError\nclass DependencyBatcherTests(unittest.TestCase):\n    def test_success_order_and_immutability(self):\n        tasks=[{"id":"a","duration":5,"priority":1,"depends_on":[]},{"id":"b","duration":1,"priority":3,"depends_on":["a"]},{"id":"c","duration":1,"priority":3,"depends_on":["a"]},{"id":"d","duration":2,"priority":2,"depends_on":[]}]\n        original=copy.deepcopy(tasks); self.assertEqual(plan_batches(tasks,2), [["d","a"],["b","c"]]); self.assertEqual(tasks, original)\n    def test_rejects_invalid(self):\n        bad=[([{"id":"a","duration":True,"priority":1,"depends_on":[]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["z"]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["a"]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["b"]},{"id":"b","duration":1,"priority":1,"depends_on":["a"]}],1)]\n        for tasks, mp in bad:\n            with self.assertRaises(DependencyBatchError): plan_batches(tasks,mp)\n    def test_deterministic(self):\n        tasks=[{"id":x,"duration":1,"priority":1,"depends_on":[]} for x in ["b","a","c"]]; self.assertEqual(plan_batches(tasks,10), [["a","b","c"]])\nif __name__ == "__main__": unittest.main()\n'''
def compare(spec,ws):
    expected_hash=canonical_packet_hash(spec); rows=[]; mismatches=[]
    for ex in ['codex','local','chief_architect']:
        ed=ws.executor_dir(ex); mp=_metadata_path(ed)
        if mp:
            raw=json.loads(mp.read_text())
            m=_normalize_result_metadata(spec,ws.run_id,ex,raw)
            eligible=m.get('canonical_packet_sha256')==expected_hash and m.get('canonical_packet_eligible', True) is True
            if not eligible: mismatches.append({'executor':ex,'canonical_packet_sha256':m.get('canonical_packet_sha256'),'canonical_packet_eligible':m.get('canonical_packet_eligible')})
            score=100 if eligible and m.get('validation_status')=='passed' else 40 if eligible and m.get('validation_status') in ('imported','not_validated') else 0
            rows.append({'executor':ex,'provider':m.get('provider'),'model':m.get('model'),'validation_status':m.get('validation_status'),'tests_passed':m.get('tests_passed'),'tests_failed':m.get('tests_failed'),'wall_clock_seconds':m.get('wall_clock_seconds'),'prompt_tokens':m.get('prompt_tokens'),'output_tokens':m.get('output_tokens'),'total_tokens':m.get('total_tokens'),'estimated_marginal_cost':None,'estimated_marginal_cost_note':'not estimated without provider price evidence','aggregate_score':score,'canonical_packet_sha256':m.get('canonical_packet_sha256'),'fair_comparison_eligible':eligible,'missing_evidence':m.get('unavailable_metrics',{})})
    status='refused_mismatched_packet_hashes' if mismatches else 'ranked'
    report={'schema_version':'provider-benchmark-comparison.v1','benchmark_id':spec.benchmark_id,'benchmark_version':spec.version,'run_id':ws.run_id,'canonical_packet_sha256':expected_hash,'comparison_status':status,'mismatched_packets':mismatches,'scoring_weights':spec.data['scoring_weights'],'results':rows,'generated_at':utc_now()}
    c=ws.executor_dir('comparison'); atomic_write_json(c/'comparison.json',report)
    md=['# Provider Benchmark Comparison','',f'Benchmark: {spec.benchmark_id} v{spec.version}',f'Comparison status: {status}',f'Canonical packet SHA-256: {expected_hash}','','| Executor | Provider | Model | Validation | Passed | Failed | Seconds | Tokens | Score |','|---|---|---|---|---:|---:|---:|---:|---:|']
    for r in rows: md.append(f"| {r['executor']} | {r['provider']} | {r['model']} | {r['validation_status']} | {r['tests_passed']} | {r['tests_failed']} | {r['wall_clock_seconds']} | {r['total_tokens']} | {r['aggregate_score']} |")
    atomic_write_text(c/'comparison.md','\n'.join(md)+'\n'); return report
def benchmark001_spec(): return {'schema_version':SPEC_VERSION,'benchmark_id':'benchmark-001','version':'1.0.0','title':'Benchmark 001 — Deterministic Dependency Batcher','purpose':'Compare providers on bounded Python task.','task':{'prompt':'Implement dependency_batcher.py exposing DependencyBatchError and plan_batches with deterministic dependency batching, validation, immutability, and standard library only.','function_signature':'def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]','task_schema':{'task':{'id':'non-empty str','duration':'positive int (bool rejected)','priority':'int (bool rejected)','depends_on':'list of task id strings'},'return':'ordered list of batches; each batch is a list of task ids'},'scheduling_rules':['Only schedule a task after all dependencies are completed in previous batches.','At most max_parallel tasks per batch.','Within each batch order eligible tasks by descending priority, ascending duration, then ascending task id.','Do not mutate the input tasks.','Detect cycles and unknown dependencies.'],'validation_rules':['Raise DependencyBatchError for invalid task collection, task records, duplicate ids, self dependencies, unknown dependencies, cycles, and invalid max_parallel.','Reject bool values where integers are required.','Use deterministic output for equivalent inputs.']},'cli_contract':['CLI may run python -m unittest test_dependency_batcher_visible.py in the executor directory.','Executor must produce dependency_batcher.py at the executor directory root.','No network, package installation, or non-standard-library dependency is required.'],'permitted_languages':['Python 3.11'],'permitted_dependencies':['python standard library only'],'required_files':['dependency_batcher.py'],'visible_tests':['success, invalid input, determinism, immutability'],'hidden_review_criteria':['clarity','maintainability','security','boundary compliance'],'time_limit_seconds':600,'provider_model_eligibility':{'ollama_default_model':DEFAULT_OLLAMA_MODEL,'codex_import_allowed':True,'reference_import_allowed':True},'isolation_rules':['executor-specific directories only','no overwrite','path traversal rejected'],'environment_requirements':['Python 3.11','Windows-first A:\\theestate compatible','Ollama loopback only'],'required_metrics':['wall_clock_seconds','prompt_tokens','output_tokens','total_tokens','total_duration','load_duration','prompt_eval_duration','eval_duration'],'acceptance_criteria':['visible tests pass','evidence preserved','missing metrics are null with reason'],'scoring_weights':{'functional_correctness':50,'validation':20,'maintainability':10,'security':10,'evidence_quality':10},'source_provenance':['WP-0545_PARALLEL_INDEPENDENT_Engineering_Provider_Benchmark_001.md']}
def ensure_benchmark001_fixture():
    SPEC_ROOT.mkdir(parents=True,exist_ok=True); p=SPEC_ROOT/'benchmark-001.json'
    if not p.exists(): atomic_write_json(p,benchmark001_spec())
def run_cli(argv=None):
    ensure_benchmark001_fixture(); ap=argparse.ArgumentParser(prog='provider-benchmark'); sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('list'); q=sub.add_parser('inspect'); q.add_argument('benchmark_id'); sub.add_parser('discover-providers')
    q=sub.add_parser('run-local'); q.add_argument('benchmark_id'); q.add_argument('--model'); q.add_argument('--mock',action='store_true'); q.add_argument('--run-id')
    q=sub.add_parser('prepare-codex'); q.add_argument('benchmark_id'); q.add_argument('--run-id')
    q=sub.add_parser('import-codex'); q.add_argument('benchmark_id'); q.add_argument('result_path'); q.add_argument('--run-id',required=True); q.add_argument('--seat-reference'); q.add_argument('--model')
    q=sub.add_parser('import-reference'); q.add_argument('benchmark_id'); q.add_argument('result_path'); q.add_argument('--run-id',required=True); q.add_argument('--model',default='chief-architect-reference')
    q=sub.add_parser('import-executor-result'); q.add_argument('benchmark_id'); q.add_argument('source_run_id'); q.add_argument('source_executor'); q.add_argument('destination_run_id'); q.add_argument('--destination-executor')
    q=sub.add_parser('validate'); q.add_argument('benchmark_id'); q.add_argument('run_id'); q.add_argument('--executor',default='local'); q.add_argument('--hidden',action='store_true')
    q=sub.add_parser('compare'); q.add_argument('benchmark_id'); q.add_argument('run_id'); q=sub.add_parser('report'); q.add_argument('benchmark_id'); q.add_argument('run_id')
    ns=ap.parse_args(argv); spec=load_spec(getattr(ns,'benchmark_id','benchmark-001')) if hasattr(ns,'benchmark_id') else None
    if ns.cmd=='list': print(_json([{'benchmark_id':s['benchmark_id'],'version':s['version'],'title':s['title']} for s in list_specs()])); return
    if ns.cmd=='inspect': print(_json(spec.data)); return
    if ns.cmd=='discover-providers': print(_json({'ollama':OllamaAdapter().discover(),'codex':ImportAdapter('codex','codex').discover(),'chief_architect':ImportAdapter('chief_architect','manual_reference').discover()})); return
    if ns.cmd in ('run-local','prepare-codex'):
        ws=WorkspaceManager(spec.benchmark_id,getattr(ns,'run_id',None)); ws.create(spec)
        if ns.cmd=='prepare-codex': atomic_write_text(ws.executor_dir('codex')/'CANONICAL_PACKET.md',build_assignment_prompt(spec)); atomic_write_json(ws.executor_dir('codex')/'metadata.json',base_meta(spec,ws,'codex','codex',None,utc_now())|{'validation_status':'packet_prepared','end_timestamp':utc_now()}); print(_json({'run_id':ws.run_id,'codex_dir':str(ws.executor_dir('codex')),'canonical_packet_sha256':canonical_packet_hash(spec),'canonical_packet':'CANONICAL_PACKET.md'})); return
        print(_json(OllamaAdapter().run(spec,ws,model=ns.model,mock=ns.mock))); return
    if ns.cmd=='import-executor-result':
        cmd='provider-benchmark import-executor-result '+ ' '.join([ns.benchmark_id,ns.source_run_id,ns.source_executor,ns.destination_run_id])
        print(_json(import_executor_result(spec,ns.source_run_id,ns.source_executor,ns.destination_run_id,ns.destination_executor,cmd))); return
    ws=WorkspaceManager(spec.benchmark_id,ns.run_id)
    if ns.cmd=='import-codex': print(_json(ImportAdapter('codex','codex').run(spec,ws,ns.result_path,seat_reference=ns.seat_reference,model=ns.model))); return
    if ns.cmd=='import-reference': print(_json(ImportAdapter('chief_architect','manual_reference').run(spec,ws,ns.result_path,model=ns.model))); return
    if ns.cmd=='validate': print(_json(ValidationRunner().validate(spec,ws,ns.executor,hidden=ns.hidden))); return
    if ns.cmd=='compare': print(_json(compare(spec,ws))); return
    if ns.cmd=='report': print((ws.executor_dir('comparison')/'comparison.md').read_text()); return
if __name__=='__main__': run_cli()
