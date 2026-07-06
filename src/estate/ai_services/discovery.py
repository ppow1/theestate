import json
from datetime import datetime, timezone
from pathlib import Path
from .paths import IMPLEMENTATIONS, REGISTRY, STATE, AUDIT
from .manifest import validate_manifest

def now(): return datetime.now(timezone.utc).isoformat()
def rel(p, root):
    try: return str(p.relative_to(root)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')

def manifest_paths(root=None):
    base = (Path(root) / "runtime/ai_services/implementations") if root else IMPLEMENTATIONS
    return sorted(base.glob("*/service.manifest.json"))

def append_audit(record, root=None):
    path = (Path(root)/"runtime/ai_services/audit_log.jsonl") if root else AUDIT
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now(), **record}
    with path.open("a", encoding="utf-8") as f: f.write(json.dumps(payload, sort_keys=True)+"\n")
    return payload

def rediscover(root=None, actor="system"):
    rootp = Path(root) if root else None
    valid=[]; rejected=[]
    for path in manifest_paths(rootp):
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
            check=validate_manifest(data)
        except Exception as e:
            data={}; check={"valid":False,"errors":[{"type":"manifest_parse_error","message":str(e)}]}
        row={"path": rel(path, rootp or path.parents[4]), "service_id": data.get("service_id"), "validation": check}
        if check["valid"]:
            valid.append({**data, "manifest_path": row["path"]})
        else: rejected.append(row)
    registry={"version":"ai-services-registry-v1","generated_at":now(),"source":"manifest_rediscovery","service_count":len(valid),"services":valid,"rejected_manifests":rejected}
    reg = (rootp/"runtime/ai_services/registry.json") if rootp else REGISTRY
    st = (rootp/"runtime/ai_services/state.json") if rootp else STATE
    reg.parent.mkdir(parents=True, exist_ok=True); reg.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    if not st.exists(): st.write_text(json.dumps({"version":"ai-services-state-v1","services":{}}, indent=2, sort_keys=True), encoding="utf-8")
    append_audit({"actor":actor,"operation":"rediscover","service_id":None,"authority":"system","policy_result":"allowed","result":"success","details":{"service_count":len(valid),"rejected_count":len(rejected)}}, rootp)
    return registry

def load_registry(root=None):
    path=(Path(root)/"runtime/ai_services/registry.json") if root else REGISTRY
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else rediscover(root)

def discovery_report(registry):
    lines=["# AI Services Discovery Report", "", f"Generated: {registry.get('generated_at')}", "", "## Services"]
    for s in registry.get("services",[]): lines.append(f"- {s['service_id']} — {s.get('display_name')} ({s.get('default_endpoint')})")
    if registry.get("rejected_manifests"):
        lines += ["", "## Rejected manifests"] + [f"- {r.get('path')}: {r.get('validation')}" for r in registry["rejected_manifests"]]
    return "\n".join(lines)+"\n"
