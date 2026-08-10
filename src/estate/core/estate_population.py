"""Governed, resumable repository population for the Estate knowledge index.

The scope contract is checked before traversal. Providers receive only
deterministically selected work packets and can submit candidate interpretations;
they never receive a raw filesystem authority or canonical mutation capability.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from estate.core.estate_knowledge_store import (
    KnowledgeStoreError, _asset_id, _file_type, _git, _hash,
    _component_for, _index_operational_knowledge, _index_model, _model, _now,
    _registry_by_path, _tags, classification_for, connect, database_path,
    estate_root, init_store, owner_for,
)

SCOPE_PATH = Path("docs/operations/troubleshooting/population-scope.json")
SCOPE_SCHEMA = "estate.population_scope.v1"
PACKET_CONTRACT = "estate.troubleshooting.comprehension.work_packet.v1"
PACKET_VERSION = "estate.troubleshooting.comprehension.work_packet.v2"
PROMPT_CONTRACT_VERSION = "estate.troubleshooting.evidence_enriched_prompt.v2"
RESULT_CONTRACT = "estate.troubleshooting.comprehension.result.v1"
EVIDENCE_FACT_ID_PATTERN = re.compile(r"^fact:[0-9a-f]{64}$")
POLICIES = {"STRUCTURAL_SCAN", "METADATA_ONLY", "NO_CONTENT", "EXCLUDED"}
REPOSITORY_URL = "https://github.com/ppow1/theestate.git"


class PopulationScopeError(KnowledgeStoreError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _relative(value: str | Path) -> str:
    raw = str(value).replace("\\", "/")
    path = PurePosixPath(raw)
    if raw.startswith("/") or ":" in raw.split("/", 1)[0] or ".." in path.parts:
        raise PopulationScopeError(f"unsafe population scope path: {value}")
    return "." if raw in {"", "."} else path.as_posix().strip("/")


def _within_requested(path: str, requested: str | None) -> bool:
    if not requested:
        return True
    prefix = _relative(requested).rstrip("/")
    return path == prefix or path.startswith(prefix + "/")


def load_scope(root: str | Path | None = None) -> dict[str, Any]:
    base = estate_root(root).resolve()
    path = base / SCOPE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PopulationScopeError(f"population scope unavailable: {path}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("repository", {}).get("name") != "theestate":
        raise PopulationScopeError("invalid population scope contract")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise PopulationScopeError("population scope has no entries")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("pattern"), str) or entry.get("policy") not in POLICIES:
            raise PopulationScopeError("invalid population scope entry")
        if entry["pattern"] in seen:
            raise PopulationScopeError(f"duplicate population scope pattern: {entry['pattern']}")
        seen.add(entry["pattern"])
        for required in ("reason", "authority", "introduced_revision"):
            if not entry.get(required):
                raise PopulationScopeError(f"population scope entry missing {required}")
    return payload


def validate_root(root: str | Path | None = None) -> Path:
    base = estate_root(root).resolve()
    if not base.is_dir() or not (base / ".git").exists():
        raise PopulationScopeError("population root must be the governed Git worktree")
    remote = _git(base, "config", "--get", "remote.origin.url").rstrip("/")
    if remote != REPOSITORY_URL:
        raise PopulationScopeError(f"unexpected repository remote: {remote or 'UNKNOWN'}")
    top = _git(base, "rev-parse", "--show-toplevel")
    if top == "UNKNOWN" or Path(top).resolve() != base:
        raise PopulationScopeError("population root is not the Git worktree top-level")
    return base


def _matches(pattern: str, rel: str) -> bool:
    if pattern == "*":
        return "/" not in rel
    if pattern.startswith("*.") or pattern.startswith(".env"):
        return fnmatch.fnmatch(PurePosixPath(rel).name, pattern)
    return rel == pattern or rel.startswith(pattern.rstrip("/") + "/")


def resolve_entry(scope: dict[str, Any], rel: str | Path) -> dict[str, Any] | None:
    normalized = _relative(rel)
    matches = [entry for entry in scope["entries"] if _matches(entry["pattern"], normalized)]
    if not matches:
        return None
    return max(enumerate(matches), key=lambda pair: (len(PurePosixPath(pair[1]["pattern"].replace("*", "x")).parts), pair[1]["policy"] == "EXCLUDED", pair[0]))[1]


def validate_requested_scope(root: str | Path | None, requested: str | None = None) -> dict[str, Any]:
    base = validate_root(root)
    scope = load_scope(base)
    if requested is not None:
        rel = _relative(requested)
        if rel != "." and not (base / rel).exists():
            raise PopulationScopeError(f"requested path does not exist in governed worktree: {requested}")
        entry = resolve_entry(scope, rel)
        if entry is None or entry["policy"] == "EXCLUDED":
            raise PopulationScopeError(f"requested path is outside admitted population scope: {requested}")
    return {"root": str(base), "scope_id": scope["scope_id"], "source_revision": _git(base, "rev-parse", "HEAD"), "scope": scope}


def _safe_candidate(base: Path, candidate: Path) -> Path:
    if candidate.is_symlink():
        resolved = candidate.resolve()
        try:
            resolved.relative_to(base)
        except ValueError as exc:
            raise PopulationScopeError(f"symlink escapes governed root: {candidate}") from exc
        raise PopulationScopeError(f"symlink traversal is not admitted: {candidate}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise PopulationScopeError(f"path escapes governed root: {candidate}") from exc
    return resolved


def _walk(base: Path, start: Path, scope: dict[str, Any], found: list[tuple[Path, dict[str, Any]]], boundaries: list[dict[str, Any]]) -> None:
    start = _safe_candidate(base, start)
    if start.is_file():
        rel = start.relative_to(base).as_posix()
        entry = resolve_entry(scope, rel)
        if entry is None or entry["policy"] == "EXCLUDED":
            boundaries.append({"path": rel, "policy": entry["policy"] if entry else "EXCLUDED", "reason": entry["reason"] if entry else "not admitted"})
        elif entry.get("deterministic_scan", True):
            found.append((start, entry))
        return
    for item in sorted(os.scandir(start), key=lambda x: x.name):
        candidate = Path(item.path)
        rel = candidate.relative_to(base).as_posix()
        entry = resolve_entry(scope, rel)
        if item.is_symlink():
            _safe_candidate(base, candidate)
        if item.is_dir(follow_symlinks=False):
            if entry is None:
                boundaries.append({"path": rel, "policy": "EXCLUDED", "reason": "adjacent boundary is not explicitly admitted; contents not traversed"})
            elif entry["policy"] == "EXCLUDED" or not entry.get("child_traversal", True):
                boundaries.append({"path": rel, "policy": entry["policy"], "reason": entry["reason"]})
            else:
                _walk(base, candidate, scope, found, boundaries)
        elif item.is_file(follow_symlinks=False):
            if entry is None or entry["policy"] == "EXCLUDED":
                boundaries.append({"path": rel, "policy": entry["policy"] if entry else "EXCLUDED", "reason": entry["reason"] if entry else "not admitted"})
            elif entry.get("deterministic_scan", True):
                found.append((candidate, entry))


def _admitted_files(base: Path, scope: dict[str, Any], requested: str | None) -> tuple[list[tuple[Path, dict[str, Any]]], list[dict[str, Any]]]:
    found: list[tuple[Path, dict[str, Any]]] = []
    boundaries: list[dict[str, Any]] = []
    if requested is not None:
        start = base / _relative(requested)
        _walk(base, start, scope, found, boundaries)
    else:
        for entry in scope["entries"]:
            pattern = entry["pattern"]
            if not entry.get("deterministic_scan", True) or "*" in pattern or pattern.startswith("."):
                continue
            candidate = base / pattern
            if candidate.exists():
                _walk(base, candidate, scope, found, boundaries)
        for candidate in sorted(base.iterdir()):
            if candidate.is_dir():
                entry = resolve_entry(scope, candidate.name)
                if entry is None:
                    boundaries.append({"path": candidate.name, "policy": "EXCLUDED", "reason": "adjacent directory is not explicitly admitted; contents not traversed"})
                elif entry["policy"] == "EXCLUDED":
                    boundaries.append({"path": candidate.name, "policy": entry["policy"], "reason": entry["reason"]})
                continue
            if candidate.is_file():
                rel = candidate.name
                entry = resolve_entry(scope, rel)
                if entry and entry.get("deterministic_scan", True) and entry["policy"] != "EXCLUDED":
                    found.append((candidate, entry))
                elif entry is None:
                    boundaries.append({"path": rel, "policy": "EXCLUDED", "reason": "root artifact is not explicitly admitted"})
    unique = {}
    for path, entry in found:
        unique[path.resolve()] = (path.resolve(), entry)
    boundary_map = {(item["path"], item["policy"]): item for item in boundaries}
    return list(unique.values()), list(boundary_map.values())


def _record_scope(connection, scope: dict[str, Any], source_revision: str, boundaries: list[dict[str, Any]], base: Path) -> None:
    now = _now()
    connection.execute("INSERT OR REPLACE INTO population_scopes(scope_id,schema_version,repository,source_path,source_revision,loaded_at,current_state) VALUES(?,?,?,?,?,?,?)", (scope["scope_id"], SCOPE_SCHEMA, scope["repository"]["remote_url"], SCOPE_PATH.as_posix(), source_revision, now, "CURRENT"))
    for entry in scope["entries"]:
        connection.execute("INSERT OR REPLACE INTO scope_entries(scope_id,pattern,policy,reason,authority,introduced_revision,child_traversal,provider_content,deterministic_scan) VALUES(?,?,?,?,?,?,?,?,?)", (scope["scope_id"], entry["pattern"], entry["policy"], entry["reason"], entry["authority"], entry["introduced_revision"], int(entry["child_traversal"]), int(entry["provider_content"]), int(entry["deterministic_scan"])))
    for item in boundaries:
        path = item["path"]
        connection.execute("INSERT OR REPLACE INTO scope_boundaries(boundary_id,scope_id,path,policy,reason,source_revision,observed_at,current_state) VALUES(?,?,?,?,?,?,?,?)", ("boundary:" + _sha_text(scope["scope_id"] + path), scope["scope_id"], path, item["policy"], item["reason"], source_revision, now, "CURRENT"))


def scope_report(root: str | Path | None = None, *, output: str | Path | None = None) -> dict[str, Any]:
    context = validate_requested_scope(root)
    base, scope = Path(context["root"]), context["scope"]
    _, boundaries = _admitted_files(base, scope, None)
    report = {"contract": SCOPE_SCHEMA, "scope_id": scope["scope_id"], "repository": scope["repository"], "admitted_patterns": [x["pattern"] for x in scope["entries"] if x["policy"] != "EXCLUDED"], "future_scope_review": sorted(boundaries, key=lambda x: x["path"]), "traversed_contents": False, "source_revision": context["source_revision"]}
    if output:
        destination = base / _relative(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _upsert_governed_asset(connection, base: Path, path: Path, scan_id: str, revision: str, repository: str, registry: dict[str, dict[str, Any]], model: dict[str, Any] | None, entry: dict[str, Any], git_blob: str | None) -> tuple[bool, bool]:
    rel = path.relative_to(base).as_posix()
    digest = _hash(path)
    asset_id = _asset_id(repository, rel)
    old = connection.execute("SELECT current_content_hash,comprehension_status FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
    unchanged = bool(old and old[0] == digest)
    policy = entry["policy"]
    text = path.read_text(encoding="utf-8", errors="replace") if policy == "STRUCTURAL_SCAN" else ""
    file_type, tag, purpose = _file_type(path, rel)
    component_id, component_owner = _component_for(rel, model)
    owner = component_owner or owner_for(rel, registry)
    owner_known = bool(component_owner or rel.split("/", 1)[0] in {"operations", "collaboration", "constitution", "departments", "validation"})
    unknown_reason = None if owner_known and purpose else "; ".join(x for x, ok in (("ownership unresolved", owner_known), ("purpose unresolved", bool(purpose))) if not ok)
    if policy != "STRUCTURAL_SCAN":
        status, state = "METADATA_ONLY", "CURRENT"
    elif unchanged:
        status, state = (old[1] if old else ("PARTIAL" if purpose else "UNKNOWN")), "CURRENT"
    elif old and old[1] in {"COMPREHENDED", "CANDIDATE_REVIEW"}:
        status, state = "STALE", "REVALIDATION_REQUIRED"
    else:
        status, state = ("COMPREHENDED" if component_id else ("PARTIAL" if purpose else "UNKNOWN")), "CURRENT"
    now = _now()
    blob = git_blob
    classification = classification_for(rel, text) if text else tag
    connection.execute("""INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,source_kind,current_state,scope_policy,provider_content_allowed) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(asset_id) DO UPDATE SET current_path=excluded.current_path,current_source_revision=excluded.current_source_revision,current_git_blob=excluded.current_git_blob,current_content_hash=excluded.current_content_hash,file_type=excluded.file_type,extension=excluded.extension,size_bytes=excluded.size_bytes,classification=excluded.classification,scan_status=excluded.scan_status,comprehension_status=excluded.comprehension_status,purpose_summary=excluded.purpose_summary,owner=excluded.owner,unknown_reason=excluded.unknown_reason,last_seen=excluded.last_seen,last_scanned=excluded.last_scanned,current_state=excluded.current_state,scope_policy=excluded.scope_policy,provider_content_allowed=excluded.provider_content_allowed""", (asset_id, rel, repository, revision, blob if blob != "UNKNOWN" else None, digest, file_type, path.suffix.lower(), path.stat().st_size, classification, "METADATA_ONLY" if policy != "STRUCTURAL_SCAN" else ("SKIPPED_UNCHANGED" if unchanged else "CLASSIFIED"), status, purpose or None, owner, unknown_reason, now, now, now, "DETERMINISTIC", state, policy, int(entry["provider_content"])))
    connection.execute("INSERT OR IGNORE INTO asset_revisions(asset_id,source_revision,git_blob,content_hash,size_bytes,observed_at,scan_id) VALUES(?,?,?,?,?,?,?)", (asset_id, revision, blob if blob != "UNKNOWN" else None, digest, path.stat().st_size, now, scan_id))
    for value in _tags(rel, file_type, tag) | ({"METADATA_ONLY"} if policy != "STRUCTURAL_SCAN" else set()):
        connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, value, "DETERMINISTIC", "HIGH", rel, revision, "CURRENT"))
    if not owner_known:
        connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, "OWNER_UNKNOWN", "DETERMINISTIC", "HIGH", rel, revision, "CURRENT"))
    if not purpose:
        connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, "PURPOSE_UNKNOWN", "DETERMINISTIC", "HIGH", rel, revision, "CURRENT"))
    if component_id:
        connection.execute("INSERT OR REPLACE INTO component_assets(component_id,asset_id,source_ref,certainty,source_revision) VALUES(?,?,?,?,?)", (component_id, asset_id, rel, "DETERMINISTIC", revision))
    return unchanged, not owner_known or not purpose


def _git_blob_map(base: Path) -> tuple[dict[str, str], set[str]]:
    blobs: dict[str, str] = {}
    for line in _git(base, "ls-tree", "-r", "HEAD").splitlines():
        if "\t" not in line:
            continue
        header, rel = line.split("\t", 1)
        parts = header.split()
        if len(parts) >= 3:
            blobs[rel] = parts[2]
    dirty = set()
    for line in _git(base, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if len(line) > 3:
            dirty.add(line[3:].replace("\\", "/").split(" -> ")[-1])
    return blobs, dirty


def governed_scan(root: str | Path | None = None, *, requested: str | None = None, limit: int | None = None) -> dict[str, Any]:
    started_clock = time.perf_counter()
    context = validate_requested_scope(root, requested)
    base, scope, revision = Path(context["root"]), context["scope"], context["source_revision"]
    files, boundaries = _admitted_files(base, scope, requested)
    if limit is not None:
        files = files[:limit]
    repository = _git(base, "config", "--get", "remote.origin.url")
    registry, model = _registry_by_path(base), _model(base)
    blob_map, dirty_paths = _git_blob_map(base)
    scan_id = "scan:" + uuid.uuid4().hex
    with connect(base) as connection:
        _record_scope(connection, scope, revision, boundaries, base)
        connection.execute("UPDATE scan_runs SET status='INTERRUPTED',ended_at=? WHERE status='RUNNING'", (_now(),))
        connection.execute("INSERT INTO scan_runs(scan_id,scope,repository,source_revision,scanner_version,status,phase,started_at,provider) VALUES(?,?,?,?,?,?,?,?,?)", (scan_id, requested or ".", repository, revision, "estate-governed-population/1.0", "RUNNING", "GOVERNED_DETERMINISTIC", _now(), None))
        processed = unchanged = unknown = failed = metadata = 0
        seen_paths = set()
        try:
            for path, entry in files:
                try:
                    rel = path.relative_to(base).as_posix()
                    seen_paths.add(rel)
                    current_blob = _git(base, "hash-object", "--", rel) if rel in dirty_paths or rel not in blob_map else blob_map[rel]
                    same, unclear = _upsert_governed_asset(connection, base, path, scan_id, revision, repository, registry, model, entry, current_blob or None)
                    processed += 1; unchanged += int(same); unknown += int(unclear); metadata += int(entry["policy"] != "STRUCTURAL_SCAN")
                except (OSError, ValueError):
                    failed += 1
            missing = 0
            for row in connection.execute("SELECT asset_id,current_path FROM assets WHERE current_state='CURRENT'").fetchall():
                if not _within_requested(row["current_path"], requested):
                    continue
                if row["current_path"] not in seen_paths:
                    entry = resolve_entry(scope, row["current_path"])
                    if entry and entry["policy"] != "EXCLUDED":
                        connection.execute("UPDATE assets SET current_state='MISSING',scan_status='MISSING' WHERE asset_id=?", (row["asset_id"],))
                        missing += 1
            _index_model(connection, base, revision, model)
            _index_operational_knowledge(connection, base, revision)
            connection.execute("UPDATE scan_runs SET status=?,ended_at=?,files_discovered=?,files_processed=?,files_unchanged=?,files_unknown=?,files_failed=?,resume_cursor=? WHERE scan_id=?", ("COMPLETED" if failed == 0 else "COMPLETED_WITH_FAILURES", _now(), len(files), processed, unchanged, unknown, failed, None, scan_id))
        except Exception as exc:
            connection.execute("UPDATE scan_runs SET status=?,ended_at=?,error=? WHERE scan_id=?", ("FAILED", _now(), str(exc), scan_id)); raise
    return {"status": "COMPLETED" if failed == 0 else "COMPLETED_WITH_FAILURES", "scope_id": scope["scope_id"], "scan_id": scan_id, "source_revision": revision, "files_admitted": len(files), "files_processed": processed, "files_unchanged": unchanged, "files_unknown": unknown, "files_failed": failed, "files_missing": missing, "metadata_only": metadata, "excluded_boundaries": len(boundaries), "elapsed_ms": round((time.perf_counter() - started_clock) * 1000, 2), "database": str(database_path(base))}


def governed_rebuild(root: str | Path | None = None) -> dict[str, Any]:
    base = validate_root(root)
    path = database_path(base)
    for target in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if target.exists():
            target.unlink()
    init_store(base)
    return governed_scan(base)


def population_coverage(root: str | Path | None = None) -> dict[str, Any]:
    context = validate_requested_scope(root)
    with connect(context["root"], create=False) as connection:
        row = connection.execute("SELECT COUNT(*),SUM(scope_policy='METADATA_ONLY'),SUM(scope_policy='NO_CONTENT'),SUM(scope_policy='STRUCTURAL_SCAN'),SUM(comprehension_status='COMPREHENDED'),SUM(comprehension_status='PARTIAL'),SUM(comprehension_status='UNKNOWN'),SUM(comprehension_status='STALE'),SUM(unknown_reason LIKE '%ownership unresolved%'),SUM(unknown_reason LIKE '%purpose unresolved%') FROM assets").fetchone()
        pending = connection.execute("SELECT COUNT(*) FROM assets a WHERE a.scope_policy='STRUCTURAL_SCAN' AND (a.comprehension_status IN ('PARTIAL','UNKNOWN','STALE') OR a.current_state='REVALIDATION_REQUIRED') AND NOT EXISTS (SELECT 1 FROM comprehension_batch_assets ba JOIN comprehension_batches b ON b.batch_id=ba.batch_id WHERE ba.asset_id=a.asset_id AND b.state IN ('OPEN','ASSIGNED','PROCESSING'))").fetchone()[0]
        return {"scope_id": context["scope_id"], "source_revision": context["source_revision"], "assets_total": row[0] or 0, "metadata_only": row[1] or 0, "no_content": row[2] or 0, "structural": row[3] or 0, "comprehended": row[4] or 0, "partial": row[5] or 0, "unknown": row[6] or 0, "stale": row[7] or 0, "unknown_owner": row[8] or 0, "unknown_purpose": row[9] or 0, "missing": connection.execute("SELECT COUNT(*) FROM assets WHERE scan_status='MISSING'").fetchone()[0], "pending_work": pending, "future_scope_boundaries": connection.execute("SELECT COUNT(*) FROM scope_boundaries").fetchone()[0], "failed_batches": connection.execute("SELECT COUNT(*) FROM comprehension_batches WHERE state='FAILED'").fetchone()[0], "database": str(database_path(context["root"]))}


def next_batch(root: str | Path | None = None, *, limit: int = 10, provider_type: str | None = None, provider_model: str | None = None, worker_identity: str | None = None, asset_prefix: str | None = None, allow_reprocess: bool = False, exclude_asset_ids: Iterable[str] = ()) -> dict[str, Any]:
    context = validate_requested_scope(root)
    with connect(context["root"], create=False) as connection:
        query = "SELECT a.* FROM assets a WHERE a.scope_policy='STRUCTURAL_SCAN' AND (a.comprehension_status IN ('PARTIAL','UNKNOWN','STALE') OR a.current_state='REVALIDATION_REQUIRED')"
        if allow_reprocess:
            query += " AND NOT EXISTS (SELECT 1 FROM comprehension_batch_assets ba JOIN comprehension_batches b ON b.batch_id=ba.batch_id WHERE ba.asset_id=a.asset_id AND b.state IN ('OPEN','ASSIGNED','PROCESSING'))"
        else:
            query += " AND NOT EXISTS (SELECT 1 FROM comprehension_batch_assets ba JOIN comprehension_batches b ON b.batch_id=ba.batch_id WHERE ba.asset_id=a.asset_id AND (b.state IN ('OPEN','ASSIGNED','PROCESSING') OR (b.state='COMPLETED' AND a.current_state!='REVALIDATION_REQUIRED')))"
        params: list[Any] = []
        excluded = list(exclude_asset_ids)
        if excluded:
            query += " AND a.asset_id NOT IN (" + ",".join("?" for _ in excluded) + ")"
            params.extend(excluded)
        if asset_prefix:
            prefix = _relative(asset_prefix)
            query += " AND (a.current_path = ? OR a.current_path LIKE ?)"
            params.extend([prefix, prefix.rstrip("/") + "/%"])
        query += " ORDER BY CASE WHEN a.current_state='REVALIDATION_REQUIRED' THEN 0 ELSE 1 END,a.current_path LIMIT ?"
        params.append(max(1, min(limit, 100)))
        rows = connection.execute(query, tuple(params)).fetchall()
        if not rows:
            return {"status": "NO_WORK", "scope_id": context["scope_id"], "source_revision": context["source_revision"], "asset_ids": [], "asset_count": 0}
        batch_id = "batch:" + uuid.uuid4().hex
        now = _now()
        selection_reason = "explicit bounded reprocessing for evidence-enriched model comparison" if allow_reprocess else "next structural assets requiring comprehension or revalidation"
        connection.execute("INSERT INTO comprehension_batches(batch_id,scope_id,source_revision,selection_reason,created_at,updated_at,provider_type,provider_model,worker_identity,state,attempt_count) VALUES(?,?,?,?,?,?,?,?,?,?,0)", (batch_id, context["scope_id"], context["source_revision"], selection_reason, now, now, provider_type, provider_model, worker_identity, "ASSIGNED" if provider_type or worker_identity else "OPEN"))
        for position, row in enumerate(rows):
            connection.execute("INSERT INTO comprehension_batch_assets(batch_id,asset_id,position) VALUES(?,?,?)", (batch_id, row["asset_id"], position))
        return {"batch_id": batch_id, "scope_id": context["scope_id"], "source_revision": context["source_revision"], "state": "ASSIGNED" if provider_type or worker_identity else "OPEN", "asset_ids": [row["asset_id"] for row in rows], "asset_count": len(rows), "selection_reason": selection_reason}


def _batch_rows(connection, batch_id: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute("SELECT a.* FROM assets a JOIN comprehension_batch_assets ba ON ba.asset_id=a.asset_id WHERE ba.batch_id=? ORDER BY ba.position", (batch_id,)).fetchall()]


def _packet_evidence(connection, asset_ids: list[str], *, limit: int = 24, max_bytes: int = 16384) -> tuple[dict[str, list[dict[str, Any]]], list[str], dict[str, int]]:
    """Select current, revision-grounded facts for a bounded provider packet."""
    if not asset_ids:
        return {}, [], {}
    marks = ",".join("?" for _ in asset_ids)
    rows = connection.execute(
        """SELECT ef.*, source.current_path AS source_path, target.current_path AS target_path
           FROM evidence_facts ef
           LEFT JOIN assets source ON source.asset_id=ef.source_asset_id
           LEFT JOIN assets target ON target.asset_id=ef.target_asset_id
           WHERE ef.target_asset_id IN (""" + marks + """) AND ef.current_state='CURRENT'
           ORDER BY CASE ef.certainty
             WHEN 'AUTHORITATIVE_GOVERNANCE' THEN 0
             WHEN 'AUTHORITATIVE_REGISTRY' THEN 1
             WHEN 'DETERMINISTIC_SOURCE_RELATIONSHIP' THEN 2
             WHEN 'EXECUTABLE_TEST' THEN 3
             WHEN 'CURRENT_DOCUMENTATION' THEN 4
             WHEN 'DERIVED_STATIC_ANALYSIS' THEN 5 ELSE 6 END,
             ef.fact_kind,ef.evidence_path,ef.fact_id""",
        tuple(asset_ids),
    ).fetchall()
    selected: dict[str, list[dict[str, Any]]] = {asset_id: [] for asset_id in asset_ids}
    omitted: dict[str, int] = {asset_id: 0 for asset_id in asset_ids}
    ids: list[str] = []
    used = 0
    for row in rows:
        target = row["target_asset_id"]
        if len(selected.get(target, [])) >= max(1, limit):
            omitted[target] += 1
            continue
        fact = {
            "evidence_fact_id": row["fact_id"],
            "fact_kind": row["fact_kind"],
            "source_asset_id": row["source_asset_id"],
            "source_path": row["source_path"],
            "target_asset_id": row["target_asset_id"],
            "target_path": row["target_path"],
            "value": json.loads(row["value_json"]),
            "evidence_strength": row["certainty"],
            "source_revision": row["source_revision"],
            "source_hash": row["source_hash"],
            "location": row["evidence_location"],
            "evidence_path": row["evidence_path"],
            "current_state": row["current_state"],
        }
        encoded = len(_canonical(fact).encode("utf-8"))
        if used + encoded > max_bytes and ids:
            omitted[target] += 1
            continue
        used += encoded
        selected[target].append(fact)
        ids.append(row["fact_id"])
    return selected, ids, omitted


def batch_packet(root: str | Path | None, batch_id: str, *, max_bytes: int = 262144, evidence_limit: int = 24, evidence_bytes: int = 16384) -> dict[str, Any]:
    context = validate_requested_scope(root)
    with connect(context["root"], create=False) as connection:
        batch = connection.execute("SELECT * FROM comprehension_batches WHERE batch_id=?", (batch_id,)).fetchone()
        if not batch:
            raise PopulationScopeError(f"unknown comprehension batch: {batch_id}")
        assets = []
        batch_rows = _batch_rows(connection, batch_id)
        asset_ids = [row["asset_id"] for row in batch_rows]
        evidence_by_asset, evidence_ids, omitted_by_asset = _packet_evidence(connection, asset_ids, limit=evidence_limit, max_bytes=evidence_bytes)
        remaining = max(1, max_bytes)
        for row in batch_rows:
            if row["scope_policy"] != "STRUCTURAL_SCAN" or not row["provider_content_allowed"]:
                raise PopulationScopeError(f"batch contains non-provider asset: {row['current_path']}")
            path = Path(context["root"]) / row["current_path"]
            if not path.is_file() or _hash(path) != row["current_content_hash"]:
                raise PopulationScopeError(f"asset changed or disappeared before packet creation: {row['current_path']}")
            content = path.read_text(encoding="utf-8", errors="replace")
            encoded = content.encode("utf-8")[:remaining]
            content = encoded.decode("utf-8", errors="ignore")
            remaining -= len(content.encode("utf-8"))
            asset = {"asset_id": row["asset_id"], "path": row["current_path"], "source_revision": row["current_source_revision"], "content_hash": row["current_content_hash"], "scope_policy": row["scope_policy"], "content": content, "deterministic_evidence": evidence_by_asset.get(row["asset_id"], [])}
            asset["evidence_omitted"] = omitted_by_asset.get(row["asset_id"], 0)
            assets.append(asset)
        packet = {"contract": PACKET_CONTRACT, "packet_version": PACKET_VERSION, "prompt_contract_version": PROMPT_CONTRACT_VERSION, "provider_neutral": True, "batch_id": batch_id, "scope_id": batch["scope_id"], "source_revision": batch["source_revision"], "selection_reason": batch["selection_reason"], "evidence_selection_policy": {"max_facts_per_asset": evidence_limit, "max_evidence_bytes": evidence_bytes, "relationship_depth": 1, "omitted_context": any(omitted_by_asset.values())}, "evidence_fact_ids": evidence_ids, "assets": assets, "component_context": [], "workflow_context": [], "known_knowledge": [], "allowed_outputs": ["PURPOSE", "SCHEMA_CLASSIFICATION", "DETERMINISTIC_TAG", "COMPONENT_LINKAGE", "OWNER", "UNRESOLVED_QUESTION", "NEEDS_MORE_CONTEXT", "NO_ASSERTABLE_CLAIM"], "forbidden_actions": ["add filesystem paths", "read outside packet", "mutate canonical files", "promote truth", "advance accepted baseline", "authorize remediation"]}
        return packet


def validate_result(root: str | Path | None, payload: dict[str, Any], *, packet: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("contract") != RESULT_CONTRACT:
        raise PopulationScopeError("invalid comprehension result contract")
    for key in ("result_id", "batch_id", "source_revision", "provider", "items"):
        if key not in payload:
            raise PopulationScopeError(f"comprehension result missing {key}")
    allowed_top = {"contract", "packet_version", "prompt_contract_version", "result_id", "batch_id", "source_revision", "provider", "items", "quality", "telemetry", "context_requests", "unsupported_assertions"}
    if set(payload) - allowed_top:
        raise PopulationScopeError("unknown comprehension result fields")
    if "quality" in payload and payload["quality"] not in {"ACCEPTED_CANDIDATE", "PARTIAL_CANDIDATE", "NEEDS_MORE_CONTEXT", "RETRYABLE_PROVIDER_FAILURE", "INVALID_RESULT", "CONFLICT_REVIEW_REQUIRED", "HIGHER_REASONING_REQUIRED", "HUMAN_REVIEW_REQUIRED"}:
        raise PopulationScopeError("unknown comprehension quality outcome")
    for key in ("context_requests", "unsupported_assertions"):
        if key in payload and (not isinstance(payload[key], list) or not all(isinstance(value, str) for value in payload[key])):
            raise PopulationScopeError(f"{key} must be a list of strings")
    provider = payload["provider"]
    if not isinstance(provider, dict) or not provider.get("type") or not provider.get("worker_identity"):
        raise PopulationScopeError("provider type and worker_identity are required")
    if set(provider) - {"type", "model", "worker_identity"}:
        raise PopulationScopeError("unknown provider provenance fields")
    if payload.get("lifecycle") in {"VERIFIED", "CANONICAL"} or payload.get("canonical_promotion"):
        raise PopulationScopeError("provider result cannot self-promote")
    context = validate_requested_scope(root)
    with connect(context["root"], create=False) as connection:
        batch = connection.execute("SELECT * FROM comprehension_batches WHERE batch_id=?", (payload["batch_id"],)).fetchone()
        if not batch:
            raise PopulationScopeError("result references unknown batch")
        if payload["source_revision"] != batch["source_revision"]:
            raise PopulationScopeError("result source revision does not match batch")
        allowed = {row["asset_id"] for row in _batch_rows(connection, payload["batch_id"])}
    if not isinstance(payload["items"], list):
        raise PopulationScopeError("result items must be an array")
    for item in payload["items"]:
        if not isinstance(item, dict) or item.get("asset_id") not in allowed:
            raise PopulationScopeError("provider result contains an asset outside its assigned batch")
        if set(item) - {"asset_id", "lifecycle", "purpose", "owner_candidate", "summary", "classification", "tags", "unresolved_questions", "evidence_refs", "verification_state"}:
            raise PopulationScopeError("unknown provider interpretation fields")
        if item.get("lifecycle", "CANDIDATE") not in {"CANDIDATE", "PROPOSED"}:
            raise PopulationScopeError("provider interpretation must remain candidate/proposed")
        if "path" in item or "filesystem_path" in item:
            raise PopulationScopeError("provider results may not introduce filesystem paths")
        if "evidence_refs" in item and (not isinstance(item["evidence_refs"], list) or not all(isinstance(ref, str) for ref in item["evidence_refs"])):
            raise PopulationScopeError("evidence_refs must be a list of strings")
        if item.get("classification") is not None and not isinstance(item["classification"], str):
            raise PopulationScopeError("classification must be a string or null")
    if payload.get("packet_version") == PACKET_VERSION:
        if packet is None:
            raise PopulationScopeError("evidence-enriched result requires the exact provider packet for citation validation")
        allowed_facts = set(packet.get("evidence_fact_ids") or [])
        with connect(context["root"], create=False) as connection:
            known_facts = {row[0] for row in connection.execute("SELECT fact_id FROM evidence_facts WHERE fact_id IN ({})".format(",".join("?" for _ in allowed_facts | {ref for item in payload["items"] for ref in (item.get("evidence_refs") or [])})), tuple(allowed_facts | {ref for item in payload["items"] for ref in (item.get("evidence_refs") or [])})).fetchall()} if allowed_facts or any(item.get("evidence_refs") for item in payload["items"]) else set()
        for item in payload["items"]:
            errors = packet_citation_errors(item, allowed_facts, known_facts)
            if errors:
                first = errors[0]
                raise PopulationScopeError(f"{first['code']}: {first['message']}")
    return {"valid": True, "batch_id": payload["batch_id"], "asset_count": len(payload["items"]), "provider_type": provider["type"], "candidate_only": True}


def packet_citation_errors(item: dict[str, Any], allowed_facts: set[str], known_facts: set[str] | None = None) -> list[dict[str, str]]:
    """Return precise packet-local citation failures before candidate admission."""
    refs = item.get("evidence_refs") or []
    positive = any(item.get(key) for key in ("purpose", "owner_candidate", "summary", "classification")) or bool(item.get("tags"))
    errors: list[dict[str, str]] = []
    if positive and not refs:
        errors.append({"code": "MISSING_EVIDENCE_CITATION", "message": "positive assertion has no evidence_refs"})
        return errors
    known = known_facts or set()
    for ref in refs:
        if not isinstance(ref, str) or not EVIDENCE_FACT_ID_PATTERN.fullmatch(ref):
            errors.append({"code": "MALFORMED_EVIDENCE_ID", "message": f"evidence reference is not a fact ID: {ref!r}"})
        elif ref not in allowed_facts:
            code = "EVIDENCE_ID_NOT_IN_PACKET" if ref in known else "EVIDENCE_ID_UNKNOWN"
            errors.append({"code": code, "message": f"evidence fact {ref} is not admitted in this packet" if code.endswith("PACKET") else f"evidence fact {ref} is unknown"})
    return errors


def record_comprehension_attempt(root: str | Path | None, *, attempt_id: str, batch_id: str, result_id: str | None,
                                 provider_type: str, provider_model: str | None, worker_identity: str,
                                 source_revision: str, packet_version: str | None, prompt_contract_version: str | None,
                                 packet_hash: str | None, raw_output: str | None, validation_state: str,
                                 validation_code: str | None = None, validation_message: str | None = None,
                                 telemetry: dict[str, Any] | None = None) -> None:
    with connect(validate_requested_scope(root)["root"], create=False) as connection:
        now = _now()
        connection.execute("""INSERT OR REPLACE INTO comprehension_attempts
          (attempt_id,batch_id,result_id,provider_type,provider_model,worker_identity,source_revision,
           packet_version,prompt_contract_version,packet_hash,raw_output,validation_state,validation_code,
           validation_message,telemetry_json,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (attempt_id, batch_id, result_id, provider_type,
          provider_model, worker_identity, source_revision, packet_version, prompt_contract_version, packet_hash,
          raw_output, validation_state, validation_code, validation_message,
          _canonical(telemetry or {}), now, now))


def ingest_result(root: str | Path | None, payload: dict[str, Any], *, packet: dict[str, Any] | None = None) -> dict[str, Any]:
    context = validate_requested_scope(root)
    validate_result(context["root"], payload, packet=packet)
    encoded = _canonical(payload)
    output_hash = _sha_text(encoded)
    with connect(context["root"], create=False) as connection:
        existing = connection.execute("SELECT output_hash FROM comprehension_results WHERE result_id=?", (payload["result_id"],)).fetchone()
        if existing:
            if existing[0] == output_hash:
                return {"status": "IDEMPOTENT", "result_id": payload["result_id"], "canonical_mutation": False}
            raise PopulationScopeError("conflicting result_id already exists; earlier candidate preserved")
        batch = connection.execute("SELECT * FROM comprehension_batches WHERE batch_id=?", (payload["batch_id"],)).fetchone()
        input_hash = _sha_text(_canonical({"batch_id": payload["batch_id"], "source_revision": payload["source_revision"]}))
        provider = payload["provider"]
        connection.execute("INSERT INTO comprehension_results(result_id,batch_id,provider_type,provider_model,worker_identity,source_revision,input_hash,output_hash,output_json,validation_state,created_at,human_review_required) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)", (payload["result_id"], payload["batch_id"], provider["type"], provider.get("model"), provider["worker_identity"], payload["source_revision"], input_hash, output_hash, encoded, "VALIDATED_CANDIDATE", _now()))
        for item in payload["items"]:
            interpretation_id = "interpretation:" + _sha_text(payload["result_id"] + ":" + item["asset_id"])
            asset = connection.execute("SELECT current_content_hash FROM assets WHERE asset_id=?", (item["asset_id"],)).fetchone()
            connection.execute("INSERT INTO candidate_interpretations(interpretation_id,result_id,batch_id,asset_id,candidate_json,lifecycle,provider_type,provider_model,worker_identity,source_revision,content_hash,created_at,validation_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (interpretation_id, payload["result_id"], payload["batch_id"], item["asset_id"], _canonical(item), item.get("lifecycle", "CANDIDATE"), provider["type"], provider.get("model"), provider["worker_identity"], payload["source_revision"], asset[0] if asset else "UNKNOWN", _now(), "CANDIDATE_REVIEW_REQUIRED"))
        connection.execute("UPDATE comprehension_batches SET state='COMPLETED',result_state='ACCEPTED_CANDIDATE',updated_at=?,attempt_count=attempt_count+1 WHERE batch_id=?", (_now(), payload["batch_id"]))
    return {"status": "INGESTED_CANDIDATE", "result_id": payload["result_id"], "batch_id": payload["batch_id"], "candidate_count": len(payload["items"]), "canonical_mutation": False, "human_review_required": True}


def work_status(root: str | Path | None = None) -> dict[str, Any]:
    context = validate_requested_scope(root)
    with connect(context["root"], create=False) as connection:
        rows = [dict(row) for row in connection.execute("SELECT batch_id,scope_id,source_revision,state,attempt_count,result_state,failure_reason,created_at,updated_at FROM comprehension_batches ORDER BY created_at DESC").fetchall()]
        return {"scope_id": context["scope_id"], "batches": rows, "pending": sum(row["state"] in {"OPEN", "ASSIGNED", "PROCESSING", "RETRYABLE"} for row in rows)}


def retry_batch(root: str | Path | None, batch_id: str) -> dict[str, Any]:
    context = validate_requested_scope(root)
    with connect(context["root"], create=False) as connection:
        if not connection.execute("SELECT 1 FROM comprehension_batches WHERE batch_id=?", (batch_id,)).fetchone():
            raise PopulationScopeError(f"unknown comprehension batch: {batch_id}")
        connection.execute("UPDATE comprehension_batches SET state='RETRYABLE',failure_reason=NULL,updated_at=? WHERE batch_id=?", (_now(), batch_id))
    return {"status": "RETRYABLE", "batch_id": batch_id}
