from pathlib import Path

from estate.core import estate_comprehension_routing as routing
from estate.core.estate_knowledge_store import init_store, connect


def test_work_class_is_explicit_and_non_collapsing():
    assert routing.work_class("data/registry/services.json") == "REGISTRIES_CONTRACTS"
    assert routing.work_class("data/discovery/metrics.json") == "SIMPLE_CONFIGURATION"
    assert routing.work_class("schemas/troubleshooting/x.json") == "JSON_SCHEMA"
    assert routing.work_class("docs/readme.md") == "DOCUMENTATION"
    assert routing.work_class("migrations/store/README.md") == "MIGRATIONS"


def test_registry_route_disallows_model_with_citation_failures(tmp_path, monkeypatch):
    init_store(tmp_path)

    def stats(_connection, model, cls):
        if model == "qwen3:8b":
            return {"attempts": 2, "valid": 0, "invalid_citations": 2, "timeouts": 0}
        return {"attempts": 2, "valid": 2, "invalid_citations": 0, "timeouts": 0}

    monkeypatch.setattr(routing, "_stats", stats)
    result = routing.select_route(tmp_path, "REGISTRIES_CONTRACTS")
    assert result["selected_model"] == "qwen3-coder:30b-qwencode-20k"
    assert any(row["state"] == "DISALLOWED_FOR_CLASS" for row in result["decisions"])
    with connect(tmp_path, create=False) as connection:
        assert connection.execute("SELECT COUNT(*) FROM comprehension_route_decisions").fetchone()[0] == 2


def test_route_status_is_readable_and_non_authoritative(tmp_path):
    init_store(tmp_path)
    result = routing.routing_status(tmp_path)
    assert result["canonical_mutation"] is False
    assert result["routes"] == []


def test_migration_route_uses_current_full_population_and_disallows_current_invalid_model(tmp_path, monkeypatch):
    init_store(tmp_path)
    with connect(tmp_path) as connection:
        for index, path in enumerate(("migrations/a.json", "migrations/store/README.md"), 1):
            connection.execute("INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,last_comprehended,source_kind,current_state,scope_policy,provider_content_allowed) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f"asset:{index}", path, "repo", "rev", f"blob:{index}", f"hash:{index}", "documentation", ".md", 1, "estate", "CLASSIFIED", "PARTIAL", None, None, None, "now", "now", "now", None, "DETERMINISTIC", "CURRENT", "STRUCTURAL_SCAN", 1))

    def stats(_connection, model, cls):
        common = {"attempts": 3, "valid": 1, "invalid_results": 2, "invalid_citations": 2, "timeouts": 0}
        if model == "qwen3:8b":
            return common | {"current_attempts": 2, "current_valid": 0, "current_invalid_results": 2, "current_invalid_citations": 2, "current_timeouts": 0, "current_valid_assets": 0}
        return common | {"attempts": 3, "valid": 2, "invalid_results": 1, "invalid_citations": 1, "current_attempts": 2, "current_valid": 2, "current_invalid_results": 0, "current_invalid_citations": 0, "current_timeouts": 0, "current_valid_assets": 2}

    monkeypatch.setattr(routing, "_stats", stats)
    result = routing.select_route(tmp_path, "MIGRATIONS")
    assert result["selected_model"] == "qwen3-coder:30b-qwencode-20k"
    states = {row["model"]: row["state"] for row in result["decisions"]}
    assert states == {"qwen3:8b": "DISALLOWED_FOR_CLASS", "qwen3-coder:30b-qwencode-20k": "PRIMARY"}
