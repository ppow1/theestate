from .discovery import load_registry, rediscover, append_audit
from .policy import evaluate

def _service(service_id, root=None):
    reg=load_registry(root)
    for s in reg.get("services",[]):
        if s.get("service_id")==service_id: return s
    return None

def status(root=None):
    return {"control_plane":"ai-services-v1","registry":load_registry(root),"state_path":"runtime/ai_services/state.json","local_only":True}

def request(operation, service_id, actor="alfred", approved_by=None, root=None, **kwargs):
    svc=_service(service_id, root)
    if not svc:
        pol={"allowed":False,"reasons":["unknown_service"],"authority":"unapproved"}; result="failed"
    else:
        pol=evaluate(operation, svc, actor=actor, approved_by=approved_by); result="planned_only" if pol["allowed"] else "failed"
    plan={"operation":operation,"service_id":service_id,"policy":pol,"result":result,"planned_command": None,"details":kwargs}
    if svc and pol["allowed"]:
        op=svc.get("operations",{}).get(operation,{})
        plan["planned_command"] = op.get("command_template") or op.get("status_check") or op.get("api_template")
        if operation=="load_model" and plan["planned_command"] and kwargs.get("model"):
            plan["planned_command"] = plan["planned_command"].replace("{model}", kwargs["model"])
    append_audit({"actor":actor,"operation":operation,"service_id":service_id,"requested_model":kwargs.get("model"),"authority":pol["authority"],"policy_result":"allowed" if pol["allowed"] else "denied","result":result,"details":{"reasons":pol["reasons"]}}, root)
    return plan
