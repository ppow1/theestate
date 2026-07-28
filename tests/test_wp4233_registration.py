import importlib.util
from pathlib import Path

from estate.core.openwebui_resident_surface import resident_model_catalog
from estate.core.resident_gateway import chat_completion


def _load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def test_grace_model_is_the_only_resident_associated_with_bridge():
    models = resident_model_catalog()["data"]
    grace = next(item for item in models if item["id"] == "estate/grace")
    others = [item for item in models if item["id"] != "estate/grace"]
    assert grace["info"]["meta"]["toolIds"] == ["grace_runtime_bridge"]
    assert grace["info"]["meta"]["filterIds"] == ["grace_runtime_grounding"]
    assert all(not item["info"]["meta"]["toolIds"] and not item["info"]["meta"]["filterIds"] for item in others)


def test_deployment_merges_bridge_ids_without_duplicates():
    module = _load(Path(__file__).parents[1] / "scripts/deploy_openwebui_grace_bridge.py")
    merged = module.merge_grace_bridge_metadata({"toolIds": ["existing"], "filterIds": ["existing-filter"]})
    assert merged["toolIds"] == ["existing", "grace_runtime_bridge"]
    assert merged["filterIds"] == ["existing-filter", "grace_runtime_grounding"]
    assert module.merge_grace_bridge_metadata(merged) == merged


def test_grounding_filter_requires_runtime_result_for_operational_claims():
    module = _load(Path(__file__).parents[1] / "deploy/openwebui/functions/grace_runtime_grounding.py")
    filter_ = module.Filter()
    body = {"messages": [{"role": "user", "content": "What is the current readiness?"}]}
    filter_.inlet(body)
    assert body["metadata"]["estate_runtime_grounding_required"] is True
    body["messages"].append({"role": "assistant", "content": "invented readiness"})
    filter_.outlet(body)
    assert body["messages"][-1]["content"].startswith("I cannot state operational runtime facts")


def test_grounding_filter_leaves_conversation_only_turns_unchanged():
    module = _load(Path(__file__).parents[1] / "deploy/openwebui/functions/grace_runtime_grounding.py")
    filter_ = module.Filter(); body = {"messages": [{"role": "user", "content": "Tell me a short story."}]}
    filter_.inlet(body); body["messages"].append({"role": "assistant", "content": "story"}); filter_.outlet(body)
    assert body["messages"][-1]["content"] == "story"


def test_grace_gateway_uses_runtime_bridge_for_operational_questions(tmp_path, monkeypatch):
    from estate.core.grace_momentum_service import FakeGraceMomentumService, TEST_IDENTITIES, production_http_server
    import threading
    service = FakeGraceMomentumService(tmp_path)
    server = production_http_server(service, port=0, authentication_issuer="estate-control")
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    monkeypatch.setenv("ESTATE_GRACE_MOMENTUM_URL", f"http://127.0.0.1:{server.server_port}")
    try:
        code, body = chat_completion({"model": "estate/grace", "messages": [{"role": "user", "content": "Return current objective as raw JSON."}]}, root=tmp_path)
        assert code == 200
        assert body["estate"]["authoritative_runtime"] is True
        assert '"status": "NO_RECORD"' in body["choices"][0]["message"]["content"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_grace_gateway_routes_explicit_readiness_operation_name(tmp_path, monkeypatch):
    from estate.core.grace_momentum_service import FakeGraceMomentumService, TEST_IDENTITIES, production_http_server
    import threading
    service = FakeGraceMomentumService(tmp_path)
    server = production_http_server(service, port=0, authentication_issuer="estate-control")
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    monkeypatch.setenv("ESTATE_GRACE_MOMENTUM_URL", f"http://127.0.0.1:{server.server_port}")
    try:
        code, body = chat_completion({"model": "estate/grace", "messages": [{"role": "user", "content": "Use get_runtime_readiness and return the complete result."}]}, root=tmp_path)
        assert code == 200
        assert body["estate"]["runtime_status"] == "AUTHORITATIVE_RESULT"
        assert '"source_operation": "get_runtime_readiness"' in body["choices"][0]["message"]["content"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
