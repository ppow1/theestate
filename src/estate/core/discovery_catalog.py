import json
from datetime import datetime
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

CATALOG_PATH = ESTATE_ROOT / "runtime" / "discovery" / "catalog.json"
LATEST_OBSERVATION_PATH = ESTATE_ROOT / "runtime" / "discovery" / "ai_environment_latest.json"


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def load_discovery_catalog():
    return _load_json(CATALOG_PATH, {
        "version": 1,
        "updated_at": None,
        "entities": [],
    })


def _entity_id(kind, name):
    safe = str(name).strip().lower().replace("\\", "/")
    return f"{kind}:{safe}"


def _add_entity(seen, kind, name, evidence=None):
    if not name:
        return

    entity_id = _entity_id(kind, name)
    seen[entity_id] = {
        "id": entity_id,
        "kind": kind,
        "name": str(name),
        "evidence": evidence or {},
    }


def extract_discovered_entities(observation):
    seen = {}

    for item in observation.get("python_envs", []) or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("path") or item.get("python")
        else:
            name = item
        _add_entity(seen, "python_env", name, item if isinstance(item, dict) else {})

    for item in observation.get("tools", []) or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("path")
        else:
            name = item
        _add_entity(seen, "tool", name, item if isinstance(item, dict) else {})

    for item in observation.get("tts", []) or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("path")
        else:
            name = item
        _add_entity(seen, "tts", name, item if isinstance(item, dict) else {})

    ollama = observation.get("ollama", {}) or {}
    if ollama.get("running") is not None:
        _add_entity(seen, "provider", "ollama", {"running": ollama.get("running")})

    for model in ollama.get("models", []) or []:
        if isinstance(model, dict):
            name = model.get("name") or model.get("model") or model.get("id")
        else:
            name = model
        _add_entity(seen, "model", name, model if isinstance(model, dict) else {})

    return seen


def update_discovery_catalog(observation):
    now = _now()
    catalog = load_discovery_catalog()
    existing = {entity["id"]: entity for entity in catalog.get("entities", []) if isinstance(entity, dict) and entity.get("id")}
    seen = extract_discovered_entities(observation)

    for entity_id, observed in seen.items():
        entity = existing.get(entity_id, {
            "id": entity_id,
            "kind": observed["kind"],
            "name": observed["name"],
            "first_seen": now,
            "last_seen": None,
            "observations": 0,
            "status": "active",
            "evidence": {},
        })

        entity["kind"] = observed["kind"]
        entity["name"] = observed["name"]
        entity["last_seen"] = now
        entity["observations"] = int(entity.get("observations", 0)) + 1
        entity["status"] = "active"
        entity["evidence"] = observed.get("evidence", {})
        existing[entity_id] = entity

    for entity_id, entity in existing.items():
        if entity_id not in seen and entity.get("status") == "active":
            entity["status"] = "inactive"
            entity["last_missing"] = now

    catalog = {
        "version": 1,
        "updated_at": now,
        "entities": sorted(existing.values(), key=lambda item: (item.get("kind", ""), item.get("name", ""))),
    }

    _write_json(CATALOG_PATH, catalog)
    return catalog


def sync_discovery_catalog_from_latest():
    observation = _load_json(LATEST_OBSERVATION_PATH, {})
    return update_discovery_catalog(observation)


def summarize_discovery_catalog(catalog=None):
    catalog = catalog or load_discovery_catalog()
    entities = catalog.get("entities", []) or []

    by_kind = {}
    active = 0
    inactive = 0

    for entity in entities:
        kind = entity.get("kind", "unknown")
        by_kind.setdefault(kind, {"active": 0, "inactive": 0, "total": 0})
        by_kind[kind]["total"] += 1

        if entity.get("status") == "active":
            active += 1
            by_kind[kind]["active"] += 1
        else:
            inactive += 1
            by_kind[kind]["inactive"] += 1

    return {
        "version": catalog.get("version"),
        "updated_at": catalog.get("updated_at"),
        "total": len(entities),
        "active": active,
        "inactive": inactive,
        "by_kind": by_kind,
    }


def format_discovery_catalog_report(catalog=None):
    catalog = catalog or load_discovery_catalog()
    summary = summarize_discovery_catalog(catalog)

    lines = [
        "=========================================",
        "Estate Discovery Catalog",
        "=========================================",
        f"Updated: {summary.get('updated_at')}",
        f"Total entities: {summary.get('total')}",
        f"Active: {summary.get('active')}",
        f"Inactive: {summary.get('inactive')}",
        "",
        "By Kind:",
    ]

    for kind, counts in sorted(summary.get("by_kind", {}).items()):
        lines.append(f"- {kind}: active={counts['active']} inactive={counts['inactive']} total={counts['total']}")

    lines.append("")
    lines.append("Active Entities:")

    for entity in catalog.get("entities", []):
        if entity.get("status") == "active":
            lines.append(f"- {entity.get('kind')} | {entity.get('name')} | observations={entity.get('observations')}")

    return "\n".join(lines)
