"""Unified institutional search contract for Estate Office, CLI, and API callers.

This service reuses the Estate knowledge index.  It intentionally remains a
retrieval projection: results navigate to canonical files/surfaces and never
become a second source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from estate.core.estate_knowledge_index import inspect_index, query_index, status as index_status

SOURCE_TYPE_ALIASES = {
    "doctrine": {"doctrine", "constitutional_record", "architectural_decision"},
    "manual": {"manual", "document", "onboarding_material"},
    "work_package": {"work_package"},
    "validation": {"validation_report", "validation_record"},
    "resident": {"resident_artifact"},
    "mail": {"mail", "message", "office_artifact"},
    "history": {"lesson_learned", "development_record"},
    "research": {"research_record", "external_research"},
    "lesson": {"lesson_learned"},
    "service": {"registry_record", "operational_artifact"},
    "project": {"operational_artifact", "work_package"},
    "operations": {"operational_artifact", "office_artifact"},
}

OFFICE_BY_PATH = {
    "constitution/": "steward",
    "docs/governance/": "governance",
    "collaboration/": "collaboration",
    "operations/validation/": "validation",
    "operations/history/": "historian",
    "operations/services/": "operations",
    "operations/residents/": "resident_office",
    "operations/": "operations",
    "archive/": "historian",
    "residents/": "resident_office",
    "data/registry/": "registry",
    "departments/": "office",
    "docs/": "documentation",
}

SOURCE_TRUTH_BY_PATH = {
    "archive/": "historical_record",
    "examples/research_office/": "external_research",
    "operations/research/": "external_research",
    "collaboration/work_packages/completions/": "accepted_institutional_record",
    "operations/validation/": "operational_evidence",
    "operations/": "operational_record",
    "constitution/": "accepted_institutional_record",
    "data/registry/": "accepted_institutional_record",
}

DETAIL_TABS = [
    ("collaboration/work_packages/", "work-packages"),
    ("collaboration/messages/", "mailboxes"),
    ("collaboration/mailboxes/", "mailboxes"),
    ("residents/", "alfred"),
    ("data/objects/RES-", "alfred"),
    ("operations/validation/", "validation"),
    ("operations/boards/daily_board", "daily-board"),
    ("operations/boards/parking_lot", "parking"),
    ("operations/services/", "ai-services-models"),
    ("docs/", "help"),
]


@dataclass(frozen=True)
class InstitutionalSearchQuery:
    query: str = ""
    source_type: str | None = None
    office: str | None = None
    resident: str | None = None
    project: str | None = None
    classification: str | None = None
    date: str | None = None
    status: str | None = None
    limit: int = 20
    include_private: bool = False
    caller_context: dict[str, Any] = field(default_factory=dict)


def _office_for(path: str, owner: str | None) -> str:
    for prefix, office in OFFICE_BY_PATH.items():
        if path.startswith(prefix):
            return office
    return owner or "estate"


def _truth_kind(path: str) -> str:
    for prefix, kind in SOURCE_TRUTH_BY_PATH.items():
        if path.startswith(prefix):
            return kind
    return "institutional_source_projection"


def _navigation(path: str) -> dict[str, str]:
    tab = "search"
    for prefix, candidate in DETAIL_TABS:
        if path.startswith(prefix):
            tab = candidate
            break
    return {"surface": "office", "tab": tab, "path": path, "href": f"#{tab}:{path}"}


def _allowed_private(query: InstitutionalSearchQuery) -> bool:
    if not query.include_private:
        return False
    ctx = query.caller_context or {}
    return bool(ctx.get("include_private") or ctx.get("role") in {"steward", "privacy_officer"})


def _matches_metadata(result: dict[str, Any], query: InstitutionalSearchQuery) -> bool:
    hay = " ".join(str(result.get(k, "")) for k in ("path", "title", "owner", "classification", "artifact_type")).lower()
    if query.office and query.office.lower() not in {_office_for(result["path"], result.get("owner")).lower(), str(result.get("owner", "")).lower()} and query.office.lower() not in hay:
        return False
    if query.resident and query.resident.lower() not in hay:
        return False
    if query.project and query.project.lower() not in hay:
        return False
    if query.status and query.status.lower() not in hay:
        return False
    if query.date and query.date not in str(result.get("modified_time", "")):
        return False
    return True


def _matches_source_type(result: dict[str, Any], source_type: str | None) -> bool:
    if not source_type:
        return True
    normalized = source_type.lower().replace("-", "_")
    allowed = SOURCE_TYPE_ALIASES.get(normalized, {normalized})
    if result.get("artifact_type") in allowed:
        return True
    path = str(result.get("path", "")).lower()
    return normalized in path


def search_institutional(query: InstitutionalSearchQuery | dict[str, Any] | str, *, root: str | Path | None = None, refresh: bool = False) -> dict[str, Any]:
    contract = query if isinstance(query, InstitutionalSearchQuery) else InstitutionalSearchQuery(query=query) if isinstance(query, str) else InstitutionalSearchQuery(**query)
    private_allowed = _allowed_private(contract)
    raw = query_index(contract.query, root=root, classification=contract.classification, include_private=private_allowed, limit=max(contract.limit * 4, contract.limit), refresh=refresh)
    inspection = inspect_index(root)
    idx_status = index_status(root)
    permission_filtered = 0
    results = []
    unfiltered = query_index(contract.query, root=root, classification=contract.classification, include_private=True, limit=max(contract.limit * 4, contract.limit), refresh=False)
    private_paths = {r["path"] for r in unfiltered.get("results", []) if r.get("classification") == "protected_private"}
    visible_paths = {r["path"] for r in raw.get("results", [])}
    permission_filtered = len(private_paths - visible_paths) if not private_allowed else 0
    for item in raw.get("results", []):
        if not _matches_source_type(item, contract.source_type) or not _matches_metadata(item, contract):
            continue
        path = item["path"]
        results.append({
            "title": item.get("title") or path,
            "path": path,
            "source_type": item.get("artifact_type"),
            "snippet": item.get("snippet", ""),
            "provenance": {**(item.get("provenance") or {}), "truth_kind": _truth_kind(path)},
            "classification": item.get("classification"),
            "freshness": {"modified_time": item.get("modified_time"), "index_stale": path in inspection.get("stale_entries", []), "index_missing": path in inspection.get("missing_entries", [])},
            "owning_office": _office_for(path, item.get("owner")),
            "score": item.get("score", 0),
            "navigation": _navigation(path),
        })
        if len(results) >= contract.limit:
            break
    diagnostics = {
        "stale_index": not inspection.get("ok", True),
        "stale_entries": inspection.get("stale_entries", []),
        "unavailable_sources": [w for w in raw.get("warnings", []) if str(w).startswith("missing location:")],
        "zero_results": not results,
        "permission_filtered_count": permission_filtered,
        "index_generated_at": idx_status.get("generated_at"),
    }
    return {
        "schema_version": "estate.institutional_search.v1",
        "query": contract.__dict__,
        "match_count": len(results),
        "results": results,
        "diagnostics": diagnostics,
        "warnings": raw.get("warnings", []),
        "truth_notice": "Unified institutional search reuses the Estate knowledge index as a local retrieval projection; canonical source files remain authoritative.",
    }


def format_unified_search_report(payload: dict[str, Any]) -> str:
    q = payload.get("query", {})
    lines = ["Unified Institutional Search", f"Query: {q.get('query', '')}", f"Matches: {payload.get('match_count', 0)}", f"Notice: {payload.get('truth_notice')}"]
    d = payload.get("diagnostics", {})
    if d.get("zero_results") or d.get("permission_filtered_count") or d.get("stale_index") or d.get("unavailable_sources"):
        lines.append(f"Diagnostics: zero={d.get('zero_results')} stale={d.get('stale_index')} permission_filtered={d.get('permission_filtered_count')} unavailable={len(d.get('unavailable_sources') or [])}")
    for result in payload.get("results", []):
        lines.extend(["", f"- {result['title']} ({result['score']})", f"  path: {result['path']}", f"  type: {result['source_type']} | office: {result['owning_office']} | classification: {result['classification']}", f"  truth: {(result.get('provenance') or {}).get('truth_kind')}", f"  navigate: {(result.get('navigation') or {}).get('href')}"])
    return "\n".join(lines)
