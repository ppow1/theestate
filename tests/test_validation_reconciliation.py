import json
from pathlib import Path
from estate.core.validation_reconciliation import ValidationReconciliationService

def w(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d))

def test_reconciliation_mixed_rows(tmp_path):
    c=tmp_path/'runtime/merge_discovery/canonical'
    for i in range(50):
        kind='installed'
        receipt=f'collaboration/work_packages/completions/WP-{i:04d}_done.json'
        if i%10==1: receipt='collaboration/work_packages/pending/WP-plan.md'
        w(c/f'{i}.json', {'target_id':'estate-main','work_package_id':f'WP-{i:04d}','source_reference':f'abc{i}','completion_receipt_path':receipt,'state':'discovered','created_at':'2026-07-10T00:00:00Z'})
        if i%10 not in {1,2}: w(tmp_path/receipt, {'ok':True})
    payload=ValidationReconciliationService(tmp_path).rebuild()
    s=payload['summary']
    assert len(payload['rows'])==50
    assert s['work_packages_identified']==50
    assert s['installed_packages']>0 and s['staged_packages']>0 and s['planning_only_packages']>0
    assert s['invariant_holds']
