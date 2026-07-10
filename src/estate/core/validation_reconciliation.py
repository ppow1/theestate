"""Canonical post-merge validation reconciliation ledger."""
from __future__ import annotations

import json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANON = Path('runtime/merge_discovery/canonical')
REQ = Path('runtime/post_merge_audit/requests')
VERD = Path('runtime/post_merge_audit')
OUT = Path('runtime/validation_reconciliation')
TERMINAL = {'completed','blocked','failed','validation_failed','ring2_required','already_audited','no_recipe'}
ACTIVE = {'claimed','running','running_validation','running_ring2'}
PENDING = {'pending','admitted'}


def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def read(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def write(p: Path, d: Any): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, indent=2, sort_keys=True)+'\n', encoding='utf-8')

def rel(p: Path, root: Path) -> str:
    try: return str(p.relative_to(root)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')

def classify_package(c: dict[str,Any], root: Path) -> tuple[str,str]:
    wp = c.get('work_package_id') or ''
    receipt = c.get('completion_receipt_path') or ((c.get('metadata') or {}).get('receipt') or {}).get('path')
    text = ' '.join(str(x).lower() for x in [wp, c.get('source_reference'), receipt, c.get('title'), c.get('summary')])
    if 'planning' in text or '/pending/' in text or 'work_packages/pending' in text: return 'planning_only','not_installed'
    if 'documentation' in text or 'audit' in text and 'wp-' not in wp.lower(): return 'documentation_or_audit','not_installed'
    if receipt and not (root / receipt).exists(): return 'staged_not_installed','staged'
    if wp: return 'installed','installed'
    return 'unknown','unknown'

class ValidationReconciliationService:
    def __init__(self, root: Path|None=None): self.root=Path(root or Path.cwd())
    def _load_jsons(self, d: Path):
        base=self.root/d
        if not base.exists(): return []
        out=[]
        for p in sorted(base.glob('*.json')):
            try: x=read(p); x['_path']=rel(p,self.root); out.append(x)
            except Exception: pass
        return out
    def _verdicts(self):
        out=[]
        for base in [self.root/VERD/'verdicts', self.root/VERD/'evidence']:
            if not base.exists(): continue
            for p in list(base.glob('*.json'))+list(base.glob('*/verdict.json')):
                try: x=read(p); x['_path']=rel(p,self.root); out.append(x)
                except Exception: pass
        return out
    def rebuild(self, target='estate-main', since=None, max_commits=500, admit=False):
        candidates=[c for c in self._load_jsons(CANON) if c.get('target_id',target)==target]
        reqs=self._load_jsons(REQ); verdicts=self._verdicts(); rows=[]; now=utc_now_iso()
        seen=set()
        for c in candidates:
            wp=c.get('work_package_id') or 'unknown'; rev=c.get('source_commit') or c.get('source_reference') or c.get('merge_commit') or 'unknown'; key=(target,wp,rev); seen.add(key)
            matching=[r for r in reqs if r.get('target_id')==target and r.get('work_package_id')==wp and (((r.get('metadata') or {}).get('canonical_discovery_id')==c.get('canonical_discovery_id')) or r.get('source_reference')==rev)]
            req=matching[0] if matching else {}
            vers=[v for v in verdicts if v.get('target_id')==target and v.get('work_package_id')==wp]
            ver=vers[-1] if vers else {}
            pkg, inst = classify_package(c,self.root)
            rs=req.get('state') or req.get('status')
            val=ver.get('validation_status') or req.get('validation_result')
            verdict=ver.get('verdict') or req.get('verdict')
            if not c.get('work_package_id'): state='ambiguous'; reason='ambiguous_or_missing_work_package_id'
            elif verdict in {'no_recipe'} or val=='no_recipe': state='no_recipe'; reason='validation_recipe_missing'
            elif verdict in {'validation_failed'} or val=='failed': state='failed'; reason='validation_failed'
            elif val in {'passed','passed_with_findings'} or verdict in {'accepted','accepted_with_notes'}: state='passed'; reason=None
            elif rs in ACTIVE: state='running'; reason=None
            elif rs in PENDING: state='pending'; reason=None
            elif rs in TERMINAL or verdict: state=verdict or rs; reason=None
            elif pkg in {'staged_not_installed','planning_only','documentation_or_audit'}: state='ineligible'; reason=pkg
            else: state='undiscovered' if not c else 'discovered'; reason='missing_audit_request' if pkg=='installed' else None
            receipt=c.get('completion_receipt_path') or ((c.get('metadata') or {}).get('completion_receipt_path'))
            rows.append({'schema_version':1,'target_id':target,'work_package_id':wp,'merge_commit':rev,'merged_at':c.get('merged_at') or c.get('created_at'), 'source_reference':c.get('source_reference') or rev,'completion_receipt_path':receipt,'completion_receipt_present': bool(receipt and (self.root/receipt).exists()),'package_kind':pkg,'installation_state':inst,'discovery_id':c.get('canonical_discovery_id'),'discovery_state':c.get('state','discovered'),'identity_evidence':{'canonical_path':c.get('_path')},'admission_state':(c.get('admission') or {}).get('classification') or c.get('state'),'admission_reason':reason or ';'.join((c.get('admission') or {}).get('blocking_reasons') or []),'audit_id':req.get('audit_id'),'request_state':rs,'validation_recipe_state':'missing' if state=='no_recipe' else 'unknown','validation_status':val or state,'verdict':verdict or state,'verdict_path':ver.get('_path') or req.get('verdict_path'),'blocking_reason':reason,'retry_eligible': state in {'no_recipe','failed','blocked'},'first_seen_at':c.get('created_at') or now,'last_attempt_at':req.get('claimed_at') or req.get('created_at'),'terminal_at': ver.get('created_at') if state in TERMINAL|{'passed','failed','no_recipe'} else None})
        summary=self.summarize(rows,target)
        payload={'schema_version':1,'target_id':target,'generated_at':now,'rows':rows,'summary':summary,'provider_execution_performed':False,'dispatch_execution_performed':False}
        write(self.root/OUT/'ledger.json',payload); write(self.root/OUT/'summary.json',summary)
        return payload
    def summarize(self, rows, target='estate-main'):
        def n(pred): return sum(1 for r in rows if pred(r))
        terminal_states={'passed','failed','blocked','no_recipe','ring2_required','already_audited','completed','validation_failed'}
        active_states={'pending','running','claimed'}
        s={'target_id':target,'merges_examined':len(rows),'work_packages_identified':len(rows),'installed_packages':n(lambda r:r['package_kind']=='installed'),'staged_packages':n(lambda r:r['package_kind']=='staged_not_installed'),'planning_only_packages':n(lambda r:r['package_kind']=='planning_only'),'unknown_packages':n(lambda r:r['package_kind']=='unknown'),'discovered':n(lambda r:r['discovery_state'] not in {'undiscovered','ambiguous'}),'ambiguous':n(lambda r:r['discovery_state']=='ambiguous' or r['work_package_id']=='unknown'),'held':n(lambda r:r['admission_state'] in {'manual_hold','held'}),'eligible':n(lambda r:r['admission_state']=='eligible'),'pending':n(lambda r:r['request_state']=='pending' or r['verdict']=='pending'),'running':n(lambda r:r['request_state'] in ACTIVE),'terminal':n(lambda r:r['verdict'] in terminal_states),'passed':n(lambda r:r['verdict']=='passed' or r['validation_status'] in {'passed','passed_with_findings'}),'failed':n(lambda r:r['verdict'] in {'failed','validation_failed'} or r['validation_status']=='failed'),'blocked':n(lambda r:r['verdict']=='blocked'),'no_recipe':n(lambda r:r['verdict']=='no_recipe' or r['validation_status']=='no_recipe'),'ring2_required':n(lambda r:r['verdict']=='ring2_required'),'already_audited':n(lambda r:r['verdict']=='already_audited'),'unaccounted':0}
        accounted=n(lambda r: r['verdict'] in terminal_states or r['request_state'] in ACTIVE|PENDING or r['admission_state'] in {'manual_hold','held','ineligible','historical_backfill'} or r['package_kind'] in {'staged_not_installed','planning_only','documentation_or_audit'} or r['work_package_id']=='unknown')
        s['unaccounted']=max(0,len(rows)-accounted); s['invariant_holds']= (len(rows)==accounted+s['unaccounted']); s['unaccounted_rows']=[r for r in rows if r.get('blocking_reason')=='missing_audit_request']
        return s
    def status(self,target='estate-main'):
        p=self.root/OUT/'ledger.json'
        return read(p) if p.exists() else self.rebuild(target)
    def list(self,target='estate-main'): return self.status(target).get('rows',[])
    def inspect(self, wp, target='estate-main'):
        return [r for r in self.list(target) if r.get('work_package_id')==wp]
