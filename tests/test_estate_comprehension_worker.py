import json
from pathlib import Path

import pytest

from estate.core.estate_comprehension_worker import _estate_result_id, _extract_json, _quality, difficulty_for, provider_status
from estate.core.estate_population import PopulationScopeError, validate_result


def test_provider_status_is_truthful_and_has_no_authority():
    class Fake:
        def __init__(self, *args, **kwargs):
            pass
        def discover_models(self):
            return {"available": True, "provider": "ollama", "endpoint": "http://127.0.0.1:11434", "models": ["qwen3:8b"], "model": "qwen3:8b", "discovery": "test"}
    import estate.core.estate_comprehension_worker as worker
    old = worker.LocalOllamaAdapter
    worker.LocalOllamaAdapter = Fake
    try:
        result = provider_status()
    finally:
        worker.LocalOllamaAdapter = old
    assert result["available"] is True
    assert result["canonical_authority"] is False
    assert result["scope_authority"] == "Estate deterministic population tooling"


def test_malformed_provider_json_fails_closed():
    with pytest.raises(ValueError):
        _extract_json("I do not know enough to produce structured output")


def test_quality_downgrades_unsupported_certainty_without_evidence():
    packet = {"assets": [{"asset_id": "asset:1"}]}
    payload = {"items": [{"asset_id": "asset:1", "purpose": "certain fact", "evidence_refs": []}]}
    quality, reasons = _quality(payload, packet)
    assert quality == "PARTIAL_CANDIDATE"
    assert reasons


def test_result_with_invented_asset_or_path_is_rejected(tmp_path):
    from estate.core.estate_knowledge_store import init_store, connect
    from estate.core.estate_population import governed_scan, next_batch, batch_packet
    root = Path(__file__).resolve().parents[1]
    init_store(tmp_path)
    # Use a real governed scope in a test root by creating only the contract and a source file.
    scope_dir = tmp_path / "docs/operations/troubleshooting"
    scope_dir.mkdir(parents=True)
    (tmp_path / "docs/operations/troubleshooting/population-scope.json").write_text((root / "docs/operations/troubleshooting/population-scope.json").read_text(), encoding="utf-8")
    (scope_dir / "sample.md").write_text("known evidence\n", encoding="utf-8")
    # This assertion specifically covers the deterministic validator contract.
    with pytest.raises(PopulationScopeError):
        validate_result(tmp_path, {"contract": "estate.troubleshooting.comprehension.result.v1", "result_id": "r", "batch_id": "missing", "source_revision": "x", "provider": {"type": "local_ai", "worker_identity": "w"}, "items": [{"asset_id": "invented", "path": "C:/secret"}]})


def test_difficulty_is_deterministic():
    assert difficulty_for({"assets": [{"path": "docs/readme.md"}]}) == "LEVEL_1"
    assert difficulty_for({"assets": [{"path": "src/estate/core/worker.py"}]}) == "LEVEL_2"
    assert difficulty_for({"assets": [{"path": "src/estate/diagnostics/x.py"}]}) == "LEVEL_3"
    assert difficulty_for({"assets": [{"path": "collaboration/parking_lot/old.md"}]}) == "LEVEL_4"


def test_estate_result_identity_is_batch_scoped_and_provider_id_independent():
    payload = {"source_revision": "rev", "items": [{"asset_id": "asset:1"}], "result_id": "model-placeholder"}
    assert _estate_result_id("batch:one", payload) != _estate_result_id("batch:two", payload)
