from .manifest import is_loopback
ALFRED_ALLOWED = {"status", "rediscover", "start", "stop", "load_model"}

def evaluate(operation, service=None, actor="system", approved_by=None, host="127.0.0.1"):
    reasons=[]
    if host not in {"127.0.0.1", "localhost", "::1"}: reasons.append("control_api_must_bind_loopback")
    if service and not is_loopback(service.get("default_endpoint")): reasons.append("cloud_or_non_loopback_endpoint_rejected")
    ops = service.get("operations", {}) if service else {}
    if service and operation not in ops and operation not in {"status","rediscover"}: reasons.append("unknown_or_unmodeled_operation")
    if actor == "alfred" and operation not in ALFRED_ALLOWED: reasons.append("alfred_operation_not_allowed")
    approval = (service or {}).get("approval", {}).get(operation, {})
    if approval.get("required") and approved_by != "steward": reasons.append("steward_approval_required")
    if operation in {"stop", "load_model"} and service and approval.get("required") is not True: reasons.append("explicit_approval_model_required")
    return {"allowed": not reasons, "reasons": reasons, "authority": "steward_approved" if approved_by=="steward" else "unapproved"}
