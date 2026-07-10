"""Historian Office runtime for auditable institutional timelines."""
from __future__ import annotations

import hashlib, json, re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.estate_knowledge_index import query_index, rebuild_index, source_hash
from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate.historian.v1"
STORE = Path("runtime/historian")
EVENTS = STORE / "events.json"
TIMELINE = STORE / "timeline.json"
OFFICE = Path("runtime/office/historian_timeline.json")
ALLOWED_SIG = {"low", "normal", "high", "landmark"}


def root_path(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")

def read_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path

def event_id_for(date: str, title: str, sources: list[dict[str, Any]]) -> str:
    seed = json.dumps([date, title, sorted(s.get("path", "") for s in sources)], sort_keys=True)
    return "HE-" + hashlib.sha256(seed.encode()).hexdigest()[:12].upper()

def citation_for(source_path: str, root: Path) -> dict[str, Any]:
    p = root / source_path
    if not p.exists():
        raise ValueError(f"historian source does not exist: {source_path}")
    text = p.read_text(encoding="utf-8")
    return {"schema_version": SCHEMA_VERSION, "path": source_path, "source_hash": source_hash(text), "artifact_type": query_index(source_path, root=root, limit=1).get("results", [{}])[0].get("artifact_type"), "exists": True}

def load_events(root: str | Path | None = None) -> dict[str, Any]:
    base = root_path(root)
    return read_json(base / EVENTS, {"schema_version": SCHEMA_VERSION, "events": [], "corrections": []})

def save_events(data: dict[str, Any], root: str | Path | None = None) -> Path:
    data["schema_version"] = SCHEMA_VERSION
    return write_json(root_path(root) / EVENTS, data)

def validate_event(event: dict[str, Any], root: Path) -> None:
    if event.get("schema_version") != SCHEMA_VERSION: event["schema_version"] = SCHEMA_VERSION
    for field_name in ("date", "title", "claims", "citations"):
        if not event.get(field_name): raise ValueError(f"missing historian event field: {field_name}")
    if event.get("significance", "normal") not in ALLOWED_SIG: raise ValueError("invalid significance")
    for claim in event["claims"]:
        if not claim.get("text") or not claim.get("citation_paths"):
            raise ValueError("every historical claim requires text and citation_paths")
    paths = {c["path"] for c in event["citations"]}
    for claim in event["claims"]:
        missing = set(claim["citation_paths"]) - paths
        if missing: raise ValueError(f"claim cites sources not attached to event: {sorted(missing)}")
    for c in event["citations"]:
        p = root / c["path"]
        if not p.exists(): raise ValueError(f"citation source disappeared: {c['path']}")
        if c.get("source_hash") != source_hash(p.read_text(encoding="utf-8")):
            raise ValueError(f"citation hash mismatch: {c['path']}")

def create_event(*, date: str, title: str, claims: list[dict[str, Any]], source_paths: list[str], office: str = "historian", project: str | None = None, resident: str | None = None, artifact_type: str = "institutional_history", significance: str = "normal", root: str | Path | None = None) -> dict[str, Any]:
    base = root_path(root); rebuild_index(base, write=True)
    citations = [citation_for(p, base) for p in source_paths]
    event = {"schema_version": SCHEMA_VERSION, "event_id": event_id_for(date, title, citations), "date": date, "title": title, "office": office, "project": project, "resident": resident, "artifact_type": artifact_type, "significance": significance, "claims": claims, "citations": citations, "created_at": now(), "superseded_by": None}
    validate_event(event, base)
    data = load_events(base)
    if any(e["event_id"] == event["event_id"] and not e.get("superseded_by") for e in data["events"]):
        raise ValueError(f"duplicate active historian event: {event['event_id']}")
    data["events"].append(event); save_events(data, base); generate_timeline(root=base); return event

def correct_event(event_id: str, replacement: dict[str, Any], reason: str, root: str | Path | None = None) -> dict[str, Any]:
    base = root_path(root); data = load_events(base)
    old = next((e for e in data["events"] if e["event_id"] == event_id and not e.get("superseded_by")), None)
    if not old: raise ValueError(f"active event not found: {event_id}")
    new = dict(old); new.update(replacement); new["event_id"] = event_id_for(new["date"], new["title"], new["citations"]); new["created_at"] = now(); new["corrects"] = event_id
    validate_event(new, base); old["superseded_by"] = new["event_id"]
    data["events"].append(new); data["corrections"].append({"from_event_id": event_id, "to_event_id": new["event_id"], "reason": reason, "corrected_at": now()})
    save_events(data, base); generate_timeline(root=base); return new

def generate_timeline(*, root: str | Path | None = None, **filters: str | None) -> dict[str, Any]:
    base = root_path(root); data = load_events(base); active = [e for e in data["events"] if not e.get("superseded_by")]
    for key, value in filters.items():
        if value: active = [e for e in active if str(e.get(key)) == str(value)]
    active.sort(key=lambda e: (e["date"], e["event_id"]))
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": now(), "source_store": str(EVENTS), "uses_knowledge_index": True, "filters": {k:v for k,v in filters.items() if v}, "events": active}
    write_json(base / TIMELINE, payload); write_json(base / OFFICE, {"schema_version": SCHEMA_VERSION, "read_only": True, "surface": "historian_timeline", "timeline": payload}); return payload

def inspect_source(path: str, root: str | Path | None = None) -> dict[str, Any]:
    base = root_path(root); p = base / path
    return {"path": path, "exists": p.exists(), "source_hash": source_hash(p.read_text(encoding="utf-8")) if p.exists() else None, "knowledge_matches": query_index(path, root=base, limit=5, refresh=False)["results"]}

def historical_query(query: str, root: str | Path | None = None, **filters: str | None) -> dict[str, Any]:
    timeline = generate_timeline(root=root, **filters); terms = [t.lower() for t in re.findall(r"[a-z0-9_\-]+", query)]
    events = [e for e in timeline["events"] if not terms or all(t in json.dumps(e).lower() for t in terms)]
    return {"schema_version": SCHEMA_VERSION, "query": query, "events": events, "knowledge_index": query_index(query, root=root_path(root), limit=10), "summary_policy": "source_fact_interpretation_uncertainty_separated"}

def summarize(events: list[dict[str, Any]]) -> dict[str, Any]:
    facts = [claim["text"] for e in events for claim in e.get("claims", []) if claim.get("claim_type", "source_fact") == "source_fact"]
    interpretations = [claim["text"] for e in events for claim in e.get("claims", []) if claim.get("claim_type") == "interpretation"]
    uncertainty = [claim["text"] for e in events for claim in e.get("claims", []) if claim.get("claim_type") == "uncertainty"]
    return {"source_facts": facts, "interpretations": interpretations, "unresolved_uncertainty": uncertainty}
