"""Compatibility layer for Estate institutional search.

The implementation delegates to the governed Estate knowledge index so existing
Office/search surfaces keep working while using one retrieval contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from estate.core.estate_knowledge_index import (
    INDEX_PATH,
    artifact_type,
    classification_for,
    detect_title,
    estate_root,
    format_query_report,
    query_index,
    rebuild_index,
)


def _compat_classification(path: str, classification: str | None) -> str | None:
    if path.startswith("operations/") and ("briefing" in path or "projection" in path or "surface" in path):
        return "generated_operational_projection"
    return classification


def classify_path(path: str, text: str = "") -> dict[str, Any]:
    classification = _compat_classification(path, classification_for(path, text))
    return {"classification": classification, "policy_classification": classification, "authoritative": path.startswith("collaboration/messages/") or path.startswith("data/registry/") or path.startswith("constitution/")}


def build_institutional_search_index(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    payload = rebuild_index(root, write=write)
    if write:
        base = estate_root(root)
        legacy = base / "runtime/search/institutional_search_index.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        import json
        legacy.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    records = []
    for record in payload.get("records", []):
        records.append({
            "path": record.get("path"),
            "title": record.get("title"),
            "artifact_type": record.get("artifact_type"),
            "excerpt": record.get("search_text", "")[:220],
            "policy_classification": _compat_classification(str(record.get("path", "")), record.get("classification")),
            "classification": _compat_classification(str(record.get("path", "")), record.get("classification")),
            "owner": record.get("owner"),
            "provenance": record.get("provenance"),
            "authoritative": False,
            "source_of_truth_rule": "Search result is a local retrieval projection; inspect source and registry provenance for authority.",
        })
    return {**payload, "records": records}


def search_institutional_index(query: str, root: str | Path | None = None, refresh: bool = True, **filters: Any) -> dict[str, Any]:
    result = query_index(query, root=root, refresh=refresh, **filters)
    matches = []
    for item in result.get("results", []):
        matches.append({
            **item,
            "excerpt": item.get("snippet", ""),
            "policy_classification": _compat_classification(str(item.get("path", "")), item.get("classification")),
            "authoritative": False,
            "source_of_truth_rule": "Search result is a local retrieval projection; inspect source and registry provenance for authority.",
        })
    return {"query": query, "index_path": str(INDEX_PATH), "match_count": result.get("match_count", 0), "warnings": result.get("warnings", []), "matches": matches, "truth_notice": result.get("truth_notice")}


def format_search_report(result: dict[str, Any]) -> str:
    converted = {"query": result.get("query", ""), "match_count": result.get("match_count", 0), "results": result.get("matches", []), "truth_notice": result.get("truth_notice")}
    return format_query_report(converted)
