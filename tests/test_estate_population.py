import json
from pathlib import Path

import pytest

from estate.core.estate_population import (
    PopulationScopeError,
    _relative,
    _within_requested,
    load_scope,
    resolve_entry,
    validate_requested_scope,
)
import estate.core.estate_knowledge_store as store


ROOT = Path(__file__).resolve().parents[1]


def test_governed_scope_contract_has_explicit_sensitive_policies():
    scope = load_scope(ROOT)
    assert scope["scope_id"] == "ESTATE.REPOSITORY.GOVERNED.V1"
    policies = {entry["pattern"]: entry["policy"] for entry in scope["entries"]}
    assert policies["runtime"] == "EXCLUDED"
    assert policies["data"] == "METADATA_ONLY"
    assert policies["archive"] == "NO_CONTENT"
    assert policies["src"] == "STRUCTURAL_SCAN"
    assert resolve_entry(scope, "docs/operations/troubleshooting/generated/index.html")["policy"] == "EXCLUDED"


@pytest.mark.parametrize("value", ["C:\\", "A:\\other-project", "../other", "src/../../other"])
def test_scope_path_escape_fails_closed(value):
    with pytest.raises(PopulationScopeError):
        _relative(value)


def test_requested_scope_must_be_admitted_and_repository_root_is_verified():
    context = validate_requested_scope(ROOT, "src/estate/diagnostics")
    assert context["scope_id"] == "ESTATE.REPOSITORY.GOVERNED.V1"
    with pytest.raises(PopulationScopeError):
        validate_requested_scope(ROOT, "runtime")
    with pytest.raises(PopulationScopeError):
        validate_requested_scope(ROOT, "not-an-admitted-sibling")


def test_bounded_missing_detection_does_not_cross_requested_scope():
    assert _within_requested("src/estate/core/worker.py", "src/estate/core")
    assert not _within_requested("docs/README.md", "src/estate/core")


def test_batch_packet_contains_bounded_revision_grounded_evidence(tmp_path, monkeypatch):
    from estate.core.estate_population import _hash, batch_packet

    db = tmp_path / "projection.sqlite3"
    monkeypatch.setattr(store, "database_path", lambda root=None: db)
    store.init_store(ROOT)
    asset_id = "asset:packet-test"
    path = "docs/operations/troubleshooting/diagnostic-impact-packet.schema.json"
    content_hash = _hash(ROOT / path)
    with store.connect(ROOT) as connection:
        connection.execute("INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,last_comprehended,source_kind,current_state,scope_policy,provider_content_allowed) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (asset_id, path, "repo", "rev", None, content_hash, "schema", ".json", 10, "estate", "CLASSIFIED", "PARTIAL", None, None, None, "now", "now", "now", None, "DETERMINISTIC", "CURRENT", "STRUCTURAL_SCAN", 1))
        connection.execute("INSERT INTO comprehension_batches(batch_id,scope_id,source_revision,selection_reason,created_at,updated_at,provider_type,provider_model,worker_identity,state,attempt_count) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ("batch:packet-test", "scope", "rev", "test", "now", "now", "local_ai", "qwen3:8b", "test", "ASSIGNED", 0))
        connection.execute("INSERT INTO comprehension_batch_assets(batch_id,asset_id,position) VALUES(?,?,?)", ("batch:packet-test", asset_id, 0))
        connection.execute("INSERT INTO evidence_facts(fact_id,fact_kind,source_asset_id,target_asset_id,value_json,evidence_path,evidence_location,source_revision,source_hash,extractor,certainty,current_state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("fact:packet-test", "SCHEMA_METADATA", asset_id, asset_id, json.dumps({"key": "title", "value": "Estate Diagnostic Impact Packet"}), path, "json-pointer:/title", "rev", content_hash, "test", "DETERMINISTIC", "CURRENT", "now", "now"))
    packet = batch_packet(ROOT, "batch:packet-test", evidence_limit=1, evidence_bytes=4096)
    assert packet["packet_version"] == "estate.troubleshooting.comprehension.work_packet.v2"
    assert packet["evidence_fact_ids"] == ["fact:packet-test"]
    assert packet["assets"][0]["deterministic_evidence"][0]["evidence_fact_id"] == "fact:packet-test"
    assert "content" in packet["assets"][0]
    assert _within_requested("docs/README.md", None)
