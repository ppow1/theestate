from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from estate.core import canonical_webui_gateway_runtime as runtime


def config(tmp_path: Path) -> dict:
    source = Path(__file__).parents[1]
    database = tmp_path / "data" / "webui.db"
    database.parent.mkdir()
    sqlite3.connect(database).close()
    return {
        "schema_version": "estate.canonical-webui-gateway.v1",
        "source_root": str(source),
        "gateway": {"host": "127.0.0.1", "active_port": 11435, "candidate_port": 11436, "health_path": "/v1/models", "expected_model": "estate/grace", "python": "python", "module": "estate.cli.main"},
        "open_webui": {"host": "127.0.0.1", "active_port": 8080, "candidate_port": 8081, "executable": "open-webui.exe", "working_directory": str(tmp_path), "data_dir": str(database.parent), "database": str(database), "version": "0.10.2", "health_path": "/", "expected_model": "estate/grace-grounded-test", "expected_base_model": "estate/grace"},
        "state_root": str(tmp_path / "state"),
        "bridge_deployment_version": "estate-openwebui-grace-bridge.v1",
    }


def test_mismatched_inherited_state_override_fails_closed(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    value = config(tmp_path)
    path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///wrong.db")
    with pytest.raises(runtime.RuntimeControlError, match="DATABASE_URL"):
        runtime.load_config(path)


def test_canonical_inherited_state_is_accepted(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    value = config(tmp_path)
    path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str((tmp_path / "data").resolve()))
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str((tmp_path / "data" / "webui.db").resolve().as_posix()))
    monkeypatch.setenv("PYTHONPATH", str((Path(__file__).parents[1] / "src").resolve()))
    assert runtime.load_config(path)["source_root"] == value["source_root"]


def test_process_command_contains_explicit_canonical_state(tmp_path):
    value = config(tmp_path)
    value["open_webui"]["secret_key_file"] = str(tmp_path / "secret")
    (tmp_path / "secret").write_text("test-secret", encoding="utf-8")
    _, _, environment = runtime._process_command(value, runtime.SLOTS["blue"])
    assert environment["DATA_DIR"] == str((tmp_path / "data").resolve())
    assert environment["DATABASE_URL"] == "sqlite:///" + str((tmp_path / "data" / "webui.db").resolve().as_posix())
    assert environment["PYTHONPATH"] == str((Path(__file__).parents[1] / "src").resolve())


def test_gateway_semantic_readiness_requires_grace(monkeypatch, tmp_path):
    value = config(tmp_path)
    monkeypatch.setattr(runtime, "_http_json", lambda url: (200, {"data": [{"id": "estate/grace", "estate": {"resident_id": "grace", "resident_gateway_capable": True, "privileged_actions_enabled": False}}]}))
    result = runtime.gateway_readiness(value, runtime.SLOTS["blue"])
    assert result["ready"] is True
    monkeypatch.setattr(runtime, "_http_json", lambda url: (200, {"data": []}))
    assert runtime.gateway_readiness(value, runtime.SLOTS["blue"])["ready"] is False


def test_webui_semantic_readiness_requires_admin_and_bridge(monkeypatch, tmp_path):
    value = config(tmp_path)
    monkeypatch.setattr(runtime, "_http_status", lambda url: 200)
    monkeypatch.setattr(runtime, "_sqlite_identity", lambda database: {"quick_check": "ok", "users": [("1", "Pat", "p@example.com", "admin")], "models": [("estate/grace-grounded-test", "Grace", "estate/grace", json.dumps({"toolIds": ["grace_runtime_bridge"], "filterIds": ["grace_runtime_grounding"]}))], "tools": [("grace_runtime_bridge", "Grace")], "functions": [("grace_runtime_grounding", "Grounding", 1, 0)]})
    assert runtime.webui_readiness(value, runtime.SLOTS["blue"])["ready"] is True


def test_invalid_candidate_cannot_replace_active_slot(tmp_path, monkeypatch):
    value = config(tmp_path)
    state, active_path, manifests = runtime._state_paths(value)
    runtime._write_json(active_path, {"active_slot": "blue", "schema_version": "estate.runtime-promotion.v1"})
    runtime._write_json(manifests / "green.json", {"validation_status": "failed"})
    with pytest.raises(runtime.RuntimeControlError, match="validated"):
        runtime.promote(value, "green")
    assert json.loads(active_path.read_text(encoding="utf-8"))["active_slot"] == "blue"


def test_promotion_and_rollback_preserve_shared_state(tmp_path, monkeypatch):
    value = config(tmp_path)
    _, active_path, manifests = runtime._state_paths(value)
    manifest = {"validation_status": "validated", "source_commit": "a" * 40, "state_identity": {"database": str(Path(value["open_webui"]["database"]))}}
    runtime._write_json(manifests / "blue.json", manifest)
    runtime._write_json(manifests / "green.json", manifest)
    runtime._write_json(active_path, {"schema_version": "estate.runtime-promotion.v1", "active_slot": "blue"})
    monkeypatch.setattr(runtime, "gateway_readiness", lambda *args: {"ready": True})
    monkeypatch.setattr(runtime, "webui_readiness", lambda *args: {"ready": True})
    monkeypatch.setattr(runtime, "stop_slot", lambda *args: {"terminated_pids": []})
    monkeypatch.setattr(runtime, "start_slot", lambda *args, **kwargs: {"source_commit": "a" * 40, "state_identity": manifest["state_identity"], "validation": {"gateway": {"ready": True}, "webui": {"ready": True}}})
    promoted = runtime.promote(value, "green")
    assert promoted["active_slot"] == "green"
    rolled_back = runtime.rollback(value)
    assert rolled_back["active_slot"] == "blue"
    assert rolled_back["state_identity"]["database"] == manifest["state_identity"]["database"]


def test_status_rejects_stale_process_record_even_when_ports_are_semantically_ready(tmp_path, monkeypatch):
    value = config(tmp_path)
    root, active_path, _ = runtime._state_paths(value)
    runtime._write_json(active_path, {"schema_version": "estate.runtime-promotion.v1", "active_slot": "blue"})
    runtime._write_json(root / "blue-processes.json", {"slot_id": "blue", "pids": [101, 202], "started_at": runtime.utc_now()})
    monkeypatch.setattr(runtime, "_process_snapshot", lambda pid: None)
    monkeypatch.setattr(runtime, "gateway_readiness", lambda *args: {"ready": True})
    monkeypatch.setattr(runtime, "webui_readiness", lambda *args: {"ready": True})
    result = runtime.status(value)
    assert result["runtime"]["processes_match"] is False
    assert result["runtime"]["healthy"] is False
    assert result["runtime"]["state"] == "degraded"


def test_process_identity_rejects_gateway_from_wrong_command_root(tmp_path):
    slot = runtime.SLOTS["blue"]
    snapshot = {
        "CommandLine": r"C:\Python314\python.exe -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435",
        "ExecutablePath": r"C:\Python314\python.exe",
    }
    assert runtime._identity_matches(snapshot, slot, "gateway") is True
    assert runtime._identity_matches({**snapshot, "CommandLine": "python unrelated-service --port 11435"}, slot, "gateway") is False
