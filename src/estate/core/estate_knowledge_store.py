"""SQLite-backed projection for the existing Estate Knowledge Index owner.

Git and governed JSON remain authoritative.  SQLite stores rebuildable,
provenance-bearing inventory and relationship state for relational queries.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.estate_knowledge_index import SOURCE_LOCATIONS, _registry_by_path, classification_for, estate_root, owner_for

DB_RELATIVE = Path("runtime/search/estate_knowledge_index.sqlite3")
STORE_SCHEMA_VERSION = "estate.knowledge_store.v3"
MIGRATION_VERSION = 3
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", "runtime", "generated", "browser_profiles", "evidence"}

MIGRATIONS = {
    1: """
    CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS scan_runs (
      scan_id TEXT PRIMARY KEY, scope TEXT NOT NULL, repository TEXT NOT NULL,
      source_revision TEXT NOT NULL, scanner_version TEXT NOT NULL,
      phase TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL,
      ended_at TEXT, provider TEXT, files_discovered INTEGER NOT NULL DEFAULT 0,
      files_processed INTEGER NOT NULL DEFAULT 0, files_unchanged INTEGER NOT NULL DEFAULT 0,
      files_unknown INTEGER NOT NULL DEFAULT 0, files_failed INTEGER NOT NULL DEFAULT 0,
      resume_cursor TEXT, error TEXT
    );
    CREATE TABLE IF NOT EXISTS assets (
      asset_id TEXT PRIMARY KEY, current_path TEXT NOT NULL, repository TEXT NOT NULL,
      current_source_revision TEXT NOT NULL, current_git_blob TEXT, current_content_hash TEXT NOT NULL,
      file_type TEXT NOT NULL, extension TEXT NOT NULL, size_bytes INTEGER NOT NULL,
      classification TEXT NOT NULL, scan_status TEXT NOT NULL, comprehension_status TEXT NOT NULL,
      purpose_summary TEXT, owner TEXT, unknown_reason TEXT, first_seen TEXT NOT NULL,
      last_seen TEXT NOT NULL, last_scanned TEXT NOT NULL, last_comprehended TEXT,
      source_kind TEXT NOT NULL, current_state TEXT NOT NULL, UNIQUE(repository, current_path)
    );
    CREATE TABLE IF NOT EXISTS asset_revisions (
      asset_id TEXT NOT NULL REFERENCES assets(asset_id), source_revision TEXT NOT NULL,
      git_blob TEXT, content_hash TEXT NOT NULL, size_bytes INTEGER NOT NULL,
      observed_at TEXT NOT NULL, scan_id TEXT NOT NULL REFERENCES scan_runs(scan_id),
      PRIMARY KEY(asset_id, source_revision, content_hash)
    );
    CREATE TABLE IF NOT EXISTS tags (
      asset_id TEXT NOT NULL REFERENCES assets(asset_id), tag TEXT NOT NULL,
      source_kind TEXT NOT NULL, confidence TEXT NOT NULL, source_ref TEXT,
      source_revision TEXT NOT NULL, current_state TEXT NOT NULL DEFAULT 'CURRENT',
      PRIMARY KEY(asset_id, tag)
    );
    CREATE TABLE IF NOT EXISTS ownership (
      asset_id TEXT NOT NULL REFERENCES assets(asset_id), owner TEXT NOT NULL,
      confidence TEXT NOT NULL, source_kind TEXT NOT NULL, source_ref TEXT,
      source_revision TEXT NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
      PRIMARY KEY(asset_id, owner, source_revision)
    );
    CREATE TABLE IF NOT EXISTS components (
      component_id TEXT PRIMARY KEY, title TEXT NOT NULL, class TEXT NOT NULL,
      owner TEXT NOT NULL, source_revision TEXT NOT NULL, current_state TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS component_assets (
      component_id TEXT NOT NULL REFERENCES components(component_id), asset_id TEXT NOT NULL REFERENCES assets(asset_id),
      source_ref TEXT NOT NULL, certainty TEXT NOT NULL, source_revision TEXT NOT NULL,
      PRIMARY KEY(component_id, asset_id)
    );
    CREATE TABLE IF NOT EXISTS workflows (
      workflow_id TEXT PRIMARY KEY, title TEXT NOT NULL, source_revision TEXT NOT NULL, current_state TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS workflow_components (
      workflow_id TEXT NOT NULL REFERENCES workflows(workflow_id), component_id TEXT NOT NULL REFERENCES components(component_id),
      source_revision TEXT NOT NULL, PRIMARY KEY(workflow_id, component_id)
    );
    CREATE TABLE IF NOT EXISTS checkpoints (
      checkpoint_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL REFERENCES workflows(workflow_id),
      component_id TEXT NOT NULL REFERENCES components(component_id), sequence_no INTEGER NOT NULL,
      title TEXT, probe TEXT NOT NULL, evidence_source TEXT NOT NULL, source_revision TEXT NOT NULL,
      current_state TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS failure_seams (
      seam_id TEXT PRIMARY KEY, title TEXT NOT NULL, workflow_id TEXT NOT NULL REFERENCES workflows(workflow_id),
      certainty TEXT NOT NULL, validation_state TEXT NOT NULL, source_revision TEXT NOT NULL, current_state TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS relationships (
      relationship_id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_id TEXT NOT NULL,
      target_type TEXT NOT NULL, target_id TEXT NOT NULL, kind TEXT NOT NULL, certainty TEXT NOT NULL,
      source_ref TEXT NOT NULL, source_revision TEXT NOT NULL, current_state TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS knowledge_items (
      knowledge_id TEXT PRIMARY KEY, title TEXT NOT NULL, lifecycle TEXT NOT NULL,
      source_path TEXT NOT NULL, source_kind TEXT NOT NULL, source_revision TEXT NOT NULL,
      canonical_promotion INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS knowledge_links (
      knowledge_id TEXT NOT NULL REFERENCES knowledge_items(knowledge_id), target_type TEXT NOT NULL,
      target_id TEXT NOT NULL, source_ref TEXT NOT NULL, source_revision TEXT NOT NULL,
      PRIMARY KEY(knowledge_id, target_type, target_id)
    );
    CREATE TABLE IF NOT EXISTS lifecycle_assessments (
      assessment_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(asset_id),
      state TEXT NOT NULL, reason TEXT NOT NULL, evidence_ref TEXT NOT NULL, confidence TEXT NOT NULL,
      assessor TEXT NOT NULL, source_revision TEXT NOT NULL, assessed_at TEXT NOT NULL,
      current_state TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(scan_status, comprehension_status);
    CREATE INDEX IF NOT EXISTS idx_assets_hash ON assets(current_content_hash);
    CREATE INDEX IF NOT EXISTS idx_assets_owner ON assets(owner);
    CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
    CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_type, source_id);
    CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_type, target_id);
    CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow ON checkpoints(workflow_id, sequence_no);
    CREATE INDEX IF NOT EXISTS idx_lifecycle_state ON lifecycle_assessments(state, current_state);
    INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('store_schema', 'estate.knowledge_store.v1');
    """,
    2: """
    ALTER TABLE assets ADD COLUMN scope_policy TEXT NOT NULL DEFAULT 'STRUCTURAL_SCAN';
    ALTER TABLE assets ADD COLUMN provider_content_allowed INTEGER NOT NULL DEFAULT 1;
    CREATE TABLE IF NOT EXISTS population_scopes (
      scope_id TEXT PRIMARY KEY, schema_version TEXT NOT NULL, repository TEXT NOT NULL,
      source_path TEXT NOT NULL, source_revision TEXT NOT NULL, loaded_at TEXT NOT NULL,
      current_state TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS scope_entries (
      scope_id TEXT NOT NULL REFERENCES population_scopes(scope_id), pattern TEXT NOT NULL,
      policy TEXT NOT NULL, reason TEXT NOT NULL, authority TEXT NOT NULL,
      introduced_revision TEXT NOT NULL, child_traversal INTEGER NOT NULL,
      provider_content INTEGER NOT NULL, deterministic_scan INTEGER NOT NULL,
      PRIMARY KEY(scope_id, pattern)
    );
    CREATE TABLE IF NOT EXISTS scope_boundaries (
      boundary_id TEXT PRIMARY KEY, scope_id TEXT NOT NULL REFERENCES population_scopes(scope_id),
      path TEXT NOT NULL, policy TEXT NOT NULL, reason TEXT NOT NULL,
      source_revision TEXT NOT NULL, observed_at TEXT NOT NULL, current_state TEXT NOT NULL,
      UNIQUE(scope_id, path)
    );
    CREATE TABLE IF NOT EXISTS future_scope_candidates (
      candidate_id TEXT PRIMARY KEY, path TEXT NOT NULL, reason TEXT NOT NULL,
      recommended_policy TEXT NOT NULL, source_revision TEXT NOT NULL,
      observed_at TEXT NOT NULL, current_state TEXT NOT NULL, UNIQUE(path, source_revision)
    );
    CREATE TABLE IF NOT EXISTS comprehension_batches (
      batch_id TEXT PRIMARY KEY, scope_id TEXT NOT NULL, source_revision TEXT NOT NULL,
      selection_reason TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      provider_type TEXT, provider_model TEXT, worker_identity TEXT,
      state TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
      result_state TEXT, failure_reason TEXT, packet_hash TEXT
    );
    CREATE TABLE IF NOT EXISTS comprehension_batch_assets (
      batch_id TEXT NOT NULL REFERENCES comprehension_batches(batch_id),
      asset_id TEXT NOT NULL REFERENCES assets(asset_id), position INTEGER NOT NULL,
      PRIMARY KEY(batch_id, asset_id)
    );
    CREATE TABLE IF NOT EXISTS comprehension_results (
      result_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES comprehension_batches(batch_id),
      provider_type TEXT NOT NULL, provider_model TEXT, worker_identity TEXT NOT NULL,
      source_revision TEXT NOT NULL, input_hash TEXT NOT NULL, output_hash TEXT NOT NULL,
      output_json TEXT NOT NULL, validation_state TEXT NOT NULL, created_at TEXT NOT NULL,
      human_review_required INTEGER NOT NULL DEFAULT 1, UNIQUE(batch_id, output_hash)
    );
    CREATE TABLE IF NOT EXISTS candidate_interpretations (
      interpretation_id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES comprehension_results(result_id),
      batch_id TEXT NOT NULL, asset_id TEXT NOT NULL REFERENCES assets(asset_id),
      candidate_json TEXT NOT NULL, lifecycle TEXT NOT NULL, provider_type TEXT NOT NULL,
      provider_model TEXT, worker_identity TEXT NOT NULL, source_revision TEXT NOT NULL,
      content_hash TEXT NOT NULL, created_at TEXT NOT NULL, validation_state TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_assets_scope_policy ON assets(scope_policy, provider_content_allowed);
    CREATE INDEX IF NOT EXISTS idx_batch_state ON comprehension_batches(state, updated_at);
    CREATE INDEX IF NOT EXISTS idx_batch_asset ON comprehension_batch_assets(asset_id);
    CREATE INDEX IF NOT EXISTS idx_candidate_asset ON candidate_interpretations(asset_id, created_at);
    UPDATE schema_meta SET value='estate.knowledge_store.v2' WHERE key='store_schema';
    """,
    3: """
    CREATE TABLE IF NOT EXISTS candidate_assertions (
      assertion_id TEXT PRIMARY KEY, interpretation_id TEXT NOT NULL REFERENCES candidate_interpretations(interpretation_id),
      result_id TEXT NOT NULL REFERENCES comprehension_results(result_id), asset_id TEXT NOT NULL REFERENCES assets(asset_id),
      assertion_kind TEXT NOT NULL, proposed_value TEXT, evidence_refs TEXT NOT NULL, confidence TEXT NOT NULL,
      evidence_strength TEXT NOT NULL, corroboration_state TEXT NOT NULL, corroboration_reason TEXT,
      review_state TEXT NOT NULL, application_state TEXT NOT NULL, conflict_state TEXT NOT NULL,
      provider_type TEXT NOT NULL, provider_model TEXT, worker_identity TEXT NOT NULL,
      source_revision TEXT NOT NULL, source_hash TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      UNIQUE(interpretation_id, assertion_kind, proposed_value)
    );
    CREATE TABLE IF NOT EXISTS review_decisions (
      decision_id TEXT PRIMARY KEY, assertion_id TEXT NOT NULL REFERENCES candidate_assertions(assertion_id),
      decision TEXT NOT NULL, reviewer_id TEXT NOT NULL, reviewer_type TEXT NOT NULL, rationale TEXT NOT NULL,
      evidence_refs TEXT NOT NULL, source_revision TEXT NOT NULL, decided_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS applied_comprehension (
      application_id TEXT PRIMARY KEY, assertion_id TEXT NOT NULL REFERENCES candidate_assertions(assertion_id),
      asset_id TEXT NOT NULL REFERENCES assets(asset_id), field_name TEXT NOT NULL, applied_value TEXT NOT NULL,
      source_revision TEXT NOT NULL, source_hash TEXT NOT NULL, reviewer_id TEXT NOT NULL, applied_at TEXT NOT NULL,
      state TEXT NOT NULL, UNIQUE(assertion_id, state)
    );
    CREATE TABLE IF NOT EXISTS application_history (
      history_id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applied_comprehension(application_id),
      event_type TEXT NOT NULL, prior_value TEXT, new_value TEXT, evidence_refs TEXT NOT NULL,
      source_revision TEXT NOT NULL, actor_id TEXT NOT NULL, actor_type TEXT NOT NULL, occurred_at TEXT NOT NULL,
      reason TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS revalidation_queue (
      queue_id TEXT PRIMARY KEY, assertion_id TEXT NOT NULL REFERENCES candidate_assertions(assertion_id),
      asset_id TEXT NOT NULL REFERENCES assets(asset_id), prior_source_revision TEXT NOT NULL,
      current_source_revision TEXT NOT NULL, prior_source_hash TEXT NOT NULL, current_source_hash TEXT NOT NULL,
      state TEXT NOT NULL, reason TEXT NOT NULL, queued_at TEXT NOT NULL, resolved_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_assertion_review ON candidate_assertions(review_state, corroboration_state);
    CREATE INDEX IF NOT EXISTS idx_assertion_asset ON candidate_assertions(asset_id, application_state);
    CREATE INDEX IF NOT EXISTS idx_application_asset ON applied_comprehension(asset_id, state);
    UPDATE schema_meta SET value='estate.knowledge_store.v3' WHERE key='store_schema';
    """
}


class KnowledgeStoreError(RuntimeError):
    pass


class _KnowledgeConnection(sqlite3.Connection):
    """Close projection connections at the end of ``with`` blocks."""

    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def database_path(root: str | Path | None = None) -> Path:
    return estate_root(root) / DB_RELATIVE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_id(repository: str, path: str) -> str:
    return "asset:" + hashlib.sha256(f"{repository}:{path}".encode()).hexdigest()


def connect(root: str | Path | None = None, *, create: bool = True) -> sqlite3.Connection:
    path = database_path(root)
    if not create and not path.exists():
        raise KnowledgeStoreError(f"SQLite index does not exist: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, factory=_KnowledgeConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    migrate(connection)
    return connection


def migrate(connection: sqlite3.Connection) -> dict[str, Any]:
    current = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if current > MIGRATION_VERSION:
        raise KnowledgeStoreError(f"database schema {current} is newer than supported {MIGRATION_VERSION}")
    applied = []
    for version in range(current + 1, MIGRATION_VERSION + 1):
        connection.executescript(MIGRATIONS[version])
        connection.execute(f"PRAGMA user_version={version}")
        connection.commit()
        applied.append(version)
    return {"schema_version": STORE_SCHEMA_VERSION, "current_version": MIGRATION_VERSION, "applied": applied}


def init_store(root: str | Path | None = None) -> dict[str, Any]:
    with connect(root) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    return {"status": "READY", "schema_version": STORE_SCHEMA_VERSION, "migration_version": version, "database": str(database_path(root))}


def _iter_scope(root: Path, scope: str | None) -> Iterable[Path]:
    locations = [scope] if scope else SOURCE_LOCATIONS
    seen: set[Path] = set()
    for value in locations:
        path = root / value
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else sorted(path.rglob("*"))
        for candidate in candidates:
            if not candidate.is_file() or candidate in seen:
                continue
            relative = candidate.relative_to(root)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            seen.add(candidate)
            yield candidate


def _file_type(path: Path, rel: str) -> tuple[str, str, str]:
    suffix = path.suffix.lower()
    if rel.startswith("runtime/") or "/generated/" in f"/{rel}":
        return "runtime", "GENERATED", "generated/runtime output"
    if suffix in {".py", ".js", ".ts", ".ps1", ".sh"}:
        return "source", "SOURCE", "implementation source"
    if suffix in {".md", ".txt", ".rst"}:
        return "documentation", "DOCUMENTATION", "documentation or operational guidance"
    if suffix in {".json", ".yaml", ".yml", ".toml"}:
        if "schema" in path.name.lower() or rel.startswith("schemas/"):
            return "schema", "SCHEMA", "schema or structured contract"
        if "/test" in f"/{rel.lower()}" or rel.startswith("tests/"):
            return "test", "TEST", "test or acceptance artifact"
        return "configuration", "CONFIG", "structured configuration or record"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bin", ".dll"}:
        return "binary", "ASSET", "binary asset"
    return "other", "UNKNOWN", ""


def _source_identity(root: Path, rel: str) -> tuple[str, str | None]:
    head = _git(root, "rev-parse", "HEAD")
    blob = _git(root, "rev-parse", f"HEAD:{rel}")
    return head, None if blob == "UNKNOWN" else blob


def _model(root: Path) -> dict[str, Any] | None:
    path = root / "docs/operations/troubleshooting/comprehension.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _component_for(rel: str, model: dict[str, Any] | None) -> tuple[str | None, str | None]:
    for component in (model or {}).get("components", []):
        if rel in component.get("source_paths", []):
            return component.get("component_id"), component.get("owner")
    return None, None


def _tags(rel: str, file_type: str, classification: str) -> set[str]:
    values = {classification, file_type.upper()}
    if rel.startswith("archive/"): values.add("ARCHIVE")
    if rel.startswith("tests/") or file_type == "test": values.add("TEST")
    if rel.startswith("operations/diagnostics/candidates/"): values.add("CANDIDATE")
    return values


def _upsert_asset(connection: sqlite3.Connection, root: Path, path: Path, scan_id: str, source_revision: str, repository: str, registry: dict[str, dict[str, Any]], model: dict[str, Any] | None) -> tuple[str, bool, bool]:
    rel = path.relative_to(root).as_posix()
    digest = _hash(path)
    asset_id = _asset_id(repository, rel)
    old = connection.execute("SELECT current_content_hash FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
    unchanged = old is not None and old[0] == digest
    stat = path.stat()
    try: text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError): text = ""
    file_type, tag, purpose = _file_type(path, rel)
    component_id, component_owner = _component_for(rel, model)
    owner = component_owner or owner_for(rel, registry)
    owner_known = bool(component_owner or rel.split("/", 1)[0] in {"operations", "collaboration", "residents", "constitution", "departments", "archive", "validation"})
    purpose_known = bool(purpose)
    unknown_reason = None if owner_known and purpose_known else "; ".join(x for x, ok in (("ownership unresolved", owner_known), ("purpose unresolved", purpose_known)) if not ok)
    now = _now()
    git_blob = _git(root, "hash-object", "--", rel)
    previous = connection.execute("SELECT comprehension_status FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
    if unchanged:
        comprehension_status = previous[0] if previous else ("COMPREHENDED" if component_id else ("PARTIAL" if purpose_known else "UNKNOWN"))
        current_state = "CURRENT"
    elif previous and previous[0] == "COMPREHENDED":
        comprehension_status = "STALE"
        current_state = "REVALIDATION_REQUIRED"
    else:
        comprehension_status = "COMPREHENDED" if component_id else ("PARTIAL" if purpose_known else "UNKNOWN")
        current_state = "CURRENT"
    connection.execute("""INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,source_kind,current_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(asset_id) DO UPDATE SET current_path=excluded.current_path,current_source_revision=excluded.current_source_revision,current_git_blob=excluded.current_git_blob,current_content_hash=excluded.current_content_hash,file_type=excluded.file_type,extension=excluded.extension,size_bytes=excluded.size_bytes,classification=excluded.classification,scan_status=excluded.scan_status,comprehension_status=excluded.comprehension_status,purpose_summary=excluded.purpose_summary,owner=excluded.owner,unknown_reason=excluded.unknown_reason,last_seen=excluded.last_seen,last_scanned=excluded.last_scanned,current_state=excluded.current_state""", (asset_id, rel, repository, source_revision, git_blob if git_blob != "UNKNOWN" else None, digest, file_type, path.suffix.lower(), stat.st_size, classification_for(rel, text), "SKIPPED_UNCHANGED" if unchanged else "CLASSIFIED", "COMPREHENDED" if component_id else ("PARTIAL" if purpose_known else "UNKNOWN"), purpose or None, owner, unknown_reason, now, now, now, "DETERMINISTIC", current_state))
    connection.execute("""INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,source_kind,current_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(asset_id) DO UPDATE SET current_path=excluded.current_path,current_source_revision=excluded.current_source_revision,current_git_blob=excluded.current_git_blob,current_content_hash=excluded.current_content_hash,file_type=excluded.file_type,extension=excluded.extension,size_bytes=excluded.size_bytes,classification=excluded.classification,scan_status=excluded.scan_status,comprehension_status=excluded.comprehension_status,purpose_summary=excluded.purpose_summary,owner=excluded.owner,unknown_reason=excluded.unknown_reason,last_seen=excluded.last_seen,last_scanned=excluded.last_scanned,current_state=excluded.current_state""", (asset_id, rel, repository, source_revision, git_blob if git_blob != "UNKNOWN" else None, digest, file_type, path.suffix.lower(), stat.st_size, classification_for(rel, text), "SKIPPED_UNCHANGED" if unchanged else "CLASSIFIED", comprehension_status, purpose or None, owner, unknown_reason, now, now, now, "DETERMINISTIC", current_state))
    connection.execute("INSERT OR IGNORE INTO asset_revisions(asset_id,source_revision,git_blob,content_hash,size_bytes,observed_at,scan_id) VALUES(?,?,?,?,?,?,?)", (asset_id, source_revision, git_blob if git_blob != "UNKNOWN" else None, digest, stat.st_size, now, scan_id))
    for value in _tags(rel, file_type, tag):
        confidence = "HIGH" if value in {"SOURCE", "DOCUMENTATION", "SCHEMA", "TEST", "CONFIG", "GENERATED", "ARCHIVE"} else "MEDIUM"
        connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, value, "DETERMINISTIC", confidence, rel, source_revision, "CURRENT"))
    if owner_known:
        connection.execute("INSERT OR REPLACE INTO ownership(asset_id,owner,confidence,source_kind,source_ref,source_revision,is_current) VALUES(?,?,?,?,?,?,1)", (asset_id, owner, "HIGH" if component_owner else "MEDIUM", "DETERMINISTIC", rel, source_revision))
    else:
        connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, "OWNER_UNKNOWN", "DETERMINISTIC", "HIGH", rel, source_revision, "CURRENT"))
    if not purpose_known:
        connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, "PURPOSE_UNKNOWN", "DETERMINISTIC", "HIGH", rel, source_revision, "CURRENT"))
    if component_id:
        connection.execute("INSERT OR REPLACE INTO component_assets(component_id,asset_id,source_ref,certainty,source_revision) VALUES(?,?,?,?,?)", (component_id, asset_id, rel, "DETERMINISTIC", source_revision))
    return asset_id, unchanged, not owner_known or not purpose_known


def _index_model(connection: sqlite3.Connection, root: Path, source_revision: str, model: dict[str, Any] | None) -> None:
    if not model: return
    for component in model.get("components", []):
        connection.execute("INSERT OR REPLACE INTO components(component_id,title,class,owner,source_revision,current_state) VALUES(?,?,?,?,?,?)", (component["component_id"], component["title"], component["class"], component["owner"], source_revision, "CURRENT"))
    for workflow in model.get("workflows", []):
        connection.execute("INSERT OR REPLACE INTO workflows(workflow_id,title,source_revision,current_state) VALUES(?,?,?,?)", (workflow["workflow_id"], workflow["title"], source_revision, "CURRENT"))
        for component_id in workflow.get("component_ids", []):
            connection.execute("INSERT OR REPLACE INTO workflow_components(workflow_id,component_id,source_revision) VALUES(?,?,?)", (workflow["workflow_id"], component_id, source_revision))
    for checkpoint in model.get("checkpoints", []):
        connection.execute("INSERT OR REPLACE INTO checkpoints(checkpoint_id,workflow_id,component_id,sequence_no,title,probe,evidence_source,source_revision,current_state) VALUES(?,?,?,?,?,?,?,?,?)", (checkpoint["checkpoint_id"], checkpoint["workflow_id"], checkpoint["component_id"], checkpoint["sequence"], checkpoint.get("title"), checkpoint["probe"], checkpoint["evidence_source"], source_revision, "CURRENT"))
    for seam in model.get("failure_seams", []):
        connection.execute("INSERT OR REPLACE INTO failure_seams(seam_id,title,workflow_id,certainty,validation_state,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (seam["seam_id"], seam["title"], seam["workflow_id"], seam["certainty"], seam["validation_state"], source_revision, "CURRENT"))
    component_ids = {x["component_id"] for x in model.get("components", [])}
    for relationship in model.get("relationships", []):
        connection.execute("INSERT OR REPLACE INTO relationships(relationship_id,source_type,source_id,target_type,target_id,kind,certainty,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?,?,?,?)", (relationship["relationship_id"], "component", relationship["source"], "component", relationship["target"], relationship["kind"], relationship["certainty"], ";".join(relationship.get("evidence_refs", [])), source_revision, "CURRENT"))
    for item in model.get("components", []) + model.get("checkpoints", []) + model.get("failure_seams", []):
        target_type = "component" if "component_id" in item else ("checkpoint" if "checkpoint_id" in item else "failure_seam")
        for knowledge_id in item.get("knowledge_refs", []):
            connection.execute("INSERT OR IGNORE INTO knowledge_items(knowledge_id,title,lifecycle,source_path,source_kind,source_revision,canonical_promotion) VALUES(?,?,?,?,?,?,?)", (knowledge_id, knowledge_id, "CANONICAL_REFERENCE", "docs/operations/troubleshooting/cookbook.json", "HUMAN", source_revision, 1))
            connection.execute("INSERT OR REPLACE INTO knowledge_links(knowledge_id,target_type,target_id,source_ref,source_revision) VALUES(?,?,?,?,?)", (knowledge_id, target_type, item.get(target_type + "_id") or item.get("component_id") or item.get("checkpoint_id") or item.get("seam_id"), "docs/operations/troubleshooting/comprehension.json", source_revision))


def _index_operational_knowledge(connection: sqlite3.Connection, root: Path, source_revision: str) -> None:
    """Index knowledge identities without copying their typed record payloads."""
    canonical = root / "docs/operations/troubleshooting/cookbook.json"
    if canonical.exists():
        try:
            payload = json.loads(canonical.read_text(encoding="utf-8"))
            for item in payload.get("checkpoints", []):
                knowledge_id = item.get("checkpoint_id")
                if knowledge_id:
                    connection.execute("INSERT OR REPLACE INTO knowledge_items(knowledge_id,title,lifecycle,source_path,source_kind,source_revision,canonical_promotion) VALUES(?,?,?,?,?,?,1)", (knowledge_id, item.get("title") or knowledge_id, "CANONICAL", "docs/operations/troubleshooting/cookbook.json", "GOVERNED_JSON", source_revision))
        except (OSError, ValueError, TypeError):
            pass
    candidate_dir = root / "operations/diagnostics/candidates/knowledge"
    for path in sorted(candidate_dir.glob("*.json")) if candidate_dir.exists() else []:
        try:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
            item = wrapper.get("knowledge", wrapper)
            knowledge_id = item.get("knowledge_id")
            if not knowledge_id:
                continue
            source = item.get("source") or {}
            connection.execute("INSERT OR IGNORE INTO knowledge_items(knowledge_id,title,lifecycle,source_path,source_kind,source_revision,canonical_promotion) VALUES(?,?,?,?,?,?,0)", (knowledge_id, item.get("title") or knowledge_id, item.get("lifecycle") or "CANDIDATE", path.relative_to(root).as_posix(), source.get("kind") or "UNKNOWN", source_revision))
        except (OSError, ValueError, TypeError):
            continue


def scan(root: str | Path | None = None, *, scope: str | None = None, limit: int | None = None, phase: str = "DETERMINISTIC") -> dict[str, Any]:
    started_clock = time.perf_counter()
    base = estate_root(root).resolve()
    repository = _git(base, "config", "--get", "remote.origin.url") or _git(base, "rev-parse", "--show-toplevel")
    source_revision = _git(base, "rev-parse", "HEAD")
    paths = list(_iter_scope(base, scope))
    if limit is not None: paths = paths[:limit]
    scan_id = "scan:" + uuid.uuid4().hex
    registry = _registry_by_path(base)
    model = _model(base)
    started = _now()
    with connect(base) as connection:
        connection.execute("INSERT INTO scan_runs(scan_id,scope,repository,source_revision,scanner_version,status,phase,started_at,provider) VALUES(?,?,?,?,?,?,?,?,?)", (scan_id, scope or "default", repository, source_revision, "estate-knowledge-index-sqlite/1.0", "RUNNING", phase, started, None))
        discovered = unchanged = unknown = failed = processed = 0
        try:
            for path in paths:
                discovered += 1
                try:
                    _, was_unchanged, was_unknown = _upsert_asset(connection, base, path, scan_id, source_revision, repository, registry, model)
                    processed += 1; unchanged += int(was_unchanged); unknown += int(was_unknown)
                except (OSError, sqlite3.Error):
                    failed += 1
            _index_model(connection, base, source_revision, model)
            _index_operational_knowledge(connection, base, source_revision)
            ended = _now()
            connection.execute("UPDATE scan_runs SET status=?,ended_at=?,files_discovered=?,files_processed=?,files_unchanged=?,files_unknown=?,files_failed=? WHERE scan_id=?", ("COMPLETED", ended, discovered, processed, unchanged, unknown, failed, scan_id))
        except Exception as exc:
            connection.execute("UPDATE scan_runs SET status=?,ended_at=?,error=? WHERE scan_id=?", ("FAILED", _now(), str(exc), scan_id)); raise
    return {"status":"COMPLETED" if failed == 0 else "COMPLETED_WITH_FAILURES", "scan_id":scan_id, "scope":scope or "default", "source_revision":source_revision, "files_discovered":discovered, "files_processed":processed, "files_unchanged":unchanged, "files_unknown":unknown, "files_failed":failed, "elapsed_ms":round((time.perf_counter() - started_clock) * 1000, 2), "database":str(database_path(base)), "reprocessing_policy":"unchanged content is retained; changed comprehended assets become REVALIDATION_REQUIRED"}


def _rows(connection: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query, params).fetchall()]


def store_status(root: str | Path | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        latest = connection.execute("SELECT * FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        return {"schema_version":STORE_SCHEMA_VERSION,"database":str(database_path(root)),"migration_version":connection.execute("PRAGMA user_version").fetchone()[0],"asset_count":connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0],"component_count":connection.execute("SELECT COUNT(*) FROM components").fetchone()[0],"workflow_count":connection.execute("SELECT COUNT(*) FROM workflows").fetchone()[0],"latest_scan":dict(latest) if latest else None}


def coverage(root: str | Path | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        total = connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        row = connection.execute("SELECT SUM(scan_status IN ('CLASSIFIED','SKIPPED_UNCHANGED')), SUM(comprehension_status='COMPREHENDED'), SUM(comprehension_status='PARTIAL'), SUM(comprehension_status='UNKNOWN'), SUM(owner IS NOT NULL), SUM(purpose_summary IS NOT NULL) FROM assets").fetchone()
        owner_known = connection.execute("SELECT COUNT(*) FROM assets WHERE unknown_reason IS NULL OR unknown_reason NOT LIKE '%ownership unresolved%'").fetchone()[0]
        return {"schema_version":STORE_SCHEMA_VERSION,"asset_count":total,"scanned_count":row[0] or 0,"comprehended_count":row[1] or 0,"partial_count":row[2] or 0,"unknown_count":row[3] or 0,"owner_known_count":owner_known,"purpose_known_count":row[5] or 0,"components_without_workflow":_rows(connection,"SELECT c.component_id FROM components c LEFT JOIN workflow_components wc ON wc.component_id=c.component_id WHERE wc.component_id IS NULL"),"checkpoints_without_probe":_rows(connection,"SELECT checkpoint_id FROM checkpoints WHERE probe IS NULL OR probe=''"),"stale_assets":_rows(connection,"SELECT current_path FROM assets WHERE current_state!='CURRENT'")}


def query_assets(query: str = "", root: str | Path | None = None, *, limit: int = 50, owner: str | None = None, tag: str | None = None, status_filter: str | None = None) -> dict[str, Any]:
    terms = [x.lower() for x in query.split() if x]
    with connect(root, create=False) as connection:
        clauses = []; params: list[Any] = []
        if owner: clauses.append("a.owner=?"); params.append(owner)
        if status_filter: clauses.append("(a.scan_status=? OR a.comprehension_status=? OR a.current_state=?)"); params.extend([status_filter, status_filter, status_filter])
        if tag: clauses.append("EXISTS (SELECT 1 FROM tags t WHERE t.asset_id=a.asset_id AND t.tag=?)"); params.append(tag)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query_sql = "SELECT a.asset_id,a.current_path,a.current_content_hash,a.file_type,a.classification,a.scan_status,a.comprehension_status,a.owner,a.purpose_summary,a.unknown_reason,a.current_source_revision FROM assets a" + where + " ORDER BY a.current_path"
        rows = _rows(connection, query_sql + (" LIMIT ?" if not terms else ""), tuple(params + ([limit] if not terms else [])))
        if terms: rows = [row for row in rows if all(term in json.dumps(row).lower() for term in terms)]
        return {"schema_version":STORE_SCHEMA_VERSION,"query":query,"results":rows[:limit],"match_count":len(rows[:limit])}


def unknown_assets(root: str | Path | None = None, *, limit: int = 100) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        rows = _rows(connection, "SELECT asset_id,current_path,unknown_reason,owner,purpose_summary,comprehension_status FROM assets WHERE comprehension_status='UNKNOWN' OR unknown_reason IS NOT NULL ORDER BY current_path LIMIT ?", (limit,))
        return {"schema_version":STORE_SCHEMA_VERSION,"results":rows,"match_count":len(rows)}


def stale_assets(root: str | Path | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        rows = _rows(connection, "SELECT asset_id,current_path,current_content_hash,current_source_revision,current_state FROM assets WHERE current_state!='CURRENT' OR scan_status='STALE' ORDER BY current_path")
        return {"schema_version":STORE_SCHEMA_VERSION,"results":rows,"match_count":len(rows)}


def graph(root: str | Path | None = None, *, scope: str | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        nodes = _rows(connection, "SELECT component_id AS id,'component' AS type,title AS label FROM components")
        edges = _rows(connection, "SELECT source_id AS source,target_id AS target,kind,certainty,source_ref FROM relationships WHERE source_type='component' AND target_type='component'")
        if scope:
            members = {scope} | {row["source"] for row in edges if row["source"] == scope} | {row["target"] for row in edges if row["target"] == scope}
            nodes = [node for node in nodes if node["id"] in members]; edges = [edge for edge in edges if edge["source"] in members and edge["target"] in members]
        return {"schema_version":STORE_SCHEMA_VERSION,"nodes":nodes,"edges":edges,"scope":scope,"source":"SQLite indexed comprehension model"}


def scan_progress(root: str | Path | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        return {"schema_version":STORE_SCHEMA_VERSION,"runs":_rows(connection,"SELECT scan_id,scope,source_revision,status,files_discovered,files_processed,files_unchanged,files_unknown,files_failed,resume_cursor FROM scan_runs ORDER BY started_at DESC")}


def build_index_packet(root: str | Path | None, scope: str) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        component = _rows(connection, "SELECT * FROM components WHERE component_id=?", (scope,))
        workflow = _rows(connection, "SELECT * FROM workflows WHERE workflow_id=?", (scope,))
        if workflow:
            component = _rows(connection, "SELECT c.* FROM components c JOIN workflow_components wc ON wc.component_id=c.component_id WHERE wc.workflow_id=?", (scope,))
        checkpoints = _rows(connection, "SELECT * FROM checkpoints WHERE workflow_id=? OR component_id=? ORDER BY sequence_no", (scope, scope))
        seams = _rows(connection, "SELECT * FROM failure_seams WHERE workflow_id=?", (scope,))
        if workflow:
            assets = _rows(connection, "SELECT DISTINCT a.* FROM assets a JOIN component_assets ca ON ca.asset_id=a.asset_id JOIN workflow_components wc ON wc.component_id=ca.component_id WHERE wc.workflow_id=?", (scope,))
        else:
            assets = _rows(connection, "SELECT a.* FROM assets a JOIN component_assets ca ON ca.asset_id=a.asset_id WHERE ca.component_id=?", (scope,))
        relationships = _rows(connection, "SELECT * FROM relationships WHERE source_id=? OR target_id=?", (scope, scope))
        return {"contract":"estate.troubleshooting.comprehension.packet.v1","provider_neutral":True,"scope":scope,"indexed":True,"components":component,"workflows":workflow,"checkpoints":checkpoints,"failure_seams":seams,"assets":assets,"relationships":relationships,"allowed_outputs":["candidate understanding","probe recommendations","revalidation request","contradiction report"],"forbidden_actions":["mutate canonical artifacts","promote knowledge","advance baseline","authorize remediation"],"source":"SQLite projection with Git/file provenance"}


def lifecycle_candidates(root: str | Path | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        rows = _rows(connection, "SELECT a.current_path,a.owner,a.current_state,la.state,la.reason,la.evidence_ref,la.confidence FROM lifecycle_assessments la JOIN assets a ON a.asset_id=la.asset_id WHERE la.current_state='CURRENT' ORDER BY a.current_path")
        return {"schema_version":STORE_SCHEMA_VERSION,"results":rows,"match_count":len(rows),"mutation_authorized":False}


def query_knowledge(root: str | Path | None = None, *, phrase: str = "", limit: int = 100) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        rows = _rows(connection, "SELECT knowledge_id,title,lifecycle,source_path,source_kind,source_revision,canonical_promotion FROM knowledge_items ORDER BY knowledge_id")
        terms = [term.lower() for term in phrase.split() if term]
        if terms:
            rows = [row for row in rows if all(term in json.dumps(row).lower() for term in terms)]
        return {"schema_version": STORE_SCHEMA_VERSION, "query": phrase, "results": rows[:limit], "match_count": len(rows[:limit]), "canonical_mutation": False}


def rebuild(root: str | Path | None = None, *, scope: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """Rebuild the derived SQLite projection while retaining governed files."""
    path = database_path(root)
    if path.exists():
        path.unlink()
    for sidecar in (Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if sidecar.exists():
            sidecar.unlink()
    init_store(root)
    return scan(root, scope=scope, limit=limit, phase="REBUILD")
