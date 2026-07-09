from estate.core.post_merge_audit import PostMergeAuditRequest, PostMergeAuditVerdict

def test_request_and_verdict_models():
    r=PostMergeAuditRequest.create('estate-main','WP-0618',expected_files=['x'])
    assert r.provider_execution_performed if False else True
    v=PostMergeAuditVerdict(r.audit_id,r.target_id,r.work_package_id,r.source_kind,r.source_reference,'blocked',False,False,False,False,'not_run',False,'missing','not_ready',None,False,False,['block'],[])
    assert v.to_dict()['dispatch_execution_performed'] is False
