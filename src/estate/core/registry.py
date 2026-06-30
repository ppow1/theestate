import json
from pathlib import Path
from estate.core.paths import REGISTRY_DIR, OBJECTS_DIR
from estate.core.time import now

def ensure_dirs():
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    OBJECTS_DIR.mkdir(parents=True, exist_ok=True)

def registry_path(object_type):
    ensure_dirs()
    return REGISTRY_DIR / f"{object_type}.json"

def load_registry(object_type):
    path = registry_path(object_type)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def save_registry(object_type, items):
    path = registry_path(object_type)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")

def add_registry_object(object_type, obj):
    items = load_registry(object_type)
    obj["registered_at"] = obj.get("registered_at") or now()
    items.append(obj)
    save_registry(object_type, items)

def write_object_file(object_id, obj):
    ensure_dirs()
    path = OBJECTS_DIR / f"{object_id}.json"
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return path
