"""Local Estate discovery and rediscovery engine.

This module scans only configured Estate roots, emits normalized discovery evidence,
and applies projections through existing generated status/index registries. It is
not an institutional source of truth.
"""
from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.ai_services.discovery import rediscover as rediscover_ai_services
from estate.core.estate_knowledge_index import incremental_update as update_knowledge_index
from estate.core.service_status_board import generate_service_status_board
from estate.model_control.discovery import rediscover_models

SCHEMA_VERSION = "estate.discovery.v1"
CONFIG_PATH = Path("config/discovery/approved_roots.json")
STATE_PATH = Path("runtime/discovery/estate_discovery_state.json")
EVIDENCE_PATH = Path("runtime/discovery/estate_discovery_evidence.json")
STATUS_PATH = Path("runtime/discovery/estate_discovery_status.json")
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
PROTECTED_PARTS = {"private", "protected", "secrets", ".ssh", ".gnupg"}
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".py", ".ps1", ".ahk"}


def _root(root=None) -> Path: return Path(root) if root is not None else Path.cwd()
def _now() -> str: return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _rel(path: Path, root: Path) -> str: return str(path.relative_to(root)).replace("\\", "/")
def _read_json(path: Path, default: Any) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except json.JSONDecodeError: return default

def default_config(root=None) -> dict[str, Any]:
    base = _root(root)
    candidates = ["src/estate", "runtime/ai_services/implementations", "runtime/model_control", "docs", "operations", "tools", "collaboration/work_packages", "data/registry", "config"]
    return {"schema_version": SCHEMA_VERSION, "approved_roots": [{"path": p, "category": p.split('/')[0], "owner": "estate"} for p in candidates if (base/p).exists()], "ignored_path_parts": sorted(IGNORED_PARTS), "protected_path_parts": sorted(PROTECTED_PARTS)}

def load_config(root=None) -> dict[str, Any]:
    base = _root(root); cfg = _read_json(base/CONFIG_PATH, None)
    return cfg if cfg else default_config(base)

def _hash_file(path: Path) -> tuple[str, str | None]:
    data = path.read_bytes(); ch = hashlib.sha256(data).hexdigest()
    meta = f"{path.stat().st_size}:{ch}"; return hashlib.sha256(meta.encode()).hexdigest(), ch

def _type(path: Path, rel: str) -> str:
    name = path.name.lower()
    if name == "service.manifest.json": return "ai_service_manifest"
    if rel.startswith("runtime/model_control") or "model" in name: return "model_control_artifact"
    if rel.startswith("data/registry"): return "registry_artifact"
    if rel.startswith("collaboration/work_packages"): return "work_package"
    if path.suffix.lower() in {".py", ".ps1", ".ahk"}: return "tool_or_code"
    if path.suffix.lower() in {".md", ".txt"}: return "document"
    return "artifact"

def _hints(path: Path, text: str) -> list[str]:
    hay = (path.name + " " + text[:2000]).lower(); hints=[]
    for token in ("service", "model", "workflow", "tool", "registry", "health", "validation", "resident"):
        if token in hay: hints.append(token)
    return hints

def _item(path: Path, base: Path, owner: str) -> dict[str, Any] | None:
    rel = _rel(path, base); parts = set(Path(rel).parts)
    if parts & PROTECTED_PARTS: return None
    digest, content_hash = _hash_file(path)
    text = ""
    if path.suffix.lower() in TEXT_SUFFIXES:
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: text = ""
    typ = _type(path, rel)
    return {"schema_version": SCHEMA_VERSION, "discovery_id": "disc_"+hashlib.sha256(f"{rel}:{digest}".encode()).hexdigest()[:24], "canonical_path": rel, "source_path": rel, "type": typ, "owner": owner, "capability_hints": _hints(path, text), "version": None, "health_evidence": {"exists": True, "size_bytes": path.stat().st_size}, "classification": "local_runtime" if rel.startswith("runtime/") else "estate_internal", "last_seen_at": _now(), "content_hash": content_hash, "path_metadata_hash": digest}

def scan(root=None) -> dict[str, Any]:
    base = _root(root); cfg = load_config(base); warnings=[]; items=[]
    for entry in cfg.get("approved_roots", []):
        start = base / entry.get("path", "")
        if not start.exists(): warnings.append({"type":"missing_approved_root","path":entry.get("path")}); continue
        paths = [start] if start.is_file() else sorted(p for p in start.rglob("*") if p.is_file())
        for p in paths:
            relparts=set(p.relative_to(base).parts)
            if relparts & (set(cfg.get("ignored_path_parts", [])) | IGNORED_PARTS): continue
            if relparts & (set(cfg.get("protected_path_parts", [])) | PROTECTED_PARTS): continue
            try:
                rec=_item(p, base, entry.get("owner") or "estate")
                if rec: items.append(rec)
            except (OSError, ValueError) as exc: warnings.append({"type":"malformed_or_unreadable","path":str(p),"message":str(exc)})
    by_hash={}
    for it in items: by_hash.setdefault(it["content_hash"], []).append(it["canonical_path"])
    duplicates=[{"content_hash": h, "paths": ps} for h, ps in by_hash.items() if h and len(ps)>1]
    return {"schema_version": SCHEMA_VERSION, "generated_at": _now(), "approved_roots": cfg.get("approved_roots", []), "item_count": len(items), "items": sorted(items, key=lambda x:x["canonical_path"]), "duplicates": duplicates, "warnings": warnings, "truth_notice": "Discovery evidence is a local projection; apply updates existing registries/status surfaces only."}

def diff(root=None) -> dict[str, Any]:
    base=_root(root); current=scan(base); previous=_read_json(base/STATE_PATH, {"items":[]})
    oldp={i["canonical_path"]:i for i in previous.get("items",[])}; newp={i["canonical_path"]:i for i in current["items"]}
    added=sorted(set(newp)-set(oldp)); missing=sorted(set(oldp)-set(newp)); changed=sorted(p for p in set(newp)&set(oldp) if newp[p].get("content_hash")!=oldp[p].get("content_hash"))
    new_by_hash={}
    for pth in added:
        new_by_hash.setdefault(newp[pth].get("content_hash"), []).append(newp[pth])
    moved=[]
    for pth in missing:
        old=oldp[pth]
        candidates=new_by_hash.get(old.get("content_hash"), [])
        if candidates:
            new=candidates.pop(0)
            moved.append({"from":old["canonical_path"],"to":new["canonical_path"],"content_hash":old.get("content_hash")})
    stale=missing
    return {**current, "diff": {"added": added, "changed": changed, "moved": moved, "missing": missing, "stale": stale, "duplicate_count": len(current["duplicates"])}}

def apply(root=None, dry_run=False) -> dict[str, Any]:
    base=_root(root); result=diff(base)
    if dry_run: return {**result, "applied": False, "apply_actions": []}
    (base/EVIDENCE_PATH).parent.mkdir(parents=True, exist_ok=True); (base/EVIDENCE_PATH).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8"); (base/STATE_PATH).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    actions=[]
    for label, func in (("ai_service_catalog", rediscover_ai_services), ("model_control", rediscover_models), ("knowledge_index", update_knowledge_index), ("office_status", generate_service_status_board)):
        try: func(base); actions.append({"surface":label,"result":"updated"})
        except Exception as exc: actions.append({"surface":label,"result":"warning","message":str(exc)})
    status={"schema_version":SCHEMA_VERSION,"generated_at":_now(),"summary":result["diff"],"evidence_path":str(EVIDENCE_PATH),"state_path":str(STATE_PATH),"apply_actions":actions}
    (base/STATUS_PATH).write_text(json.dumps(status, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return {**result, "applied": True, "apply_actions": actions}

def status(root=None) -> dict[str, Any]:
    base=_root(root); return _read_json(base/STATUS_PATH, {"schema_version":SCHEMA_VERSION,"generated_at":None,"summary":diff(base).get("diff"),"evidence_path":str(EVIDENCE_PATH)})

def inspect(root=None, discovery_id=None, path=None) -> dict[str, Any]:
    data=scan(root)
    matches=[i for i in data["items"] if (discovery_id and i["discovery_id"]==discovery_id) or (path and i["canonical_path"]==path)]
    return {"schema_version":SCHEMA_VERSION,"matches":matches,"match_count":len(matches)}
