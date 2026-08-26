"""Deterministic post-merge audit runtime."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT
from estate.core.post_merge_audit import PostMergeAuditRequest, PostMergeAuditVerdict
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.work_package_validation import validate_work_package
from estate.core.production_readiness_validation import validate_receipt, calculate_production_readiness
from estate.core.runtime_recovery import _atomic_write_json
BASE=Path('runtime/post_merge_audit')
def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _write(path:Path,payload:Any): _atomic_write_json(path, payload)
def _rel(p:Path,r:Path):
    try: return str(p.relative_to(r)).replace('\\','/')
    except ValueError: return str(p).replace('\\','/')
def _git(path:Path,*args):
    try: return subprocess.run(['git',*args],cwd=path,text=True,capture_output=True,check=False)
    except OSError: return None
class PostMergeAuditRuntime:
    def __init__(self,root=None): self.root=_root(root); self.targets=OperationalTargetRuntime(self.root)
    def create_request(self,target_id,work_package_id,source_kind='merge',source_reference='HEAD',expected_files=None,metadata=None):
        req=PostMergeAuditRequest.create(target_id,work_package_id,source_kind,source_reference,expected_files,metadata); _write(self.root/BASE/'requests'/f'{req.audit_id}.json',req.to_dict()); return req
    def generate_ring2_prompt(self,req,blocking):
        text=f"# Ring 2 Review Prompt\n\nAudit: {req.audit_id}\nTarget: {req.target_id}\nWork package: {req.work_package_id}\n\nQuestions: Does this preserve Estate authority and avoid provider/dispatch execution?\n\nBlocking reasons: {blocking}\n"
        p=self.root/BASE/'ring2_prompts'/f'{req.audit_id}.md'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8'); return p
    def run_audit(self,req:PostMergeAuditRequest):
        target=self.targets.get(req.target_id); ws=Path(target.workspace_root or target.local_path or self.root)
        if not ws.exists(): ws=Path(target.local_path or self.root)
        blocking=[]; findings=[]
        gr=_git(ws,'status','--porcelain'); clean=bool(gr and gr.returncode==0 and not gr.stdout.strip())
        if not clean: blocking.append('validation_workspace_dirty_or_unavailable')
        br=_git(ws,'branch','--show-current'); on_branch=bool(br and br.stdout.strip()==target.base_branch)
        if not on_branch: blocking.append('validation_workspace_not_on_expected_branch')
        missing=[f for f in req.expected_files if not (ws/f).exists()]
        if missing: blocking.append('expected_files_missing: '+', '.join(missing))
        merge_verified=True
        validation_status='not_run'
        if not blocking:
            try:
                report=validate_work_package(req.work_package_id, root=ws, write=True); validation_status=report.get('validation_status','unknown')
                if validation_status not in {'passed','passed_with_findings'}: blocking.append('deterministic_validation_failed')
            except Exception as e:
                validation_status='failed'; blocking.append(f'deterministic_validation_exception: {e}')
        receipt=validate_receipt(req.work_package_id, root=ws)
        readiness=calculate_production_readiness(validation_status, receipt)
        if not readiness.get('production_ready'): blocking.extend(readiness.get('blocking_reasons') or [])
        findings.extend(readiness.get('non_blocking_findings') or [])
        ring2_status='required' if not blocking else 'not_ready'
        ring2=self.generate_ring2_prompt(req,blocking)
        verdict='needs_repair' if blocking else 'ring2_required'
        if not blocking and req.metadata.get('ring2_complete') and req.metadata.get('steward_acceptance'): verdict='accepted'
        art={'ring2_prompt':_rel(ring2,self.root)}
        v=PostMergeAuditVerdict(req.audit_id,req.target_id,req.work_package_id,req.source_kind,req.source_reference,verdict,merge_verified,clean,on_branch,not missing,validation_status,bool(readiness.get('production_ready')),receipt.get('receipt_status','unknown'),ring2_status,None,False,False,blocking,findings,artifacts=art,metadata={'no_provider_execution':True,'no_dispatch_execution':True})
        _write(self.root/BASE/'verdicts'/f'{req.audit_id}.json',v.to_dict())
        md=self.root/BASE/'verdicts'/f'{req.audit_id}.md'; md.parent.mkdir(parents=True,exist_ok=True); md.write_text(f"# Post-Merge Audit Verdict\n\n- Verdict: {v.verdict}\n- Target: {v.target_id}\n- Work package: {v.work_package_id}\n- Provider execution performed: false\n- Dispatch execution performed: false\n",encoding='utf-8'); return v
