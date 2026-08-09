"""Governed local Estate knowledge index and retrieval service.

The index is a local projection over existing Estate artifacts. It is designed to
find and cite source records; it is never a second source of institutional truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.document_registry import load_document_registry
from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate.knowledge_index.v1"
INDEX_PATH = Path("runtime/search/estate_knowledge_index.json")
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".txt"}
PRIVATE_MARKERS = ("/private/", "/protected/", "/secrets/", "private", "protected")

SOURCE_LOCATIONS = [
    "AI_HINTS.md",
    "AI_START_HERE.md",
    "README.md",
    "constitution",
    "orientation",
    "standards",
    "policies",
    "development",
    "docs",
    "Architecture/ADR",
    "collaboration/work_packages",
    "collaboration/messages",
    "operations",
    "validation",
    "archive/institutional_memory",
    "departments",
    "residents",
    "data/registry",
    "data/discovery",
    "schemas",
]

ARTIFACT_RULES = [
    ("constitution/", "constitutional_record"),
    ("Architecture/ADR/", "architectural_decision"),
    ("collaboration/work_packages/", "work_package"),
    ("operations/validation/", "validation_report"),
    ("validation/", "validation_record"),
    ("orientation/", "onboarding_material"),
    ("archive/institutional_memory/", "lesson_learned"),
    ("residents/", "resident_artifact"),
    ("data/registry/", "registry_record"),
    ("standards/", "doctrine"),
    ("policies/", "doctrine"),
    ("development/", "development_record"),
    ("docs/", "document"),
    ("departments/", "office_artifact"),
    ("operations/", "operational_artifact"),
]


def estate_root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_title(text: str, path: Path) -> str:
    for line in text.splitlines()[:50]:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        if stripped.lower().startswith("title:"):
            return stripped.split(":", 1)[1].strip()
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return path.name
        if isinstance(payload, dict):
            for key in ("title", "name", "id", "message_id", "work_package_id"):
                if payload.get(key):
                    return str(payload[key])
    return path.name


def artifact_type(rel_path: str) -> str:
    for prefix, kind in ARTIFACT_RULES:
        if rel_path.startswith(prefix):
            return kind
    if "manual" in rel_path.lower():
        return "manual"
    return "artifact"


def owner_for(rel_path: str, registry_docs: dict[str, dict[str, Any]]) -> str:
    if rel_path in registry_docs:
        return str(registry_docs[rel_path].get("owner") or registry_docs[rel_path].get("category") or "document_registry")
    first = rel_path.split("/", 1)[0]
    return {
        "operations": "operations",
        "collaboration": "collaboration",
        "residents": "resident_office",
        "constitution": "steward",
        "departments": "office",
        "archive": "historian",
        "validation": "validation",
    }.get(first, "estate")


def classification_for(rel_path: str, text: str = "") -> str:
    lowered = f"/{rel_path.lower()}\n{text[:1000].lower()}"
    if any(marker in lowered for marker in PRIVATE_MARKERS):
        return "protected_private"
    if rel_path.startswith("runtime/"):
        return "local_runtime"
    if rel_path.startswith("collaboration/work_packages/completions/") or rel_path.startswith("operations/validation/"):
        return "institutional_evidence"
    if rel_path.startswith("constitution/") or rel_path.startswith("data/registry/"):
        return "constitutional_or_registry_source"
    return "estate_internal"


def provenance_for(rel_path: str, registry_docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    doc = registry_docs.get(rel_path)
    return {
        "source_path": rel_path,
        "registry_id": doc.get("id") if doc else None,
        "registry_source_of_truth": doc.get("source_of_truth") if doc else None,
        "indexed_as_projection": True,
        "truth_notice": "Indexed text is a retrieval projection and is not newly approved institutional truth.",
    }


def _registry_by_path(root: Path) -> dict[str, dict[str, Any]]:
    try:
        registry = load_document_registry(root)
    except (OSError, json.JSONDecodeError):
        return {}
    return {str(doc.get("path")): doc for doc in registry.get("documents", []) if doc.get("path")}


def _iter_candidate_files(root: Path, warnings: list[str]) -> Iterable[Path]:
    for location in SOURCE_LOCATIONS:
        path = root / location
        if not path.exists():
            warnings.append(f"missing location: {location}")
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                yield child


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9_\-]+", value.lower())


def _snippet(text: str, terms: list[str], length: int = 260) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    low = compact.lower()
    positions = [low.find(term) for term in terms if term and low.find(term) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    return compact[start : start + length]


def _record_for(path: Path, root: Path, registry_docs: dict[str, dict[str, Any]], text: str) -> dict[str, Any]:
    rel = _rel(path, root)
    stat = path.stat()
    classification = classification_for(rel, text)
    return {
        "schema_version": SCHEMA_VERSION,
        "path": rel,
        "title": detect_title(text, path),
        "artifact_type": artifact_type(rel),
        "owner": owner_for(rel, registry_docs),
        "classification": classification,
        "modified_time": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
        "size_bytes": stat.st_size,
        "source_hash": source_hash(text),
        "provenance": provenance_for(rel, registry_docs),
        "search_text": text,
    }


def rebuild_index(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    base = estate_root(root)
    warnings: list[str] = []
    registry_docs = _registry_by_path(base)
    records = []
    seen: set[str] = set()
    for path in _iter_candidate_files(base, warnings):
        rel = _rel(path, base)
        if rel in seen or rel == str(INDEX_PATH):
            continue
        seen.add(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warnings.append(f"unreadable text artifact: {rel}")
            continue
        records.append(_record_for(path, base, registry_docs, text))
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": _now(), "index_path": str(INDEX_PATH), "local_only": True, "record_count": len(records), "warnings": warnings, "records": records}
    if write:
        out = base / INDEX_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def load_index(root: str | Path | None = None) -> dict[str, Any]:
    path = estate_root(root) / INDEX_PATH
    if not path.exists():
        return rebuild_index(root, write=True)
    return json.loads(path.read_text(encoding="utf-8"))


def incremental_update(root: str | Path | None = None) -> dict[str, Any]:
    base = estate_root(root)
    existing = load_index(base)
    by_path = {record["path"]: record for record in existing.get("records", [])}
    warnings: list[str] = []
    registry_docs = _registry_by_path(base)
    current_paths: set[str] = set()
    changed: list[str] = []
    added: list[str] = []
    for path in _iter_candidate_files(base, warnings):
        rel = _rel(path, base)
        current_paths.add(rel)
        text = path.read_text(encoding="utf-8")
        digest = source_hash(text)
        if rel not in by_path:
            added.append(rel)
            by_path[rel] = _record_for(path, base, registry_docs, text)
        elif by_path[rel].get("source_hash") != digest:
            changed.append(rel)
            by_path[rel] = _record_for(path, base, registry_docs, text)
    removed = sorted(set(by_path) - current_paths)
    for rel in removed:
        by_path.pop(rel, None)
    records = [by_path[key] for key in sorted(by_path)]
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": _now(), "index_path": str(INDEX_PATH), "local_only": True, "record_count": len(records), "warnings": warnings, "last_incremental": {"added": added, "changed": changed, "removed": removed}, "records": records}
    out = base / INDEX_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def inspect_index(root: str | Path | None = None) -> dict[str, Any]:
    base = estate_root(root)
    index = load_index(base)
    stale, missing = [], []
    for record in index.get("records", []):
        path = base / record["path"]
        if not path.exists():
            missing.append(record["path"])
            continue
        try:
            digest = source_hash(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        if digest != record.get("source_hash"):
            stale.append(record["path"])
    return {"schema_version": SCHEMA_VERSION, "index_path": str(INDEX_PATH), "record_count": index.get("record_count", 0), "stale_entries": stale, "missing_entries": missing, "ok": not stale and not missing, "warnings": index.get("warnings", [])}


def query_index(query: str = "", *, root: str | Path | None = None, artifact_type: str | None = None, owner: str | None = None, classification: str | None = None, include_private: bool = False, limit: int = 20, refresh: bool = False) -> dict[str, Any]:
    base = estate_root(root)
    index = rebuild_index(base, write=True) if refresh else load_index(base)
    terms = _tokenize(query)
    results = []
    for record in index.get("records", []):
        if not include_private and record.get("classification") == "protected_private":
            continue
        if artifact_type and record.get("artifact_type") != artifact_type:
            continue
        if owner and record.get("owner") != owner:
            continue
        if classification and record.get("classification") != classification:
            continue
        haystack = " ".join(str(record.get(k, "")) for k in ("path", "title", "artifact_type", "owner", "classification", "search_text")).lower()
        if terms and not all(term in haystack for term in terms):
            continue
        title_hits = sum(3 for term in terms if term in str(record.get("title", "")).lower())
        path_hits = sum(2 for term in terms if term in record.get("path", "").lower())
        body_hits = sum(haystack.count(term) for term in terms)
        score = title_hits + path_hits + body_hits + (1 if not terms else 0)
        results.append({
            "path": record["path"],
            "title": record.get("title"),
            "artifact_type": record.get("artifact_type"),
            "owner": record.get("owner"),
            "classification": record.get("classification"),
            "modified_time": record.get("modified_time"),
            "source_hash": record.get("source_hash"),
            "provenance": record.get("provenance"),
            "score": score,
            "snippet": _snippet(record.get("search_text", ""), terms),
        })
    results.sort(key=lambda item: (-item["score"], item["path"]))
    return {"query": query, "schema_version": SCHEMA_VERSION, "index_path": str(INDEX_PATH), "match_count": len(results), "results": results[:limit], "warnings": index.get("warnings", []), "truth_notice": "Indexed text is a retrieval projection and is not newly approved institutional truth."}


def status(root: str | Path | None = None) -> dict[str, Any]:
    index = load_index(root)
    inspection = inspect_index(root)
    return {"schema_version": SCHEMA_VERSION, "index_path": str(INDEX_PATH), "record_count": index.get("record_count", 0), "generated_at": index.get("generated_at"), "ok": inspection["ok"], "stale_count": len(inspection["stale_entries"]), "missing_count": len(inspection["missing_entries"]), "warnings": index.get("warnings", [])}


def format_query_report(result: dict[str, Any]) -> str:
    lines = ["Estate Knowledge Index", f"Query: {result.get('query', '')}", f"Matches: {result.get('match_count', 0)}", f"Notice: {result.get('truth_notice')}"]
    for match in result.get("results", []):
        lines.extend(["", f"- {match['path']} (score {match['score']})", f"  title: {match.get('title')}", f"  type: {match.get('artifact_type')} | owner: {match.get('owner')} | classification: {match.get('classification')}", f"  snippet: {match.get('snippet', '')}"])
    return "\n".join(lines)


# The JSON index remains the compatibility/retrieval projection.  These lazy
# adapters let the existing owner expose the relational projection without a
# second registry or a competing CLI owner (the SQLite module imports this
# module's governed source helpers).
def sqlite_init(root=None):
    from estate.core.estate_knowledge_store import init_store
    return init_store(root)


def sqlite_scan(root=None, **kwargs):
    from estate.core.estate_knowledge_store import scan
    return scan(root, **kwargs)


def sqlite_rebuild(root=None, **kwargs):
    from estate.core.estate_knowledge_store import rebuild
    return rebuild(root, **kwargs)


def sqlite_status(root=None):
    from estate.core.estate_knowledge_store import store_status
    return store_status(root)


def sqlite_coverage(root=None):
    from estate.core.estate_knowledge_store import coverage
    return coverage(root)


def sqlite_query(query="", root=None, **kwargs):
    from estate.core.estate_knowledge_store import query_assets
    return query_assets(query, root=root, **kwargs)


def sqlite_unknown(root=None, **kwargs):
    from estate.core.estate_knowledge_store import unknown_assets
    return unknown_assets(root, **kwargs)


def sqlite_stale(root=None):
    from estate.core.estate_knowledge_store import stale_assets
    return stale_assets(root)


def sqlite_graph(root=None, **kwargs):
    from estate.core.estate_knowledge_store import graph
    return graph(root, **kwargs)


def sqlite_progress(root=None):
    from estate.core.estate_knowledge_store import scan_progress
    return scan_progress(root)


def sqlite_packet(root=None, scope=None):
    from estate.core.estate_knowledge_store import build_index_packet
    return build_index_packet(root, scope)


def sqlite_lifecycle(root=None):
    from estate.core.estate_knowledge_store import lifecycle_candidates
    return lifecycle_candidates(root)


def sqlite_knowledge(root=None, **kwargs):
    from estate.core.estate_knowledge_store import query_knowledge
    return query_knowledge(root, **kwargs)
