from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

SCHEMA = "estate.office_unified_search.v1"
RESULT_CATEGORIES = {
    "work_package",
    "resident",
    "project",
    "validation",
    "decision",
    "git_evidence",
    "artifact",
    "conversation",
    "command",
}
BLOCKED_COMMAND_SCHEMES = ("shell:", "python:", "url:", "handler:", "http://", "https://", "file:")


@dataclass(frozen=True)
class SearchDocument:
    id: str
    category: str
    title: str
    body: str = ""
    source_path: str | None = None
    destination: str | None = None
    updated_at: str | None = None
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SafeAction:
    id: str
    label: str
    destination: str
    handler: Callable[[Mapping[str, Any] | None], Mapping[str, Any]] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_query_contract(query: str, *, categories: Iterable[str] | None = None, filters: Mapping[str, Any] | None = None, include_stale: bool = True, limit: int = 25) -> dict[str, Any]:
    requested = [category for category in (categories or RESULT_CATEGORIES) if category in RESULT_CATEGORIES]
    return {
        "schema": SCHEMA,
        "staged_not_installed": True,
        "query": query,
        "categories": requested,
        "filters": copy.deepcopy(dict(filters or {})),
        "include_stale": include_stale,
        "limit": max(1, int(limit)),
    }


def _terms(query: str) -> list[str]:
    return [term.casefold() for term in query.split() if term.strip()]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness(source_path: str | None, updated_at: str | None, root: Path, stale_after_days: int) -> dict[str, Any]:
    if source_path:
        candidate = root / source_path
        if not candidate.exists():
            return {"state": "missing", "source_exists": False, "checked_at": utc_now()}
    updated = _parse_dt(updated_at)
    if updated is None:
        return {"state": "unknown", "source_exists": source_path is None or (root / source_path).exists(), "checked_at": utc_now()}
    age_days = (datetime.now(timezone.utc) - updated.astimezone(timezone.utc)).days
    return {"state": "stale" if age_days > stale_after_days else "fresh", "age_days": age_days, "source_exists": source_path is None or (root / source_path).exists(), "checked_at": utc_now()}


def _score(doc: SearchDocument, terms: Sequence[str]) -> float:
    if not terms:
        return 0.1
    title = doc.title.casefold()
    body = doc.body.casefold()
    tags = " ".join(doc.tags).casefold()
    score = 0.0
    for term in terms:
        if term in title:
            score += 5.0
        if term in tags:
            score += 2.0
        if term in body:
            score += 1.0
        if term in doc.id.casefold():
            score += 3.0
    return score


def unified_search(contract: Mapping[str, Any], documents: Iterable[SearchDocument | Mapping[str, Any]], *, root: str | Path = ".", stale_after_days: int = 30) -> dict[str, Any]:
    base = Path(root)
    terms = _terms(str(contract.get("query", "")))
    categories = set(contract.get("categories") or RESULT_CATEGORIES)
    filters = dict(contract.get("filters") or {})
    include_stale = bool(contract.get("include_stale", True))
    results: list[dict[str, Any]] = []
    warnings: list[str] = []
    for raw in documents:
        doc = raw if isinstance(raw, SearchDocument) else SearchDocument(**raw)
        if doc.category not in categories:
            continue
        if filters.get("tag") and filters["tag"] not in doc.tags:
            continue
        relevance = _score(doc, terms)
        if terms and relevance <= 0:
            continue
        freshness = _freshness(doc.source_path, doc.updated_at, base, stale_after_days)
        if freshness["state"] == "missing":
            warnings.append(f"missing source: {doc.id}")
        if freshness["state"] in {"stale", "missing"} and not include_stale:
            continue
        results.append({
            "id": doc.id,
            "category": doc.category,
            "title": doc.title,
            "excerpt": doc.body[:240],
            "relevance": relevance,
            "filters": {"tags": list(doc.tags)},
            "freshness": freshness,
            "source": {"path": doc.source_path, "artifact": doc.source_path},
            "navigation": {"destination": doc.destination or doc.source_path, "available": bool(doc.destination or doc.source_path)},
            "metadata": copy.deepcopy(dict(doc.metadata)),
        })
    results.sort(key=lambda item: (-item["relevance"], item["category"], item["title"]))
    limit = int(contract.get("limit", 25))
    return {"schema": SCHEMA, "staged_not_installed": True, "query": contract.get("query", ""), "count": min(len(results), limit), "results": results[:limit], "warnings": warnings}


def record_recent_search(settings: Mapping[str, Any], query: str, *, allow_recent_searches: bool) -> dict[str, Any]:
    state = copy.deepcopy(dict(settings))
    if not allow_recent_searches:
        state.setdefault("recent_searches", [])
        return state
    recent = [item for item in state.get("recent_searches", []) if item != query]
    state["recent_searches"] = [query] + recent[:9]
    return state


def pin_query(settings: Mapping[str, Any], query: str, *, allow_pinned_queries: bool) -> dict[str, Any]:
    state = copy.deepcopy(dict(settings))
    if not allow_pinned_queries:
        state.setdefault("pinned_queries", [])
        return state
    pinned = list(state.get("pinned_queries", []))
    if query not in pinned:
        pinned.append(query)
    state["pinned_queries"] = pinned
    return state


def invoke_registered_action(action_id: str, registry: Mapping[str, SafeAction | Mapping[str, Any]], payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if action_id.startswith(BLOCKED_COMMAND_SCHEMES) or any(token in action_id for token in (";", "&&", "|", "`")):
        return {"ok": False, "status": "rejected", "reason": "arbitrary command, URL, Python, shell, or handler execution is forbidden"}
    raw = registry.get(action_id)
    if raw is None:
        return {"ok": False, "status": "unregistered", "reason": "only registered safe Office actions may be invoked"}
    action = raw if isinstance(raw, SafeAction) else SafeAction(**raw)
    if action.handler is None:
        return {"ok": True, "status": "ready", "action_id": action.id, "destination": action.destination, "message": "registered safe Office action"}
    result = dict(action.handler(payload or {}))
    result.update({"ok": bool(result.get("ok", True)), "action_id": action.id, "destination": action.destination})
    return result
