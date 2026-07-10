import json
from estate.core.validation_reconciliation_runtime import drain

def w(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d))

def test_drain_attempts_bounded_batch_and_continues_after_failure(tmp_path):
    req=tmp_path/'runtime/post_merge_audit/requests'
    for i in range(5): w(req/f'a{i}.json', {'audit_id':f'a{i}','target_id':'estate-main','work_package_id':f'WP-{i}','state':'pending'})
    class Fake:
        def __init__(self, root): self.root=root; self.calls=0
        def list_requests(self):
            return [json.loads(p.read_text()) for p in sorted((self.root/'runtime/post_merge_audit/requests').glob('*.json'))]
        def process_all(self,max_count=10):
            rows=self.list_requests(); out=[]
            for r in rows[:max_count]:
                r['state']='failed' if not out else 'completed'; w(self.root/'runtime/post_merge_audit/requests'/f"{r['audit_id']}.json", r); out.append({'request':r,'processed':True,'error':'x'} if len(out)==0 else {'request':r,'processed':True,'verdict':{'state':'completed'}})
            return {'results':out,'zero_throughput_reason':None}
    import estate.core.validation_reconciliation_runtime as m
    old=m.PostMergeAuditProcessor; m.PostMergeAuditProcessor=Fake
    try: res=drain(tmp_path,max_audit_requests=5)
    finally: m.PostMergeAuditProcessor=old
    assert res['audits_attempted_this_cycle']==5
    assert res['backlog_remaining']==0
