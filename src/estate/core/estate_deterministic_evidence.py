"""Revision-grounded deterministic evidence for comprehension assertions.

This module is deliberately provider-free. It extracts reusable facts from the
already indexed/admitted repository and links those facts to candidate
assertions only through the governed corroboration service.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.estate_knowledge_store import connect, database_path
from estate.core.estate_population import validate_requested_scope

EXTRACTOR = "estate-deterministic-evidence.v1"
EVIDENCE_STRENGTHS = {
    "AUTHORITATIVE_GOVERNANCE",
    "AUTHORITATIVE_REGISTRY",
    "DETERMINISTIC_SOURCE_RELATIONSHIP",
    "EXECUTABLE_TEST",
    "CURRENT_DOCUMENTATION",
    "HISTORICAL_DOCUMENTATION",
    "DERIVED_STATIC_ANALYSIS",
    "PROVIDER_INFERENCE",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tokens(value: str | None) -> set[str]:
    return {token for token in _TOKEN_RE.findall((value or "").lower()) if len(token) > 2}


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _line_for(text: str, needle: str) -> str | None:
    for number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return f"line:{number}"
    return None


def _asset_rows(connection, asset_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    if asset_ids is None:
        query = "SELECT * FROM assets WHERE scope_policy <> 'METADATA_ONLY' ORDER BY current_path"
        return [dict(row) for row in connection.execute(query).fetchall()]
    ids = list(asset_ids)
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    return [dict(row) for row in connection.execute(f"SELECT * FROM assets WHERE asset_id IN ({marks})", ids).fetchall()]


def _insert_fact(connection, *, fact_kind: str, source: dict[str, Any], target: dict[str, Any] | None,
                 value: Any, location: str | None, extractor: str, certainty: str,
                 revision: str, source_hash: str) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # Revision changes alone do not create a new logical fact. Reuse the
    # existing hash-grounded fact so a new checkout revision does not multiply
    # unchanged evidence. A genuinely changed source hash still creates a new
    # historical fact and the caller marks the prior hash stale.
    existing = connection.execute(
        """SELECT fact_id,current_state FROM evidence_facts
           WHERE fact_kind=? AND source_asset_id=? AND target_asset_id IS ?
             AND value_json=? AND evidence_path=? AND evidence_location IS ?
             AND source_hash=? AND extractor=?
           ORDER BY CASE WHEN current_state='CURRENT' THEN 0 ELSE 1 END, updated_at DESC
           LIMIT 1""",
        (fact_kind, source["asset_id"], target["asset_id"] if target else None, encoded,
         source["current_path"], location, source_hash, extractor),
    ).fetchone()
    if existing:
        if existing[1] != "CURRENT":
            connection.execute("UPDATE evidence_facts SET current_state='CURRENT',updated_at=? WHERE fact_id=?", (_now(), existing[0]))
        return existing[0]
    fact_id = "fact:" + _sha({"kind": fact_kind, "source": source["asset_id"], "target": target["asset_id"] if target else None,
                               "value": value, "path": source["current_path"], "location": location, "hash": source_hash, "extractor": extractor})
    now = _now()
    connection.execute(
        """INSERT OR IGNORE INTO evidence_facts
        (fact_id,fact_kind,source_asset_id,target_asset_id,value_json,evidence_path,evidence_location,
         source_revision,source_hash,extractor,certainty,current_state,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (fact_id, fact_kind, source["asset_id"], target["asset_id"] if target else None, encoded,
         source["current_path"], location, revision, source_hash, extractor, certainty, "CURRENT", now, now),
    )
    return fact_id


def _schema_facts(connection, source: dict[str, Any], target: dict[str, Any], text: str, revision: str, source_hash: str) -> int:
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return 0
    if not isinstance(document, dict):
        return 0
    count = 0
    for key in ("$schema", "$id", "title", "description", "type"):
        if key in document and isinstance(document[key], (str, int, float, bool)):
            _insert_fact(connection, fact_kind="SCHEMA_METADATA", source=source, target=target,
                         value={"key": key, "value": document[key]}, location=f"json-pointer:/{key}",
                         extractor=EXTRACTOR, certainty="DERIVED_STATIC_ANALYSIS", revision=revision, source_hash=source_hash)
            count += 1
    for key in ("required", "properties", "$defs", "definitions", "$ref", "allOf", "oneOf", "anyOf", "enum", "const"):
        if key in document:
            value = document[key]
            if key == "properties" and isinstance(value, dict):
                value = sorted(value)
            _insert_fact(connection, fact_kind="SCHEMA_STRUCTURE", source=source, target=target,
                         value={"key": key, "value": value}, location=f"json-pointer:/{key}",
                         extractor=EXTRACTOR, certainty="DERIVED_STATIC_ANALYSIS", revision=revision, source_hash=source_hash)
            count += 1
    return count


def _owner_and_component_facts(connection, source: dict[str, Any], revision: str, source_hash: str) -> int:
    count = 0
    for row in connection.execute("SELECT owner,confidence,source_kind,source_ref FROM ownership WHERE asset_id=? AND is_current=1", (source["asset_id"],)):
        if row[2].lower() in {"provider", "local_ai", "inference"}:
            continue
        _insert_fact(connection, fact_kind="OWNER_EVIDENCE", source=source, target=source,
                     value={"owner": row[0], "confidence": row[1], "source_kind": row[2], "source_ref": row[3]},
                     location=row[3], extractor=EXTRACTOR, certainty="AUTHORITATIVE_REGISTRY" if row[1] == "HIGH" else "DETERMINISTIC",
                     revision=revision, source_hash=source_hash)
        count += 1
    rows = connection.execute("""SELECT ca.component_id,c.owner,c.title,ca.source_ref,ca.certainty
                                FROM component_assets ca JOIN components c ON c.component_id=ca.component_id
                                WHERE ca.asset_id=? AND c.current_state='CURRENT'""", (source["asset_id"],)).fetchall()
    for row in rows:
        _insert_fact(connection, fact_kind="COMPONENT_LINKAGE", source=source, target=source,
                     value={"component_id": row[0], "title": row[2], "owner": row[1], "source_ref": row[3]},
                     location=row[3], extractor=EXTRACTOR, certainty="DETERMINISTIC_SOURCE_RELATIONSHIP",
                     revision=revision, source_hash=source_hash)
        count += 1
    return count


def _reference_facts(connection, source: dict[str, Any], target: dict[str, Any], text: str, revision: str, source_hash: str, schema_id: str | None = None) -> int:
    needles = [target["current_path"], Path(target["current_path"]).name]
    if schema_id:
        needles.append(schema_id)
    needle = next((item for item in needles if item and item in text and item != source["current_path"]), None)
    if not needle:
        return 0
    if source["file_type"] == "test":
        kind, certainty = "TEST_REFERENCE", "EXECUTABLE_TEST"
    elif source["file_type"] == "source" and source["extension"] == ".py":
        kind, certainty = "PYTHON_REFERENCE", "DERIVED_STATIC_ANALYSIS"
    elif source["file_type"] == "documentation":
        kind, certainty = "DOCUMENTATION_REFERENCE", "CURRENT_DOCUMENTATION"
    else:
        kind, certainty = "SOURCE_REFERENCE", "DETERMINISTIC_SOURCE_RELATIONSHIP"
    _insert_fact(connection, fact_kind=kind, source=source, target=target,
                 value={"reference": needle}, location=_line_for(text, needle), extractor=EXTRACTOR,
                 certainty=certainty, revision=revision, source_hash=source_hash)
    return 1


def _python_structure_facts(connection, source: dict[str, Any], text: str, revision: str, source_hash: str) -> int:
    count = 0
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from ") and " import " in stripped:
            _insert_fact(connection, fact_kind="PYTHON_IMPORT", source=source, target=None,
                         value={"statement": stripped}, location=f"line:{number}", extractor=EXTRACTOR,
                         certainty="DERIVED_STATIC_ANALYSIS", revision=revision, source_hash=source_hash)
            count += 1
        match = re.match(r"(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", stripped) or re.match(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if match:
            _insert_fact(connection, fact_kind="PYTHON_DEFINITION", source=source, target=None,
                         value={"name": match.group(1)}, location=f"line:{number}", extractor=EXTRACTOR,
                         certainty="DERIVED_STATIC_ANALYSIS", revision=revision, source_hash=source_hash)
            count += 1
    return count


def _migration_self_facts(connection, source: dict[str, Any], text: str, revision: str, source_hash: str) -> int:
    """Extract only explicit, low-risk migration metadata from a migration asset."""
    if not source["current_path"].startswith("migrations/"):
        return 0
    count = 0

    def add(kind: str, value: Any, location: str) -> None:
        nonlocal count
        _insert_fact(
            connection, fact_kind=kind, source=source, target=source, value=value,
            location=location, extractor=EXTRACTOR, certainty="DERIVED_STATIC_ANALYSIS",
            revision=revision, source_hash=source_hash,
        )
        count += 1

    add("MIGRATION_CLASSIFICATION", "MIGRATION", "governed-scope:migrations")
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        document = None
    if isinstance(document, dict):
        for key, kind in (
            ("migration_id", "MIGRATION_ID"),
            ("schema_version", "MIGRATION_SCHEMA_VERSION"),
            ("purpose", "MIGRATION_PURPOSE"),
            ("applies_to", "MIGRATION_COMPONENT"),
        ):
            if isinstance(document.get(key), str):
                add(kind, document[key], f"json-pointer:/{key}")
        for index, action in enumerate(document.get("actions") or []):
            if isinstance(action, str):
                add("MIGRATION_TRANSFORMATION", action, f"json-pointer:/actions/{index}")
        if isinstance(document.get("destructive"), bool):
            add(
                "MIGRATION_DESTRUCTIVE_DECLARATION",
                {"declared": document["destructive"], "not_a_safety_proof": True},
                "json-pointer:/destructive",
            )
        return count

    current = re.search(r"current migration is version\s+(\d+)", text, re.I)
    if current:
        add("MIGRATION_VERSION_CURRENT", int(current.group(1)), _line_for(text, current.group(0)) or "text")
    schema_range = re.search(r"estate_knowledge_store_v(\d+)\.schema\.json`?\s+through\s+`?data/schemas/estate_knowledge_store_v(\d+)\.schema\.json", text, re.I)
    if schema_range:
        add("MIGRATION_SCHEMA_RANGE", {"first": int(schema_range.group(1)), "last": int(schema_range.group(2))}, _line_for(text, schema_range.group(0)) or "text")
    for match in re.finditer(r"Migration\s+(\d+)\s+(.+?)(?=Migration\s+\d+|A database with|$)", text.replace("\n", " "), re.I):
        add("MIGRATION_ORDER_RELATIONSHIP", {"version": int(match.group(1)), "description": " ".join(match.group(2).split()).rstrip(". ")}, f"migration:{match.group(1)}")
    for module in re.findall(r"`(estate\.core\.[A-Za-z0-9_]+)`", text):
        add("MIGRATION_LOADER", module, _line_for(text, module) or "text")
    return count


def _migration_store_facts(connection, base: Path, target: dict[str, Any], revision: str) -> int:
    """Link the documented SQLite migration map to its admitted source implementation."""
    if target["current_path"] != "migrations/estate_knowledge_store/README.md":
        return 0
    source = connection.execute("SELECT * FROM assets WHERE current_path='src/estate/core/estate_knowledge_store.py'").fetchone()
    if not source:
        return 0
    source = dict(source)
    path = base / source["current_path"]
    text = _read(path)
    if text is None:
        return 0
    source_hash = _file_hash(path)
    if source_hash != source["current_content_hash"] or source["current_state"] != "CURRENT":
        return 0
    try:
        tree = ast.parse(text)
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign) and any(isinstance(name, ast.Name) and name.id == "MIGRATIONS" for name in node.targets)
        )
        migrations = ast.literal_eval(assignment.value)
    except (SyntaxError, ValueError, StopIteration):
        return 0
    if not isinstance(migrations, dict):
        return 0
    count = 0

    def add(kind: str, value: Any, location: str) -> None:
        nonlocal count
        _insert_fact(
            connection, fact_kind=kind, source=source, target=target, value=value,
            location=location, extractor=EXTRACTOR, certainty="DERIVED_STATIC_ANALYSIS",
            revision=revision, source_hash=source_hash,
        )
        count += 1

    versions = sorted(version for version in migrations if isinstance(version, int))
    add("MIGRATION_LOADER", {"module": "estate.core.estate_knowledge_store", "map": "MIGRATIONS", "versions": versions}, "symbol:MIGRATIONS")
    for version in versions:
        sql = str(migrations[version])
        add("MIGRATION_SCHEMA_VERSION_TRANSITION", {"from": version - 1, "to": version}, f"MIGRATIONS[{version}]")
        for table in sorted(set(re.findall(r"(?:CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?|ALTER\s+TABLE)\s+[\"']?([A-Za-z_][A-Za-z0-9_]*)", sql, re.I))):
            add("MIGRATION_AFFECTED_TABLE", {"version": version, "table": table}, f"MIGRATIONS[{version}]")
        for index in sorted(set(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+[\"']?([A-Za-z_][A-Za-z0-9_]*)", sql, re.I))):
            add("MIGRATION_AFFECTED_INDEX", {"version": version, "index": index}, f"MIGRATIONS[{version}]")
    return count


def extract_evidence(root: str | Path | None = None, *, asset_ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Extract/update facts for selected assets using the existing inventory.

    The selected assets receive schema/ownership facts. Consumer relationships
    are found by reading only already-admitted source/test/documentation assets;
    no arbitrary filesystem traversal is performed.
    """
    context = validate_requested_scope(root)
    base = Path(context["root"])
    revision = context["source_revision"]
    started = time.perf_counter()
    with connect(base, create=False) as connection:
        fact_count_before = connection.execute("SELECT COUNT(*) FROM evidence_facts").fetchone()[0]
        targets = [row for row in _asset_rows(connection, asset_ids) if row["current_state"] != "MISSING"]
        target_paths = {row["current_path"] for row in targets}
        target_by_path = {row["current_path"]: row for row in targets}
        targets_with_ids = {row["asset_id"]: row for row in targets}
        source_rows = _asset_rows(connection)
        facts = 0
        relationships = 0
        for target in targets:
            target_path = base / target["current_path"]
            text = _read(target_path)
            if text is None:
                continue
            source_hash = _file_hash(target_path)
            connection.execute("UPDATE evidence_facts SET current_state='STALE',updated_at=? WHERE source_asset_id=? AND source_hash<>? AND current_state='CURRENT'", (_now(), target["asset_id"], source_hash))
            if target["file_type"] == "schema":
                facts += _schema_facts(connection, target, target, text, revision, source_hash)
            facts += _owner_and_component_facts(connection, target, revision, source_hash)
            facts += _migration_self_facts(connection, target, text, revision, source_hash)
            facts += _migration_store_facts(connection, base, target, revision)
        # A single admitted-inventory pass supplies reusable consumers for all selected targets.
        for source in source_rows:
            if source["current_path"] in target_paths or source["file_type"] in {"binary", "other"}:
                continue
            path = base / source["current_path"]
            text = _read(path)
            if text is None:
                continue
            source_hash = _file_hash(path)
            connection.execute("UPDATE evidence_facts SET current_state='STALE',updated_at=? WHERE source_asset_id=? AND source_hash<>? AND current_state='CURRENT'", (_now(), source["asset_id"], source_hash))
            if source["file_type"] == "source" and source["extension"] == ".py":
                facts += _python_structure_facts(connection, source, text, revision, source_hash)
            for target in targets:
                schema_id = None
                if target["file_type"] == "schema":
                    try:
                        schema = json.loads(_read(base / target["current_path"]) or "")
                        schema_id = str(schema.get("$id")) if isinstance(schema, dict) and schema.get("$id") else None
                    except json.JSONDecodeError:
                        schema_id = None
                relationships += _reference_facts(connection, source, target, text, revision, source_hash, schema_id)
        # Derived tags are independent of candidate/provider output.
        for target in targets:
            if target["file_type"] == "schema":
                source_hash = _file_hash(base / target["current_path"])
                _insert_fact(connection, fact_kind="TAG_DERIVATION", source=target, target=target,
                             value={"tag": "SCHEMA", "rule": "file_type=schema"}, location="inventory:file_type",
                             extractor=EXTRACTOR, certainty="DETERMINISTIC_SOURCE_RELATIONSHIP",
                             revision=revision, source_hash=source_hash)
                facts += 1
        fact_count_after = connection.execute("SELECT COUNT(*) FROM evidence_facts").fetchone()[0]
        return {"status": "READY", "facts_created_or_reused": facts, "facts_new": max(0, fact_count_after - fact_count_before),
                "facts_reused": max(0, facts - max(0, fact_count_after - fact_count_before)), "relationships_found": relationships,
                "assets": len(targets), "source_revision": revision, "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "database": str(database_path(base)), "canonical_mutation": False}


def _fact_rows(connection, *, asset_id: str | None = None, assertion_id: str | None = None) -> list[dict[str, Any]]:
    if assertion_id:
        return [dict(row) for row in connection.execute("""SELECT ef.*,ae.assertion_id,ae.relation
            FROM evidence_facts ef JOIN assertion_evidence ae ON ae.fact_id=ef.fact_id
            WHERE ae.assertion_id=? ORDER BY ef.fact_kind,ef.evidence_path""", (assertion_id,)).fetchall()]
    if asset_id:
        return [dict(row) for row in connection.execute("""SELECT * FROM evidence_facts
            WHERE (source_asset_id=? OR target_asset_id=?) ORDER BY fact_kind,evidence_path""", (asset_id, asset_id)).fetchall()]
    return [dict(row) for row in connection.execute("SELECT * FROM evidence_facts ORDER BY evidence_path,fact_kind").fetchall()]


def evidence_asset(root: str | Path | None, asset_id: str) -> dict[str, Any]:
    base = Path(validate_requested_scope(root)["root"])
    extract_evidence(base, asset_ids=[asset_id])
    with connect(base, create=False) as connection:
        facts = _fact_rows(connection, asset_id=asset_id)
    return {"asset_id": asset_id, "facts": facts, "fact_count": len(facts), "canonical_mutation": False}


def evidence_assertion(root: str | Path | None, assertion_id: str) -> dict[str, Any]:
    base = Path(validate_requested_scope(root)["root"])
    with connect(base, create=False) as connection:
        assertion = connection.execute("SELECT * FROM candidate_assertions WHERE assertion_id=?", (assertion_id,)).fetchone()
        if not assertion:
            raise ValueError(f"unknown assertion: {assertion_id}")
        facts = _fact_rows(connection, assertion_id=assertion_id)
    return {"assertion": dict(assertion), "facts": facts, "fact_count": len(facts), "canonical_mutation": False}


def link_facts(connection, assertion_id: str, fact_ids: Iterable[str], relation: str = "SUPPORTS") -> None:
    now = _now()
    connection.execute("DELETE FROM assertion_evidence WHERE assertion_id=?", (assertion_id,))
    connection.executemany("INSERT OR IGNORE INTO assertion_evidence(assertion_id,fact_id,relation,linked_at) VALUES(?,?,?,?)", [(assertion_id, fact_id, relation, now) for fact_id in fact_ids])


def corroboration_exceptions(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(validate_requested_scope(root)["root"])
    with connect(base, create=False) as connection:
        rows = [dict(row) for row in connection.execute("""SELECT assertion_id,asset_id,assertion_kind,proposed_value,
            corroboration_state,corroboration_reason,evidence_strength,review_state
            FROM candidate_assertions WHERE corroboration_state IN
            ('NOT_CORROBORATED','CONTRADICTED','NOT_DETERMINISTICALLY_VERIFIABLE')
            ORDER BY updated_at,assertion_id""").fetchall()]
    return {"exceptions": rows, "exception_count": len(rows), "canonical_mutation": False}
