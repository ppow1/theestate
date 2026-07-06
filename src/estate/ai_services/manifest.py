from urllib.parse import urlparse
REQUIRED = {"service_id", "display_name", "service_type", "local_only", "host_policy", "default_endpoint", "ports", "paths", "operations", "approval"}
ALLOWED_OPS = {"status", "start", "stop", "load_model", "list_models", "running_models", "inventory_models"}

def is_loopback(url):
    if not url:
        return True
    p = urlparse(url)
    return p.scheme in {"http", "https", ""} and (p.hostname in {None, "127.0.0.1", "localhost", "::1"})

def validate_manifest(data):
    errors = []
    missing = sorted(REQUIRED - set(data))
    if missing: errors.append({"type":"missing_fields","fields":missing})
    sid = data.get("service_id", "")
    if not sid or not sid.replace("_", "").replace("-", "").isalnum(): errors.append({"type":"invalid_service_id","service_id":sid})
    if data.get("local_only") is not True: errors.append({"type":"local_only_required"})
    hp = data.get("host_policy", {})
    if hp.get("allow_public_bind") is True: errors.append({"type":"public_bind_rejected"})
    endpoint = data.get("default_endpoint")
    if endpoint and not is_loopback(endpoint): errors.append({"type":"non_loopback_endpoint_rejected","endpoint":endpoint})
    for op in data.get("operations", {}):
        if op not in ALLOWED_OPS: errors.append({"type":"unknown_operation","operation":op})
    if any(str(v).startswith(("http://", "https://")) and not is_loopback(str(v)) for v in data.get("paths", {}).values()):
        errors.append({"type":"cloud_path_rejected"})
    return {"valid": not errors, "errors": errors}
