import importlib.util
from pathlib import Path

from estate.core.grace_momentum_service import FakeGraceMomentumService, GraceMomentumClient, TEST_IDENTITIES, production_http_server, reference_command
from estate.core.grace_runtime_bridge import GraceRuntimeBridge


def test_bridge_exposes_only_read_operations_and_no_record_is_explicit(tmp_path):
    bridge = GraceRuntimeBridge(GraceMomentumClient(FakeGraceMomentumService(tmp_path), TEST_IDENTITIES["grace"]))
    discovered = bridge.list_grace_runtime_operations()
    assert discovered["status"] == "AUTHORITATIVE_RESULT"
    assert "get_current_objective" in discovered["payload"]["operations"]
    assert discovered["payload"]["mutations_exposed"] is False
    assert bridge.get_current_objective()["status"] == "NO_RECORD"


def test_bridge_current_objective_is_runtime_selected_not_prompt_derived(tmp_path):
    service = FakeGraceMomentumService(tmp_path)
    service.command(reference_command("objective.create_or_correlate", objective_id="persisted-objective", idempotency_key="objective"), TEST_IDENTITIES["grace"])
    bridge = GraceRuntimeBridge(GraceMomentumClient(service, TEST_IDENTITIES["grace"]))
    result = bridge.get_current_objective()
    assert result["status"] == "AUTHORITATIVE_RESULT"
    assert result["payload"]["objective_id"] == "persisted-objective"
    assert "prompt" not in result["payload"]


def test_loopback_bridge_reads_runtime_queries_without_file_access(tmp_path):
    service = FakeGraceMomentumService(tmp_path)
    service.command(reference_command("objective.create_or_correlate", objective_id="http-objective", idempotency_key="objective"), TEST_IDENTITIES["grace"])
    server = production_http_server(service, port=0, authentication_issuer="issuer")
    server_thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        from estate.core.grace_momentum_service import LoopbackGraceMomentumClient
        client = LoopbackGraceMomentumClient(f"http://127.0.0.1:{server.server_port}", {"iss":"issuer", "sub":"grace", "office":"Grace", "authority_source":"test", "active":True})
        bridge = GraceRuntimeBridge(client)
        assert bridge.get_runtime_readiness()["status"] == "AUTHORITATIVE_RESULT"
        assert bridge.get_current_objective()["payload"]["objective_id"] == "http-objective"
        assert bridge.get_replay_cursor()["payload"]["next_cursor"] >= 1
    finally:
        server.shutdown(); server.server_close(); server_thread.join(timeout=2)


def test_openwebui_tool_has_registered_read_only_operations_and_loopback_guard():
    path = Path(__file__).parents[1] / "deploy" / "openwebui" / "tools" / "grace_runtime_bridge.py"
    spec = importlib.util.spec_from_file_location("grace_runtime_bridge_tool", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    tool = module.Tools()
    names = [name for name in dir(tool) if name.startswith("get_") or name.startswith("list_")]
    assert "get_current_objective" in names
    assert not any(name in names for name in ("send", "execute", "dispatch", "complete", "authorize"))
    tool.valves.runtime_url = "http://127.0.0.1.evil:8766"
    assert tool.get_runtime_readiness({})["status"] == "RUNTIME_UNAVAILABLE"
