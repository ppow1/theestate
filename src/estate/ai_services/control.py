from .discovery import load_registry, rediscover, append_audit
from .policy import evaluate
from .execution import record_approval_request, has_approval, validate_model, planned_command_for, execute_plan, load_state, approvals_path, state_path

def _service(service_id, root=None):
    reg=load_registry(root)
    for s in reg.get('services',[]):
        if s.get('service_id')==service_id: return s
    return None

def status(root=None):
    return {'control_plane':'ai-services-v2','registry':load_registry(root),'state':load_state(root),'state_path':'runtime/ai_services/state.json','approval_path':'runtime/ai_services/approvals.json','local_only':True}

def request(operation, service_id, actor='alfred', approved_by=None, root=None, dry_run=True, reason=None, runner=None, health_checker=None, health_timeout_seconds=30, health_interval_seconds=2, **kwargs):
    svc=_service(service_id, root)
    model=kwargs.get('model')
    if not svc:
        pol={'allowed':False,'reasons':['unknown_service'],'authority':'unapproved'}; state='failed'; result='failed'
    else:
        if operation=='load_model':
            ok, why=validate_model(svc, model, root)
            if not ok:
                pol={'allowed':False,'reasons':[why],'authority':'unapproved'}; state='denied'; result='failed'; svc=None
            else:
                pol=evaluate(operation, svc, actor=actor, approved_by=approved_by); state='planned'; result='planned'
        else:
            pol=evaluate(operation, svc, actor=actor, approved_by=approved_by); state='planned'; result='planned'
    plan={'operation':operation,'service_id':service_id,'actor':actor,'policy':pol,'approval_state':state,'result':result,'dry_run':dry_run,'planned_command':None,'command_description':None,'details':kwargs,'process_state_path':'runtime/ai_services/state.json'}
    if svc:
        op=svc.get('operations',{}).get(operation,{})
        plan['planned_command']=planned_command_for(svc, operation, model=model)
        plan['command_description']=op.get('command_template') or op.get('command_type') or op.get('status_check') or op.get('api_template')
    if not pol['allowed']:
        needs_approval = svc and 'steward_approval_required' in pol.get('reasons', [])
        if needs_approval:
            plan['approval_state']='requires_approval'; plan['result']='requires_approval'; plan['approval_request']=record_approval_request(operation, service_id, actor, reason, model, root)
            audit_result='approval_requested'
        else:
            plan['approval_state']='denied'; plan['result']='failed'; audit_result='policy_denied'
        append_audit({'actor':actor,'operation':operation,'service_id':service_id,'requested_model':model,'authority':pol['authority'],'policy_result':'denied','result':audit_result,'details':{'reasons':pol['reasons'],'dry_run':dry_run}}, root)
        return plan
    required=(svc.get('approval',{}).get(operation,{}) or {}).get('required') is True
    if required and not has_approval(operation, service_id, actor, approved_by, model, root):
        plan['approval_state']='requires_approval'; plan['result']='requires_approval'; plan['approval_request']=record_approval_request(operation, service_id, actor, reason, model, root); return plan
    plan['approval_state']='approved' if required else 'planned'
    if dry_run:
        plan['result']='planned'; append_audit({'actor':actor,'operation':operation,'service_id':service_id,'requested_model':model,'authority':pol['authority'],'policy_result':'allowed','result':'planned_dry_run','details':{'dry_run':True}}, root); return plan
    return execute_plan(plan, svc, runner=runner, root=root, health_checker=health_checker, health_timeout_seconds=health_timeout_seconds, health_interval_seconds=health_interval_seconds)
