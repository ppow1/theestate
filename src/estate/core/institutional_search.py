"""Local institutional search index for Estate text artifacts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import ESTATE_ROOT

INDEX_PATH = Path("runtime/search/institutional_search_index.json")
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".txt"}

SOURCE_LOCATIONS = [
    "AI_HINTS.md",
    "AI_START_HERE.md",
    "constitution",
    "docs",
    "collaboration/messages",
    "collaboration/work_packages",
    "operations",
    "archive/institutional_memory",
]

RUNTIME_REPORTS = [
    "runtime/validation/*.json",
    "runtime/dependencies/*.json",
    "runtime/alfred/operational_briefing.json",
    "runtime/operations/*.json",
    "runtime/capabilities/*.json",
]

GENERATED_PROJECTION_PREFIXES = (
    "collaboration/status/",
    "operations/updates/check_updates_latest.md",
    "operations/mailboxes/synchronization_duty.md",
    "operations/validation/",
    "operations/capabilities/lifecycle_status.md",
    "operations/dependencies/dependency_graph.md",
    "operations/alfred/operational_briefing.md",
    "operations/board/latest.md",
    "operations/steward/dashboard.md",
    "runtime/validation/",
    "runtime/dependencies/",
    "runtime/alfred/operational_briefing.json",
    "runtime/operations/",
    "runtime/capabilities/",
)

AUTHORITATIVE_PREFIXES = (
    "collaboration/messages/",
    "collaboration/work_packages/pending/",
    "collaboration/work_packages/open/",
    "data/registry/",
    "docs/",
    "operations/boards/",
)

EVIDENCE_PREFIXES = (
    "collaboration/work_packages/completions/",
    "collaboration/work_packages/reviews/",
    "operations/history/",
)


def estate_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def classify_path(rel_path: str) -> dict[str, Any]:
    if rel_path == "runtime/search/institutional_search_index.json":
        return {
            "classification": "generated_search_index",
            "authoritative": False,
            "source_of_truth_rule": "Local search projection generated from indexed source artifacts.",
        }
    if rel_path.startswith(EVIDENCE_PREFIXES):
        return {"classification": "institutional_evidence", "authoritative": False, "source_of_truth_rule": "Evidence of declared work/review; inspect source artifacts for authority."}
    if rel_path.startswith(GENERATED_PROJECTION_PREFIXES):
        return {"classification": "generated_operational_projection", "authoritative": False, "source_of_truth_rule": "Derived view; use to locate source records, not as independent authority."}
    if rel_path.startswith(AUTHORITATIVE_PREFIXES) or rel_path in {"AI_HINTS.md", "AI_START_HERE.md"} or rel_path.startswith("constitution/") or rel_path.startswith("archive/institutional_memory/"):
        return {"classification": "authoritative_source_artifact", "authoritative": True, "source_of_truth_rule": "Authored institutional/source artifact unless the file declares otherwise."}
    if rel_path.startswith("operations/"):
        return {"classification": "operational_artifact", "authoritative": False, "source_of_truth_rule": "Operational artifact; confirm source-of-truth status before authority-sensitive use."}
    if rel_path.startswith("runtime/"):
        return {"classification": "local_only_runtime_artifact", "authoritative": False, "source_of_truth_rule": "Runtime artifact; not authoritative unless explicitly promoted by policy/work package."}
    return {"classification": "unknown", "authoritative": False, "source_of_truth_rule": "Unclassified; treat conservatively."}


def artifact_type(rel_path: str) -> str:
    if rel_path.startswith("collaboration/messages/"):
        return "message"
    if rel_path.startswith("collaboration/work_packages/"):
        return "work_package"
    if rel_path.startswith("docs/"):
        return "document"
    if rel_path.startswith("operations/"):
        return "operation"
    if rel_path.startswith("runtime/"):
        return "runtime_report"
    if rel_path.startswith("archive/institutional_memory/"):
        return "institutional_memory"
    if rel_path.startswith("constitution/"):
        return "constitution"
    return "artifact"


def detect_title(text: str, path: Path) -> str:
    for line in text.splitlines()[:40]:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        if stripped.lower().startswith("title:"):
            return stripped.split(":", 1)[1].strip()
    if path.suffix == ".json":
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                title = payload.get("title") or payload.get("id") or payload.get("message_id")
                if not title and isinstance(payload.get("payload"), dict):
                    title = payload["payload"].get("title")
                if title:
                    return str(title)
        except json.JSONDecodeError:
            pass
    return path.name


def short_excerpt(text: str, query: str | None = None, length: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    if query:
        haystack = compact.lower()
        positions = [haystack.find(term.lower()) for term in query.split() if term]
        positions = [p for p in positions if p >= 0]
        if positions:
            start = max(0, min(positions) - 60)
            return compact[start : start + length]
    return compact[:length]


def _iter_candidate_files(root: Path, warnings: list[str]) -> Iterable[Path]:
    for location in SOURCE_LOCATIONS:
        path = root / location
        if not path.exists():
            warnings.append(f"missing location: {location}")
            continue
        if path.is_file():
            yield path
        else:
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                    yield child
    for pattern in RUNTIME_REPORTS:
        matches = sorted(root.glob(pattern))
        if not matches:
            warnings.append(f"missing runtime report pattern: {pattern}")
        for child in matches:
            if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                yield child


def build_institutional_search_index(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    base = estate_root(root)
    warnings: list[str] = []
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    for path in _iter_candidate_files(base, warnings):
        rel = _rel(path, base)
        if rel in seen:
            continue
        seen.add(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warnings.append(f"unreadable text artifact: {rel}")
            continue
        policy = classify_path(rel)
        records.append({
            "path": rel,
            "title": detect_title(text, path),
            "artifact_type": artifact_type(rel),
            "excerpt": short_excerpt(text),
            "policy_classification": policy["classification"],
            "authoritative": policy["authoritative"],
            "source_of_truth_rule": policy["source_of_truth_rule"],
        })
    payload = {"generated_at": _now(), "index_path": str(INDEX_PATH), "record_count": len(records), "warnings": warnings, "records": records}
    if write:
        out = base / INDEX_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def search_institutional_index(query: str, root: str | Path | None = None, refresh: bool = True) -> dict[str, Any]:
    base = estate_root(root)
    index_file = base / INDEX_PATH
    if refresh or not index_file.exists():
        index = build_institutional_search_index(base, write=True)
    else:
        index = json.loads(index_file.read_text(encoding="utf-8"))
    terms = [term.lower() for term in query.split() if term]
    matches = []
    for record in index.get("records", []):
        haystack = " ".join(str(record.get(k, "")) for k in ("path", "title", "artifact_type", "excerpt", "policy_classification")).lower()
        if all(term in haystack for term in terms) or query.lower() in haystack:
            rec = dict(record)
            source = base / rec["path"]
            if source.exists():
                try:
                    rec["excerpt"] = short_excerpt(source.read_text(encoding="utf-8"), query)
                except UnicodeDecodeError:
                    pass
            matches.append(rec)
    return {"query": query, "index_path": str(INDEX_PATH), "match_count": len(matches), "warnings": index.get("warnings", []), "matches": matches}


def format_search_report(result: dict[str, Any]) -> str:
    lines = ["Estate Institutional Search", f"Query: {result['query']}", f"Matches: {result['match_count']}"]
    for warning in result.get("warnings", []):
        lines.append(f"WARNING: {warning}")
    for match in result.get("matches", []):
        authority = "authoritative" if match.get("authoritative") else match.get("policy_classification")
        lines.extend(["", f"- {match['path']}", f"  title: {match.get('title', '')}", f"  type: {match.get('artifact_type')} | {authority}", f"  excerpt: {match.get('excerpt', '')}"])
    return "\n".join(lines)
