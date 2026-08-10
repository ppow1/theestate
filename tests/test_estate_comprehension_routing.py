from pathlib import Path

from estate.core import estate_comprehension_routing as routing
from estate.core.estate_knowledge_store import init_store, connect


def test_work_class_is_explicit_and_non_collapsing():
    assert routing.work_class("data/registry/services.json") == "REGISTRIES_CONTRACTS"
    assert routing.work_class("data/discovery/metrics.json") == "SIMPLE_CONFIGURATION"
    assert routing.work_class("schemas/troubleshooting/x.json") == "JSON_SCHEMA"
    assert routing.work_class("docs/readme.md") == "DOCUMENTATION"


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
