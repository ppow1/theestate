"""Runtime helpers for validation reconciliation queue drain and write-path audit."""
from __future__ import annotations
import json, os, math, subprocess
from pathlib import Path
from typing import Any
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor
from estate.core.merge_discovery_admission import MergeDiscoveryAdmission
from estate.core.validation_reconciliation import ValidationReconciliationService, write, utc_now_iso

INVALID = 'invalid_checkout_write'

def drain(root: Path|None=None, target='estate-main', max_audit_requests=5) -> dict[str,Any]:
    root=Path(root or Path.cwd())
    proc=PostMergeAuditProcessor(root)
    before=proc.list_requests(); active={'pending','claimed','running','running_validation','running_ring2'}; terminal={'completed','blocked','failed','validation_failed','ring2_required','already_audited','no_recipe'}
    pending=sum(1 for r in before if r.get('state')=='pending'); running=sum(1 for r in before if r.get('state') in {'claimed','running','running_validation','running_ring2'}); term=sum(1 for r in before if r.get('state') in terminal)
    available=max(0,max_audit_requests-running)
    result=proc.process_all(max_count=min(max_audit_requests, max(available,pending)))
    after=proc.list_requests(); pending_after=sum(1 for r in after if r.get('state')=='pending'); running_after=sum(1 for r in after if r.get('state') in {'claimed','running','running_validation','running_ring2'}); term_after=sum(1 for r in after if r.get('state') in terminal)
    attempted=len(result.get('results',[])); terminal_this=max(0,term_after-term); oldest=None
    payload={'generated_at':utc_now_iso(),'active_audit_limit':max_audit_requests,'active_request_count':pending_after+running_after,'pending_request_count':pending_after,'running_request_count':running_after,'terminal_request_count':term_after,'available_capacity_before':available,'available_capacity_after':max(0,max_audit_requests-running_after),'audits_attempted_this_cycle':attempted,'audits_terminal_this_cycle':terminal_this,'backlog_remaining':pending_after,'estimated_cycles_remaining':math.ceil(pending_after/max_audit_requests) if max_audit_requests else None,'oldest_pending_age_seconds':oldest,'queue_starvation_detected':bool(pending_after and attempted==0),'zero_throughput_reason':result.get('zero_throughput_reason'),'results':result.get('results',[]),'provider_execution_performed':False,'dispatch_execution_performed':False}
    write(root/'runtime/validation_reconciliation/drain_latest.json',payload); return payload

def admit_eligible(root: Path|None=None,target='estate-main',max_requests=5):
    return MergeDiscoveryAdmission(Path(root or Path.cwd())).auto_admit(target,max_requests=max_requests)

def write_path_audit(root: Path|None=None) -> dict[str,Any]:
    root=Path(root or Path.cwd()).resolve(); paths=[]
    checks=[root/'config/background_operations/extensions.json', root/'runtime', root/'operations/validation/reports']
    for p in checks:
        cls='committed_source' if 'operations/validation/reports' in str(p).replace('\\','/') else ('ignored_local_runtime' if '/runtime' in str(p).replace('\\','/') else INVALID)
        paths.append({'path':str(p),'exists':p.exists(),'classification':cls})
    invalid=[p for p in paths if p['exists'] and p['classification']==INVALID]
    payload={'generated_at':utc_now_iso(),'paths':paths,'invalid_checkout_writes':len(invalid),'valid':not invalid}
    write(root/'runtime/validation_reconciliation/write_path_audit.json',payload); return payload
