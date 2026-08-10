import json

import estate.core.estate_deterministic_evidence as evidence
import estate.core.estate_knowledge_store as store
import estate.core.estate_comprehension_governance as governance

from test_estate_comprehension_governance import ROOT, _setup


def _add_consumer(connection):
    for asset_id, path, file_type, extension in (("asset:test-consumer", "docs/operations/troubleshooting/README.md", "documentation", ".md"), ("asset:test-python-consumer", "src/estate/core/estate_comprehension_worker.py", "source", ".py")):
        connection.execute(
            "INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,last_comprehended,source_kind,current_state,scope_policy,provider_content_allowed) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (asset_id, path, "https://github.com/ppow1/theestate.git", "rev-current", None, "consumer-hash", file_type, extension, 10, "estate_internal", "CLASSIFIED", "PARTIAL", None, None, None, "now", "now", "now", None, "DETERMINISTIC", "CURRENT", "STRUCTURAL_SCAN", 1),
        )


def test_schema_metadata_consumer_and_assertion_evidence_are_queryable(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(evidence, "database_path", lambda root=None: tmp_path / "projection.sqlite3")
    with store.connect(ROOT, create=False) as connection:
        _add_consumer(connection)
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    result = evidence.extract_evidence(ROOT, asset_ids=[asset_id])
    assert result["facts_created_or_reused"] >= 5
    assert result["relationships_found"] >= 1
    second = evidence.extract_evidence(ROOT, asset_ids=[asset_id])
    assert second["facts_created_or_reused"] == result["facts_created_or_reused"]
    assert second["facts_new"] == 0
    assert second["facts_reused"] == second["facts_created_or_reused"]
    with store.connect(ROOT, create=False) as connection:
        purpose_id = connection.execute("SELECT assertion_id FROM candidate_assertions WHERE assertion_kind='PURPOSE'").fetchone()[0]
    governance.corroborate(ROOT, assertion_ids=[purpose_id])
    detail = evidence.evidence_assertion(ROOT, purpose_id)
    assert detail["facts"]
    assert all(fact["certainty"] != "PROVIDER_INFERENCE" for fact in detail["facts"])
    assert any(fact["fact_kind"] == "SCHEMA_METADATA" for fact in detail["facts"])
    with store.connect(ROOT, create=False) as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence_facts WHERE fact_kind='PYTHON_IMPORT'").fetchone()[0] >= 1


def test_provider_tag_is_not_deterministic_evidence(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch, tags=("PROVIDER_ONLY",))
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    with store.connect(ROOT, create=False) as connection:
        assertion_id = connection.execute("SELECT assertion_id FROM candidate_assertions WHERE assertion_kind='DETERMINISTIC_TAG'").fetchone()[0]
    governance.corroborate(ROOT, assertion_ids=[assertion_id])
    detail = evidence.evidence_assertion(ROOT, assertion_id)
    assert detail["facts"] == []
    with store.connect(ROOT, create=False) as connection:
        assert connection.execute("SELECT corroboration_state FROM candidate_assertions WHERE assertion_id=?", (assertion_id,)).fetchone()[0] == "NOT_CORROBORATED"


def test_explicitly_contradicted_purpose_is_not_application_eligible(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    with store.connect(ROOT, create=False) as connection:
        candidate = json.loads(connection.execute("SELECT candidate_json FROM candidate_interpretations WHERE interpretation_id=?", (interpretation_id,)).fetchone()[0])
        candidate["purpose"] = "not a schema"
        connection.execute("UPDATE candidate_interpretations SET candidate_json=? WHERE interpretation_id=?", (json.dumps(candidate), interpretation_id))
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    with store.connect(ROOT, create=False) as connection:
        assertion_id = connection.execute("SELECT assertion_id FROM candidate_assertions WHERE assertion_kind='PURPOSE'").fetchone()[0]
    governance.corroborate(ROOT, assertion_ids=[assertion_id])
    with store.connect(ROOT, create=False) as connection:
        assert tuple(connection.execute("SELECT corroboration_state,application_state FROM candidate_assertions WHERE assertion_id=?", (assertion_id,)).fetchone()) == ("CONTRADICTED", "NOT_ELIGIBLE")


def test_evidence_fact_source_hash_is_revision_aware(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(evidence, "database_path", lambda root=None: tmp_path / "projection.sqlite3")
    evidence.extract_evidence(ROOT, asset_ids=[asset_id])
    monkeypatch.setattr(evidence, "_file_hash", lambda path: "changed-source-hash")
    evidence.extract_evidence(ROOT, asset_ids=[asset_id])
    with store.connect(ROOT, create=False) as connection:
        old_hashes = {row[0] for row in connection.execute("SELECT source_hash FROM evidence_facts WHERE current_state='STALE'")}
        assert old_hashes
        assert connection.execute("SELECT COUNT(*) FROM evidence_facts WHERE current_state='STALE'").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM evidence_facts WHERE current_state='CURRENT' AND source_hash='changed-source-hash'").fetchone()[0] > 0


def test_migration_evidence_exposes_explicit_metadata_and_store_transitions(tmp_path, monkeypatch):
    from estate.core.estate_population import governed_scan

    db = tmp_path / "projection.sqlite3"
    monkeypatch.setattr(store, "database_path", lambda root=None: db)
    monkeypatch.setattr(evidence, "database_path", lambda root=None: db)
    store.init_store(ROOT)
    governed_scan(ROOT, requested="migrations")
    governed_scan(ROOT, requested="src/estate/core/estate_knowledge_store.py")
    with store.connect(ROOT, create=False) as connection:
        json_asset = connection.execute("SELECT asset_id FROM assets WHERE current_path='migrations/WP-0545_provider_benchmark_backfill_v1.json'").fetchone()[0]
        readme_asset = connection.execute("SELECT asset_id FROM assets WHERE current_path='migrations/estate_knowledge_store/README.md'").fetchone()[0]
    evidence.extract_evidence(ROOT, asset_ids=[json_asset, readme_asset])
    with store.connect(ROOT, create=False) as connection:
        json_kinds = {row[0] for row in connection.execute("SELECT fact_kind FROM evidence_facts WHERE target_asset_id=? AND current_state='CURRENT'", (json_asset,))}
        readme_kinds = {row[0] for row in connection.execute("SELECT fact_kind FROM evidence_facts WHERE target_asset_id=? AND current_state='CURRENT'", (readme_asset,))}
    assert {"MIGRATION_CLASSIFICATION", "MIGRATION_ID", "MIGRATION_PURPOSE", "MIGRATION_COMPONENT", "MIGRATION_TRANSFORMATION", "MIGRATION_DESTRUCTIVE_DECLARATION"} <= json_kinds
    assert {"MIGRATION_VERSION_CURRENT", "MIGRATION_SCHEMA_RANGE", "MIGRATION_ORDER_RELATIONSHIP", "MIGRATION_LOADER", "MIGRATION_SCHEMA_VERSION_TRANSITION", "MIGRATION_AFFECTED_TABLE", "MIGRATION_AFFECTED_INDEX"} <= readme_kinds
