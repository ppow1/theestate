"""File-backed control surface for operational targets."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT
from estate.core.operational_targets import OperationalTarget, OperationalTargetStatus, default_targets, utc_now_iso, default_validation_root

BASE=Path('runtime/operational_targets'); REGISTRY=BASE/'registry.json'; STATUS=BASE/'status'
def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _write(path:Path,payload:Any): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def _read(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def _rel(p:Path,root:Path):
    try: return str(p.relative_to(root)).replace('\\','/')
    except ValueError: return str(p).replace('\\','/')

class OperationalTargetRuntime:
    def __init__(self,root=None): self.root=_root(root)
    @property
    def registry_path(self): return self.root/REGISTRY
    def ensure_registry(self):
        if not self.registry_path.exists(): self.write_targets(default_targets(str(self.root)))
    def load_targets(self):
        self.ensure_registry(); data=_read(self.registry_path); return [OperationalTarget.from_dict(x) for x in data.get('targets',[])]
    def write_targets(self,targets): _write(self.registry_path,{'targets':[t.to_dict() for t in targets],'updated_at':utc_now_iso()})
    def get(self,target_id):
        for t in self.load_targets():
            if t.target_id==target_id: return t
        raise ValueError(f'unknown target {target_id}')
    def transition(self,target_id,state):
        targets=self.load_targets(); found=None
        for t in targets:
            if t.target_id==target_id:
                t.watch_state=state; t.watch_enabled=(state=='enabled'); found=t
        if not found: raise ValueError(f'unknown target {target_id}')
        self.write_targets(targets); self.write_status(); return found.to_dict()
    def list_payload(self): return {'targets':[t.to_dict() for t in self.load_targets()]}
    def inspect_git_hygiene(self,t:OperationalTarget):
        issues=[]; path=Path(t.local_path or '')
        if 'git' not in t.capabilities or not path.exists(): return {'target_id':t.target_id,'issues':issues,'checked':False}
        def git(*args):
            r=subprocess.run(['git',*args],cwd=path,text=True,capture_output=True,check=False); return r.stdout.strip(), r.returncode
        branch,rc=git('branch','--show-current')
        if rc!=0: issues.append('not_a_git_worktree')
        elif not branch: issues.append('detached_HEAD')
        elif branch!=t.base_branch: issues.append('wrong_branch')
        status,_=git('status','--porcelain')
        if status: issues.append('dirty_validation_workspace' if str(path)!=str(self.root) else 'active_tree_dirty_reported_not_repaired')
        git('fetch','--quiet','origin')
        cnt,_=git('rev-list','--left-right','--count',f'{t.base_branch}...origin/{t.base_branch}')
        if cnt:
            ahead,behind=(cnt.split()+['0','0'])[:2]
            if ahead!='0': issues.append('local_main_ahead_origin_main')
            if behind!='0': issues.append('local_main_behind_origin_main')
        return {'target_id':t.target_id,'issues':issues,'checked':True}
    def status_payload(self):
        targets=self.load_targets(); latest={}
        verdict_dir=self.root/'runtime/post_merge_audit/verdicts'
        if verdict_dir.exists():
            for p in sorted(verdict_dir.glob('*.json')):
                d=_read(p); latest[d.get('target_id','unknown')]=d
        hygiene={t.target_id:self.inspect_git_hygiene(t) for t in targets if 'git' in t.capabilities}
        payload=OperationalTargetStatus(utc_now_iso(), [t.to_dict() for t in targets], [t.target_id for t in targets if t.watch_state=='enabled'], [t.target_id for t in targets if t.watch_state=='paused'], [t.target_id for t in targets if t.watch_state=='blocked'], [t.target_id for t in targets if t.watch_state=='import_candidate'], latest_audit_verdict_by_target=latest, latest_git_hygiene_issue_by_target=hygiene, validation_evidence_root=default_validation_root()).to_dict()
        payload['summary']={'operational_targets_available':len(targets),'watched_targets_count':len(payload['watched_targets']),'paused_targets_count':len(payload['paused_targets']),'blocked_targets_count':len(payload['blocked_targets']),'import_candidates_count':len(payload['import_candidates']),'latest_git_hygiene_issue':next((v for v in hygiene.values() if v.get('issues')),None),'latest_post_merge_audit_verdict':next(reversed(latest.values()),None) if latest else None,'latest_target_requiring_attention':next((k for k,v in hygiene.items() if v.get('issues')),None),'validation_evidence_root':payload['validation_evidence_root'],'warnings':payload['warnings']}
        return payload
    def write_status(self):
        p=self.status_payload(); _write(self.root/STATUS/'latest.json',p); _write(self.root/STATUS/'summary.json',p['summary']); return p
