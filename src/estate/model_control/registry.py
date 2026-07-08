import json
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path('runtime/model_control/registry.json')
DIAGNOSTICS_PATH = Path('runtime/model_control/diagnostics.json')

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def rootp(root=None): return Path(root) if root is not None else Path.cwd()
def path(root=None): return rootp(root)/REGISTRY_PATH

def empty_registry():
    return {'version':'estate-model-registry-v1','generated_at':now(),'models':[],'source':'ai_services_control_plane'}

def load_registry(root=None):
    p=path(root)
    if not p.exists(): return empty_registry()
    return json.loads(p.read_text(encoding='utf-8'))

def save_registry(registry, root=None):
    p=path(root); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(registry, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    return registry

def write_diagnostics(payload, root=None):
    p=rootp(root)/DIAGNOSTICS_PATH; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    return payload

def find_model(model_id, root=None, registry=None):
    for m in (registry or load_registry(root)).get('models',[]):
        if m.get('model_id')==model_id: return m
    return None
